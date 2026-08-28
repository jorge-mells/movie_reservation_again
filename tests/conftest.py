import os
import tempfile
from collections.abc import Generator

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient

from alembic import command
from main import app
from utils.utils import get_settings


@pytest.fixture(autouse=True)
def _run_migrations_and_setup(  # pyright: ignore[reportUnusedFunction]
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None]:
    db_fd, db_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(db_fd)

    test_db_url = f"sqlite:///{db_path}"

    monkeypatch.setenv("DATABASE_URL", test_db_url)
    monkeypatch.setenv(
        "SECRET_KEY", "075dceedeae24b879c14191991d80e2c9bd5035834391d4985adab81cfb055d2"
    )
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_SECONDS", "5")
    monkeypatch.setenv("FASTAPI_ENV", "development")

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    yield

    get_settings.cache_clear()

    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture(scope="function")
def client(_run_migrations_and_setup: None) -> Generator[TestClient]:
    with TestClient(app) as c:
        yield c
