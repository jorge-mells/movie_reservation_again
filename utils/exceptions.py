import logging
from typing import Any

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    def __init__(
        self, status_code: int, detail: str, headers: dict[Any, Any] | None = None
    ):
        self.status_code = status_code
        self.detail = detail
        if headers:
            self.headers = headers
        super().__init__(detail)
