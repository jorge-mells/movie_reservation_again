import os
import tempfile
from collections.abc import Generator
from time import sleep

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient

from alembic import command
from main import app
from utils.utils import get_settings


@pytest.fixture(autouse=True)
def _run_migrations_and_setup(  # pyright: ignore[reportUnusedFunction]
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None]:
    db_fd, db_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(db_fd)

    test_db_url = f"sqlite:///{db_path}"

    monkeypatch.setenv("DATABASE_URL", test_db_url)
    monkeypatch.setenv(
        "SECRET_KEY", "075dceedeae24b879c14191991d80e2c9bd5035834391d4985adab81cfb055d2"
    )
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_SECONDS", "5")

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    yield

    get_settings.cache_clear()

    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture(scope="function")
def client(_run_migrations_and_setup: None) -> Generator[TestClient]:
    with TestClient(app) as c:
        yield c


def test_correct_auth_flow(client: TestClient) -> None:
    response = client.post(
        "/login", data={"username": "testuser1", "password": "testuser1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    # access protected route
    token = data["access_token"]
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "username": "testuser1",
        "refresh_token": data["refresh_token"],
    }

    # logout
    refresh_token = data["refresh_token"]
    response = client.post("/logout", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert response.json() == {"message": "logged out successfully"}

    # test unauthorized access to protected route
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_incorrect_login(client: TestClient) -> None:
    response = client.post(
        "/login", data={"username": "testuser2", "password": "testuser3"}
    )
    assert response.status_code == 401

    # test unauthorized access to protected route
    response = client.get("/users/me", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401

    # test invalid logout
    response = client.post("/logout", json={"refresh_token": "invalid_refresh_token"})
    assert response.status_code == 401

    # test invalid refresh
    response = client.post("/refresh", json={"refresh_token": "invalid_refresh_token"})
    assert response.status_code == 401


def test_refresh_token(client: TestClient) -> None:
    response = client.post(
        "/login", data={"username": "testuser2", "password": "testuser2"}
    )
    data = response.json()
    old_token = data["access_token"]
    old_refresh_token = data["refresh_token"]

    # test unauthorized access to protected route because of token expiry
    sleep(6)
    response = client.get("/users/me", headers={"Authorization": f"Bearer {old_token}"})
    assert response.status_code == 401

    # test refreshing token
    response = client.post("/refresh", json={"refresh_token": old_refresh_token})
    assert response.status_code == 200

    # test new token works
    data = response.json()
    new_token = data["access_token"]
    new_refresh_token = data["refresh_token"]
    response = client.get("/users/me", headers={"Authorization": f"Bearer {new_token}"})
    assert response.status_code == 200

    # test invalid logout with old refresh token
    response = client.post("/logout", json={"refresh_token": old_refresh_token})
    assert response.status_code == 401

    # logout with new refresh token
    response = client.post("/logout", json={"refresh_token": new_refresh_token})
    assert response.status_code == 200

    # test unauthorized access to protected route
    response = client.get("/users/me", headers={"Authorization": f"Bearer {new_token}"})
    assert response.status_code == 401


def test_register_flow(client: TestClient) -> None:
    # register nonexistent user
    response = client.post(
        "/register",
        json={"username": "testuser3", "password": "gremium-random-really-not"},
    )
    assert response.status_code == 200

    # login
    response = client.post(
        "/login",
        data={"username": "testuser3", "password": "gremium-random-really-not"},
    )
    assert response.status_code == 200
    data = response.json()

    # access protected route
    token = data["access_token"]
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    # logout
    refresh_token = data["refresh_token"]
    response = client.post("/logout", json={"refresh_token": refresh_token})
    assert response.status_code == 200

    # test unauthorized access to protected route
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_various_failed_register_login_scenarios(client: TestClient) -> None:
    # register exiting user
    response = client.post(
        "/register",
        json={"username": "testuser2", "password": "gremium-random-really-not"},
    )
    assert response.status_code == 409

    # register user with weak password
    response = client.post(
        "/register",
        json={"username": "testuser2", "password": "abc"},
    )
    assert response.status_code == 422
    data = response.json()
    error = data["detail"][0]
    assert "Weak password" in error["msg"]

    # login nonexistent user
    response = client.post(
        "/login",
        data={"username": "testuser3", "password": "gremium-random-really-not"},
    )
    assert response.status_code == 401
