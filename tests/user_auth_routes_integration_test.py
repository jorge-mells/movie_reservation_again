from time import sleep

from fastapi.testclient import TestClient


def test_correct_auth_flow(client: TestClient) -> None:
    response = client.post(
        "/login", data={"username": "testuser1", "password": "testuser1"}
    )
    print(response.json())
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

    # test admin incorrectly logging in as user
    response = client.post("/login", data={"username": "admin1", "password": "admin1"})
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
