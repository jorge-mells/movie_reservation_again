from datetime import datetime

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

from models.users import User


class Theater(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str


class Seat(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    theater_id: int = Field(default=None, foreign_key="theater.id")
    theater: Theater = Relationship()


class Genre(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str


class MovieGenres(SQLModel, table=True):
    movie_id: int | None = Field(default=None, foreign_key="movie.id", primary_key=True)
    genre_id: int | None = Field(default=None, foreign_key="genre.id", primary_key=True)


class Movie(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str
    genres: list[Genre] = Relationship(link_model=MovieGenres)


class Showtime(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    movie_id: int = Field(default=None, foreign_key="movie.id")
    movie: Movie = Relationship()
    theater_id: int = Field(default=None, foreign_key="theater.id")
    theater: Theater = Relationship()
    start_date: datetime
    end_date: datetime


class Reservation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(default=None, foreign_key="user.id")
    user: User = Relationship()
    showtime_id: int = Field(default=None, foreign_key="showtime.id")
    showtime: Showtime = Relationship()
    seat_id: int = Field(default=None, foreign_key="seat.id")
    seat: Seat = Relationship()


class ReservationResponse(SQLModel):
    id: int | None
    showtime: Showtime
    movie: Movie


class ReservationCreate(BaseModel):
    showtime_id: int
    seat_id: int
