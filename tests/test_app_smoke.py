"""Render every page against a throwaway Postgres and assert nothing raises.

Runs only when SMOKE_DATABASE_URL points at a disposable database with the
migrations applied (CI provides one). Skipped otherwise, so it can never touch
Neon by accident. The database is empty: no real or personal data is involved.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("streamlit.testing.v1")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["app.py"] + sorted(f"pages/{p.name}" for p in (ROOT / "pages").glob("*.py"))

pytestmark = pytest.mark.skipif(
    not os.getenv("SMOKE_DATABASE_URL"), reason="SMOKE_DATABASE_URL not set"
)


@pytest.mark.parametrize("page", PAGES)
def test_page_renders_without_exception(page, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", os.environ["SMOKE_DATABASE_URL"])
    at = AppTest.from_file(str(ROOT / page), default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]


def test_database_is_disposable():
    url = os.environ["SMOKE_DATABASE_URL"]
    assert "neon" not in url.lower()
