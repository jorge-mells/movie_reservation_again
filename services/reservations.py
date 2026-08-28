from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends, status
from sqlmodel import Session, col, select

from models.reservations import Movie, Reservation, Seat, Showtime
from models.users import User
from utils.exceptions import ServiceError
from utils.utils import get_db


class ReservationService:
    def __init__(self, db: Session) -> None:
        self.db: Session = db

    def get_movies(self) -> Sequence[Movie]:
        movies = self.db.exec(select(Movie)).all()
        return movies

    def get_showtimes(self, movie_id: int) -> Sequence[Showtime]:
        showtimes = self.db.exec(
            select(Showtime).where(Showtime.movie_id == movie_id)
        ).all()
        return showtimes

    def get_seats(self, showtime_id: int) -> Sequence[Seat]:
        # select all seats that have not been reserved for the given showtime.
        statement = (
            select(Seat)
            .join(Showtime, col(Showtime.theater_id) == col(Seat.theater_id))
            .outerjoin(Reservation, (col(Reservation.seat_id) == col(Seat.id)))
            .where(Showtime.id == showtime_id)
            .where(col(Reservation.id).is_(None))
        )

        return self.db.exec(statement).all()

    def get_reservations(self, user_id: int) -> Sequence[Reservation]:
        results = self.db.exec(
            select(Reservation).where(Reservation.user_id == user_id)
        ).all()
        return results

    def get_reserved_seats(self, showtime_id: int) -> Sequence[Seat]:
        seats = self.db.exec(
            select(Seat)
            .join(Reservation, col(Reservation.seat_id) == col(Seat.id))
            .join(Showtime, col(Showtime.id) == col(Reservation.showtime_id))
            .where(Showtime.id == showtime_id)
        ).all()
        return seats

    def get_reserved_showtimes(self, user_id: int) -> Sequence[Showtime]:
        showtimes = self.db.exec(
            select(Showtime)
            .join(Reservation, col(Reservation.showtime_id) == col(Showtime.id))
            .where(Reservation.user_id == user_id)
        ).all()
        return showtimes

    def already_exists[T](self, cls: type[T], id: int, error_message: str) -> T:
        existing_item = self.db.get(cls, id)
        if not existing_item:
            raise ServiceError(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_message,
            )
        return existing_item

    def create_reservation(
        self, user_id: int, showtime_id: int, seat_id: int
    ) -> Reservation:
        existing_reservation = self.db.exec(
            select(Reservation).where(
                showtime_id == Reservation.showtime_id, seat_id == Reservation.seat_id
            )
        ).first()
        if existing_reservation:
            raise ServiceError(
                status_code=status.HTTP_409_CONFLICT,
                detail="This seat has already been reserved for the showtime provided",
            )
        _ = self.already_exists(User, user_id, "This user does not exist")
        existing_showtime = self.already_exists(
            Showtime, showtime_id, "This showtime does not exist"
        )
        existing_seat = self.already_exists(Seat, seat_id, "This seat already exists")
        if existing_seat.theater_id != existing_showtime.theater_id:
            raise ServiceError(
                status_code=status.HTTP_409_CONFLICT,
                detail="The seat must match the theater",
            )
        new_reservation = Reservation(
            user_id=user_id, showtime_id=showtime_id, seat_id=seat_id
        )
        self.db.add(new_reservation)
        self.db.commit()
        self.db.refresh(new_reservation)
        return new_reservation

    def delete_reservation(self, reservation_id: int) -> None:
        existing_reservation = self.already_exists(
            Reservation, reservation_id, "This reservation does not exist"
        )
        self.db.delete(existing_reservation)


def get_reservation_service(
    db: Annotated[Session, Depends(get_db)],
) -> ReservationService:
    return ReservationService(db)
