from collections.abc import Sequence
from datetime import datetime
from typing import Annotated

from fastapi import Depends, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from models import Genre, Movie, Seat, Showtime, Theater
from utils.exceptions import ServiceError
from utils.utils import get_db


class AdminService:
    def __init__(self, db: Session) -> None:
        self.db: Session = db

    def create_theater(self, name: str) -> Theater:
        theater = Theater(name=name)
        try:
            self.db.add(theater)
            self.db.commit()
            self.db.refresh(theater)
        except IntegrityError as exc:
            self.db.rollback()
            if "name" in str(exc).lower():
                raise ServiceError(
                    detail="theather name already taken",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        return theater

    def delete_theater(self, theater_id: int) -> None:
        theater = self.db.get(Theater, theater_id)
        if not theater:
            raise ServiceError(
                detail="theater not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        self.db.delete(theater)
        self.db.commit()

    def create_seats(self, theater_id: int, num_seats: int) -> Sequence[Seat]:
        seats = [Seat(theater_id=theater_id) for _ in range(num_seats)]
        try:
            self.db.add_all(seats)
            self.db.commit()
            self.db.refresh(seats)
        except IntegrityError as exc:
            self.db.rollback()
            if "name" in str(exc).lower():
                raise ServiceError(
                    detail="theather name already taken",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        return seats

    def delete_seat(self, seat_id: int) -> None:
        seat = self.db.get(Seat, seat_id)
        if not seat:
            raise ServiceError(
                detail="seat not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        self.db.delete(seat)
        self.db.commit()

    def create_genre(self, name: str) -> Genre:
        genre = Genre(name=name)
        try:
            self.db.add(genre)
            self.db.commit()
            self.db.refresh(genre)
        except IntegrityError as exc:
            self.db.rollback()
            if "name" in str(exc).lower():
                raise ServiceError(
                    detail="genre name already taken",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        return genre

    def delete_genre(self, genre_id: int) -> None:
        genre = self.db.get(Genre, genre_id)
        if not genre:
            raise ServiceError(
                detail="genre not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        self.db.delete(genre)
        self.db.commit()

    def _get_or_create_genres(self, genre_names: list[str]) -> list[Genre]:
        existing = self.db.exec(
            select(Genre).where(col(Genre.name).in_(genre_names))
        ).all()

        new_genres = [
            Genre(name=name)
            for name in genre_names
            if name not in {g.name for g in existing}
        ]

        try:
            self.db.add_all(new_genres)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()

        return list(
            self.db.exec(select(Genre).where(col(Genre.name).in_(genre_names))).all()
        )

    def create_movie(
        self, name: str, description: str, genre_names: list[str]
    ) -> Movie:
        genres = self._get_or_create_genres(genre_names)
        movie = Movie(name=name, description=description, genres=genres)
        self.db.add(movie)
        self.db.commit()
        self.db.refresh(movie)
        return movie

    def update_movie(
        self,
        movie_id: int,
        name: str | None = None,
        description: str | None = None,
        genre_names: list[str] | None = None,
    ) -> Movie:
        movie = self.db.get(Movie, movie_id)
        if not movie:
            raise ServiceError(
                detail="movie not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if name is not None:
            movie.name = name
        if description is not None:
            movie.description = description
        if genre_names is not None:
            movie.genres = self._get_or_create_genres(genre_names)
        self.db.add(movie)
        self.db.commit()
        self.db.refresh(movie)
        return movie

    def delete_movie(self, movie_id: int) -> None:
        movie = self.db.get(Movie, movie_id)
        if not movie:
            raise ServiceError(
                detail="movie not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        self.db.delete(movie)
        self.db.commit()

    def create_showtime(
        self, movie_id: int, theater_id: int, start_date: datetime, end_date: datetime
    ) -> Showtime:
        # BUG: toctou or something like that!!!
        existing = self.db.exec(
            select(Showtime).where(Showtime.theater_id == theater_id)
        ).all()
        for showtime in existing:
            if showtime.start_date < end_date and showtime.end_date > start_date:
                raise ServiceError(
                    detail="this showtime overlaps with another in the theater",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        showtime = Showtime(
            movie_id=movie_id,
            theater_id=theater_id,
            start_date=start_date,
            end_date=end_date,
        )
        self.db.add(showtime)
        self.db.commit()
        self.db.refresh(showtime)
        return showtime

    def update_showtime(
        self,
        showtime_id: int,
        movie_id: int | None = None,
        theater_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> Showtime:
        # BUG: possible toctou!!
        showtime = self.db.get(Showtime, showtime_id)
        if not showtime:
            raise ServiceError(
                detail="showtime not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if movie_id is not None:
            showtime.movie_id = movie_id
        if theater_id is not None:
            showtime.theater_id = theater_id
        if start_date is not None:
            showtime.start_date = start_date
        if end_date is not None:
            showtime.end_date = end_date
        self.db.add(showtime)
        self.db.commit()
        self.db.refresh(showtime)
        return showtime

    def delete_showtime(self, showtime_id: int) -> None:
        showtime = self.db.get(Showtime, showtime_id)
        if not showtime:
            raise ServiceError(
                detail="showtime not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        self.db.delete(showtime)
        self.db.commit()

    def get_showtimes(self) -> Sequence[Showtime]:
        return self.db.exec(select(Showtime)).all()


def get_admin_service(
    db: Annotated[Session, Depends(get_db)],
) -> AdminService:
    return AdminService(db)
