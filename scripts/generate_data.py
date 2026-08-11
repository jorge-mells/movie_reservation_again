import random
from datetime import datetime

from faker import Faker
from faker.providers import DynamicProvider
from pwdlib import PasswordHash
from sqlmodel import Session

from models.reservations import Genre, Movie, Reservation, Seat, Showtime, Theater
from models.users import User

fake = Faker()
genre_provider = DynamicProvider(
    provider_name="movie_genre",
    elements=[
        "Action",
        "Comedy",
        "Drama",
        "Sci-Fi",
        "Horror",
        "Thriller",
        "Documentary",
    ],
)
fake.add_provider(genre_provider)


def generate_users(num=5) -> list[User]:
    users = [
        User(username=fake.name(), hashed_password=fake.password()) for _ in range(num)
    ]
    return users


def generate_theaters(num=2) -> list[Theater]:
    theaters = [Theater(name=fake.name()) for _ in range(num)]
    return theaters


def generate_seats(theaters: list[Theater], num=50) -> list[Seat]:
    """Generate $num seats per theater"""
    seats = []
    for theater in theaters:
        seats += [Seat(theater=theater) for _ in range(num)]

    return seats


def generate_genres(num=10) -> list[Genre]:
    genres = [Genre(name=fake.movie_genre()) for _ in range(num)]
    return genres


def generate_movies(genres: list[Genre], num=20) -> list[Movie]:
    movies = []
    for _ in range(num):
        random_genres = random.choices(genres, k=random.randrange(len(genres)))
        movie = Movie(
            name=fake.name(), description=fake.paragraph(), genres=random_genres
        )
        movies.append(movie)
    return movies


def get_or_create_concrete[T](
    db: Session, model_class: type[T], items_data: list[dict]
) -> list[T]:
    """
    Ensures a list of concrete items with explicit IDs exist in the database.
    If an item with a given ID already exists, it uses the existing one.
    Otherwise, it creates a new record.
    """
    instances = []
    for data in items_data:
        item_id = data.get("id")

        # Check if it already exists in the database
        existing = db.get(model_class, item_id) if item_id is not None else None

        if existing:
            instances.append(existing)
        else:
            instance = model_class(**data)
            db.add(instance)
            db.flush()
            instances.append(instance)

    db.commit()
    return instances


def generate_concrete_users(db: Session) -> list[User]:
    password_hash = PasswordHash.recommended()
    user_data = [
        {
            "id": 1,
            "username": "testuser1",
            "hashed_password": password_hash.hash("testuser1"),
        },
        {
            "id": 2,
            "username": "testuser2",
            "hashed_password": password_hash.hash("testuser2"),
        },
    ]
    return get_or_create_concrete(db, User, user_data)


def generate_concrete_theaters(db: Session) -> list[Theater]:
    theater_data = [
        {"id": 1, "name": "test theater 1"},
        {"id": 2, "name": "test theater 2"},
    ]
    return get_or_create_concrete(db, Theater, theater_data)


def generate_concrete_genres(db: Session) -> list[Genre]:
    genre_data = [
        {"id": 1, "name": "action"},
        {"id": 2, "name": "horror"},
        {"id": 3, "name": "adventure"},
    ]
    return get_or_create_concrete(db, Genre, genre_data)


def generate_concrete_seats(db: Session) -> list[Seat]:
    theater1, theater2 = generate_concrete_theaters(db)
    seat_data = [
        {"id": 1, "theater": theater1},
        {"id": 2, "theater": theater1},
        {"id": 3, "theater": theater1},
        {"id": 4, "theater": theater1},
        {"id": 5, "theater": theater2},
        {"id": 6, "theater": theater2},
        {"id": 7, "theater": theater2},
        {"id": 8, "theater": theater2},
    ]
    return get_or_create_concrete(db, Seat, seat_data)


def generate_concrete_movies(db: Session) -> list[Movie]:
    genre1, genre2, genre3 = generate_concrete_genres(db)

    movie_data = [
        {
            "id": 1,
            "name": "The adventures of Tintin",
            "description": "Tintin embarks on an adventure in Egypt where he encounters several challenges, and eventually is taken on a wild ride through time",
            "genres": [genre1, genre3],
        },
        {
            "id": 2,
            "name": "Scream",
            "description": "A gripping horror movie with action elements",
            "genres": [genre1, genre2],
        },
        {
            "id": 3,
            "name": "The Horrors of Dora",
            "description": "A simple adventure in the Amazons turns into a horror scenario for Dora",
            "genres": [genre2, genre3],
        },
    ]

    return get_or_create_concrete(db, Movie, movie_data)


def generate_concrete_showtimes(db: Session) -> list[Showtime]:
    theater1, theater2 = generate_concrete_theaters(db)
    movie1, movie2, movie3 = generate_concrete_movies(db)

    showtime_data = [
        {
            "id": 1,
            "movie": movie1,
            "theater": theater1,
            "start_date": datetime(2026, 7, 8, 14),
            "end_date": datetime(2026, 7, 8, 16),
        },
        {
            "id": 2,
            "movie": movie1,
            "theater": theater2,
            "start_date": datetime(2026, 7, 8, 10),
            "end_date": datetime(2026, 7, 8, 12),
        },
        {
            "id": 3,
            "movie": movie2,
            "theater": theater1,
            "start_date": datetime(2026, 7, 9, 10),
            "end_date": datetime(2026, 7, 9, 12),
        },
        {
            "id": 4,
            "movie": movie2,
            "theater": theater2,
            "start_date": datetime(2026, 7, 9, 15),
            "end_date": datetime(2026, 7, 9, 17),
        },
        {
            "id": 5,
            "movie": movie3,
            "theater": theater1,
            "start_date": datetime(2026, 7, 10, 15),
            "end_date": datetime(2026, 7, 10, 17),
        },
        {
            "id": 6,
            "movie": movie3,
            "theater": theater2,
            "start_date": datetime(2026, 7, 10, 9),
            "end_date": datetime(2026, 7, 10, 12),
        },
    ]
    return get_or_create_concrete(db, Showtime, showtime_data)


def generate_concrete_reservations(db: Session) -> list[Reservation]:
    user1, user2 = generate_concrete_users(db)
    seat11, seat12, _, _, _, seat22, _, _ = generate_concrete_seats(db)
    showtime1, _, _, showtime4, showtime5, _ = generate_concrete_showtimes(db)

    reservation_data = [
        {"id": 1, "user": user1, "showtime": showtime1, "seat": seat11},
        {"id": 2, "user": user1, "showtime": showtime4, "seat": seat22},
        {"id": 3, "user": user2, "showtime": showtime5, "seat": seat12},
    ]
    return get_or_create_concrete(db, Reservation, reservation_data)
