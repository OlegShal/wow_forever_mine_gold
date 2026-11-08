import hashlib
import json

import httpx
import pytest

from app import db
from app.blizzard import Fetch
from app.config import FOREVERDB_MANIFEST, FOREVERDB_SITE
from app.lua_data import parse_ns_tables
from app.recipes_update import (
    IntegrityError,
    cross_check,
    fetch_blizzard_recipes,
    normalize,
    ru_names,
    run,
)

LUA = """-- Data: ForeverDB.net (https://foreverdb.net), build 1.60.1.70862.
local _, ns = ...
-- [profession] = {{spell, name, skill needed, yellow, green, grey, makes item, how many, reagents, learned from, ...}}
ns.recipes = {Alchemy={{2330,"Minor Healing Potion",1,55,75,95,118,1,"2447:1,765:1,3371:1","a",0,0,0},{2330,"Dup",1,1,1,1,118,1,"765:1","t",0,0,0},{2331,"Minor Mana Potion",25,65,85,105,2455,1,"785:1,2447:1,3371:1","t",0,0,1},{3230,"Elixir of Minor Agility",0,80,100,120,2457,1,"2452:1,765:1,3371:1","i2553",0,1,0},{9999,"No reagents",1,1,1,1,1234,1,"","t",0,0,0},{9998,"No output",1,1,1,1,0,1,"765:1","t",0,0,0}},Engineering={{3947,"Crafted Light Shot",75,75,85,95,8067,150,"2840:1,4357:1,77777:2","t",0,0,0,100,200}},Mining={{2657,"Smelt Copper",1,25,47,70,2840,1,"2770:1","t",0,0,0},{14891,"Smelt Dark Iron",0,230,230,230,11371,1,"11370:8","",0,0,0},{1,"Garbage",0,1,1,1,5,1,"2770:1","x9",0,0,0}},Tailoring={{2387,"Linen Cloak",1,1,1,1,2570,1,"2589:3","t",0,0,0}},Jewelcrafting={{9000,"Not In Config",1,1,1,1,9001,1,"2589:3","t",0,0,0}}}
ns.names = {[118]="Minor Healing Potion",[2447]="Peacebloom",[765]="Silverleaf",[3371]="Empty Vial",[2455]="Minor Mana Potion",[785]="Mageroyal",[2457]="Elixir of Minor Agility",[2452]="Swiftthistle",[2553]="Recipe: Elixir of Minor Agility",[8067]="Crafted Light Shot",[2840]="Copper Bar",[4357]="Rough Blasting Powder",[2770]="Copper Ore",[2570]="Linen Cloak",[2589]="Linen Cloth"}
"""


@pytest.fixture
def tables():
    return parse_ns_tables(LUA)


def test_normalize(tables):
    data, stats = normalize(tables["recipes"], tables["names"])
    by_id = {r["id"]: r for r in data["recipes"]}

    assert stats["recipes_by_profession"] == {"alchemy": 3, "engineering": 1, "mining": 2, "tailoring": 1}
    assert stats["skipped"] == {"no_output": 1, "no_reagents": 1, "bad_source": 1, "duplicate_spell": 1}
    assert stats["sources"] == {"auto": 1, "trainer": 4, "scroll": 1, "unknown": 1}
    assert by_id[2387]["profession"] == "tailoring"
    assert 9000 not in by_id  # профессии не из config.PROFESSIONS не берём
    assert 1 not in by_id     # нераспознанный источник
    dark = by_id[14891]       # пустой источник = неизвестен (квест и т.п.), рецепт остаётся
    assert (dark["source_type"], dark["recipe_item_id"], dark["learn_skill"]) == ("unknown", None, None)

    auto = by_id[2330]
    assert (auto["source_type"], auto["recipe_item_id"], auto["learn_skill"]) == ("auto", None, 1)
    assert auto["name"] == "Minor Healing Potion"  # первая запись, дубль отброшен
    assert auto["reagents"] == [{"item_id": 2447, "qty": 1}, {"item_id": 765, "qty": 1}, {"item_id": 3371, "qty": 1}]

    trainer = by_id[2331]
    assert trainer["source_type"] == "trainer"
    assert trainer["source_cost"] is None
    assert trainer["skill"] == {"yellow": 65, "green": 85, "grey": 105}

    scroll = by_id[3230]
    assert (scroll["source_type"], scroll["recipe_item_id"]) == ("scroll", 2553)
    assert scroll["learn_skill"] is None      # 0 = неизвестно
    assert scroll["new_in_forever"] is True

    shot = by_id[3947]
    assert shot["output_qty"] == 150.0        # «how many» — уже среднее при случайном выходе
    assert shot["profession"] == "engineering"

    items = {it["id"]: it for it in data["items"]}
    assert 2553 in items and 2770 in items and 118 in items
    assert 2570 in items and 2589 in items
    assert 9001 not in items  # предметы профессий не из config.PROFESSIONS не попадают
    assert items[77777] == {"id": 77777, "name": "Item 77777", "name_en": "Item 77777"}
    assert items[118]["name"] == items[118]["name_en"] == "Minor Healing Potion"


def test_normalize_uses_russian_names(tables):
    data, _ = normalize(
        tables["recipes"], tables["names"],
        ru_items={118: "Слабое лечебное зелье", 2447: "Мироцвет"},
        ru_recipes={("alchemy", 118): "Слабое лечебное зелье"},
    )
    items = {it["id"]: it for it in data["items"]}
    assert items[118] == {"id": 118, "name": "Слабое лечебное зелье", "name_en": "Minor Healing Potion"}
    assert items[2447]["name"] == "Мироцвет"
    rec = next(r for r in data["recipes"] if r["id"] == 2330)
    assert rec["name"] == "Слабое лечебное зелье"
    assert rec["name_en"] == "Minor Healing Potion"


