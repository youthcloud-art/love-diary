import io
import json
import secrets
from urllib.parse import parse_qs, urlencode

import httpx
import qrcode
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.deps import current_user
from app.models import OAuthLoginSession, SocialIdentity, User
from app.schemas import LoginIn, PhoneBase, PhoneCodeLoginIn, PhonePasswordLoginIn, PhoneRegisterIn, RegisterIn
from app.security import decode, hash_password, tokens, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
verification_codes: dict[str, tuple[str, datetime]] = {}
OAUTH_SESSION_TTL = timedelta(minutes=5)


def phone_email(phone: str) -> str:
    """Map phone accounts onto the existing unique account field for compatibility."""
    return f"{phone}@phone.love-diary.local"


def verify_code(phone: str, code: str) -> None:
    saved = verification_codes.get(phone)
    if not saved or saved[0] != code or saved[1] < datetime.now(timezone.utc):
        raise HTTPException(401, "验证码错误或已过期")
    verification_codes.pop(phone, None)


def oauth_provider_config(provider: str) -> tuple[str, str, str]:
    callback = f"{settings.public_base_url.rstrip('/')}/api/v1/auth/oauth/{provider}/callback"
    if provider == "wechat":
        return settings.wechat_web_appid, settings.wechat_web_secret, callback
    if provider == "qq":
        return settings.qq_appid, settings.qq_secret, callback
    raise HTTPException(404, "不支持的扫码登录方式")


def oauth_authorize_url(provider: str, appid: str, callback: str, state: str) -> str:
    if provider == "wechat":
        query = urlencode({"appid": appid, "redirect_uri": callback, "response_type": "code", "scope": "snsapi_login", "state": state})
        return f"https://open.weixin.qq.com/connect/qrconnect?{query}#wechat_redirect"
    query = urlencode({"response_type": "code", "client_id": appid, "redirect_uri": callback, "state": state, "display": "pc"})
    return f"https://graph.qq.com/oauth2.0/authorize?{query}"


def social_user(db: Session, provider: str, provider_user_id: str, nickname: str) -> User:
    identity = db.query(SocialIdentity).filter_by(provider=provider, provider_user_id=provider_user_id).first()
    if identity:
        return identity.user
    user = User(nickname=nickname or ("微信恋人" if provider == "wechat" else "QQ恋人"))
    db.add(user); db.flush()
    db.add(SocialIdentity(provider=provider, provider_user_id=provider_user_id, user_id=user.id))
    db.commit(); db.refresh(user)
    return user


def exchange_oauth_code(provider: str, code: str, callback: str) -> tuple[str, str]:
    appid, secret, _ = oauth_provider_config(provider)
    try:
        if provider == "wechat":
            response = httpx.get("https://api.weixin.qq.com/sns/oauth2/access_token", params={"appid": appid, "secret": secret, "code": code, "grant_type": "authorization_code"}, timeout=10)
            result = response.json()
            if "openid" not in result:
                raise HTTPException(401, result.get("errmsg", "微信授权失败"))
            profile = httpx.get("https://api.weixin.qq.com/sns/userinfo", params={"access_token": result["access_token"], "openid": result["openid"], "lang": "zh_CN"}, timeout=10).json()
            return str(result["openid"]), str(profile.get("nickname") or "微信恋人")
        token_response = httpx.get("https://graph.qq.com/oauth2.0/token", params={"grant_type": "authorization_code", "client_id": appid, "client_secret": secret, "code": code, "redirect_uri": callback, "fmt": "json"}, timeout=10)
        try:
            token_result = token_response.json()
        except json.JSONDecodeError:
            token_result = {key: values[0] for key, values in parse_qs(token_response.text).items()}
        access_token = token_result.get("access_token")
        if not access_token:
            raise HTTPException(401, str(token_result.get("error_description") or "QQ 授权失败"))
        me = httpx.get("https://graph.qq.com/oauth2.0/me", params={"access_token": access_token, "fmt": "json"}, timeout=10).json()
        openid = me.get("openid")
        if not openid:
            raise HTTPException(401, str(me.get("error_description") or "无法获取 QQ 身份"))
        profile = httpx.get("https://graph.qq.com/user/get_user_info", params={"access_token": access_token, "oauth_consumer_key": appid, "openid": openid, "fmt": "json"}, timeout=10).json()
        return str(openid), str(profile.get("nickname") or "QQ恋人")
    except httpx.HTTPError as exc:
        raise HTTPException(502, "登录平台暂时不可用，请稍后重试") from exc


