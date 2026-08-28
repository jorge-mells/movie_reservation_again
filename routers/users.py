from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from models.users import AuthRequest, Token, User, UserBase, UserCreate, UserResponse
from services.users import UserService, get_user_service
from utils.utils import get_settings, oauth2_scheme

router = APIRouter(tags=["Authentication"])


@router.post("/login")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> Token:
    settings = get_settings()
    user = user_service.authenticate_user(form_data.username, form_data.password)
    if not isinstance(user, UserBase):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)
    access_token = user_service.create_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = user_service.create_token(
        data={"sub": user.username}, expires_delta=refresh_token_expires
    )
    _ = await user_service.update_user(user.username, None, None, refresh_token)
    return Token(
        refresh_token=refresh_token, access_token=access_token, token_type="bearer"
    )


@router.post("/logout")
async def logout_current_session(
    data: AuthRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> dict[str, str]:
    username = await user_service.validate_refresh_token(data.refresh_token)
    _ = await user_service.update_user(username, None, None, "")
    return {"message": "logged out successfully"}


@router.post("/refresh")
async def refresh_current_session(
    data: AuthRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> Token:
    settings = get_settings()
    username = await user_service.validate_refresh_token(data.refresh_token)
    access_token_expires = timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)
    access_token = user_service.create_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = user_service.create_token(
        data={"sub": username}, expires_delta=refresh_token_expires
    )
    _ = await user_service.update_user(username, None, None, refresh_token)
    return Token(
        refresh_token=refresh_token, access_token=access_token, token_type="bearer"
    )


@router.post("/register", response_model=UserResponse)
async def create_new_user(
    data: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserBase:
    user = await user_service.create_user(data.username, data.password)
    return user


@router.get("/users/me", response_model=UserResponse)
async def read_users_me(
    user_service: Annotated[UserService, Depends(get_user_service)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    user = await user_service.get_current_user(token)
    assert isinstance(user, User)  # to silence the typechecker
    return user
