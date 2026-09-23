from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Membership, User
from app.security import decode

bearer = HTTPBearer(auto_error=False)


def current_user(auth: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not auth:
        raise HTTPException(401, "未登录")
    try:
        user = db.get(User, decode(auth.credentials, "access"))
    except Exception:
        user = None
    if not user:
        raise HTTPException(401, "登录已过期")
    return user


def membership(user: User, db: Session) -> Membership:
    row = db.query(Membership).filter_by(user_id=user.id).first()
    if not row:
        raise HTTPException(409, "尚未加入双人空间")
    return row

