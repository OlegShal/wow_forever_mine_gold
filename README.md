# wow_forever_mine_gold

Калькулятор выгоды крафта для **WoW Forever** (регион EU). Сайт на английском по умолчанию, русский — кнопкой RU.

Все профессии с рецептами: алхимия, кузнечное дело, наложение чар, инженерное дело, кожевничество, портняжное дело,
горное дело (плавка), кулинария, первая помощь и лагерные рецепты травничества, снятия шкур и рыбной ловли.
Чары на вещь (без предмета-результата) не считаются — их не продать на аукционе.

Для каждого рецепта:
- цена результата на аукционе;
- себестоимость в двух вариантах — **из сырья** (промежуточные реагенты — слитки, рулоны ткани, эссенции — делаешь сам,
  сырьё покупаешь на аукционе) и **реагенты с аукциона** (всё, что просит рецепт, покупаешь готовым);
- прибыль по каждому варианту: цена продажи − 5% комиссии аукциона − себестоимость;
- уровень навыка для изучения и цена рецепта (тренер / свиток с аукциона);
- разбор «по кускам» — дерево того, из чего складывается себестоимость.

Аукцион выбирается в два шага: фракция (Альянс / Орда / Черноводье — нейтральный), потом дом.
Blizzard отдаёт дома без названий серверов; цены между домами сильно различаются, поэтому в одну цену они не сводятся.

## Как устроено

| Часть | Где | Что делает |
|---|---|---|
| Сбор данных | GitHub Actions, cron раз в 30 мин (`.github/workflows/collect.yml`) | `python -m app.job`: рецепты из ForeverDB (если вышла новая выгрузка) → цены аукциона Blizzard → расчёт таблиц и деревьев по каждому дому → Postgres |
| База и вход | Supabase | Схема `craft` (данные калькулятора, наружу не выставлена) и `public.saved_filters` (выборки, RLS: каждый видит только свои) |
| Сайт и API | Vercel | Статика из `public/`, Python-функция `api/index.py` (FastAPI, только чтение готовых результатов) |

Источники данных:
- **Цены** — только аукцион Blizzard Game Data API (`dynamic-forever-eu`): рыночная цена = средняя по самым дешёвым 15% выставленного количества.
- **Рецепты и источник рецепта** — выгрузка аддона [ForeverDB](https://foreverdb.net) (`Data/Recipes.lua`, проверка sha256), оттуда же английские названия. Data from ForeverDB.net, GPL-3.0 — ссылка на сайте обязательна.
- **Русские названия** — Blizzard static API (`static-forever-eu`), реагенты сверяются с ForeverDB.

Цены обучения у тренера в открытых данных нет — в таблице «тренер, цена ?».

## Настройка (один раз)

1. **Supabase**: создать проект. Схема создастся сама при первом прогоне джоба.
   - Authentication → Sign In / Providers → **Google**: Client ID и Secret из Google Cloud Console
     (APIs & Services → Credentials → OAuth client ID → Web application;
     Authorized redirect URI: `https://<project-ref>.supabase.co/auth/v1/callback`).
   - Authentication → URL Configuration: **Site URL** = адрес сайта на Vercel; в Redirect URLs добавить его же
     и `http://localhost:8000` для локальной разработки.
2. **GitHub → Settings → Secrets and variables → Actions**:
   `BLIZZ_CLIENT_ID`, `BLIZZ_CLIENT_SECRET` (develop.battle.net → API Access), `DATABASE_URL`
   (Supabase → Connect → **Transaction pooler**, порт 6543 — прямое подключение Supabase только IPv6, раннеры GitHub его не видят).
3. **Vercel**: импорт репозитория, Framework Preset **Other**, Output Directory `public`. Environment Variables:
   `DATABASE_URL` (тот же pooler), `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY` (публичный `sb_publishable_…`).
   **Секретный ключ Supabase (`sb_secret_…`) никуда не класть** — он не нужен; API его в браузер не отдаст, даже если перепутать переменные.
4. Actions → **collect** → Run workflow (первый прогон ~1,5 мин). Дальше — автоматически каждые 30 минут.
   GitHub отключает расписание после 60 дней без коммитов — включить обратно: Actions → collect → Enable workflow.

## Локальная разработка

```bash
docker run -d --name forever-pg -e POSTGRES_PASSWORD=postgres -p 127.0.0.1:55432:5432 postgres:16
export DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:55432/postgres
uv sync
uv run python -m app.job                         # креды Blizzard: env или ~/battlenet.creds
SERVE_STATIC=1 uv run uvicorn app.api:app --port 8000
TEST_DATABASE_URL=$DATABASE_URL uv run pytest    # тесты сносят схему craft — только локальная база
```

Перегенерировать `requirements.txt` после смены зависимостей:
`uv export --no-dev --no-hashes --no-header --format requirements-txt -o requirements.txt`.
