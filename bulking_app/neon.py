"""Neon PostgreSQL connection helpers."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

import psycopg
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


def database_url() -> str:
    value = os.getenv("DATABASE_URL", "").strip()
    if not value:
        try:
            value = str(st.secrets.get("DATABASE_URL", "")).strip()
        except StreamlitSecretNotFoundError:
            value = ""

    if not value:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set it as a local environment "
            "variable or add DATABASE_URL to Streamlit Cloud → App settings → Secrets."
        )
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
