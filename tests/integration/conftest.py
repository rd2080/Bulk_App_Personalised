"""Fixtures for Postgres integration tests.

Runs only against a throwaway database named by SMOKE_DATABASE_URL (CI provides
one). Skips when unset. Refuses to run (fails closed) if the URL looks like
production or Neon. All data is synthetic and rolled back per test.
"""

from __future__ import annotations

import os
from pathlib import Path

from urllib.parse import urlparse

import pytest

psycopg = pytest.importorskip("psycopg")

MIGRATIONS = Path(__file__).resolve().parents[2] / "database" / "migrations"
FORBIDDEN = ("production", "neon")


def _allowed_hosts() -> set[str]:
    hosts = {"localhost", "127.0.0.1", "::1"}
    extra = os.getenv("SMOKE_ALLOW_HOST", "").strip().lower()
    if extra:
        hosts.add(extra)
    return hosts


def check_url() -> str:
    """Allowlist guard: only local/explicitly allowed hosts; never production/neon."""
    url = os.getenv("SMOKE_DATABASE_URL", "").strip()
    if not url:
        pytest.skip("SMOKE_DATABASE_URL not set (no throwaway database)")
    host = (urlparse(url).hostname or "").lower()
    if host not in _allowed_hosts():
        pytest.fail(f"Refusing to run: host {host!r} is not allowlisted.", pytrace=False)
    if any(word in url.lower() for word in FORBIDDEN):
        pytest.fail("Refusing to run: database URL names production/neon.", pytrace=False)
    return url


@pytest.fixture(scope="session")
def db_url() -> str:
    url = check_url()
    with psycopg.connect(url) as conn:
        exists = conn.execute("SELECT to_regclass('public.daily_checkins')").fetchone()[0]
        if exists is None:
            tables = conn.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"
            ).fetchone()[0]
            if tables and os.getenv("SMOKE_ALLOW_MIGRATE") != "1":
                pytest.fail("Refusing to migrate a partly migrated database "
                            "(set SMOKE_ALLOW_MIGRATE=1 to override).", pytrace=False)
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
