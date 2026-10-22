"""Fixtures for Postgres integration tests.

Runs only against a throwaway database named by SMOKE_DATABASE_URL (CI provides
one). Skips when unset. Refuses to run (fails closed) if the URL looks like
production or Neon. All data is synthetic and rolled back per test.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")

MIGRATIONS = Path(__file__).resolve().parents[2] / "database" / "migrations"
FORBIDDEN = ("production", "neon")


def check_url() -> str:
    url = os.getenv("SMOKE_DATABASE_URL", "").strip()
    if not url:
        pytest.skip("SMOKE_DATABASE_URL not set (no throwaway database)")
    lowered = url.lower()
    if any(word in lowered for word in FORBIDDEN):
        pytest.fail("Refusing to run: database URL names production/neon.", pytrace=False)
    return url


@pytest.fixture(scope="session")
def db_url() -> str:
    url = check_url()
    with psycopg.connect(url) as conn:
        exists = conn.execute("SELECT to_regclass('public.daily_checkins')").fetchone()[0]
        if exists is None:  # fresh database: apply every migration, sorted by name
            for path in sorted(MIGRATIONS.glob("*.sql")):
                conn.execute(path.read_text())
            conn.commit()
    return url


@pytest.fixture
def conn(db_url):
    """A connection whose work is always rolled back."""
    c = psycopg.connect(db_url)
    try:
        yield c
    finally:
        c.rollback()
        c.close()
