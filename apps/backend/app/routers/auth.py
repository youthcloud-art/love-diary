import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.deps import current_user
from app.models import User
from app.schemas import LoginIn, RegisterIn
from app.security import decode, hash_password, tokens, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


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