def oauth_session_expired(session: OAuthLoginSession) -> bool:
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < datetime.now(timezone.utc)


@router.post("/code")
def request_phone_code(data: PhoneBase):
    # Development sender. Connect an SMS provider before production deployment.
    code = "246810"
    verification_codes[data.phone] = (code, datetime.now(timezone.utc) + timedelta(minutes=5))
    payload = {"message": "验证码已发送，请在 5 分钟内使用"}
    if settings.secret_key.startswith("development-"):
        payload["dev_code"] = code
    return payload


@router.post("/phone/register")
def phone_register(data: PhoneRegisterIn, db: Session = Depends(get_db)):
    verify_code(data.phone, data.code)
    email = phone_email(data.phone)
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "该手机号已注册")
    user = User(nickname=data.nickname, email=email, password_hash=hash_password(data.password))
    db.add(user); db.commit(); db.refresh(user)
    return tokens(user.id)


@router.post("/phone/login")
def phone_password_login(data: PhonePasswordLoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=phone_email(data.phone)).first()
    if not user or not user.password_hash or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "手机号或密码错误")
    return tokens(user.id)


@router.post("/phone/code-login")
def phone_code_login(data: PhoneCodeLoginIn, db: Session = Depends(get_db)):
    verify_code(data.phone, data.code)
    user = db.query(User).filter_by(email=phone_email(data.phone)).first()
    if not user:
        raise HTTPException(404, "该手机号尚未注册")
    return tokens(user.id)


@router.post("/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "邮箱已注册")
    user = User(nickname=data.nickname, email=email, password_hash=hash_password(data.password))
    db.add(user); db.commit(); db.refresh(user)
    return tokens(user.id)


@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=data.email.lower()).first()
    if not user or not user.password_hash or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "邮箱或密码错误")
    return tokens(user.id)


@router.post("/wechat")
def wechat_login(data: dict, db: Session = Depends(get_db)):
    code = str(data.get("code", ""))
    if not code:
        raise HTTPException(422, "缺少 code")
    if settings.wechat_appid:
        response = httpx.get("https://api.weixin.qq.com/sns/jscode2session", params={"appid": settings.wechat_appid, "secret": settings.wechat_secret, "js_code": code, "grant_type": "authorization_code"}, timeout=8)
        result = response.json()
        if "openid" not in result:
            raise HTTPException(401, result.get("errmsg", "微信登录失败"))
        openid = result["openid"]
    else:
        if not code.startswith("dev-"):
            raise HTTPException(503, "开发环境请使用 dev- 开头的模拟 code")
        openid = f"mock:{code}"
    user = db.query(User).filter_by(wechat_openid=openid).first()
    if not user:
        user = User(nickname=str(data.get("nickname") or "恋人"), wechat_openid=openid)
        db.add(user); db.commit(); db.refresh(user)
    return tokens(user.id)


@router.post("/oauth/{provider}/start")
def start_oauth_qr(provider: str, db: Session = Depends(get_db)):
    appid, secret, callback = oauth_provider_config(provider)
    label = "微信" if provider == "wechat" else "QQ"
    if not appid or not secret:
        return {
            "provider": provider,
            "configured": False,
            "callback_url": callback,
            "message": f"请先在服务端配置 {label} 开放平台 AppID 和密钥",
        }
    db.query(OAuthLoginSession).filter(OAuthLoginSession.expires_at < datetime.now(timezone.utc)).delete(synchronize_session=False)
    session_id = secrets.token_urlsafe(32)
    state = secrets.token_urlsafe(32)
    authorization_url = oauth_authorize_url(provider, appid, callback, state)
    db.add(OAuthLoginSession(id=session_id, provider=provider, state=state, status="pending", expires_at=datetime.now(timezone.utc) + OAUTH_SESSION_TTL))
    db.commit()
    return {
        "provider": provider,
        "configured": True,
        "session_id": session_id,
        "authorization_url": authorization_url,
        "qr_image_url": f"{settings.public_base_url.rstrip('/')}/api/v1/auth/oauth/qr/{session_id}",
        "expires_in": int(OAUTH_SESSION_TTL.total_seconds()),
    }


