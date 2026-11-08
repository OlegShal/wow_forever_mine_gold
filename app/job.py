"""Один прогон обновления: схема → рецепты (если вышла новая выгрузка) → цены → расчёт таблиц по домам.

GitHub Actions запускает его по cron раз в 30 минут (.github/workflows/collect.yml):
    python -m app.job
Локально можно крутить в цикле:
    python -m app.job --loop
Код выхода 1, если не обновился ни один дом или упали рецепты — чтобы прогон в Actions стал красным.
"""
from __future__ import annotations

import argparse
import json
import logging
import signal
import threading
import time

import httpx
import psycopg

from . import db, recipes_update, results
from .blizzard import BlizzardClient
from .config import PRICE_INTERVAL_SEC, blizzard_creds
from .prices_update import refresh_prices

log = logging.getLogger("job")


def houses_to_compute(conn: psycopg.Connection, updated: list[int], recipes_changed: bool) -> list[int]:
    """Дома с ценами, у которых результаты устарели: обновились цены, сменились рецепты или результатов ещё нет."""
    rows = conn.execute(
        "select h.id, r.house_id is null as missing from craft.houses h "
        "left join craft.house_results r on r.house_id = h.id "
        "where h.updated_at is not null order by h.id"
    ).fetchall()
    return [x["id"] for x in rows if recipes_changed or x["missing"] or x["id"] in updated]


def run_once(conn: psycopg.Connection, client: BlizzardClient, *, http: httpx.Client | None = None,
             force_recipes: bool = False) -> dict:
    t0 = time.monotonic()
    db.migrate(conn)
    summary: dict = {}
    try:
        summary["recipes"] = recipes_update.run(conn, client, force=force_recipes, http=http)
    except Exception as e:  # цены всё равно собираем на старом справочнике
        log.exception("рецепты: ошибка")
        summary["recipes"] = {"status": "error", "error": str(e)[:300]}
    summary["prices"] = refresh_prices(conn, client)

    houses = houses_to_compute(conn, summary["prices"]["updated"], summary["recipes"].get("status") == "updated")
    has_recipes = conn.execute("select exists(select 1 from craft.recipes) as ok").fetchone()["ok"]
    if houses and has_recipes:
        version = db.bump_version(conn)
        summary["results"] = {"version": version, "rows": results.compute(conn, houses, version)}
    else:
        summary["results"] = {"skipped": "нет рецептов" if not has_recipes else "нечего пересчитывать"}
    summary["seconds"] = round(time.monotonic() - t0, 1)
    return summary


def failed(summary: dict) -> bool:
    prices = summary["prices"]
    nothing_fresh = not prices["updated"] and not prices["unchanged"]
    return nothing_fresh or summary["recipes"].get("status") == "error"


def main() -> None:
    p = argparse.ArgumentParser(description="Обновление цен, рецептов и таблиц калькулятора")
    p.add_argument("--loop", action="store_true", help=f"крутить бесконечно, раз в {PRICE_INTERVAL_SEC // 60} мин")
    p.add_argument("--force-recipes", action="store_true", help="перекачать рецепты, даже если версия та же")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    creds = blizzard_creds()
    if not creds:
        raise SystemExit("нет BLIZZ_CLIENT_ID/BLIZZ_CLIENT_SECRET (env или CREDS_FILE)")
    client = BlizzardClient(*creds)

    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())

    while True:
        started = time.monotonic()
        with db.connect() as conn:
            summary = run_once(conn, client, force_recipes=args.force_recipes)
        print(json.dumps(summary, ensure_ascii=False))
        if not args.loop:
            raise SystemExit(1 if failed(summary) else 0)
        args.force_recipes = False
        if stop.wait(max(60.0, PRICE_INTERVAL_SEC - (time.monotonic() - started))):
            return


if __name__ == "__main__":
    main()
