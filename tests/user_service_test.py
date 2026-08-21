from collections.abc import Generator

import pytest
from sqlmodel import Session, SQLModel, create_engine

from scripts.generate_data import generate_concrete_users
from services.users import UserService
from utils.exceptions import ServiceError
from utils.utils import get_settings


@pytest.fixture
def session() -> Generator[Session]:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


async def test_valid_registration(session: Session) -> None:
    generate_concrete_users(session)
    user_service = UserService(session, get_settings(), False)
    expected_username = "testuser3"
    expected_password = "correct-tapestry-window-lantern-849"
    actual_user = await user_service.create_user(expected_username, expected_password)
    assert actual_user.id == 3
    assert actual_user.username == expected_username
    assert user_service._verify_password(expected_password, actual_user.hashed_password)


async def test_invalid_registration(session: Session) -> None:
    generate_concrete_users(session)
    user_service = UserService(session, get_settings(), False)
    username = "testuser2"
    password = "correct-tapestry-window-lantern-849"
    with pytest.raises(ServiceError, match="user already exists"):
        await user_service.create_user(username, password)
