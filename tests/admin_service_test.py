from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from sqlmodel import Session, SQLModel, create_engine

from scripts.generate_data import (
    generate_concrete_genres,
    generate_concrete_movies,
    generate_concrete_seats,
    generate_concrete_showtimes,
    generate_concrete_theaters,
)
from services.admin import AdminService
from utils.exceptions import ServiceError


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


# ── Theater ───────────────────────────────────────────────────────────────────


def test_create_theater(session: Session) -> None:
    service = AdminService(session)
    theater = service.create_theater("Theater 1")
    assert theater.name == "Theater 1"
    assert theater.id is not None


def test_create_theater_duplicate_name(session: Session) -> None:
    service = AdminService(session)
    service.create_theater("Theater 1")
    with pytest.raises(ServiceError) as excinfo:
        service.create_theater("Theater 1")
    assert "theater name already taken" in str(excinfo.value).lower()


def test_delete_theater(session: Session) -> None:
    service = AdminService(session)
    theater = service.create_theater("Theater 1")
    assert theater.id is not None
    service.delete_theater(theater.id)
    assert session.get(type(theater), theater.id) is None


def test_delete_theater_not_found(session: Session) -> None:
    service = AdminService(session)
    with pytest.raises(ServiceError) as excinfo:
        service.delete_theater(999)
    assert "theater not found" in str(excinfo.value).lower()


# ── Seats ─────────────────────────────────────────────────────────────────────


def test_create_seats(session: Session) -> None:
    theaters = generate_concrete_theaters(session)
    service = AdminService(session)
    assert theaters[0].id is not None
    seats = service.create_seats(theaters[0].id, 5)
    assert len(seats) == 5
    for seat in seats:
        assert seat.theater_id == theaters[0].id


def test_create_seats_zero(session: Session) -> None:
    theaters = generate_concrete_theaters(session)
    service = AdminService(session)
    assert theaters[0].id is not None
    seats = service.create_seats(theaters[0].id, 0)
    assert len(seats) == 0


def test_create_seats_negative(session: Session) -> None:
    theaters = generate_concrete_theaters(session)
    service = AdminService(session)
    with pytest.raises((ServiceError, ValueError)):
        assert theaters[0].id is not None
        service.create_seats(theaters[0].id, -1)


def test_delete_seat(session: Session) -> None:
    seats = generate_concrete_seats(session)
    service = AdminService(session)
    assert seats[0].id is not None
    service.delete_seat(seats[0].id)
    assert session.get(type(seats[0]), seats[0].id) is None


def test_delete_seat_not_found(session: Session) -> None:
    service = AdminService(session)
    with pytest.raises(ServiceError) as excinfo:
        service.delete_seat(999)
    assert "seat not found" in str(excinfo.value).lower()


# ── Genre ─────────────────────────────────────────────────────────────────────


def test_create_genre(session: Session) -> None:
    service = AdminService(session)
    genre = service.create_genre("Action")
    assert genre.name == "Action"
    assert genre.id is not None


def test_create_genre_duplicate_name(session: Session) -> None:
    service = AdminService(session)
    service.create_genre("Action")
    with pytest.raises(ServiceError) as excinfo:
        service.create_genre("Action")
    assert "genre name already taken" in str(excinfo.value).lower()


def test_delete_genre(session: Session) -> None:
    service = AdminService(session)
    genre = service.create_genre("Action")
    assert genre.id is not None
    service.delete_genre(genre.id)
    assert session.get(type(genre), genre.id) is None


def test_delete_genre_not_found(session: Session) -> None:
    service = AdminService(session)
    with pytest.raises(ServiceError) as excinfo:
        service.delete_genre(999)
    assert "genre not found" in str(excinfo.value).lower()


# ── Movie ─────────────────────────────────────────────────────────────────────


def test_create_movie(session: Session) -> None:
    service = AdminService(session)
    movie = service.create_movie(
        "Inception", "A mind-bending thriller", ["Action", "Sci-Fi"]
    )
    assert movie.name == "Inception"
    assert movie.description == "A mind-bending thriller"
    assert len(movie.genres) == 2
    assert {g.name for g in movie.genres} == {"Action", "Sci-Fi"}


