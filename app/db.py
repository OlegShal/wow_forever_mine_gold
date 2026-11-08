"""Postgres (Supabase). Схема — app/schema.sql (+ app/schema_supabase.sql, если есть схема auth).

Соединения в autocommit; атомарные куски — в `with conn.transaction()`.
prepare_threshold=None — чтобы работать через Supavisor в режиме transaction pooling.

Нормализованный формат справочника рецептов (вход replace_recipe_data):
{
  "version": "2026-11-08.24384dfa",            # версия выгрузки ForeverDB
  "items": [{"id": 2454, "name": "Малый эликсир силы", "name_en": "Elixir of Minor Strength"}],
  "recipes": [{
     "id": 2329, "profession": "alchemy", "name": "Малый эликсир силы",
     "output_item_id": 2454, "output_qty": 1.0,
     "learn_skill": 55 | null, "skill": {"yellow": 55, "green": 75, "grey": 95},
     "source_type": "trainer" | "scroll" | "auto" | "unknown",
     "source_cost": null, "recipe_item_id": 2553 | null, "new_in_forever": true,
     "reagents": [{"item_id": 2449, "qty": 1}]
  }]
}
"""
from __future__ import annotations

from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .calc import Calculator, Reagent, Recipe
from .config import CRAFTABLE_PROFESSIONS, database_url
from .pricing import ItemPrice

_HERE = Path(__file__).parent


def connect(url: str | None = None) -> psycopg.Connection:
    return psycopg.connect(
        url or database_url(), autocommit=True, row_factory=dict_row, prepare_threshold=None, connect_timeout=15,
    )


def migrate(conn: psycopg.Connection) -> None:
    with conn.transaction():
        conn.execute((_HERE / "schema.sql").read_text())
        if conn.execute("select to_regnamespace('auth') is not null as ok").fetchone()["ok"]:
            conn.execute((_HERE / "schema_supabase.sql").read_text())


def get_meta(conn: psycopg.Connection, key: str) -> str | None:
    row = conn.execute("select value from craft.meta where key = %s", (key,)).fetchone()
    return row["value"] if row else None


def set_meta(conn: psycopg.Connection, key: str, value: str | None) -> None:
    conn.execute(
        "insert into craft.meta(key, value) values (%s, %s) on conflict (key) do update set value = excluded.value",
        (key, value),
    )


def bump_version(conn: psycopg.Connection) -> int:
    """Счётчик изменений данных: фронт по нему понимает, что пора перезагрузить таблицу."""
    row = conn.execute(
        "insert into craft.meta(key, value) values ('data_version', '1') "
        "on conflict (key) do update set value = (craft.meta.value::bigint + 1)::text returning value"
    ).fetchone()
    return int(row["value"])


def load_recipes(conn: psycopg.Connection) -> list[Recipe]:
    reagents: dict[int, list[Reagent]] = {}
    for row in conn.execute("select recipe_id, item_id, qty from craft.reagents"):
        reagents.setdefault(row["recipe_id"], []).append(Reagent(row["item_id"], row["qty"]))
    return [
        Recipe(
            id=row["id"],
            profession=row["profession"],
            name=row["name"],
            output_item_id=row["output_item_id"],
            output_qty=row["output_qty"],
            reagents=tuple(reagents.get(row["id"], ())),
            learn_skill=row["learn_skill"],
            source_type=row["source_type"],
            source_cost=row["source_cost"],
            recipe_item_id=row["recipe_item_id"],
            skill_yellow=row["skill_yellow"],
            new_in_forever=row["new_in_forever"],
            name_en=row["name_en"],
        )
        for row in conn.execute("select * from craft.recipes order by id")
    ]


def load_ah(conn: psycopg.Connection, house_id: int) -> dict[int, ItemPrice]:
    return {
        row["item_id"]: ItemPrice(row["min_unit"], row["market_unit"], row["quantity"], row["auctions"])
        for row in conn.execute("select * from craft.ah_prices where house_id = %s", (house_id,))
    }


def load_calculator(conn: psycopg.Connection, house_id: int, recipes: list[Recipe] | None = None) -> Calculator:
    return Calculator(recipes if recipes is not None else load_recipes(conn), load_ah(conn, house_id),
                      CRAFTABLE_PROFESSIONS)


def item_names(conn: psycopg.Connection) -> dict[int, str]:
    return {row["id"]: row["name"] for row in conn.execute("select id, name from craft.items")}


def item_names_en(conn: psycopg.Connection) -> dict[int, str]:
    return {row["id"]: row["name_en"] for row in conn.execute("select id, name_en from craft.items where name_en is not null")}


def replace_recipe_data(conn: psycopg.Connection, data: dict) -> None:
    """Полная атомарная замена справочника рецептов (формат — в докстринге модуля)."""
    with conn.transaction(), conn.cursor() as cur:
        cur.execute("delete from craft.reagents")
        cur.execute("delete from craft.recipes")
        cur.execute("delete from craft.items")
        cur.executemany(
            "insert into craft.items(id, name, name_en) values (%s, %s, %s)",
            [(it["id"], it["name"], it.get("name_en")) for it in data["items"]],
        )
        cur.executemany(
            "insert into craft.recipes(id, profession, name, name_en, output_item_id, output_qty, learn_skill, skill_yellow, "
            "skill_green, skill_grey, source_type, source_cost, recipe_item_id, new_in_forever) "
            "values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [
                (
                    r["id"], r["profession"], r["name"], r.get("name_en"), r["output_item_id"], r["output_qty"], r.get("learn_skill"),
                    (r.get("skill") or {}).get("yellow"), (r.get("skill") or {}).get("green"),
                    (r.get("skill") or {}).get("grey"), r["source_type"], r.get("source_cost"),
                    r.get("recipe_item_id"), bool(r.get("new_in_forever")),
                )
                for r in data["recipes"]
            ],
        )
        cur.executemany(
            "insert into craft.reagents(recipe_id, item_id, qty) values (%s, %s, %s)",
            [(r["id"], g["item_id"], g["qty"]) for r in data["recipes"] for g in r["reagents"]],
        )
        set_meta(conn, "recipes_version", data.get("version"))
        set_meta(conn, "recipes_updated_at", _now(conn))


def save_results(conn: psycopg.Connection, house_id: int, version: int, rows: list, trees: dict) -> None:
    conn.execute(
        "insert into craft.house_results(house_id, data_version, computed_at, rows, trees) "
        "values (%s, %s, now(), %s, %s) on conflict (house_id) do update set "
        "data_version = excluded.data_version, computed_at = excluded.computed_at, "
        "rows = excluded.rows, trees = excluded.trees",
        (house_id, version, Jsonb(rows), Jsonb(trees)),
    )


def _now(conn: psycopg.Connection) -> str:
    return conn.execute("""select to_char(now() at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as t""").fetchone()["t"]
