from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import FastAPI, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlmodel import Session, create_engine


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///test_db.sqlite"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 30 * 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SECRET_KEY: str
    FASTAPI_ENV: str = "production"
    model_config = SettingsConfigDict(env_file=".env")


# ensures the settings object is created once. Use this to get settings
@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg] # pyright: ignore[reportCallIssue]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    echo = False
    if settings.FASTAPI_ENV == "development":
        echo = True
    engine = create_engine(settings.DATABASE_URL, echo=echo)
    app.state.engine = engine
    if settings.FASTAPI_ENV == "development":
        from scripts.generate_data import generate_concrete_reservations

        session = Session(app.state.engine)
        _ = generate_concrete_reservations(session)
    yield
    app.state.engine.dispose()


async def get_db(request: Request) -> AsyncIterator[Session]:
    session = Session(request.app.state.engine)
    try:
        yield session
    finally:
        session.commit()
        session.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
