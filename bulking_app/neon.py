"""Neon PostgreSQL connection helpers."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

import psycopg


def database_url() -> str:
    value = os.getenv("DATABASE_URL", "").strip()
    if not value:
        raise RuntimeError("DATABASE_URL is not configured.")
    return value


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(database_url())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
