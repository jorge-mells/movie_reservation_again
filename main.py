from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from routers import users
from utils.exceptions import ServiceError
from utils.utils import lifespan

app = FastAPI(lifespan=lifespan)

# NOTE: include routers here
app.include_router(users.router)


@app.exception_handler(ServiceError)
async def service_error_handler(_request: Request, exc: ServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers or {},
    )


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "see /docs for usage"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"message": "API is working"}


# BUG: use FASTAPI_ENV to ensure that stuff that should only ran in dev ran then
# ensure users can't reserve old showtimes(add checks to ensure this)
