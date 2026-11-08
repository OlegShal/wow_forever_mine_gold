"""Полный прогон джоба на моках: ForeverDB (Recipes.lua) + Blizzard (аукцион) -> craft.house_results."""
import hashlib

import httpx
import pytest

from app.blizzard import BlizzardClient
from app.config import FOREVERDB_MANIFEST, FOREVERDB_SITE
from app.job import failed, run_once
from tests.test_prices_update import FakeBlizzard

LUA = """local _, ns = ...
ns.recipes = {Mining={{2657,"Smelt Copper",1,25,47,70,2840,1,"2770:1","t",0,0,0}},Blacksmithing={{2660,"Rough Sharpening Stone",1,15,35,55,2862,1,"2835:1,2840:1","i7",0,0,0}}}
ns.names = {[2770]="Copper Ore",[2840]="Copper Bar",[2862]="Rough Sharpening Stone",[2835]="Rough Stone",[7]="Plans"}
"""


def foreverdb(version="v1"):
    body = LUA.encode()
    manifest = {"data": {"version": version, "files": [
        {"path": "Data/Recipes.lua", "url": "downloads/addon-data/Recipes.lua?v=1",
         "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}]}}

    def handler(request):
        if str(request.url) == FOREVERDB_MANIFEST:
            return httpx.Response(200, json=manifest)
        if str(request.url).startswith(f"{FOREVERDB_SITE}/downloads/addon-data/Recipes.lua"):
            return httpx.Response(200, content=body)
        return httpx.Response(404)
    return httpx.Client(transport=httpx.MockTransport(handler))


class Blizzard(FakeBlizzard):
    """Аукцион из FakeBlizzard + 404 на static (русских имён нет — останутся английские)."""

    def __call__(self, request):
        if request.url.params.get("namespace") == "static-forever-eu":
            return httpx.Response(404)
        return super().__call__(request)


@pytest.fixture
def env(pg, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    fake = Blizzard()
    fake.house_lots[110] = [
        {"id": 1, "item": {"id": 2862}, "buyout": 500, "quantity": 1, "time_left": "LONG"},
        {"id": 2, "item": {"id": 2840}, "buyout": 100, "quantity": 1, "time_left": "LONG"},
        {"id": 3, "item": {"id": 2835}, "buyout": 6, "quantity": 1, "time_left": "LONG"},
    ]
    client = BlizzardClient("id", "secret", http=httpx.Client(transport=httpx.MockTransport(fake)))
    return pg, client, fake


def test_full_run_then_incremental(env):
    pg, client, fake = env
    s = run_once(pg, client, http=foreverdb())
    assert s["recipes"]["status"] == "updated"
    assert s["prices"]["updated"] == [110, 112]
    assert s["results"]["rows"] == {110: 2, 112: 2}
    assert not failed(s)
    rows = pg.execute("select rows from craft.house_results where house_id = 110").fetchone()["rows"]
    row = next(r for r in rows if r["id"] == 2660)
    assert row["name"] == "Rough Sharpening Stone"
    assert row["cost_craft"] == 6 + 83          # медь: руда с commodities (83) -> плавка
    assert row["profit_craft"] == round(500 * 0.95 - 89)

    # второй прогон: рецепты той же версии, аукцион не менялся (304) -> ничего не пересчитываем
    s2 = run_once(pg, client, http=foreverdb())
    assert s2["recipes"]["status"] == "skipped"
    assert s2["prices"]["unchanged"] == [110, 112]
    assert s2["results"] == {"skipped": "нечего пересчитывать"}
    assert not failed(s2)


def test_recipes_error_still_collects_prices_and_fails_run(env):
    pg, client, fake = env
    broken = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(503)))
    s = run_once(pg, client, http=broken)
    assert s["recipes"]["status"] == "error"
    assert s["prices"]["updated"] == [110, 112]
    assert s["results"] == {"skipped": "нет рецептов"}
    assert failed(s)
