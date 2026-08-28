from fastapi.testclient import TestClient


def test_correct_reservation_finding(client: TestClient) -> None:
    # user checks movies
    response = client.get("/movies")
    assert response.status_code == 200

    # user selects second movie and checks showtimes
    response = client.get("/movies/2/showtimes")
    assert response.status_code == 200

    # user selects 1 showtime and checks seats
    response = client.get("/showtimes/1/seats")
    assert response.status_code == 200

    # user logs in to reserve a seat
    response = client.post(
        "/login", data={"username": "testuser1", "password": "testuser1"}
    )
    token = response.json()["access_token"]

    # user reserves seat 3 for showtime 1
    response = client.post(
        "/users/me/reservations",
        json={"showtime_id": 1, "seat_id": 3},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    # user checks that their seat has been reserved
    response = client.get(
        "/users/me/reservations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_user_deletes_reservation(client: TestClient) -> None:
    # user logs in
    response = client.post(
        "/login", data={"username": "testuser1", "password": "testuser1"}
    )
    token = response.json()["access_token"]

    # user views all showtimes they've reserved
    response = client.get(
        "/users/me/reserved_showtimes", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # user views all seats they've reserved for showtime 1
    response = client.get(
        "/showtimes/1/reserved_seats", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # user decides to delete their reservation for showtime 1 seat 1(reservation_id = 1)
    response = client.delete(
        "/users/me/reservations/1", headers={"Authorization": f"Bearer {token}"}
    )

    # user checks that their reservation has been deleted
    response = client.get(
        "/users/me/reservations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_protected_paths(client: TestClient) -> None:
    # user tries to do the following but forgets to login and for some reason never does

    # user tries to view all showtimes they've reserved
    response = client.get("/users/me/reserved_showtimes")
    assert response.status_code == 401

    # user tries to view all seats they've reserved for showtime 1
    response = client.get("/showtimes/1/reserved_seats")
    assert response.status_code == 401

    # user tries to decide to delete their reservation for showtime 1 seat 1(reservation_id = 1)
    response = client.delete("/users/me/reservations/1")
    assert response.status_code == 401

    # user tries to check that their reservation has been deleted
    response = client.get(
        "/users/me/reservations",
    )
    assert response.status_code == 401

    # user tries to create a reservation
    response = client.post(
        "/users/me/reservations",
        json={"showtime_id": 1, "seat_id": 3},
    )
    assert response.status_code == 401
