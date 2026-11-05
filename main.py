import os

from fastapi import FastAPI

from routers import admin, auth, reservations
from utils.logging import setup_logging
from utils.middleware import LoggingMiddleware
from utils.utils import lifespan

setup_logging(debug=os.getenv("FASTAPI_ENV") == "development")
app = FastAPI(lifespan=lifespan)


# NOTE: include routers here
app.include_router(auth.router)
app.include_router(auth.admin_router)
app.include_router(reservations.router)
app.include_router(admin.router)

# NOTE: include middleware here
app.add_middleware(LoggingMiddleware)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "see /docs for usage"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"message": "API is working"}


# BUG: use FASTAPI_ENV to ensure that stuff that should only ran in dev ran then
# ensure users can't reserve old showtimes(add checks to ensure this)
