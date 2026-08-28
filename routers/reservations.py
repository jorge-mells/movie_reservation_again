from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends

from models import Movie, Reservation, Seat, Showtime
from models.reservations import ReservationCreate
from services.reservations import ReservationService, get_reservation_service
from services.users import UserService, get_user_service
from utils.utils import oauth2_scheme

router = APIRouter(tags=["Reservations"])


@router.get("/movies")
async def get_movies(
    movie_service: Annotated[ReservationService, Depends(get_reservation_service)],
) -> Sequence[Movie]:
    return movie_service.get_movies()


@router.get("/movies/{movie_id}/showtimes")
async def get_showtimes(
    movie_id: int,
    movie_service: Annotated[ReservationService, Depends(get_reservation_service)],
) -> Sequence[Showtime]:
    return movie_service.get_showtimes(movie_id)


@router.get("/showtimes/{showtime_id}/seats")
async def get_seats(
    showtime_id: int,
    movie_service: Annotated[ReservationService, Depends(get_reservation_service)],
) -> Sequence[Seat]:
    return movie_service.get_seats(showtime_id)


@router.get("/users/me/reservations")
async def get_user_reservations(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    movie_service: Annotated[ReservationService, Depends(get_reservation_service)],
) -> Sequence[Reservation]:
    user = await user_service.get_current_user(token)
    assert user.id is not None
    return movie_service.get_reservations(user.id)


@router.get("/users/me/reserved_showtimes")
async def get_reserved_showtimes(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    movie_service: Annotated[ReservationService, Depends(get_reservation_service)],
) -> Sequence[Showtime]:
    user = await user_service.get_current_user(token)
    assert user.id is not None
    return movie_service.get_reserved_showtimes(user.id)


@router.get("/showtimes/{showtime_id}/reserved_seats")
async def get_reserved_seats(
    showtime_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    movie_service: Annotated[ReservationService, Depends(get_reservation_service)],
) -> Sequence[Seat]:
    _ = await user_service.get_current_user(token)
    return movie_service.get_reserved_seats(showtime_id)


@router.post("/users/me/reservations")
async def create_reservation(
    reservationRequest: ReservationCreate,
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    movie_service: Annotated[ReservationService, Depends(get_reservation_service)],
) -> Reservation:
    user = await user_service.get_current_user(token)
    assert user.id is not None
    return movie_service.create_reservation(
        user.id, reservationRequest.showtime_id, reservationRequest.seat_id
    )


@router.delete("/users/me/reservations/{reservation_id}")
async def delete_reservation(
    reservation_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    movie_service: Annotated[ReservationService, Depends(get_reservation_service)],
) -> dict[str, str]:
    user = await user_service.get_current_user(token)
    assert user.id is not None
    movie_service.delete_reservation(reservation_id, user.id)
    return {"message": "reservation deleted successfully"}
