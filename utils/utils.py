from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import FastAPI, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlmodel import Session, create_engine

from scripts.generate_data import generate_concrete_users


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///test_db.sqlite"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SECRET_KEY: str
    model_config = SettingsConfigDict(env_file=".env")


# ensures the settings object is created once. Use this to get settings
@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg] # pyright: ignore[reportCallIssue]


# add stuff that should be run here once. If they have state place that in app.state
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL, echo=True)
    app.state.engine = engine
    # BUG: remove this in prod or add a prod variable for it!!
    session = Session(app.state.engine)
    generate_concrete_users(session)
    yield
    app.state.engine.dispose()


async def get_db(request: Request) -> AsyncIterator[Session]:
    session = Session(request.app.state.engine)
    try:
        yield session
    finally:
        session.commit()
        session.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
