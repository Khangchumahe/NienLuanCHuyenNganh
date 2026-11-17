import os
import tempfile
from pathlib import Path

import pytest

_TEST_DB_ROOT = Path(tempfile.mkdtemp(prefix="aura-pytest-"))
os.environ["AURA_DB_PATH"] = str(_TEST_DB_ROOT / "session.db")
os.environ.setdefault("SECRET_KEY", "pytest-only-secret")
os.environ.setdefault("FLASK_SECRET_KEY", "pytest-only-flask-secret")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("FLASK_DEBUG", "0")
os.environ.setdefault("GEMINI_API_KEY", "")
os.environ.setdefault("ZALOPAY_KEY1", "pytest-zalopay-key1")
os.environ.setdefault("ZALOPAY_KEY2", "pytest-zalopay-key2")
os.environ.setdefault("MOMO_SECRET_KEY", "pytest-momo-secret")
os.environ.setdefault("ADMIN_TOKEN", "")


@pytest.fixture(autouse=True)
def isolated_sqlite_database(tmp_path, monkeypatch):
    from database import db

    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "store.db"))
    db.init_db()
    yield