def test_create_movie_new_genres_created(session: Session) -> None:
    service = AdminService(session)
    movie = service.create_movie("Test Movie", "desc", ["BrandNewGenre"])
    assert any(g.name == "BrandNewGenre" for g in movie.genres)


def test_create_movie_reuses_existing_genres(session: Session) -> None:
    genres = generate_concrete_genres(session)
    service = AdminService(session)
    movie = service.create_movie("Test Movie", "desc", [genres[0].name])
    assert movie.genres[0].id == genres[0].id


def test_create_movie_no_genres(session: Session) -> None:
    service = AdminService(session)
    movie = service.create_movie("Silent Film", "desc", [])
    assert movie.genres == []


def test_update_movie_name(session: Session) -> None:
    movies = generate_concrete_movies(session)
    service = AdminService(session)
    assert movies[0].id is not None
    updated = service.update_movie(movies[0].id, name="New Name")
    assert updated.name == "New Name"
    assert updated.description == movies[0].description


def test_update_movie_genres(session: Session) -> None:
    movies = generate_concrete_movies(session)
    service = AdminService(session)
    assert movies[0].id is not None
    updated = service.update_movie(movies[0].id, genre_names=["Horror"])
    assert len(updated.genres) == 1
    assert updated.genres[0].name == "Horror"


def test_update_movie_not_found(session: Session) -> None:
    service = AdminService(session)
    with pytest.raises(ServiceError) as excinfo:
        service.update_movie(999, name="Whatever")
    assert "movie not found" in str(excinfo.value).lower()


def test_delete_movie(session: Session) -> None:
    movies = generate_concrete_movies(session)
    service = AdminService(session)
    assert movies[0].id is not None
    service.delete_movie(movies[0].id)
    assert session.get(type(movies[0]), movies[0].id) is None


def test_delete_movie_not_found(session: Session) -> None:
    service = AdminService(session)
    with pytest.raises(ServiceError) as excinfo:
        service.delete_movie(999)
    assert "movie not found" in str(excinfo.value).lower()


# ── Showtime ──────────────────────────────────────────────────────────────────


def test_create_showtime(session: Session) -> None:
    movies = generate_concrete_movies(session)
    theaters = generate_concrete_theaters(session)
    service = AdminService(session)
    assert movies[0].id is not None
    assert theaters[0].id is not None
    showtime = service.create_showtime(
        movies[0].id,
        theaters[0].id,
        datetime(2026, 8, 1, 10, tzinfo=UTC),
        datetime(2026, 8, 1, 12, tzinfo=UTC),
    )
    assert showtime.movie_id == movies[0].id
    assert showtime.theater_id == theaters[0].id


def test_create_showtime_overlapping(session: Session) -> None:
    showtimes = generate_concrete_showtimes(session)
    service = AdminService(session)
    # showtime 1: theater 1, 2026-07-08 14:00-16:00 — overlap with same window
    with pytest.raises(ServiceError) as excinfo:
        service.create_showtime(
            showtimes[0].movie_id,
            showtimes[0].theater_id,
            datetime(2026, 7, 8, 15, tzinfo=UTC),
            datetime(2026, 7, 8, 17, tzinfo=UTC),
        )
    assert "overlaps" in str(excinfo.value).lower()


def test_create_showtime_adjacent_no_overlap(session: Session) -> None:
    showtimes = generate_concrete_showtimes(session)
    service = AdminService(session)
    # starts exactly when showtime 1 ends — should not overlap
    showtime = service.create_showtime(
        showtimes[0].movie_id,
        showtimes[0].theater_id,
        datetime(2026, 7, 8, 16, tzinfo=UTC),
        datetime(2026, 7, 8, 18, tzinfo=UTC),
    )
    assert showtime.id is not None


def test_create_showtime_different_theater_no_overlap(session: Session) -> None:
    showtimes = generate_concrete_showtimes(session)
    service = AdminService(session)
    # same time window but different theater — should be fine
    showtime = service.create_showtime(
        showtimes[2].movie_id,
        showtimes[1].theater_id,  # theater 2
        datetime(2026, 7, 8, 14, tzinfo=UTC),
        datetime(2026, 7, 8, 16, tzinfo=UTC),
    )
    assert showtime.id is not None


