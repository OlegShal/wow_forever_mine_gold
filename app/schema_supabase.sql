-- «Мои выборки»: только в Supabase (нужны auth.uid() и auth.users). Браузер ходит сюда напрямую через supabase-js
-- с публичным ключом; доступ ограничен RLS — каждый пользователь видит и меняет только свои строки.
create table if not exists public.saved_filters (
    id         uuid primary key default gen_random_uuid(),
    user_id    uuid not null default auth.uid() references auth.users(id) on delete cascade,
    name       text not null check (char_length(name) between 1 and 80),
    filters    jsonb not null check (pg_column_size(filters) < 16384),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (user_id, name)
);

alter table public.saved_filters enable row level security;

drop policy if exists saved_filters_select on public.saved_filters;
drop policy if exists saved_filters_insert on public.saved_filters;
drop policy if exists saved_filters_update on public.saved_filters;
drop policy if exists saved_filters_delete on public.saved_filters;

create policy saved_filters_select on public.saved_filters
    for select to authenticated using ((select auth.uid()) = user_id);
create policy saved_filters_insert on public.saved_filters
    for insert to authenticated with check ((select auth.uid()) = user_id);
create policy saved_filters_update on public.saved_filters
    for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy saved_filters_delete on public.saved_filters
    for delete to authenticated using ((select auth.uid()) = user_id);

revoke all on public.saved_filters from anon;
grant select, insert, update, delete on public.saved_filters to authenticated;

-- Текущие фильтры вошедшего пользователя: одна строка на аккаунт, сайт сохраняет её сам при каждом изменении
-- и восстанавливает при входе с любого устройства. Доступ — только к своей строке (RLS).
create table if not exists public.user_filters (
    user_id    uuid primary key default auth.uid() references auth.users(id) on delete cascade,
    filters    jsonb not null check (pg_column_size(filters) < 16384),
    updated_at timestamptz not null default now()
);

alter table public.user_filters enable row level security;

drop policy if exists user_filters_select on public.user_filters;
drop policy if exists user_filters_insert on public.user_filters;
drop policy if exists user_filters_update on public.user_filters;

create policy user_filters_select on public.user_filters
    for select to authenticated using ((select auth.uid()) = user_id);
create policy user_filters_insert on public.user_filters
    for insert to authenticated with check ((select auth.uid()) = user_id);
create policy user_filters_update on public.user_filters
    for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

revoke all on public.user_filters from anon;
grant select, insert, update on public.user_filters to authenticated;
