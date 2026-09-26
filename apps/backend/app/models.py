from datetime import date, datetime, timezone
from uuid import uuid4
from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    nickname: Mapped[str] = mapped_column(String(64))
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    wechat_openid: Mapped[str | None] = mapped_column(String(128), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class SocialIdentity(Base):
    __tablename__ = "social_identities"
    __table_args__ = (UniqueConstraint("provider", "provider_user_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    provider: Mapped[str] = mapped_column(String(16), index=True)
    provider_user_id: Mapped[str] = mapped_column(String(128))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    user: Mapped[User] = relationship()


class OAuthLoginSession(Base):
    __tablename__ = "oauth_login_sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    state: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(16), index=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    message: Mapped[str | None] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Space(Base):
    __tablename__ = "spaces"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(64), default="我们的日记")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("space_id", "user_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    space_id: Mapped[str] = mapped_column(ForeignKey("spaces.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    role: Mapped[str] = mapped_column(String(16), default="partner")
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    space: Mapped[Space] = relationship()
    user: Mapped[User] = relationship()


class Invite(Base):
    __tablename__ = "invites"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    code: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    space_id: Mapped[str] = mapped_column(ForeignKey("spaces.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(default=False)


class Entry(Base):
    __tablename__ = "entries"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    space_id: Mapped[str] = mapped_column(ForeignKey("spaces.id"), index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(120), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    mood: Mapped[str] = mapped_column(String(20), default="")
    happened_on: Mapped[date] = mapped_column(Date, index=True)
    visibility: Mapped[str] = mapped_column(String(16), default="shared")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    author: Mapped[User] = relationship()
    media: Mapped[list["Media"]] = relationship(back_populates="entry")


class Media(Base):
    __tablename__ = "media"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    space_id: Mapped[str] = mapped_column(ForeignKey("spaces.id"))
    uploader_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    entry_id: Mapped[str | None] = mapped_column(ForeignKey("entries.id"))
    url: Mapped[str] = mapped_column(String(512))
    thumb_url: Mapped[str | None] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(64))
    entry: Mapped[Entry | None] = relationship(back_populates="media")
