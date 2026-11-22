from fastapi.testclient import TestClient


def get_admin_token(client: TestClient) -> str:
    response = client.post(
        "/admin/login", data={"username": "admin", "password": "admin"}
    )
    return str(response.json()["access_token"])


def test_admin_golden_path(client: TestClient) -> None:
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # create a theater
    response = client.post(
        "/admin/theaters", json={"name": "New Theater"}, headers=headers
    )
    assert response.status_code == 201
    theater_id = response.json()["id"]

    # add seats to it
    response = client.post(
        f"/admin/theaters/{theater_id}/seats",
        json={"num_seats": 10},
        headers=headers,
    )
    assert response.status_code == 201
    assert len(response.json()) == 10

    # create a movie
    response = client.post(
        "/admin/movies",
        json={
            "name": "New Movie",
            "description": "A great film",
            "genre_names": ["Action"],
        },
        headers=headers,
    )
    assert response.status_code == 201
    movie_id = response.json()["id"]

    # create a showtime for it
    response = client.post(
        "/admin/showtimes",
        json={
            "movie_id": movie_id,
            "theater_id": theater_id,
            "start_date": "2026-12-01T10:00:00Z",
            "end_date": "2026-12-01T12:00:00Z",
        },
        headers=headers,
    )
    assert response.status_code == 201
    showtime_id = response.json()["id"]

    # update the movie name
    response = client.patch(
        f"/admin/movies/{movie_id}",
        json={"name": "Updated Movie"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Movie"

    # delete the showtime
    response = client.delete(f"/admin/showtimes/{showtime_id}", headers=headers)
    assert response.status_code == 204

    # delete the theater
    response = client.delete(f"/admin/theaters/{theater_id}", headers=headers)
    assert response.status_code == 204


def test_protected_admin_paths(client: TestClient) -> None:
    response = client.post("/admin/theaters", json={"name": "Theater"})
    assert response.status_code == 401

    response = client.post(
        "/admin/movies",
        json={"name": "Movie", "description": "desc", "genre_names": []},
    )
    assert response.status_code == 401

    response = client.get("/admin/showtimes")
    assert response.status_code == 401

    response = client.delete("/admin/theaters/1")
    assert response.status_code == 401

    response = client.delete("/admin/movies/1")
    assert response.status_code == 401


def test_regular_user_cannot_access_admin_routes(client: TestClient) -> None:
    response = client.post(
        "/login", data={"username": "testuser1", "password": "testuser1"}
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/admin/theaters", json={"name": "Theater"}, headers=headers)
    assert response.status_code == 401

    response = client.get("/admin/showtimes", headers=headers)
    assert response.status_code == 401


def test_admin_conflict_errors(client: TestClient) -> None:
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # duplicate theater name
    response = client.post(
        "/admin/theaters", json={"name": "test theater 1"}, headers=headers
    )
    assert response.status_code == 400

    # duplicate genre name
    response = client.post("/admin/genres", json={"name": "action"}, headers=headers)
    assert response.status_code == 400

    # overlapping showtime
    response = client.post(
        "/admin/showtimes",
        json={
            "movie_id": 1,
            "theater_id": 1,
            "start_date": "2026-07-08T15:00:00Z",
            "end_date": "2026-07-08T17:00:00Z",
        },
        headers=headers,
    )
    assert response.status_code == 400


def test_admin_not_found_errors(client: TestClient) -> None:
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete("/admin/theaters/999", headers=headers)
    assert response.status_code == 404

    response = client.delete("/admin/movies/999", headers=headers)
    assert response.status_code == 404

    response = client.delete("/admin/showtimes/999", headers=headers)
    assert response.status_code == 404

    response = client.patch(
        "/admin/movies/999", json={"name": "whatever"}, headers=headers
    )
    assert response.status_code == 404
