import httpx
import pytest

from app import db
from app.blizzard import BlizzardClient
from app.prices_update import refresh_prices

LM = "Sun, 08 Nov 2026 13:12:16 GMT"


class FakeBlizzard:
    """Мок Blizzard API по путям, проверенным на живом API."""

    def __init__(self):
        self.calls: list[str] = []
        self.token_calls = 0
        self.fail_house: int | None = None
        self.house_lots = {
            110: [{"id": 1, "item": {"id": 2589}, "buyout": 100, "quantity": 1, "time_left": "LONG"},
                  {"id": 2, "item": {"id": 2589}, "buyout": 300, "quantity": 1, "time_left": "LONG"}],
            112: None,  # пустой дом: поля auctions нет вовсе
        }

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.host == "oauth.battle.net":
            self.token_calls += 1
            return httpx.Response(200, json={"access_token": f"t{self.token_calls}", "expires_in": 86399})
        path = request.url.path
        self.calls.append(path)
        assert request.headers["Authorization"].startswith("Bearer ")
        assert request.url.params["namespace"] == "dynamic-forever-eu"
        if path == "/data/wow/ruleset/index":
            return httpx.Response(200, json={"rulesets": [{"id": 1}, {"id": 2}]})
        if path in ("/data/wow/ruleset/1/auctions/", "/data/wow/ruleset/2/auctions/"):
            return httpx.Response(200, json={"auctions": [{"id": 110, "name": "Аукционный дом Альянса"},
                                                          {"id": 112, "name": "Аукционный дом Альянса"}]})
        for hid in (110, 112):
            if path == f"/data/wow/ruleset/1/auctions/{hid}":
                if hid == self.fail_house:
                    return httpx.Response(503)
                if request.headers.get("If-Modified-Since") == LM:
                    return httpx.Response(304)
                body = {"id": hid, "name": "x"}
                if self.house_lots[hid] is not None:
                    body["auctions"] = self.house_lots[hid]
                return httpx.Response(200, json=body, headers={"Last-Modified": LM})
            if path == f"/data/wow/ruleset/1/auctions/{hid}/commodities":
                if request.headers.get("If-Modified-Since") == LM:
                    return httpx.Response(304)
                return httpx.Response(200, json={"auctions": [
                    {"id": 9, "item": {"id": 2770}, "quantity": 20, "unit_price": 83, "time_left": "LONG"}]},
                    headers={"Last-Modified": LM})
        return httpx.Response(404)


@pytest.fixture
def setup(pg, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    fake = FakeBlizzard()
    client = BlizzardClient("id", "secret", http=httpx.Client(transport=httpx.MockTransport(fake)))
    return fake, client, pg


def prices(conn, hid):
    return {r["item_id"]: r for r in conn.execute("select * from craft.ah_prices where house_id = %s", (hid,))}


def test_collects_prices_and_house_meta(setup):
    fake, client, conn = setup
    s = refresh_prices(conn, client)
    assert s["updated"] == [110, 112] and not s["failed"]
    p = prices(conn, 110)
    assert p[2589]["min_unit"] == 100 and p[2589]["quantity"] == 2
    assert p[2770]["market_unit"] == 83
    assert set(prices(conn, 112)) == {2770}
    h = conn.execute("select * from craft.houses where id = 110").fetchone()
    assert h["lots"] == 3 and h["ruleset_id"] == 1 and h["lm_auctions"] == LM
    # дом 110 есть в обоих rulesets, но качается один раз
    assert fake.calls.count("/data/wow/ruleset/1/auctions/110") == 1
    assert "/data/wow/ruleset/2/auctions/110" not in fake.calls
    assert fake.token_calls == 1


def test_unchanged_houses_are_not_rewritten(setup):
    fake, client, conn = setup
    refresh_prices(conn, client)
    before = conn.execute("select updated_at from craft.houses where id = 110").fetchone()["updated_at"]
    s = refresh_prices(conn, client)
    assert s["unchanged"] == [110, 112] and s["updated"] == []
    assert conn.execute("select updated_at from craft.houses where id = 110").fetchone()["updated_at"] == before


def test_failed_house_keeps_old_prices(setup):
    fake, client, conn = setup
    refresh_prices(conn, client)
    conn.execute("update craft.houses set lm_auctions = null, lm_commodities = null")
    fake.fail_house = 110
    s = refresh_prices(conn, client)
    assert 110 in s["failed"] and s["updated"] == [112]
    assert prices(conn, 110)[2589]["min_unit"] == 100
    assert conn.execute("select last_error from craft.houses where id = 110").fetchone()["last_error"]