def test_update_showtime(session: Session) -> None:
    showtimes = generate_concrete_showtimes(session)
    movies = generate_concrete_movies(session)
    service = AdminService(session)
    assert showtimes[0].id is not None
    updated = service.update_showtime(showtimes[0].id, movie_id=movies[2].id)
    assert updated.movie_id == movies[2].id


def test_update_showtime_not_found(session: Session) -> None:
    service = AdminService(session)
    with pytest.raises(ServiceError) as excinfo:
        service.update_showtime(999, movie_id=1)
    assert "showtime not found" in str(excinfo.value).lower()


def test_update_showtime_overlapping(session: Session) -> None:
    showtimes = generate_concrete_showtimes(session)
    service = AdminService(session)
    # showtime 3 is in theater 1, 2026-07-09 10:00-12:00
    # try to move showtime 1 (theater 1, 2026-07-08 14:00-16:00) to overlap with it
    assert showtimes[0].id is not None
    with pytest.raises(ServiceError) as excinfo:
        service.update_showtime(
            showtimes[0].id,
            start_date=datetime(2026, 7, 9, 11, tzinfo=UTC),
            end_date=datetime(2026, 7, 9, 13, tzinfo=UTC),
        )
    assert "overlaps" in str(excinfo.value).lower()


def test_update_showtime_no_overlap(session: Session) -> None:
    showtimes = generate_concrete_showtimes(session)
    service = AdminService(session)
    # move showtime 1 to a time with no conflicts in theater 1
    assert showtimes[0].id is not None
    updated = service.update_showtime(
        showtimes[0].id,
        start_date=datetime(2026, 7, 11, 10, tzinfo=UTC),
        end_date=datetime(2026, 7, 11, 12, tzinfo=UTC),
    )
    assert updated.start_date == datetime(2026, 7, 11, 10, tzinfo=UTC)


def test_update_showtime_different_theater_no_conflict(session: Session) -> None:
    showtimes = generate_concrete_showtimes(session)
    service = AdminService(session)
    # move showtime 1 to theater 2 at a time that doesn't conflict there
    assert showtimes[0].id is not None
    updated = service.update_showtime(
        showtimes[0].id,
        theater_id=showtimes[1].theater_id,
        start_date=datetime(2026, 7, 11, 10, tzinfo=UTC),
        end_date=datetime(2026, 7, 11, 12, tzinfo=UTC),
    )
    assert updated.theater_id == showtimes[1].theater_id


def test_update_showtime_different_theater_with_conflict(session: Session) -> None:
    showtimes = generate_concrete_showtimes(session)
    service = AdminService(session)
    # move showtime 1 to theater 2 but overlap with showtime 2 there (10:00-12:00)
    assert showtimes[0].id is not None
    with pytest.raises(ServiceError) as excinfo:
        service.update_showtime(
            showtimes[0].id,
            theater_id=showtimes[1].theater_id,
            start_date=datetime(2026, 7, 8, 10, tzinfo=UTC),
            end_date=datetime(2026, 7, 8, 12, tzinfo=UTC),
        )
    assert "overlaps" in str(excinfo.value).lower()


def test_delete_showtime(session: Session) -> None:
    showtimes = generate_concrete_showtimes(session)
    service = AdminService(session)
    assert showtimes[0].id is not None
    service.delete_showtime(showtimes[0].id)
    assert session.get(type(showtimes[0]), showtimes[0].id) is None


def test_delete_showtime_not_found(session: Session) -> None:
    service = AdminService(session)
    with pytest.raises(ServiceError) as excinfo:
        service.delete_showtime(999)
    assert "showtime not found" in str(excinfo.value).lower()


def test_get_showtimes(session: Session) -> None:
    expected = generate_concrete_showtimes(session)
    service = AdminService(session)
    actual = service.get_showtimes()
    assert len(actual) == len(expected)
