from collections.abc import Generator

import pytest
from sqlmodel import Session, SQLModel, create_engine

from scripts.generate_data import (
    generate_concrete_movies,
    generate_concrete_reservations,
    generate_concrete_seats,
    generate_concrete_showtimes,
)
from services.reservations import ReservationService
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


def test_get_movies(session: Session) -> None:
    expected_movies = generate_concrete_movies(session)
    reservation_service = ReservationService(session)
    movies = reservation_service.get_movies()
    assert movies[0] == expected_movies[0]


def test_get_showtimes_correct(session: Session) -> None:
    possible_showtimes = generate_concrete_showtimes(session)
    reservation_service = ReservationService(session)
    actual_showtimes = reservation_service.get_showtimes(2)
    expected_showtimes = possible_showtimes[2:4]
    assert expected_showtimes == actual_showtimes


def test_get_showtimes_invalid_id(session: Session) -> None:
    generate_concrete_showtimes(session)
    reservation_service = ReservationService(session)
    actual_showtimes = reservation_service.get_showtimes(4)
    assert actual_showtimes == []
    actual_showtimes = reservation_service.get_showtimes(-1)
    assert actual_showtimes == []


def test_get_seats_correct(session: Session) -> None:
    # test having all seats unreserved
    generate_concrete_showtimes(session)
    possible_seats = generate_concrete_seats(session)
    reservation_service = ReservationService(session)
    actual_seats = reservation_service.get_seats(2)
    expected_seats = possible_seats[4:]
    assert actual_seats == expected_seats

    # test having some seats reserved
    # make sure to reserve some seats for this to work out
    generate_concrete_reservations(session)
    possible_seats = generate_concrete_seats(session)
    reservation_service = ReservationService(session)
    actual_seats = reservation_service.get_seats(1)
    expected_seats = possible_seats[2:4]
    assert actual_seats == expected_seats


def test_get_seats_invalid_id(session: Session) -> None:
    generate_concrete_reservations(session)
    reservation_service = ReservationService(session)
    actual_seats = reservation_service.get_seats(10)
    assert actual_seats == []


def test_get_reservations_correct(session: Session) -> None:
    # unfortunately you have to build the reservation response manually
    possible_reservations = generate_concrete_reservations(session)
    reservation_service = ReservationService(session)
    expected_reservations = possible_reservations[0:2]
    actual_reservations = reservation_service.get_reservations(1)
    assert actual_reservations == expected_reservations


def test_get_reservations_invalid_id(session: Session) -> None:
    generate_concrete_reservations(session)
    reservation_service = ReservationService(session)
    actual_reservations = reservation_service.get_reservations(4)
    assert actual_reservations == []


def test_get_reserved_seats_correct(session: Session) -> None:
    possible_seats = generate_concrete_seats(session)
    generate_concrete_reservations(session)
    reservation_service = ReservationService(session)
    actual_reserved_seats = reservation_service.get_reserved_seats(1)
    expected_reserved_seats = [possible_seats[0]]
    assert expected_reserved_seats == actual_reserved_seats


def test_get_reserved_seats_invalid(session: Session) -> None:
    generate_concrete_reservations(session)
    reservation_service = ReservationService(session)
    actual_reserved_seats = reservation_service.get_reserved_seats(10)
    assert [] == actual_reserved_seats


def test_get_reserved_showtimes_correct(session: Session) -> None:
    possible_showtimes = generate_concrete_showtimes(session)
    generate_concrete_reservations(session)
    reservation_service = ReservationService(session)
    actual_reserved_showtimes = reservation_service.get_reserved_showtimes(1)
    expected_reserved_showtimes = [possible_showtimes[0], possible_showtimes[3]]
    assert actual_reserved_showtimes == expected_reserved_showtimes


def test_get_reserved_showtimes_invalid(session: Session) -> None:
    generate_concrete_reservations(session)
    reservation_service = ReservationService(session)
    actual_reserved_showtimes = reservation_service.get_reserved_showtimes(4)
    assert actual_reserved_showtimes == []


def test_create_reservation_correct(session: Session) -> None:
    generate_concrete_reservations(session)
    reservation_service = ReservationService(session)
    reservation_service.create_reservation(1, 4, 5)
    assert True


def test_create_reservation_invalid(session: Session) -> None:
    generate_concrete_reservations(session)
    reservation_service = ReservationService(session)

    # NOTE: it might make sense to separate these later on
    # but since they're all not doing anything, I've combined them.

    # test seat-theater mismatch
    with pytest.raises(ServiceError) as excinfo:
        reservation_service.create_reservation(1, 4, 4)
        assert "seat must match" in str(excinfo.value).lower()

    # test nonexistent user
    with pytest.raises(ServiceError) as excinfo:
        reservation_service.create_reservation(4, 4, 4)
        assert "user does not exist" in str(excinfo.value).lower()

    # test nonexistent showtime
    with pytest.raises(ServiceError) as excinfo:
        reservation_service.create_reservation(1, 10, 4)
        assert "showtime does not exist" in str(excinfo.value).lower()

    # test nonexistent seat
    with pytest.raises(ServiceError) as excinfo:
        reservation_service.create_reservation(1, 4, 10)
        assert "seat does not exist" in str(excinfo.value).lower()

    # test already existing reservation
    with pytest.raises(ServiceError) as excinfo:
        reservation_service.create_reservation(1, 5, 2)
        assert "seat already been reserved" in str(excinfo.value).lower()
