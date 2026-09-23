import httpx
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.deps import current_user
from app.models import User
from app.schemas import LoginIn, PhoneBase, PhoneCodeLoginIn, PhonePasswordLoginIn, PhoneRegisterIn, RegisterIn
from app.security import decode, hash_password, tokens, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
verification_codes: dict[str, tuple[str, datetime]] = {}


def phone_email(phone: str) -> str:
    """Map phone accounts onto the existing unique account field for compatibility."""
    return f"{phone}@phone.love-diary.local"


def verify_code(phone: str, code: str) -> None:
    saved = verification_codes.get(phone)
    if not saved or saved[0] != code or saved[1] < datetime.now(timezone.utc):
        raise HTTPException(401, "验证码错误或已过期")
    verification_codes.pop(phone, None)


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
