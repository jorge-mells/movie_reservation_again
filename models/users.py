from pydantic import BaseModel, field_validator
from sqlmodel import Field, SQLModel
from zxcvbn import zxcvbn


class UserBase(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    hashed_password: str
    refresh_token: str = ""  # empty string denotes a logged out user


class User(UserBase, table=True):
    pass


class Admin(UserBase, table=True):
    pass


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class AuthRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    username: str
    refresh_token: str | None


class UserCreate(BaseModel):
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, password: str) -> str:
        results = zxcvbn(password)
        if results["score"] < 3:
            warning = results["feedback"]["warning"] or "Password is too guessable."
            suggestions = " ".join(results["feedback"]["suggestions"])
            raise ValueError(f"Weak password: {warning} {suggestions}")
        return password
