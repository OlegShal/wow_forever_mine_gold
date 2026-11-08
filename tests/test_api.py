import pytest
from fastapi.testclient import TestClient

from app import api, db, results

DATA = {
    "version": "test-1",
    "items": [
        {"id": 2770, "name": "Медная руда"}, {"id": 2840, "name": "Медный слиток"},
        {"id": 2862, "name": "Грубое точило", "name_en": "Rough Sharpening Stone"},
        {"id": 2835, "name": "Грубый камень", "name_en": "Rough Stone"},
        {"id": 7, "name": "Свиток", "name_en": "Plans: Rough Sharpening Stone"},
    ],
    "recipes": [
        {"id": 2657, "profession": "mining", "name": "Выплавка меди", "output_item_id": 2840, "output_qty": 1,
         "learn_skill": 1, "source_type": "trainer", "reagents": [{"item_id": 2770, "qty": 1}]},
        {"id": 2660, "profession": "blacksmithing", "name": "Грубое точило", "name_en": "Rough Sharpening Stone",
         "output_item_id": 2862, "output_qty": 1,
         "learn_skill": 1, "skill": {"yellow": 15}, "source_type": "scroll", "recipe_item_id": 7,
         "reagents": [{"item_id": 2835, "qty": 1}, {"item_id": 2840, "qty": 1}]},
    ],
}


@pytest.fixture
def client(pg, monkeypatch):
    db.replace_recipe_data(pg, DATA)
    pg.execute("insert into craft.houses(id, name, lots, updated_at) values (110, 'Аукционный дом Альянса', 3, now())")
    with pg.cursor() as cur:
        cur.executemany("insert into craft.ah_prices values (110, %s, %s, %s, %s, %s)", [
            (2770, 80, 83, 100, 3), (2840, 90, 100, 100, 3), (2835, 5, 6, 10, 1), (2862, 400, 500, 4, 2),
            (7, 9000, 9500, 1, 1),
        ])
    results.compute(pg, [110], db.bump_version(pg))
    monkeypatch.setattr(api, "_conn", None)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    return TestClient(api.app)


def test_status(client):
    r = client.get("/api/status")
    s = r.json()
    assert s["recipes"]["count"] == 2          # точило и плавка: горное дело тоже в таблице
    assert s["recipes"]["version"] == "test-1"
    assert s["houses"][0]["id"] == 110 and s["houses"][0]["updated_at"].endswith("Z")
    assert s["data_version"] == "1"
    assert "s-maxage" in r.headers["cache-control"]


def test_recipes_rows(client):
    body = client.get("/api/recipes", params={"house_id": 110}).json()
    assert body["data_version"] == "1"
    assert {r["name"] for r in body["rows"]} == {"Грубое точило", "Выплавка меди"}
    row = next(r for r in body["rows"] if r["id"] == 2660)
    assert row["cost_buy"] == 6 + 100
    assert row["cost_craft"] == 6 + 83          # слиток своей плавкой из руды
    assert row["profit_craft"] == round(500 * 0.95 - 89)
    assert row["recipe_price"] == {"amount": 9000, "source": "scroll", "item_id": 7, "name": "Свиток",
                                   "name_en": "Plans: Rough Sharpening Stone"}
    assert {g["name"] for g in row["reagents"]} == {"Грубый камень", "Медный слиток"}
    # английское имя; если его нет в данных — подставляется русское
    assert row["name_en"] == "Rough Sharpening Stone"
    assert {g["name_en"] for g in row["reagents"]} == {"Rough Stone", "Медный слиток"}
    assert row["skill_yellow"] == 15


def test_tree(client):
    t = client.get("/api/recipes/2660/tree", params={"house_id": 110}).json()
    assert t["name"] == "Грубое точило"
    bar = next(c for c in t["children"] if c["item_id"] == 2840)
    assert t["name_en"] == "Rough Sharpening Stone"
    assert bar["chosen"] == "craft" and bar["recipe_name"] == "Выплавка меди"
    assert bar["recipe_name_en"] == "Выплавка меди"     # у плавки в данных нет английского имени
    assert bar["children"][0]["name"] == "Медная руда"


def test_unknown_house_and_recipe(client):
    assert client.get("/api/recipes", params={"house_id": 999}).status_code == 404
    assert client.get("/api/recipes/424242/tree", params={"house_id": 110}).status_code == 404


def test_config_without_supabase(client):
    assert client.get("/api/config").json() == {"supabase_url": None, "supabase_anon_key": None}


def test_config_never_exposes_secret_key(client, monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_secret_oops")
    assert client.get("/api/config").json() == {"supabase_url": None, "supabase_anon_key": None}
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_ok")
    assert client.get("/api/config").json() == {"supabase_url": "https://x.supabase.co",
                                                "supabase_anon_key": "sb_publishable_ok"}
