"""Клиент Blizzard Game Data API для WoW Forever (OAuth client credentials).

Пути Forever Blizzard не документирует; проверены живыми запросами 2026-11-08:
  dynamic: /data/wow/ruleset/index
           /data/wow/ruleset/{id}/auctions/                    <- только со слешем в конце (без него 404)
           /data/wow/ruleset/{id}/auctions/{house}             <- обычные лоты, quantity всегда 1, buyout за лот
           /data/wow/ruleset/{id}/auctions/{house}/commodities <- unit_price за штуку
  static:  /data/wow/profession/{id}, /data/wow/profession/{id}/skill-tier/{tier}, /data/wow/recipe/{id}
If-Modified-Since поддерживается (304).
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass

import httpx

from .config import API_HOST, LOCALE, NS_DYNAMIC, OAUTH_URL

log = logging.getLogger(__name__)


@dataclass
class Fetch:
    status: int
    data: dict | None
    last_modified: str | None = None

    @property
    def not_modified(self) -> bool:
        return self.status == 304


class BlizzardClient:
    """Потокобезопасен: можно звать get() из нескольких потоков."""

    def __init__(self, client_id: str, client_secret: str, http: httpx.Client | None = None):
        self._id = client_id
        self._secret = client_secret
        self._http = http or httpx.Client(timeout=httpx.Timeout(90.0, connect=10.0))
        self._token: str | None = None
        self._token_exp = 0.0
        self._lock = threading.Lock()

    def _get_token(self, force: bool = False) -> str:
        with self._lock:
            if not force and self._token and time.time() < self._token_exp:
                return self._token
            r = self._http.post(OAUTH_URL, data={"grant_type": "client_credentials"}, auth=(self._id, self._secret))
            r.raise_for_status()
            body = r.json()
            self._token = body["access_token"]
            self._token_exp = time.time() + int(body.get("expires_in", 3600)) - 300
            return self._token

    def get(self, path: str, namespace: str = NS_DYNAMIC, if_modified_since: str | None = None) -> Fetch:
        """200 -> Fetch с данными; 304 -> not_modified; 404 -> Fetch(404, None). Прочие ошибки — исключение."""
        token = self._get_token()
        for attempt in range(4):
            headers = {"Authorization": f"Bearer {token}"}
            if if_modified_since:
                headers["If-Modified-Since"] = if_modified_since
            r = self._http.get(API_HOST + path, params={"namespace": namespace, "locale": LOCALE}, headers=headers)
            if r.status_code == 401 and attempt == 0:
                log.warning("401 от Blizzard на %s, обновляю токен", path)
                token = self._get_token(force=True)
                continue
            if r.status_code in (429, 500, 502, 503, 504) and attempt < 3:
                delay = float(r.headers.get("Retry-After") or 2 ** attempt)
                log.warning("%s от Blizzard на %s, повтор через %.0fс", r.status_code, path, delay)
                time.sleep(delay)
                continue
            if r.status_code == 304:
                return Fetch(304, None, if_modified_since)
            if r.status_code == 404:
                return Fetch(404, None)
            r.raise_for_status()
            return Fetch(r.status_code, r.json(), r.headers.get("Last-Modified"))
        raise RuntimeError(f"Blizzard: не удалось получить {path}")

    # --- аукцион (dynamic) ------------------------------------------------

    def ruleset_ids(self) -> list[int]:
        data = self._require("/data/wow/ruleset/index")
        rulesets = data.get("rulesets")
        if not isinstance(rulesets, list):
            raise ValueError(f"неожиданный ответ ruleset/index, ключи: {sorted(data)}")
        return [int(r["id"]) for r in rulesets]

    def houses(self, ruleset_id: int) -> list[dict]:
        data = self._require(f"/data/wow/ruleset/{ruleset_id}/auctions/")
        return [{"id": int(h["id"]), "name": text(h.get("name")) or f"#{h['id']}"} for h in data.get("auctions") or []]

    def house(self, ruleset_id: int, house_id: int, ims: str | None = None) -> Fetch:
        return self.get(f"/data/wow/ruleset/{ruleset_id}/auctions/{house_id}", if_modified_since=ims)

    def commodities(self, ruleset_id: int, house_id: int, ims: str | None = None) -> Fetch:
        return self.get(f"/data/wow/ruleset/{ruleset_id}/auctions/{house_id}/commodities", if_modified_since=ims)

    def _require(self, path: str, namespace: str = NS_DYNAMIC) -> dict:
        f = self.get(path, namespace)
        if f.data is None:
            raise RuntimeError(f"Blizzard {f.status} на {path}")
        return f.data


def text(value) -> str | None:
    """Имя может прийти строкой (с locale) или словарём локалей (без него)."""
    if isinstance(value, dict):
        return value.get(LOCALE) or value.get("en_US") or next(iter(value.values()), None)
    return value
