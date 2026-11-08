"""Константы и настройки окружения. Регион и комиссия — константы, а не настройки."""
from __future__ import annotations

import base64
import json
import logging
import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

log = logging.getLogger(__name__)

REGION = "eu"
API_HOST = f"https://{REGION}.api.blizzard.com"
OAUTH_URL = "https://oauth.battle.net/token"
NS_DYNAMIC = f"dynamic-forever-{REGION}"
NS_STATIC = f"static-forever-{REGION}"
LOCALE = "ru_RU"

# Выгрузка данных аддона ForeverDB (GPL-3.0, обязательна ссылка «Data from ForeverDB.net»).
FOREVERDB_SITE = "https://foreverdb.net"
FOREVERDB_MANIFEST = f"{FOREVERDB_SITE}/downloads/addon-manifest.json"

# slug -> (ключ в ForeverDB Recipes.lua, id профессии в Blizzard API). Все профессии с рецептами:
# все показываются в таблице и все участвуют в «крафчу сам» (плавка, рулоны ткани, эссенции и т.п.).
# Зачарования без предмета-результата (чары на вещь) отбрасываются при загрузке — их не продать на аукционе.
PROFESSIONS = {
    "alchemy": ("Alchemy", 171),
    "blacksmithing": ("Blacksmithing", 164),
    "enchanting": ("Enchanting", 333),
    "engineering": ("Engineering", 202),
    "leatherworking": ("Leatherworking", 165),
    "tailoring": ("Tailoring", 197),
    "mining": ("Mining", 186),
    "cooking": ("Cooking", 185),
    "first_aid": ("First Aid", 129),
    "herbalism": ("Herbalism", 182),
    "skinning": ("Skinning", 393),
    "fishing": ("Fishing", 356),
}
ALL_PROFESSIONS = PROFESSIONS
CRAFTABLE_PROFESSIONS = tuple(PROFESSIONS)

AH_CUT = 0.05           # комиссия аукциона с продажи
MARKET_SHARE = 0.15     # рыночная цена = средняя по самым дешёвым 15% выставленного количества

PRICE_INTERVAL_SEC = 30 * 60

# Параметры строки подключения, которые понимает libpq; остальное (например supa=... из интеграции Vercel) отбрасываем.
_LIBPQ_PARAMS = {
    "sslmode", "sslrootcert", "sslcert", "sslkey", "connect_timeout", "application_name",
    "options", "target_session_attrs", "channel_binding", "keepalives", "keepalives_idle",
}


def env(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def clean_dsn(url: str) -> str:
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if k in _LIBPQ_PARAMS]
    return urlunsplit(parts._replace(query=urlencode(query)))


def database_url() -> str:
    """DATABASE_URL (Supabase → Connect → Transaction pooler) или POSTGRES_URL из интеграции Vercel."""
    url = env("DATABASE_URL", "POSTGRES_URL")
    if not url:
        raise RuntimeError("нет DATABASE_URL: строка подключения Supabase (Connect → Transaction pooler)")
    return clean_dsn(url)


def cache_dir() -> Path:
    return Path(env("CACHE_DIR") or "data")


def _is_secret_key(key: str) -> bool:
    if key.startswith("sb_secret_"):
        return True
    parts = key.split(".")
    if len(parts) == 3:  # старый формат ключей — JWT; service_role обходит RLS
        try:
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))
            return payload.get("role") == "service_role"
        except ValueError:
            return False
    return False


def supabase_public() -> dict:
    """Публичные настройки Supabase для браузера. Секретный ключ сюда не попадёт ни при какой ошибке конфигурации."""
    url = env("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL")
    key = env("SUPABASE_PUBLISHABLE_KEY", "SUPABASE_ANON_KEY",
              "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY")
    if key and _is_secret_key(key):
        log.error("в публичной переменной Supabase лежит СЕКРЕТНЫЙ ключ — не отдаю его в браузер")
        key = None
    if not (url and key):
        return {"supabase_url": None, "supabase_anon_key": None}
    return {"supabase_url": url, "supabase_anon_key": key}


def blizzard_creds() -> tuple[str, str] | None:
    """BLIZZ_CLIENT_ID/BLIZZ_CLIENT_SECRET из окружения, иначе из файла CREDS_FILE (по умолчанию ~/battlenet.creds)."""
    cid, secret = env("BLIZZ_CLIENT_ID"), env("BLIZZ_CLIENT_SECRET")
    if cid and secret:
        return cid, secret
    path = Path(env("CREDS_FILE") or Path.home() / "battlenet.creds")
    if not path.is_file():
        return None
    values = {}
    for line in path.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip().strip('"').strip("'")
    cid, secret = values.get("BLIZZ_CLIENT_ID"), values.get("BLIZZ_CLIENT_SECRET")
    return (cid, secret) if cid and secret else None
