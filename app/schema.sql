-- Данные калькулятора. Схема craft НЕ выставлена в Supabase Data API: anon/authenticated доступа не имеют,
-- читает и пишет только серверный код по DATABASE_URL. Миграция идемпотентна (запускается каждым прогоном джоба).
create schema if not exists craft;
revoke all on schema craft from public;

create table if not exists craft.items (
    id      integer primary key,
    name    text not null,
    name_en text
);

create table if not exists craft.recipes (
    id             integer primary key,           -- spell id
    profession     text not null,
    name           text not null,
    output_item_id integer not null,
    output_qty     double precision not null,
    learn_skill    integer,
    skill_yellow   integer,
    skill_green    integer,
    skill_grey     integer,
    source_type    text not null,                 -- trainer | scroll | auto | unknown
    source_cost    bigint,
    recipe_item_id integer,
    new_in_forever boolean not null default false
);
alter table craft.recipes add column if not exists name_en text;  -- английское название (ForeverDB)

create table if not exists craft.reagents (
    recipe_id integer not null references craft.recipes(id) on delete cascade,
    item_id   integer not null,
    qty       double precision not null
);
create index if not exists reagents_recipe on craft.reagents(recipe_id);

create table if not exists craft.houses (
    id             integer primary key,
    name           text not null,
    ruleset_id     integer,
    lots           integer,
    updated_at     timestamptz,
    checked_at     timestamptz,
    last_error     text,
    lm_auctions    text,
    lm_commodities text
);

create table if not exists craft.ah_prices (
    house_id    integer not null,
    item_id     integer not null,
    min_unit    bigint not null,
    market_unit bigint not null,
    quantity    integer not null,
    auctions    integer not null,
    primary key (house_id, item_id)
);

-- Готовые строки таблицы и деревья «по кускам» на дом: API отдаёт их как есть.
create table if not exists craft.house_results (
    house_id     integer primary key references craft.houses(id) on delete cascade,
    data_version bigint not null,
    computed_at  timestamptz not null default now(),
    rows         jsonb not null,
    trees        jsonb not null
);

create table if not exists craft.meta (
    key   text primary key,
    value text
);
