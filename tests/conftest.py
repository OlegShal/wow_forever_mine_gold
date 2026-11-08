"""Тесты с базой идут на ОТДЕЛЬНОМ одноразовом Postgres (TEST_DATABASE_URL) и сносят схему craft.

Защита: только localhost — чтобы случайно не стереть данные в Supabase.
Локально:  docker run -d --name forever-pg -e POSTGRES_PASSWORD=postgres -p 127.0.0.1:55432:5432 postgres:16
           TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:55432/postgres pytest
"""
import os
from urllib.parse import urlsplit

import pytest

from app import db


def _test_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL не задан — тесты с базой пропущены")
    host = urlsplit(url).hostname
    if host not in ("localhost", "127.0.0.1", "::1"):
        pytest.exit(f"TEST_DATABASE_URL должен смотреть на локальный Postgres, а не на {host}", returncode=2)
    return url


@pytest.fixture
def pg_url(monkeypatch) -> str:
    url = _test_url()
    monkeypatch.setenv("DATABASE_URL", url)
    return url


@pytest.fixture
def pg(pg_url, tmp_path, monkeypatch):
    monkeypatch.setenv("CACHE_DIR", str(tmp_path))
    conn = db.connect(pg_url)
    conn.execute("drop schema if exists craft cascade")
    db.migrate(conn)
    yield conn
    conn.close()
