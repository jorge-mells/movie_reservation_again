from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import FastAPI, Request
from fastapi.security import OAuth2PasswordBearer
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlmodel import Session, create_engine, select

from models import Admin


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///test_db.sqlite"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 30 * 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SECRET_KEY: str
    FASTAPI_ENV: str = "production"
    ADMIN_USERNAME: str | None = None
    ADMIN_PASSWORD: str | None = None
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
    SQLAlchemyInstrumentor().instrument(engine=engine, skip_dep_check=True)
    app.state.engine = engine
    session = Session(app.state.engine)
    if settings.FASTAPI_ENV == "development":
        settings.ADMIN_USERNAME = "admin"
        settings.ADMIN_PASSWORD = "admin"
        from scripts.generate_data import generate_all_data

        generate_all_data(session)
    await bootstrap_admin(session, settings)
    session.commit()
    session.close()
    yield
    app.state.engine.dispose()


async def get_db(request: Request) -> AsyncIterator[Session]:
    session = Session(request.app.state.engine)
    try:
        yield session
    finally:
        session.commit()
        session.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", scheme_name="UserOAuth2")

admin_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/admin/login", scheme_name="AdminOAuth2"
)


async def bootstrap_admin(session: Session, settings: Settings) -> None:
    assert settings.ADMIN_USERNAME is not None
    assert settings.ADMIN_PASSWORD is not None
    existing = session.exec(
        select(Admin).where(Admin.username == settings.ADMIN_USERNAME)
    ).first()

    if existing:
        return

    from services.auth import AuthService

    await AuthService(session, settings, True).create_user(
        settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD
    )
