from datetime import datetime, timedelta, timezone
from secrets import choice
from string import ascii_uppercase, digits
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import current_user, membership
from app.models import Invite, Membership, Space, User

router = APIRouter(prefix="/api/v1/spaces", tags=["spaces"])


def issue(db: Session, space_id: str) -> str:
    code = "".join(choice(ascii_uppercase + digits) for _ in range(6))
    db.add(Invite(code=code, space_id=space_id, expires_at=datetime.now(timezone.utc) + timedelta(days=3)))
    db.commit()
    return code


def output(db: Session, space: Space):
    members = db.query(Membership).filter_by(space_id=space.id).all()
    invite = db.query(Invite).filter_by(space_id=space.id, used=False).order_by(Invite.expires_at.desc()).first()
    return {"id": space.id, "name": space.name, "invite_code": invite.code if invite else None, "members": [{"user_id": m.user_id, "nickname": m.user.nickname, "role": m.role} for m in members]}


@router.get("/current")
def current(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return output(db, membership(user, db).space)


@router.post("")
def create(data: dict, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if db.query(Membership).filter_by(user_id=user.id).first():
        raise HTTPException(409, "已加入一个空间")
    space = Space(name=str(data.get("name") or "我们的日记"))
    db.add(space); db.flush(); db.add(Membership(space_id=space.id, user_id=user.id, role="owner")); db.commit()
    issue(db, space.id)
    return output(db, space)


@router.post("/join")
def join(data: dict, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if db.query(Membership).filter_by(user_id=user.id).first():
        raise HTTPException(409, "已加入一个空间")
    invite = db.query(Invite).filter_by(code=str(data.get("code", "")).upper(), used=False).first()
    now = datetime.now(timezone.utc)
    if not invite or (invite.expires_at.replace(tzinfo=timezone.utc) if invite.expires_at.tzinfo is None else invite.expires_at) < now:
        raise HTTPException(404, "邀请码无效或已过期")
    if db.query(Membership).filter_by(space_id=invite.space_id).count() >= 2:
        raise HTTPException(409, "空间已有两位成员")
    invite.used = True; db.add(Membership(space_id=invite.space_id, user_id=user.id)); db.commit()
    return output(db, db.get(Space, invite.space_id))


@router.post("/invite")
def invite(user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = membership(user, db)
    issue(db, m.space_id)
    return output(db, m.space)

