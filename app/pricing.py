"""Сводка лотов аукциона в цену за штуку по каждому предмету."""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

from .config import MARKET_SHARE


@dataclass(frozen=True)
class ItemPrice:
    min_unit: int      # самый дешёвый лот, медь за 1 шт
    market_unit: int   # средняя по самым дешёвым MARKET_SHARE выставленного количества
    quantity: int      # всего штук на аукционе
    auctions: int      # число лотов


Lots = dict[int, list[tuple[float, int]]]


def unit_lots(auctions_payload: dict | None, commodities_payload: dict | None) -> Lots:
    """(цена за 1 шт, количество) по item id.

    Обычные лоты: buyout — за весь лот (как в Classic API), делим на quantity.
    Лоты только со ставкой (без buyout) пропускаем: купить их сразу нельзя.
    Commodities: unit_price — уже за штуку.
    """
    lots: Lots = defaultdict(list)
    for a in (auctions_payload or {}).get("auctions") or []:
        qty = int(a.get("quantity") or 1)
        buyout = a.get("buyout")
        if not buyout or qty <= 0:
            continue
        lots[int(a["item"]["id"])].append((buyout / qty, qty))
    for a in (commodities_payload or {}).get("auctions") or []:
        qty = int(a.get("quantity") or 0)
        unit = a.get("unit_price")
        if not unit or qty <= 0:
            continue
        lots[int(a["item"]["id"])].append((float(unit), qty))
    return lots


def aggregate(lots: Lots, share: float = MARKET_SHARE) -> dict[int, ItemPrice]:
    out: dict[int, ItemPrice] = {}
    for item_id, item_lots in lots.items():
        if not item_lots:
            continue
        item_lots = sorted(item_lots, key=lambda lot: lot[0])
        total = sum(q for _, q in item_lots)
        target = max(1, math.ceil(total * share))
        taken = 0
        cost = 0.0
        for price, qty in item_lots:
            take = min(qty, target - taken)
            cost += take * price
            taken += take
            if taken >= target:
                break
        out[item_id] = ItemPrice(
            min_unit=round(item_lots[0][0]),
            market_unit=round(cost / taken),
            quantity=total,
            auctions=len(item_lots),
        )
    return out
