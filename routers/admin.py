from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, status

from models import (
    Genre,
    GenreCreate,
    Movie,
    MovieCreate,
    MovieUpdate,
    Seat,
    SeatCreate,
    Showtime,
    ShowtimeCreate,
    ShowtimeUpdate,
    Theater,
    TheaterCreate,
    UserBase,
)
from services.admin import AdminService, get_admin_service
from services.auth import AuthService, get_user_service
from utils.utils import admin_oauth2_scheme

router = APIRouter(prefix="/admin", tags=["Admin Management"])


async def get_current_admin(
    token: Annotated[str, Depends(admin_oauth2_scheme)],
    user_service: Annotated[AuthService, Depends(get_user_service)],
) -> UserBase:
    user = await user_service.get_current_user(token)
    assert user.id is not None
    return user


# --- theaters ---


@router.post("/theaters", status_code=status.HTTP_201_CREATED)
async def create_theater(
    body: TheaterCreate,
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    _: Annotated[None, Depends(get_current_admin)],
) -> Theater:
    return admin_service.create_theater(body.name)


@router.delete("/theaters/{theater_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_theater(
    theater_id: int,
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    _: Annotated[None, Depends(get_current_admin)],
) -> None:
    admin_service.delete_theater(theater_id)


# --- seats ---


@router.post("/theaters/{theater_id}/seats", status_code=status.HTTP_201_CREATED)
async def create_seats(
    theater_id: int,
    body: SeatCreate,
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    _: Annotated[None, Depends(get_current_admin)],
) -> Sequence[Seat]:
    return admin_service.create_seats(theater_id, body.num_seats)


@router.delete("/seats/{seat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seat(
    seat_id: int,
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    _: Annotated[None, Depends(get_current_admin)],
) -> None:
    admin_service.delete_seat(seat_id)


# --- genres ---


@router.post("/genres", status_code=status.HTTP_201_CREATED)
async def create_genre(
    body: GenreCreate,
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    _: Annotated[None, Depends(get_current_admin)],
) -> Genre:
    return admin_service.create_genre(body.name)


@router.delete("/genres/{genre_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_genre(
    genre_id: int,
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    _: Annotated[None, Depends(get_current_admin)],
) -> None:
    admin_service.delete_genre(genre_id)


# --- movies ---


@router.post("/movies", status_code=status.HTTP_201_CREATED)
async def create_movie(
    body: MovieCreate,
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    _: Annotated[None, Depends(get_current_admin)],
) -> Movie:
    return admin_service.create_movie(
        name=body.name,
        description=body.description,
        genre_names=body.genre_names,
    )


@router.patch("/movies/{movie_id}")
async def update_movie(
    movie_id: int,
    body: MovieUpdate,
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    _: Annotated[None, Depends(get_current_admin)],
) -> Movie:
    return admin_service.update_movie(
        movie_id=movie_id,
        name=body.name,
        description=body.description,
        genre_names=body.genre_names,
    )


@router.delete("/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    _: Annotated[None, Depends(get_current_admin)],
) -> None:
    admin_service.delete_movie(movie_id)


# --- showtimes ---


@router.post("/showtimes", status_code=status.HTTP_201_CREATED)
async def create_showtime(
    body: ShowtimeCreate,
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    _: Annotated[None, Depends(get_current_admin)],
) -> Showtime:
    return admin_service.create_showtime(
        movie_id=body.movie_id,
        theater_id=body.theater_id,
        start_date=body.start_date,
        end_date=body.end_date,
    )


@router.patch("/showtimes/{showtime_id}")
async def update_showtime(
    showtime_id: int,
    body: ShowtimeUpdate,
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    _: Annotated[None, Depends(get_current_admin)],
) -> Showtime:
    return admin_service.update_showtime(
        showtime_id=showtime_id,
        movie_id=body.movie_id,
        theater_id=body.theater_id,
        start_date=body.start_date,
        end_date=body.end_date,
    )


@router.delete("/showtimes/{showtime_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_showtime(
    showtime_id: int,
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    _: Annotated[None, Depends(get_current_admin)],
) -> None:
    admin_service.delete_showtime(showtime_id)


@router.get("/showtimes")
async def get_showtimes(
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    _: Annotated[None, Depends(get_current_admin)],
) -> Sequence[Showtime]:
    return admin_service.get_showtimes()
