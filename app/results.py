"""Готовые для фронта строки и деревья по каждому дому (с именами). Считает джоб, API отдаёт как есть.

Каждое имя — в двух языках: `name` (русское, если есть, иначе английское) и `name_en` (английское).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import psycopg

from . import db
from .calc import Calculator, Recipe
from .config import PROFESSIONS

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Names:
    ru: dict[int, str]
    en: dict[int, str] = field(default_factory=dict)

    def of(self, item_id: int | None) -> dict:
        if not item_id:
            return {"name": None, "name_en": None}
        ru = self.ru.get(item_id)
        en = self.en.get(item_id)
        return {"name": ru or en or f"#{item_id}", "name_en": en or ru or f"#{item_id}"}


def _as_names(names: Names | dict[int, str]) -> Names:
    return names if isinstance(names, Names) else Names(names)


def _named(ids: list[int], names: Names) -> list[dict]:
    return [{"item_id": i, **names.of(i)} for i in ids]


def named_row(row: dict, names: Names | dict[int, str], recipe: Recipe | None = None) -> dict:
    names = _as_names(names)
    rp = row["recipe_price"]
    rp_names = names.of(rp["item_id"])
    return {
        **row,
        "name_en": (recipe.name_en if recipe else None) or row["name"],
        "missing_craft": _named(row["missing_craft"], names),
        "missing_buy": _named(row["missing_buy"], names),
        "recipe_price": {**rp, "name": rp_names["name"], "name_en": rp_names["name_en"]},
        "reagents": [{**g, **names.of(g["item_id"])} for g in row["reagents"]],
    }


def _name_node(node: dict, calc: Calculator, names: Names) -> dict:
    rid = node.get("recipe_id")
    out = {**node, **names.of(node["item_id"])}
    if "chosen" in node:
        rec = calc.recipes.get(rid)
        out["recipe_name"] = rec.name if rec else None
        out["recipe_name_en"] = (rec.name_en or rec.name) if rec else None
    out["children"] = [_name_node(c, calc, names) for c in node["children"]]
    return out


def named_tree(calc: Calculator, r: Recipe, names: Names | dict[int, str]) -> dict:
    return {**_name_node(calc.tree(r), calc, _as_names(names)), "name": r.name, "name_en": r.name_en or r.name}


def build(calc: Calculator, names: Names | dict[int, str]) -> tuple[list[dict], dict[str, dict]]:
    names = _as_names(names)
    rows: list[dict] = []
    trees: dict[str, dict] = {}
    for r in calc.recipes.values():
        if r.profession not in PROFESSIONS:
            continue
        rows.append(named_row(calc.evaluate(r), names, r))
        trees[str(r.id)] = named_tree(calc, r, names)
    return rows, trees


def compute(conn: psycopg.Connection, house_ids: list[int], version: int) -> dict[int, int]:
    """Пересчитать и сохранить результаты для домов. Возвращает {дом: число строк}."""
    recipes = db.load_recipes(conn)
    names = Names(db.item_names(conn), db.item_names_en(conn))
    out = {}
    for hid in house_ids:
        calc = db.load_calculator(conn, hid, recipes)
        rows, trees = build(calc, names)
        db.save_results(conn, hid, version, rows, trees)
        out[hid] = len(rows)
    return out
