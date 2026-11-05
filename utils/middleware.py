import logging
import time
import uuid

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from utils.exceptions import ServiceError
from utils.logging import request_id_var

logger = logging.getLogger(__name__)


# NOTE: the reason for these dot delimited lowercase error messages is to establish a convention so that searching for logs is easier


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id_var.set(request.headers.get("X-Request-ID", str(uuid.uuid4())))
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except ServiceError as exc:
            logger.warning(
                "client.error",
                extra={
                    "exc_type": type(exc).__name__,
                    "exc_message": str(exc),
                    "status_code": exc.status_code,
                    "method": request.method,
                    "path": request.url.path,
                },
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=getattr(exc, "headers", {}) or {},
            )
        except Exception as exc:
            logger.error(
                "server.error.unhandled",
                exc_info=exc,
                extra={
                    "exc_type": type(exc).__name__,
                    "exc_message": str(exc),
                    "method": request.method,
                    "path": request.url.path,
                },
            )
            return Response("Internal server error", status_code=500)
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "ms": round((time.perf_counter() - start) * 1000, 2),
            },
        )
        return response
