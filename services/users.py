from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt
from fastapi import Depends, status
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlmodel import Session, select

from models.users import Admin, TokenData, User, UserBase
from utils.exceptions import ServiceError
from utils.utils import Settings, get_db, get_settings


class UserService:
    password_hash = PasswordHash.recommended()
    DUMMY_HASH = password_hash.hash("dummypassword")

    def __init__(self, db: Session, settings: Settings, is_admin: bool = False) -> None:
        self.db = db
        self.settings = settings
        self.is_admin = is_admin

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.password_hash.verify(plain_password, hashed_password)

    def _get_password_hash(self, password: str) -> str:
        return self.password_hash.hash(password)

    def get_user(self, username: str | None) -> UserBase | None:
        cls = Admin if self.is_admin else User
        return self.db.exec(select(cls).where(cls.username == username)).one_or_none()

    def authenticate_user(self, username: str, password: str) -> bool | UserBase:
        user = self.get_user(username)
        if not user:
            self._verify_password(password, self.DUMMY_HASH)
            return False
        if not self._verify_password(password, user.hashed_password):
            return False
        return user

    async def update_user(
        self,
        username: str,
        new_username: str | None,
        password: str | None,
        refresh_token: str | None,
    ) -> UserBase:
        cls = Admin if self.is_admin else User
        user = self.db.exec(select(cls).where(cls.username == username)).one_or_none()
        if not user:
            raise ServiceError(
                status_code=status.HTTP_409_CONFLICT, detail="user does not exist"
            )
        if password:
            user.hashed_password = self._get_password_hash(password)
        if refresh_token:
            user.refresh_token = refresh_token
        if new_username:
            user.username = new_username
        self.db.commit()
        self.db.refresh(user)
        return user

    def create_token(
        self, data: dict[Any, Any], expires_delta: timedelta | None = None
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, self.settings.SECRET_KEY, algorithm=self.settings.ALGORITHM
        )
        return encoded_jwt

    async def get_current_user(self, token: str) -> UserBase:
        credentials_exception = ServiceError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        if not token:
            raise credentials_exception
        try:
            payload = jwt.decode(
                token, self.settings.SECRET_KEY, algorithms=[self.settings.ALGORITHM]
            )
            username = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except InvalidTokenError:
            raise credentials_exception
        user = self.get_user(username=token_data.username)
        if user is None:
            raise credentials_exception
        return user

    async def validate_refresh_token(self, token: str) -> str:  # return username
        credentials_exception = ServiceError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        if not token:
            raise credentials_exception
        try:
            payload = jwt.decode(
                token, self.settings.SECRET_KEY, algorithms=[self.settings.ALGORITHM]
            )
            username = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except InvalidTokenError:
            raise credentials_exception
        user = self.get_user(username=token_data.username)
        if user is None:
            raise credentials_exception

        if user.refresh_token != token:
            raise credentials_exception
        assert isinstance(username, str)
        return username

    async def create_user(self, username: str, password: str) -> UserBase:
        existing_user = self.get_user(username)
        if existing_user:
            raise ServiceError(
                status_code=status.HTTP_409_CONFLICT, detail="user already exists"
            )
        cls = Admin if self.is_admin else User
        hashed_password = self._get_password_hash(password)
        new_user = cls(username=username, hashed_password=hashed_password)
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user


def get_user_service(
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserService:
    return UserService(db, settings)


def get_admin_service(
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserService:
    return UserService(db, settings, True)
