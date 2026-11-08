"""Обновление справочника рецептов.

Из ForeverDB (выгрузка аддона, Data/Recipes.lua) берём ТОЛЬКО рецепты и источник рецепта.
Из Blizzard static API — русские имена предметов/рецептов и сверку реагентов (данные ForeverDB не меняем).
Цены здесь не участвуют вообще.

    python -m app.recipes_update [--force] [--no-names]

Данные ForeverDB: GPL-3.0, обязательна ссылка «Data from ForeverDB.net».
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx

from . import db
from .blizzard import BlizzardClient, text
from .config import (
    ALL_PROFESSIONS,
    FOREVERDB_MANIFEST,
    FOREVERDB_SITE,
    NS_STATIC,
    blizzard_creds,
    cache_dir,
)
from .lua_data import parse_ns_tables

log = logging.getLogger(__name__)

USER_AGENT = "forever-craft/0.1"
RECIPES_PATH = "Data/Recipes.lua"
NAME_WORKERS = 8


class IntegrityError(RuntimeError):
    """sha256 скачанного файла не совпал с манифестом."""


# --- скачивание -------------------------------------------------------------

def fetch_manifest(http: httpx.Client) -> tuple[str, dict]:
    """(версия выгрузки, запись манифеста для Data/Recipes.lua)."""
    r = http.get(FOREVERDB_MANIFEST)
    r.raise_for_status()
    manifest = r.json()
    version = manifest["data"]["version"]
    entry = next((f for f in manifest["data"]["files"] if f.get("path") == RECIPES_PATH), None)
    if entry is None:
        raise RuntimeError(f"в манифесте ForeverDB нет {RECIPES_PATH}")
    return version, entry


def download_entry(http: httpx.Client, entry: dict) -> bytes:
    r = http.get(f"{FOREVERDB_SITE}/{entry['url'].lstrip('/')}")
    r.raise_for_status()
    digest = hashlib.sha256(r.content).hexdigest()
    if digest != entry["sha256"]:
        raise IntegrityError(f"{entry['path']}: sha256 {digest} != манифест {entry['sha256']}")
    return r.content


# --- нормализация ForeverDB ---------------------------------------------------

def _num(x: float) -> int | float:
    x = float(x)
    return int(x) if x.is_integer() else x


def parse_reagents(spec: str) -> list[dict]:
    out = []
    for part in (spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        item, _, qty = part.partition(":")
        out.append({"item_id": int(item), "qty": _num(qty or 1)})
    return out


def parse_source(raw: Any) -> tuple[str | None, int | None]:
    """'a' -> auto, 't' -> trainer, 'i<id>' -> scroll + id свитка, '' -> unknown (квест/особый способ);
    нераспознанное значение -> (None, None)."""
    s = str(raw or "")
    if s == "":
        return "unknown", None
    if s == "a":
        return "auto", None
    if s == "t":
        return "trainer", None
    if s.startswith("i") and s[1:].isdigit():
        return "scroll", int(s[1:])
    return None, None


def normalize(
    recipes_by_prof: dict,
    names: dict,
    ru_items: dict[int, str] | None = None,
    ru_recipes: dict[tuple[str, int], str] | None = None,
) -> tuple[dict, dict]:
    """ns.recipes/ns.names -> ({"items", "recipes"}, статистика). Только профессии из ALL_PROFESSIONS."""
    ru_items = ru_items or {}
    ru_recipes = ru_recipes or {}
    skipped: Counter = Counter()
    sources: Counter = Counter()
    by_prof: Counter = Counter()
    seen: set[int] = set()
    recipes: list[dict] = []
    item_ids: set[int] = set()

    for slug, (fdb_key, _bid) in ALL_PROFESSIONS.items():
        rows = recipes_by_prof.get(fdb_key) or []
        if isinstance(rows, dict):  # на случай смешанной таблицы
            rows = [rows[k] for k in sorted(k for k in rows if isinstance(k, int))]
        for rec in rows:
            spell, name_en = int(rec[0]), str(rec[1])
            output = int(rec[6] or 0)
            reagents = parse_reagents(rec[8])
            source_type, recipe_item_id = parse_source(rec[9])
            if output <= 0 or float(rec[7] or 0) <= 0:
                skipped["no_output"] += 1
                continue
            if not reagents:
                skipped["no_reagents"] += 1
                continue
            if source_type is None:
                skipped["bad_source"] += 1
                log.warning("нераспознанный источник рецепта %r у %s (%s)", rec[9], spell, name_en)
                continue
            if spell in seen:
                skipped["duplicate_spell"] += 1
                continue
            seen.add(spell)
            skill_needed = int(rec[2] or 0)
            recipes.append({
                "id": spell,
                "profession": slug,
                "name": ru_recipes.get((slug, output)) or name_en,
                "name_en": name_en,
                "output_item_id": output,
                "output_qty": float(rec[7]),
                "learn_skill": skill_needed if skill_needed > 0 else None,
                "skill": {"yellow": int(rec[3]), "green": int(rec[4]), "grey": int(rec[5])},
                "source_type": source_type,
                "source_cost": None,
                "recipe_item_id": recipe_item_id,
                "new_in_forever": bool(rec[11]) if len(rec) > 11 else False,
                "reagents": reagents,
            })
            by_prof[slug] += 1
            sources[source_type] += 1
            item_ids.add(output)
            item_ids.update(g["item_id"] for g in reagents)
            if recipe_item_id is not None:
                item_ids.add(recipe_item_id)

    items = []
    for iid in sorted(item_ids):
        name_en = names.get(iid) or f"Item {iid}"
        items.append({"id": iid, "name": ru_items.get(iid) or name_en, "name_en": name_en})

    stats = {
        "recipes_by_profession": dict(by_prof),
        "recipes_total": len(recipes),
        "items": len(items),
        "skipped": {k: skipped.get(k, 0) for k in ("no_output", "no_reagents", "bad_source", "duplicate_spell")},
        "sources": dict(sources),
    }
    return {"items": items, "recipes": recipes}, stats


# --- Blizzard: русские имена и сверка ----------------------------------------

def _crafted(rec: dict) -> tuple[int | None, str | None]:
    item = rec.get("crafted_item") or rec.get("alliance_crafted_item") or rec.get("horde_crafted_item")
    if not item:
        return None, None
    return int(item["id"]), text(item.get("name"))


def _crafted_qty(rec: dict) -> float | None:
    q = rec.get("crafted_quantity") or {}
    if "value" in q:
        return float(q["value"])
    if "minimum" in q and "maximum" in q:
        return (float(q["minimum"]) + float(q["maximum"])) / 2
    return None


def fetch_blizzard_recipes(client: BlizzardClient, workers: int = NAME_WORKERS) -> tuple[dict[str, list[dict]], int]:
    """slug -> рецепты Blizzard [{id, name, output_item_id, output_name, output_qty, reagents{id: qty}, reagent_names{id: name}}].
    Второе значение — число рецептов, которые не удалось получить."""
    jobs: list[tuple[str, int]] = []
    for slug, (_key, bid) in ALL_PROFESSIONS.items():
        prof = client.get(f"/data/wow/profession/{bid}", namespace=NS_STATIC)
        if prof.data is None:
            log.warning("Blizzard: профессия %s (%s) -> %s", slug, bid, prof.status)
            continue
        ids: list[int] = []
        for tier in prof.data.get("skill_tiers") or []:
            t = client.get(f"/data/wow/profession/{bid}/skill-tier/{tier['id']}", namespace=NS_STATIC)
            if t.data is None:
                log.warning("Blizzard: skill-tier %s/%s -> %s", bid, tier["id"], t.status)
                continue
            for cat in t.data.get("categories") or []:
                ids.extend(int(ref["id"]) for ref in cat.get("recipes") or [])
        jobs.extend((slug, rid) for rid in dict.fromkeys(ids))

    def one(job: tuple[str, int]):
        slug, rid = job
        try:
            f = client.get(f"/data/wow/recipe/{rid}", namespace=NS_STATIC)
            return slug, rid, f.data
        except Exception as e:  # noqa: BLE001 — один рецепт не валит всё
            log.warning("Blizzard: recipe %s: %s", rid, e)
            return slug, rid, None

    out: dict[str, list[dict]] = defaultdict(list)
    errors = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for slug, rid, data in ex.map(one, jobs):
            if data is None:
                errors += 1
                continue
            out_id, out_name = _crafted(data)
            reagents: dict[int, float] = {}
            reagent_names: dict[int, str] = {}
            for g in data.get("reagents") or []:
                ref = g.get("reagent") or {}
                if "id" not in ref:
                    continue
                iid = int(ref["id"])
                reagents[iid] = reagents.get(iid, 0) + float(g.get("quantity") or 0)
                if (n := text(ref.get("name"))):
                    reagent_names[iid] = n
            out[slug].append({
                "id": int(data.get("id", rid)),
                "name": text(data.get("name")),
                "output_item_id": out_id,
                "output_name": out_name,
                "output_qty": _crafted_qty(data),
                "reagents": reagents,
                "reagent_names": reagent_names,
            })
    return dict(out), errors


def ru_names(bliz: dict[str, list[dict]]) -> tuple[dict[int, str], dict[tuple[str, int], str]]:
    items: dict[int, str] = {}
    recipes: dict[tuple[str, int], str] = {}
    for slug, recs in bliz.items():
        for r in recs:
            if r["output_item_id"] is not None:
                if r["output_name"]:
                    items.setdefault(r["output_item_id"], r["output_name"])
                if r["name"]:
                    recipes.setdefault((slug, r["output_item_id"]), r["name"])
            for iid, n in r["reagent_names"].items():
                items.setdefault(iid, n)
    return items, recipes


def cross_check(fdb_recipes: list[dict], bliz: dict[str, list[dict]], examples: int = 5) -> dict:
    """Сверка реагентов по (профессия, выходной предмет). Ничего не меняет."""
    def key_reagents(pairs) -> tuple:
        return tuple(sorted((int(i), float(q)) for i, q in pairs))

    fdb: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for r in fdb_recipes:
        fdb[(r["profession"], r["output_item_id"])].append(r)
    bl: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for slug, recs in bliz.items():
        for r in recs:
            if r["output_item_id"] is not None:
                bl[(slug, r["output_item_id"])].append(r)

    matched = mismatched = 0
    samples: list[dict] = []
    for key in fdb.keys() & bl.keys():
        f_sets = {key_reagents((g["item_id"], g["qty"]) for g in r["reagents"]) for r in fdb[key]}
        b_sets = {key_reagents(r["reagents"].items()) for r in bl[key]}
        if f_sets & b_sets:
            matched += 1
            continue
        mismatched += 1
        if len(samples) < examples:
            samples.append({
                "profession": key[0],
                "output_item_id": key[1],
                "name": fdb[key][0]["name"],
                "foreverdb": [dict(s) for s in sorted(f_sets)],
                "blizzard": [dict(s) for s in sorted(b_sets)],
            })
    return {
        "compared_outputs": matched + mismatched,
        "reagents_match": matched,
        "reagents_differ": mismatched,
        "only_in_foreverdb": len(fdb.keys() - bl.keys()),
        "only_in_blizzard": len(bl.keys() - fdb.keys()),
        "examples": samples,
    }


# --- общий прогон -------------------------------------------------------------

def run(
    conn,
    client: BlizzardClient | None,
    force: bool = False,
    *,
    http: httpx.Client | None = None,
    with_names: bool = True,
) -> dict:
    """Обновить справочник рецептов в базе. Возвращает сводку (dict, сериализуется в JSON).

    Порядок: манифест -> (пропуск, если версия та же) -> Recipes.lua с проверкой sha256 -> разбор ->
    русские имена Blizzard (ошибки не валят обновление) -> сверка -> атомарная замена в базе.
    """
    t0 = time.monotonic()
    own_http = http is None
    if own_http:
        http = httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0), headers={"User-Agent": USER_AGENT},
                            follow_redirects=True)
    try:
        version, entry = fetch_manifest(http)
        previous = db.get_meta(conn, "recipes_version")
        if not force and version == previous:
            log.info("рецепты: выгрузка %s уже загружена, пропускаю", version)
            return {"status": "skipped", "version": version, "reason": "same version"}
        raw = download_entry(http, entry)
    finally:
        if own_http:
            http.close()

    debug_copy = cache_dir() / "foreverdb" / "Recipes.lua"
    try:
        debug_copy.parent.mkdir(parents=True, exist_ok=True)
        debug_copy.write_bytes(raw)
    except OSError as e:
        log.warning("не удалось сохранить копию Recipes.lua: %s", e)

    tables = parse_ns_tables(raw.decode("utf-8"))
    if not isinstance(tables.get("recipes"), dict):
        raise RuntimeError("в Recipes.lua нет таблицы ns.recipes")

    bliz: dict[str, list[dict]] | None = None
    names_summary: dict[str, Any]
    ru_items: dict[int, str] = {}
    ru_recipes: dict[tuple[str, int], str] = {}
    if client is not None and with_names:
        try:
            bliz, errors = fetch_blizzard_recipes(client)
            ru_items, ru_recipes = ru_names(bliz)
            names_summary = {
                "blizzard_recipes": sum(len(v) for v in bliz.values()),
                "blizzard_errors": errors,
                "ru_item_names": len(ru_items),
                "ru_recipe_names": len(ru_recipes),
            }
        except Exception as e:  # noqa: BLE001 — имена необязательны
            log.warning("русские имена из Blizzard не получены, оставляю английские: %s", e)
            bliz = None
            names_summary = {"skipped": f"error: {e}"}
    else:
        names_summary = {"skipped": "no client" if client is None else "--no-names"}

    data, stats = normalize(tables["recipes"], tables.get("names") or {}, ru_items, ru_recipes)
    if not data["recipes"]:
        raise RuntimeError("после разбора не осталось ни одного рецепта — базу не трогаю")
    data["version"] = version

    check = cross_check(data["recipes"], bliz) if bliz else None
    db.replace_recipe_data(conn, data)

    ru_used = sum(1 for it in data["items"] if it["name"] != it["name_en"])
    return {
        "status": "updated",
        "version": version,
        "previous_version": previous,
        **stats,
        "names": {**names_summary, "items_with_ru_name": ru_used},
        "cross_check": check,
        "seconds": round(time.monotonic() - t0, 1),
    }


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Обновить справочник рецептов (ForeverDB + русские имена Blizzard)")
    p.add_argument("--force", action="store_true", help="обновить, даже если версия выгрузки не изменилась")
    p.add_argument("--no-names", action="store_true", help="не ходить в Blizzard за русскими именами")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    client = None
    if not args.no_names:
        creds = blizzard_creds()
        if creds:
            client = BlizzardClient(*creds)
        else:
            log.warning("нет кредов Blizzard (BLIZZ_CLIENT_ID/SECRET или ~/battlenet.creds) — имена будут английскими")
    conn = db.connect()
    db.migrate(conn)
    summary = run(conn, client, force=args.force, with_names=not args.no_names)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
