from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    hashed_password: str


class User(UserBase, table=True):
    pass


class Admin(UserBase, table=True):
    pass


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