@router.get("/oauth/qr/{session_id}")
def oauth_qr_image(session_id: str, db: Session = Depends(get_db)):
    session = db.get(OAuthLoginSession, session_id)
    if not session or oauth_session_expired(session):
        raise HTTPException(404, "二维码已过期")
    appid, _, callback = oauth_provider_config(session.provider)
    image = qrcode.make(oauth_authorize_url(session.provider, appid, callback, session.state))
    content = io.BytesIO()
    image.save(content, format="PNG")
    content.seek(0)
    return StreamingResponse(content, media_type="image/png", headers={"Cache-Control": "no-store"})


@router.get("/oauth/session/{session_id}")
def oauth_session_status(session_id: str, db: Session = Depends(get_db)):
    session = db.get(OAuthLoginSession, session_id)
    if not session:
        raise HTTPException(404, "扫码会话不存在或已过期")
    if oauth_session_expired(session):
        db.delete(session); db.commit()
        return {"status": "expired", "message": "二维码已过期，请刷新后重试"}
    if session.status == "authorized" and session.user_id:
        payload = {"status": "authorized", **tokens(session.user_id)}
        db.delete(session); db.commit()
        return payload
    if session.status == "error":
        return {"status": "error", "message": session.message or "登录失败"}
    return {"status": "pending"}


@router.get("/oauth/{provider}/callback", response_class=HTMLResponse)
def oauth_callback(provider: str, state: str = "", code: str = "", error: str = "", db: Session = Depends(get_db)):
    oauth_provider_config(provider)
    label = "微信" if provider == "wechat" else "QQ"
    session = db.query(OAuthLoginSession).filter_by(provider=provider, state=state).first()
    if not session or oauth_session_expired(session):
        return HTMLResponse("<meta charset='utf-8'><h2>登录会话已失效</h2><p>请回到电脑刷新二维码后重试。</p>", status_code=400)
    if error or not code:
        session.status = "error"; session.message = f"{label}授权已取消"; db.commit()
        return HTMLResponse(f"<meta charset='utf-8'><h2>{label}授权未完成</h2><p>请回到电脑后重试。</p>", status_code=400)
    try:
        _, _, callback = oauth_provider_config(provider)
        provider_user_id, nickname = exchange_oauth_code(provider, code, callback)
        user = social_user(db, provider, provider_user_id, nickname)
        session.status = "authorized"; session.user_id = user.id; db.commit()
    except HTTPException as exc:
        session.status = "error"; session.message = str(exc.detail); db.commit()
        return HTMLResponse(f"<meta charset='utf-8'><h2>{label}登录失败</h2><p>{exc.detail}</p>", status_code=exc.status_code)
    return HTMLResponse(f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{label}登录成功</title><style>body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#fff6f2;color:#604447;font-family:system-ui;text-align:center}}main{{padding:40px}}i{{display:grid;place-items:center;width:72px;height:72px;margin:auto;border-radius:50%;background:#43bd78;color:white;font-size:40px;font-style:normal}}</style><main><i>✓</i><h2>{label}登录成功</h2><p>请回到电脑，页面将自动完成登录。</p></main>""")


@router.post("/refresh")
def refresh(data: dict, db: Session = Depends(get_db)):
    try:
        user_id = decode(str(data.get("refresh_token", "")), "refresh")
    except Exception:
        raise HTTPException(401, "刷新令牌无效") from None
    if not db.get(User, user_id):
        raise HTTPException(401, "用户不存在")
    return tokens(user_id)


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "nickname": user.nickname, "email": user.email}
