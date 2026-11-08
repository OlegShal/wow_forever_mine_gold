"""Сбор цен аукциона Blizzard: по каждому дому — сводка в craft.ah_prices (замена целиком, атомарно).

Отказ одного дома не трогает остальные и не стирает его прошлые цены (last_error в craft.houses).
Неизменившиеся дома (If-Modified-Since -> 304) не перекачиваются.
"""
from __future__ import annotations

import logging
import time

import psycopg

from .blizzard import BlizzardClient, Fetch
from .pricing import aggregate, unit_lots

log = logging.getLogger(__name__)


def discover_houses(client: BlizzardClient) -> dict[int, dict]:
    """Все дома всех rulesets; каждый дом качаем через первый ruleset, который его отдаёт.
    Сейчас все rulesets региона отдают одни и те же дома с одинаковыми лотами."""
    houses: dict[int, dict] = {}
    for rid in client.ruleset_ids():
        for h in client.houses(rid):
            houses.setdefault(h["id"], {**h, "ruleset_id": rid})
    return houses


def _fetch_house(client: BlizzardClient, rid: int, hid: int, row: dict | None) -> tuple[Fetch, Fetch] | None:
    lm_a = row["lm_auctions"] if row else None
    lm_c = row["lm_commodities"] if row else None
    a = client.house(rid, hid, lm_a)
    c = client.commodities(rid, hid, lm_c)
    if a.not_modified and c.not_modified:
        return None
    # одна часть изменилась, другая нет — сырые лоты не храним, поэтому докачиваем вторую целиком
    if a.not_modified:
        a = client.house(rid, hid)
    if c.not_modified:
        c = client.commodities(rid, hid)
    if a.status == 404:
        raise RuntimeError(f"дом {hid}: 404 на списке лотов")
    return a, c


def refresh_prices(conn: psycopg.Connection, client: BlizzardClient) -> dict:
    started = time.time()
    summary: dict = {"updated": [], "unchanged": [], "failed": {}}
    for hid, h in sorted(discover_houses(client).items()):
        conn.execute(
            "insert into craft.houses(id, name, ruleset_id) values (%s, %s, %s) "
            "on conflict (id) do update set name = excluded.name, ruleset_id = excluded.ruleset_id",
            (hid, h["name"], h["ruleset_id"]),
        )
        row = conn.execute("select lm_auctions, lm_commodities from craft.houses where id = %s", (hid,)).fetchone()
        try:
            fetched = _fetch_house(client, h["ruleset_id"], hid, row)
            if fetched is None:
                conn.execute("update craft.houses set checked_at = now(), last_error = null where id = %s", (hid,))
                summary["unchanged"].append(hid)
                continue
            a, c = fetched
            prices = aggregate(unit_lots(a.data, c.data))
            lots = len((a.data or {}).get("auctions") or []) + len((c.data or {}).get("auctions") or [])
            with conn.transaction(), conn.cursor() as cur:
                cur.execute("delete from craft.ah_prices where house_id = %s", (hid,))
                cur.executemany(
                    "insert into craft.ah_prices(house_id, item_id, min_unit, market_unit, quantity, auctions) "
                    "values (%s, %s, %s, %s, %s, %s)",
                    [(hid, iid, p.min_unit, p.market_unit, p.quantity, p.auctions) for iid, p in prices.items()],
                )
                cur.execute(
                    "update craft.houses set lots = %s, updated_at = now(), checked_at = now(), last_error = null, "
                    "lm_auctions = %s, lm_commodities = %s where id = %s",
                    (lots, a.last_modified, c.last_modified, hid),
                )
            summary["updated"].append(hid)
            log.info("дом %s: %s лотов, %s предметов", hid, lots, len(prices))
        except Exception as e:  # один дом не должен валить остальные
            log.exception("дом %s: ошибка", hid)
            conn.execute("update craft.houses set checked_at = now(), last_error = %s where id = %s", (str(e)[:500], hid))
            summary["failed"][hid] = str(e)[:200]
    summary["seconds"] = round(time.time() - started, 1)
    return summary
