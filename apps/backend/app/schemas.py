from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterIn(BaseModel):
    nickname: str = Field(min_length=1, max_length=64)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class PhoneBase(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, value: str) -> str:
        phone = value.replace(" ", "")
        if len(phone) != 11 or not phone.isdigit() or not phone.startswith("1"):
            raise ValueError("请输入正确的 11 位手机号")
        return phone


class PhoneRegisterIn(PhoneBase):
    nickname: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=6, max_length=6)
    password: str = Field(min_length=6, max_length=128)


class PhonePasswordLoginIn(PhoneBase):
    password: str


class PhoneCodeLoginIn(PhoneBase):
    code: str = Field(min_length=6, max_length=6)


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
