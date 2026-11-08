"""HTTP API для фронта. Только чтение готовых результатов из Postgres; считает и пишет джоб.

На Vercel это Python-функция (api/index.py). Локально:
    SERVE_STATIC=1 uvicorn app.api:app --reload      # заодно раздаёт public/
"""
from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path

import psycopg
from fastapi import FastAPI, HTTPException, Query, Response

from . import db
from .config import PROFESSIONS, REGION, supabase_public

log = logging.getLogger(__name__)
app = FastAPI(title="WoW Forever craft calculator", docs_url=None, redoc_url=None)

# Данные меняются не чаще раза в 10 минут — даём CDN Vercel кэшировать ответы.
CACHE = "public, max-age=0, s-maxage=60, stale-while-revalidate=300"

_conn: psycopg.Connection | None = None
_lock = threading.Lock()


def _query(sql: str, params: tuple = ()) -> list[dict]:
    """Одно переиспользуемое соединение на тёплый инстанс функции; при обрыве — переподключение и повтор."""
    global _conn
    with _lock:
        for attempt in (1, 2):
            try:
                if _conn is None or _conn.closed or _conn.broken:
                    _conn = db.connect()
                return _conn.execute(sql, params).fetchall()
            except psycopg.OperationalError:
                if attempt == 2:
                    raise
                log.warning("соединение с базой оборвалось, переподключаюсь")
                _conn = None
    raise RuntimeError("unreachable")


def _json(body: str) -> Response:
    return Response(content=body, media_type="application/json", headers={"Cache-Control": CACHE})


_ISO = """to_char(%s at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')"""


@app.get("/api/status")
def status() -> Response:
    houses = _query(
        f"select id, name, lots, {_ISO % 'updated_at'} as updated_at, {_ISO % 'checked_at'} as checked_at, last_error "
        "from craft.houses order by id"
    )
    meta = {r["key"]: r["value"] for r in _query(
        "select key, value from craft.meta where key in ('recipes_version', 'recipes_updated_at', 'data_version')")}
    count = _query("select count(*) as n from craft.recipes where profession = any(%s)", (list(PROFESSIONS),))[0]["n"]
    now = _query(f"select {_ISO % 'now()'} as t")[0]["t"]
    return _json(json.dumps({
        "now": now,
        "region": REGION,
        "houses": houses,
        "recipes": {"count": count, "version": meta.get("recipes_version"), "updated_at": meta.get("recipes_updated_at")},
        "data_version": meta.get("data_version") or "0",
    }, ensure_ascii=False))


@app.get("/api/recipes")
def recipes(house_id: int = Query(...)) -> Response:
    rows = _query("select data_version, rows::text as rows from craft.house_results where house_id = %s", (house_id,))
    if not rows:
        raise HTTPException(404, f"нет данных по аукционному дому {house_id}")
    r = rows[0]
    # rows уже JSON из базы — не разбираем и не собираем заново ~1 МБ
    return _json(f'{{"house_id":{house_id},"data_version":"{r["data_version"]}","rows":{r["rows"]}}}')


@app.get("/api/recipes/{recipe_id}/tree")
def recipe_tree(recipe_id: int, house_id: int = Query(...)) -> Response:
    rows = _query("select (trees -> %s)::text as tree from craft.house_results where house_id = %s",
                  (str(recipe_id), house_id))
    if not rows or rows[0]["tree"] is None:
        raise HTTPException(404, f"нет рецепта {recipe_id} для дома {house_id}")
    return _json(rows[0]["tree"])


@app.get("/api/config")
def config() -> Response:
    return Response(content=json.dumps(supabase_public()), media_type="application/json",
                    headers={"Cache-Control": "public, max-age=300"})


if os.environ.get("SERVE_STATIC") == "1":
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=Path(__file__).parent.parent / "public", html=True), name="static")