# --- скачивание и запись в базу ------------------------------------------------

def _transport(version: str, body: bytes, sha: str | None = None, seen: list | None = None):
    manifest = {"data": {"version": version, "files": [
        {"path": "Data/Recipes.lua", "url": "downloads/addon-data/Recipes.lua?v=1",
         "sha256": sha or hashlib.sha256(body).hexdigest(), "bytes": len(body)},
    ]}}

    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(str(request.url))
        if str(request.url) == FOREVERDB_MANIFEST:
            return httpx.Response(200, json=manifest)
        if str(request.url).startswith(f"{FOREVERDB_SITE}/downloads/addon-data/Recipes.lua"):
            return httpx.Response(200, content=body)
        return httpx.Response(404)

    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.fixture
def conn(pg):
    return pg


def test_sha_mismatch_does_not_touch_db(conn):
    http = _transport("v2", LUA.encode(), sha="0" * 64)
    with pytest.raises(IntegrityError):
        run(conn, None, force=True, http=http)
    assert conn.execute("select count(*) as n from craft.recipes").fetchone()["n"] == 0
    assert db.get_meta(conn, "recipes_version") is None


def test_skip_when_same_version(conn):
    db.set_meta(conn, "recipes_version", "v1")
    seen: list[str] = []
    summary = run(conn, None, http=_transport("v1", LUA.encode(), seen=seen))
    assert summary == {"status": "skipped", "version": "v1", "reason": "same version"}
    assert seen == [FOREVERDB_MANIFEST]  # сам Recipes.lua не скачивали


def test_run_writes_db_and_debug_copy(conn, tmp_path):
    summary = run(conn, None, force=False, http=_transport("v3", LUA.encode()))
    assert summary["status"] == "updated"
    assert summary["version"] == "v3"
    assert summary["recipes_total"] == 7
    assert summary["names"]["skipped"] == "no client"
    assert db.get_meta(conn, "recipes_version") == "v3"
    assert conn.execute("select count(*) as n from craft.recipes").fetchone()["n"] == 7
    row = conn.execute("select source_type, recipe_item_id from craft.recipes where id = 3230").fetchone()
    assert (row["source_type"], row["recipe_item_id"]) == ("scroll", 2553)
    assert (tmp_path / "foreverdb" / "Recipes.lua").read_bytes() == LUA.encode()
    json.dumps(summary, ensure_ascii=False)  # сводка сериализуется


# --- Blizzard: имена и сверка ----------------------------------------------------

class FakeClient:
    """Отдаёт static-ответы по пути; профессия алхимии (171) с двумя рецептами."""

    def __init__(self):
        self.pages = {
            "/data/wow/profession/171": {"skill_tiers": [{"id": 2937}]},
            "/data/wow/profession/171/skill-tier/2937": {"categories": [{"recipes": [{"id": 1}, {"id": 2}, {"id": 1}]}]},
            "/data/wow/recipe/1": {
                "id": 1, "name": "Слабое лечебное зелье",
                "crafted_item": {"id": 118, "name": "Слабое лечебное зелье"},
                "reagents": [
                    {"reagent": {"id": 2447, "name": "Мироцвет"}, "quantity": 1},
                    {"reagent": {"id": 765, "name": "Сребролист"}, "quantity": 1},
                    {"reagent": {"id": 3371, "name": "Пустая колба"}, "quantity": 1},
                ],
                "crafted_quantity": {"value": 1.0},
            },
            "/data/wow/recipe/2": {
                "id": 2, "name": "Слабое зелье маны",
                "crafted_item": {"id": 2455, "name": "Слабое зелье маны"},
                "reagents": [{"reagent": {"id": 785, "name": "Магороза"}, "quantity": 2}],
                "crafted_quantity": {"minimum": 1, "maximum": 3},
            },
        }
        self.calls: list[tuple[str, str]] = []

    def get(self, path, namespace=None, if_modified_since=None):
        self.calls.append((path, namespace))
        data = self.pages.get(path)
        return Fetch(200 if data is not None else 404, data)


def test_fetch_blizzard_recipes_and_names():
    client = FakeClient()
    bliz, errors = fetch_blizzard_recipes(client, workers=2)
    assert errors == 0
    assert sorted(r["id"] for r in bliz["alchemy"]) == [1, 2]       # дубль id в категории не тянем дважды
    assert all(ns == "static-forever-eu" for _, ns in client.calls)
    mana = next(r for r in bliz["alchemy"] if r["id"] == 2)
    assert mana["output_qty"] == 2.0
    items, recipes = ru_names(bliz)
    assert items[3371] == "Пустая колба"
    assert recipes[("alchemy", 118)] == "Слабое лечебное зелье"


def test_cross_check(tables):
    data, _ = normalize(tables["recipes"], tables["names"])
    bliz, _ = fetch_blizzard_recipes(FakeClient(), workers=2)
    check = cross_check(data["recipes"], bliz)
    # 118: совпадает; 2455: у Blizzard 2 Магорозы, у ForeverDB другой состав -> расхождение
    assert check["reagents_match"] == 1
    assert check["reagents_differ"] == 1
    assert check["only_in_blizzard"] == 0
    assert check["only_in_foreverdb"] == 5   # 2457, 8067 (инженерия), 2840 и 11371 (плавка), 2570 (портняжное)
    assert check["examples"][0]["output_item_id"] == 2455
