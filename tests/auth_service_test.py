from collections.abc import Generator
from datetime import timedelta

import pytest
from sqlmodel import Session, SQLModel, create_engine

from models.users import Admin, User, UserBase
from scripts.generate_data import generate_concrete_admins, generate_concrete_users
from services.auth import AuthService
from utils.exceptions import ServiceError
from utils.utils import Settings


@pytest.fixture
def settings() -> Settings:
    secret = "075dceedeae24b879c14191991d80e2c9bd5035834391d4985adab81cfb055d2"
    return Settings(SECRET_KEY=secret, DATABASE_URL="sqlite:///:memory:")


@pytest.fixture
def session(settings: Settings) -> Generator[Session]:
    engine = create_engine(settings.DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def user_auth_service(session: Session, settings: Settings) -> AuthService:
    generate_concrete_users(session)
    generate_concrete_admins(session)
    user_service = AuthService(session, settings, False)
    return user_service


@pytest.fixture
def admin_auth_service(session: Session, settings: Settings) -> AuthService:
    generate_concrete_users(session)
    generate_concrete_admins(session)
    admin_service = AuthService(session, settings, True)
    return admin_service


async def test_valid_user_registration(
    session: Session, user_auth_service: AuthService
) -> None:
    expected_username = "testuser3"
    expected_password = "correct-tapestry-window-lantern-849"
    expected_id = 3
    await user_auth_service.create_user(expected_username, expected_password)
    session.expire_all()
    actual_user = session.get(User, expected_id)
    assert actual_user is not None
    assert actual_user.username == expected_username
    assert user_auth_service.verify_password(
        expected_password, actual_user.hashed_password
    )


async def test_valid_admin_registration(
    session: Session, admin_auth_service: AuthService
) -> None:
    expected_username = "admin2"
    expected_password = "correct-tapestry-window-lantern-849"
    expected_id = 2
    await admin_auth_service.create_user(expected_username, expected_password)
    session.expire_all()
    actual_user = session.get(Admin, expected_id)
    assert actual_user is not None
    assert actual_user.username == expected_username
    assert admin_auth_service.verify_password(
        expected_password, actual_user.hashed_password
    )


async def test_user_admin_registration_scenarios(
    session: Session, user_auth_service: AuthService, admin_auth_service: AuthService
) -> None:
    # admin can reuse already used usernames
    expected_username = "testuser3"
    expected_password = "correct-tapestry-window-lantern-849"
    expected_id = 2
    await admin_auth_service.create_user(expected_username, expected_password)
    session.expire_all()
    actual_user: UserBase | None = session.get(Admin, expected_id)
    assert actual_user is not None
    assert actual_user.username == expected_username

    # users can reuse already used admin usernames
    expected_username = "admin1"
    expected_password = "correct-tapestry-window-lantern-849"
    expected_id = 3
    await user_auth_service.create_user(expected_username, expected_password)
    session.expire_all()
    actual_user = session.get(User, expected_id)
    assert actual_user is not None
    assert actual_user.username == expected_username


async def test_invalid_registration(
    user_auth_service: AuthService, admin_auth_service: AuthService
) -> None:
    username = "testuser2"
    password = "correct-tapestry-window-lantern-849"
    with pytest.raises(ServiceError, match="user already exists"):
        await user_auth_service.create_user(username, password)

    username = "admin1"
    password = "correct-tapestry-window-lantern-849"
    with pytest.raises(ServiceError, match="user already exists"):
        await admin_auth_service.create_user(username, password)


async def test_valid_user_username_update(
    session: Session, user_auth_service: AuthService
) -> None:
    expected_id = 1
    await user_auth_service.update_user("testuser1", "testuser3", None, None)
    session.expire_all()
    actual_user = session.get(User, expected_id)
    assert actual_user is not None
    assert actual_user.username == "testuser3"
    assert user_auth_service.verify_password("testuser1", actual_user.hashed_password)
    assert actual_user.refresh_token == ""


async def test_valid_admin_username_update(
    session: Session, admin_auth_service: AuthService
) -> None:
    expected_id = 1
    await admin_auth_service.update_user("admin1", "admin2", None, None)
    session.expire_all()
    actual_user = session.get(Admin, expected_id)
    assert actual_user is not None
    assert actual_user.username == "admin2"
    assert admin_auth_service.verify_password("admin1", actual_user.hashed_password)
    assert actual_user.refresh_token == ""


async def test_valid_user_password_update(
    session: Session, user_auth_service: AuthService
) -> None:
    expected_id = 2
    await user_auth_service.update_user("testuser2", None, "newpassword", None)
    session.expire_all()
    actual_user = session.get(User, expected_id)
    assert actual_user is not None
    assert actual_user.username == "testuser2"
    assert actual_user.refresh_token == ""
    assert user_auth_service.verify_password("newpassword", actual_user.hashed_password)


async def test_valid_admin_password_update(
    session: Session, admin_auth_service: AuthService
) -> None:
    # admin test
    expected_id = 1
    await admin_auth_service.update_user("admin1", None, "newpassword", None)
    session.expire_all()
    actual_user = session.get(Admin, expected_id)
    assert actual_user is not None
    assert actual_user.username == "admin1"
    assert actual_user.refresh_token == ""
    assert admin_auth_service.verify_password(
        "newpassword", actual_user.hashed_password
    )


async def test_valid_user_refresh_token_update(
    session: Session,
    settings: Settings,
    user_auth_service: AuthService,
) -> None:
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    expected_refresh_token = user_auth_service.create_token(
        data={"sub": "testuser2", "is_admin": False},
        expires_delta=refresh_token_expires,
    )
    await user_auth_service.update_user("testuser2", None, None, expected_refresh_token)
    expected_id = 2
    session.expire_all()
    actual_user = session.get(User, expected_id)
    assert actual_user is not None
    assert actual_user.username == "testuser2"
    actual_payload = await user_auth_service.validate_refresh_token(
        expected_refresh_token
    )
    assert actual_payload["sub"] == "testuser2"
    assert user_auth_service.verify_password("testuser2", actual_user.hashed_password)


async def test_valid_admin_refresh_token_update(
    session: Session,
    settings: Settings,
    admin_auth_service: AuthService,
) -> None:
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    expected_refresh_token = admin_auth_service.create_token(
        data={"sub": "admin1", "is_admin": True},
        expires_delta=refresh_token_expires,
    )
    await admin_auth_service.update_user("admin1", None, None, expected_refresh_token)
    expected_id = 1
    session.expire_all()
    actual_user = session.get(Admin, expected_id)
    assert actual_user is not None
    assert actual_user.username == "admin1"
    actual_payload = await admin_auth_service.validate_refresh_token(
        expected_refresh_token
    )
    assert actual_payload["sub"] == "admin1"
    assert admin_auth_service.verify_password("admin1", actual_user.hashed_password)


async def test_valid_username_password_update(
    session: Session, user_auth_service: AuthService
) -> None:
    expected_id = 2
    await user_auth_service.update_user("testuser2", "testuser3", "newpassword", None)
    session.expire_all()
    actual_user = session.get(User, expected_id)
    assert actual_user is not None
    assert actual_user.username == "testuser3"
    assert actual_user.refresh_token == ""
    assert user_auth_service.verify_password("newpassword", actual_user.hashed_password)


async def test_valid_all_info_update(
    session: Session, settings: Settings, user_auth_service: AuthService
) -> None:
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    expected_refresh_token = user_auth_service.create_token(
        data={"sub": "testuser3", "is_admin": False},
        expires_delta=refresh_token_expires,
    )
    await user_auth_service.update_user(
        "testuser2", "testuser3", "newpassword", expected_refresh_token
    )
    expected_id = 2
    session.expire_all()
    actual_user = session.get(User, expected_id)
    assert actual_user is not None
    assert actual_user.username == "testuser3"
    actual_payload = await user_auth_service.validate_refresh_token(
        expected_refresh_token
    )
    assert actual_payload["sub"] == "testuser3"
    assert user_auth_service.verify_password("newpassword", actual_user.hashed_password)


# NOTE: This is probably not the best way to test a lot of this functionality since you're' relying on internal service methods, but I currently can't think of a better way, so we'll leave it like this.
