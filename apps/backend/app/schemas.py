from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    nickname: str = Field(min_length=1, max_length=64)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class EntryIn(BaseModel):
    title: str = Field(default="", max_length=120)
    body: str = ""
    mood: str = Field(default="", max_length=20)
    happened_on: date
    visibility: Literal["shared", "private"] = "shared"
    media_ids: list[str] = []


class EntryPatch(BaseModel):
    title: str
    body: str
    mood: str
    happened_on: date
    visibility: Literal["shared", "private"]
    media_ids: list[str] = []
    updated_at: datetime

