from typing import Optional


class ServiceError(Exception):
    def __init__(self, status_code: int, detail: str, headers: Optional[dict] = None):
        self.status_code = status_code
        self.detail = detail
        if headers:
            self.headers = headers
        super().__init__(detail)
