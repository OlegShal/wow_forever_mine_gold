"""RLS «моих выборок» на локальном Postgres с имитацией Supabase: схема auth, auth.uid(), роли anon/authenticated.

В Supabase auth.uid() читает sub из JWT запроса (request.jwt.claims); здесь — то же через set_config.
"""
import uuid

import psycopg
import pytest

from app import db

FAKE_SUPABASE = """
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then create role anon nologin; end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then create role authenticated nologin; end if;
end $$;
create schema if not exists auth;
create table if not exists auth.users (id uuid primary key);
create or replace function auth.uid() returns uuid language sql stable as $$
  select nullif(current_setting('request.jwt.claims', true)::json ->> 'sub', '')::uuid
$$;
grant usage on schema auth to anon, authenticated;
grant usage on schema public to anon, authenticated;
"""

ALICE, BOB = uuid.uuid4(), uuid.uuid4()


@pytest.fixture
def sb(pg):
    pg.execute("drop table if exists public.saved_filters, public.user_filters")
    pg.execute(FAKE_SUPABASE)
    pg.execute("insert into auth.users values (%s), (%s) on conflict do nothing", (ALICE, BOB))
    db.migrate(pg)  # теперь схема auth есть -> накатится schema_supabase.sql
    yield pg
    pg.execute("drop table if exists public.saved_filters, public.user_filters")
    pg.execute("drop schema if exists auth cascade")


def as_user(conn, user: uuid.UUID | None):
    """Начать транзакцию от имени пользователя (как PostgREST): роль + claims."""
    tx = conn.transaction()
    tx.__enter__()
    if user is None:
        conn.execute("set local role anon")
    else:
        conn.execute("set local role authenticated")
        conn.execute("select set_config('request.jwt.claims', %s, true)", (f'{{"sub": "{user}"}}',))
    return tx


def done(tx):
    tx.__exit__(None, None, None)


def test_users_see_only_their_filters(sb):
    tx = as_user(sb, ALICE)
    sb.execute("insert into public.saved_filters(name, filters) values ('алхимия', '{\"v\":1}')")
    done(tx)
    tx = as_user(sb, BOB)
    sb.execute("insert into public.saved_filters(name, filters) values ('кузня', '{\"v\":1}')")
    assert [r["name"] for r in sb.execute("select name from public.saved_filters")] == ["кузня"]
    # чужую запись нельзя ни изменить, ни удалить: 0 строк
    assert sb.execute("update public.saved_filters set name = 'взлом' where name = 'алхимия'").rowcount == 0
    assert sb.execute("delete from public.saved_filters where name = 'алхимия'").rowcount == 0
    done(tx)
    tx = as_user(sb, ALICE)
    assert [r["name"] for r in sb.execute("select name from public.saved_filters")] == ["алхимия"]
    done(tx)


def test_cannot_insert_for_someone_else(sb):
    tx = as_user(sb, ALICE)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        sb.execute("insert into public.saved_filters(user_id, name, filters) values (%s, 'x', '{}')", (BOB,))
    tx.__exit__(psycopg.errors.InsufficientPrivilege, None, None)


def test_anon_has_no_access(sb):
    tx = as_user(sb, None)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        sb.execute("select * from public.saved_filters")
    tx.__exit__(psycopg.errors.InsufficientPrivilege, None, None)


def test_anon_cannot_read_calculator_data(sb):
    tx = as_user(sb, ALICE)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        sb.execute("select * from craft.meta")
    tx.__exit__(psycopg.errors.InsufficientPrivilege, None, None)


def test_upsert_same_name_overwrites(sb):
    tx = as_user(sb, ALICE)
    for v in (1, 2):
        sb.execute(
            "insert into public.saved_filters(name, filters) values ('моя', %s) "
            "on conflict (user_id, name) do update set filters = excluded.filters, updated_at = now()",
            (f'{{"v":{v}}}',),
        )
    rows = sb.execute("select filters from public.saved_filters").fetchall()
    assert [r["filters"] for r in rows] == [{"v": 2}]
    done(tx)


# --- текущие фильтры аккаунта (public.user_filters): одна строка на пользователя ---

UPSERT_CURRENT = (
    "insert into public.user_filters(filters) values (%s) "
    "on conflict (user_id) do update set filters = excluded.filters, updated_at = now()"
)


def test_current_filters_one_row_per_user_and_private(sb):
    tx = as_user(sb, ALICE)
    for v in (1, 2):  # как upsert из supabase-js: второе сохранение перезаписывает ту же строку
        sb.execute(UPSERT_CURRENT, (f'{{"v":{v},"house":110}}',))
    assert [r["filters"] for r in sb.execute("select filters from public.user_filters")] == [{"v": 2, "house": 110}]
    done(tx)
    tx = as_user(sb, BOB)
    assert sb.execute("select * from public.user_filters").fetchall() == []  # чужую строку не видно
    assert sb.execute("update public.user_filters set filters = '{}'").rowcount == 0
    sb.execute(UPSERT_CURRENT, ('{"v":1,"house":113}',))
    assert [r["filters"]["house"] for r in sb.execute("select filters from public.user_filters")] == [113]
    done(tx)
    tx = as_user(sb, ALICE)
    assert [r["filters"]["house"] for r in sb.execute("select filters from public.user_filters")] == [110]
    done(tx)


def test_current_filters_cannot_write_for_someone_else(sb):
    tx = as_user(sb, ALICE)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        sb.execute("insert into public.user_filters(user_id, filters) values (%s, '{}')", (BOB,))
    tx.__exit__(psycopg.errors.InsufficientPrivilege, None, None)


def test_current_filters_anon_has_no_access(sb):
    tx = as_user(sb, None)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        sb.execute("select * from public.user_filters")
    tx.__exit__(psycopg.errors.InsufficientPrivilege, None, None)
