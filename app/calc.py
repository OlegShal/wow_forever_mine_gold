"""Себестоимость крафта в двух вариантах. Чистые функции, без I/O.

Все цены предметов — только с аукциона (рыночная цена по самым дешёвым лотам).
«Крафчу сам»: каждый промежуточный реагент, у которого есть рецепт (в CRAFTABLE_PROFESSIONS),
крафтится по самому дешёвому рецепту; сырьё покупается на аукционе.
«Покупаю»: все реагенты покупаются на аукционе.
Цена рецепта: тренер — source_cost (из справочника), свиток — минимальная цена свитка на аукционе.
Все суммы — в меди.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from .config import AH_CUT
from .pricing import ItemPrice


@dataclass(frozen=True)
class Reagent:
    item_id: int
    qty: float


@dataclass(frozen=True)
class Recipe:
    id: int
    profession: str
    name: str
    output_item_id: int
    output_qty: float               # среднее, если выход случайный
    reagents: tuple[Reagent, ...]
    learn_skill: int | None = None
    source_type: str = "trainer"    # trainer | scroll | auto
    source_cost: int | None = None  # цена у тренера, медь
    recipe_item_id: int | None = None
    skill_yellow: int | None = None
    new_in_forever: bool = False
    name_en: str | None = None


@dataclass(frozen=True)
class Cost:
    unit: float | None   # за 1 шт; None — посчитать нельзя
    source: str          # craft | ah | missing
    recipe_id: int | None = None


MISSING = Cost(None, "missing")


class Calculator:
    def __init__(
        self,
        recipes: Iterable[Recipe],
        ah: dict[int, ItemPrice],
        craftable_professions: Iterable[str],
    ):
        recipes = list(recipes)
        self.recipes = {r.id: r for r in recipes}
        self.ah = ah
        allowed = set(craftable_professions)
        self._producers: dict[int, list[Recipe]] = defaultdict(list)
        for r in recipes:
            if r.profession in allowed and r.output_qty > 0:
                self._producers[r.output_item_id].append(r)
        self._memo: dict[tuple[int, frozenset[int]], Cost] = {}

    # --- цены одной штуки -------------------------------------------------

    def buy(self, item_id: int) -> Cost:
        p = self.ah.get(item_id)
        return Cost(float(p.market_unit), "ah") if p else MISSING

    def craft(self, item_id: int, stack: frozenset[int] = frozenset()) -> Cost:
        """Свой крафт по самому дешёвому рецепту. stack — предметы выше по дереву (защита от циклов)."""
        key = (item_id, stack)
        if key in self._memo:
            return self._memo[key]
        best = MISSING
        if item_id not in stack:
            inner = stack | {item_id}
            for r in self._producers.get(item_id, ()):
                total = self._total(r, inner)
                if total is None:
                    continue
                unit = total / r.output_qty
                if best.unit is None or unit < best.unit:
                    best = Cost(unit, "craft", r.id)
        self._memo[key] = best
        return best

    def self_cost(self, item_id: int, stack: frozenset[int]) -> Cost:
        """Вариант «крафчу сам» для реагента: крафт, если можно посчитать, иначе покупка."""
        c = self.craft(item_id, stack)
        return c if c.unit is not None else self.buy(item_id)

    def _total(self, r: Recipe, stack: frozenset[int]) -> float | None:
        total = 0.0
        for g in r.reagents:
            c = self.self_cost(g.item_id, stack)
            if c.unit is None:
                return None
            total += c.unit * g.qty
        return total

    # --- строка таблицы ---------------------------------------------------

    def evaluate(self, r: Recipe) -> dict:
        stack = frozenset({r.output_item_id})
        sell = self.ah.get(r.output_item_id)
        sell_total = sell.market_unit * r.output_qty if sell else None

        reagents = []
        cost_buy = cost_craft = 0.0
        missing_buy: list[int] = []
        missing_craft: list[int] = []
        for g in r.reagents:
            b = self.buy(g.item_id)
            s = self.self_cost(g.item_id, stack)
            reagents.append({
                "item_id": g.item_id,
                "qty": g.qty,
                "buy_unit": _r(b.unit),
                "self_unit": _r(s.unit),
                "self_source": s.source,
            })
            if b.unit is None:
                missing_buy.append(g.item_id)
            else:
                cost_buy += b.unit * g.qty
            if s.unit is None:
                missing_craft.append(g.item_id)
            else:
                cost_craft += s.unit * g.qty

        cb = None if missing_buy else cost_buy
        cc = None if missing_craft else cost_craft
        return {
            "id": r.id,
            "name": r.name,
            "profession": r.profession,
            "learn_skill": r.learn_skill,
            "skill_yellow": r.skill_yellow,
            "new_in_forever": r.new_in_forever,
            "output_item_id": r.output_item_id,
            "output_qty": r.output_qty,
            "sell_unit": sell.market_unit if sell else None,
            "sell_min_unit": sell.min_unit if sell else None,
            "sell_total": _r(sell_total),
            "ah_quantity": sell.quantity if sell else 0,
            "cost_craft": _r(cc),
            "cost_buy": _r(cb),
            "profit_craft": _profit(sell_total, cc),
            "profit_buy": _profit(sell_total, cb),
            "missing_craft": missing_craft,
            "missing_buy": missing_buy,
            "recipe_price": self.recipe_price(r),
            "reagents": reagents,
        }

    def recipe_price(self, r: Recipe) -> dict:
        if r.source_type == "auto":
            return {"amount": 0, "source": "auto", "item_id": None}
        if r.source_type == "scroll":
            p = self.ah.get(r.recipe_item_id) if r.recipe_item_id is not None else None
            return {"amount": p.min_unit if p else None, "source": "scroll", "item_id": r.recipe_item_id}
        if r.source_type == "trainer":
            return {"amount": r.source_cost, "source": "trainer", "item_id": None}
        return {"amount": None, "source": "unknown", "item_id": None}   # квест, дроп без свитка и т.п.

    # --- дерево «по кускам» -----------------------------------------------

    def tree(self, r: Recipe) -> dict:
        stack = frozenset({r.output_item_id})
        return {
            "recipe_id": r.id,
            "item_id": r.output_item_id,
            "qty": r.output_qty,
            "children": [self._node(g.item_id, g.qty, stack) for g in r.reagents],
        }

    def _node(self, item_id: int, qty: float, stack: frozenset[int]) -> dict:
        b = self.buy(item_id)
        c = self.craft(item_id, stack)
        chosen = c if c.unit is not None else b
        node = {
            "item_id": item_id,
            "qty": qty,
            "buy_unit": _r(b.unit),
            "craft_unit": _r(c.unit),
            "chosen": chosen.source,
            "unit": _r(chosen.unit),
            "total": _r(chosen.unit * qty) if chosen.unit is not None else None,
            "recipe_id": chosen.recipe_id,
            "children": [],
        }
        if chosen.source == "craft":
            r = self.recipes[chosen.recipe_id]
            inner = stack | {item_id}
            mult = qty / r.output_qty
            node["children"] = [self._node(g.item_id, g.qty * mult, inner) for g in r.reagents]
        return node


def _r(x: float | None) -> int | None:
    return None if x is None else round(x)


def _profit(sell_total: float | None, cost: float | None) -> int | None:
    if sell_total is None or cost is None:
        return None
    return round(sell_total * (1 - AH_CUT) - cost)
