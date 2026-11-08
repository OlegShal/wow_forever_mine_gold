(() => {
  'use strict';

  // ---------- языки ----------
  // Английский по умолчанию, русский — по кнопке RU (выбор запоминается в браузере).

  const I18N = {
    en: {
      title: 'Craft profit calculator',
      loading: 'Loading…',
      'auth.login': 'Sign in with Google',
      'auth.logout': 'Sign out',
      'auth.signed': 'signed in',
      'auth.unavailable': (e) => `sign-in unavailable: ${e}`,
      'auth.nolib': 'sign-in unavailable: the Supabase library failed to load',
      'auth.session': (e) => `session unavailable: ${e}`,
      'auth.loginFail': (e) => `could not sign in: ${e}`,
      'auth.logoutFail': (e) => `could not sign out: ${e}`,
      filters: 'Filters',
      'f.house': 'Auction house',
      'f.faction': 'Faction',
      'hint.house.aria': 'What are these auction houses?',
      'hint.house': '<b>What are these houses?</b> Blizzard\'s API lists 15 WoW Forever (EU) auction houses '
        + 'without realm names — only the faction and an internal number. Each house is a separate market with its own '
        + 'prices: the two largest Alliance houses differ by ~15% on a typical item, smaller ones by 30–50%, '
        + 'so they are not merged into one price.<br><b>How to pick:</b> choose your faction, then your realm\'s house. '
        + 'The biggest houses (most listings) are the most populated realms. Not sure which one is yours? '
        + 'Compare a couple of common items (bars, cloth) with the in-game auction house.<br>'
        + '<b>Blackwater</b> is the neutral auction house (Booty Bay, Gadgetzan, Everlook) shared by both factions.',
      'fac.alliance': 'Alliance',
      'fac.horde': 'Horde',
      'fac.blackwater': 'Blackwater (neutral)',
      'fac.other': 'Other',
      'house.lots': (n) => `${n} listings`,
      'house.empty': 'empty',
      'house.none': 'no data',
      'f.profs': 'Professions',
      'f.search': 'Search',
      'f.search.ph': 'item name',
      'f.skill': 'Skill',
      'f.from': 'from',
      'f.to': 'to',
      'f.skill.min': 'Skill from',
      'f.skill.max': 'Skill to',
      'f.price': 'AH price, gold',
      'f.price.min': 'AH price from, gold',
      'f.price.max': 'AH price to, gold',
      'f.profit': 'Min. profit, gold',
      'f.profit.ph': 'any',
      'f.profit.aria': 'Minimum profit, gold',
      'f.variant.aria': 'Which way of crafting',
      'v.craft': 'craft from raw materials',
      'v.buy': 'buy all reagents',
      'v.best': 'whichever is better',
      'f.onah': 'only items listed on the AH',
      'f.reset': 'Reset',
      saved: 'My filters',
      'sv.list': 'Saved filters',
      'sv.pick': '— choose —',
      'sv.name.ph': 'name',
      'sv.name.aria': 'Filter set name',
      'sv.save': 'Save current',
      'sv.delete': 'Delete',
      'sv.confirm': (n) => `Really delete “${n}”?`,
      'sv.loadFail': (e) => `could not load saved filters: ${e}`,
      'prefs.loadFail': (e) => `could not load filters from your account: ${e}`,
      'prefs.saveFail': (e) => `could not save filters to your account: ${e}`,
      'sv.broken': (n) => `“${n}” is damaged, filters unchanged`,
      'sv.empty': (n) => `“${n}” has no usable fields, filters unchanged`,
      'sv.applied': (n) => `applied “${n}”`,
      'sv.noName': 'enter a name',
      'sv.tooLong': 'name is longer than 80 characters',
      'sv.saveFail': (e) => `could not save: ${e}`,
      'sv.overwritten': (n) => `“${n}” overwritten`,
      'sv.saved': (n) => `“${n}” saved`,
      'sv.deleteFail': (e) => `could not delete: ${e}`,
      'sv.deleted': (n) => `“${n}” deleted`,
      legend: '<b>From raw materials</b> — you make the intermediate reagents yourself (bars, bolts of cloth, '
        + 'essences…) and buy only raw materials on the AH (ore, cloth, herbs). '
        + '<b>Buying reagents</b> — you buy everything the recipe asks for, ready-made, on the AH. '
        + '<b>Profit</b> = AH sell price − 5% AH cut − cost. Click a row to see what the cost is made of.',
      'col.name': 'Item',
      'col.prof': 'Profession',
      'col.skill': 'Skill',
      'col.sell': 'AH price',
      'col.cost_craft': 'Cost<small>from raw materials</small>',
      'col.profit_craft': 'Profit<small>from raw materials</small>',
      'col.cost_buy': 'Cost<small>buying reagents</small>',
      'col.profit_buy': 'Profit<small>buying reagents</small>',
      'col.recipe': 'Recipe',
      'tip.skill': 'Skill level needed to learn the recipe',
      'tip.sell': 'What one craft sells for on the AH (market price of the cheapest listings)',
      'tip.craft': 'Intermediate reagents crafted by you, raw materials bought on the AH',
      'tip.buy': 'All reagents bought on the AH',
      'tip.recipe': 'How the recipe is learned and what it costs',
      'foot.recipes': 'Recipes:',
      'foot.prices': 'Prices: Blizzard API, every 30 min',
      'st.noServer': 'No connection to the server',
      'st.unavailable': (e) => `Status unavailable: ${e}`,
      'st.updated': (a) => `prices updated ${a}`,
      'st.notLoaded': 'prices not loaded yet',
      'st.stale': ' — data is stale',
      'st.lastCheck': (a) => `last check: ${a}`,
      'st.error': (e) => `update error: ${e}`,
      'st.recipes': (n) => `recipes: ${n}`,
      'st.version': (v) => ` · version ${v}`,
      'ago.never': 'never',
      'ago.now': 'just now',
      'ago.min': (m) => `${m} min ago`,
      'ago.hmin': (h, m) => `${h} h ${m} min ago`,
      'ago.h': (h) => `${h} h ago`,
      'ago.d': (d) => `${d} d ago`,
      shown: (a, b) => `Showing ${a} of ${b}`,
      'rows.fail': (e) => `Could not load recipes: ${e}`,
      'rows.none': 'Nothing matches the filters',
      'rows.nodata': 'No data',
      'm.noPrices': 'no reagent price data',
      'm.notOnAh': (list) => `not on the AH: ${list}`,
      'sell.none': 'not on the auction house',
      'sell.unit': (v) => `per item: ${v}`,
      'sell.min': (v) => `cheapest listing: ${v}`,
      'sell.qty': (n) => `listed: ${n}`,
      'sell.perCraft': (q, v) => `per craft (${q} items): ${v}`,
      'profit.noSell': 'no AH sell price',
      'skill.approx': (y) => `skill to learn unknown; yellow from ${y}`,
      'skill.unknown': 'skill unknown',
      'rp.auto': 'free',
      'rp.auto.tip': 'learned automatically',
      'rp.scroll': 'recipe item',
      'rp.scroll.tip': (n) => (n ? `Recipe item: ${n}` : 'Recipe item'),
      'rp.scroll.none': 'recipe item, not on AH',
      'rp.scroll.noneTip': ' — not on the auction house',
      'rp.scroll.minTip': ' (lowest AH price)',
      'rp.trainer': 'trainer',
      'rp.trainer.tip': 'trainer price',
      'rp.trainer.unknown': 'trainer, price ?',
      'rp.trainer.unknownTip': 'trainer cost is not in the open data',
      'rp.unknown': 'quest/drop',
      'rp.unknown.tip': 'recipe source is not specified in the data',
      'badge.new': 'new',
      'badge.new.tip': 'new in WoW Forever',
      'ch.craft': 'craft',
      'ch.ah': 'buy on AH',
      'ch.missing': 'no price',
      'node.ah': 'AH',
      'node.craft': 'craft',
      'node.notOnAh': 'not on the AH',
      'node.noCraft': 'not craftable or no prices',
      'node.vals': (u, t) => `per item ${u} · total ${t}`,
      'tree.head': (n, q) => `Cost breakdown (from raw materials): ${n} ×${q}`,
      'tree.total': (t) => `· total ${t}`,
      'tree.loading': 'Loading breakdown…',
      'tree.fail': (e) => `Could not load the breakdown: ${e}`,
      unknownError: 'unknown error',
    },
    ru: {
      title: 'Калькулятор выгоды крафта',
      loading: 'Загрузка…',
      'auth.login': 'Войти через Google',
      'auth.logout': 'Выйти',
      'auth.signed': 'вход выполнен',
      'auth.unavailable': (e) => `вход недоступен: ${e}`,
      'auth.nolib': 'вход недоступен: не загрузилась библиотека Supabase',
      'auth.session': (e) => `сессия недоступна: ${e}`,
      'auth.loginFail': (e) => `не удалось войти: ${e}`,
      'auth.logoutFail': (e) => `не удалось выйти: ${e}`,
      filters: 'Фильтры',
      'f.house': 'Аукционный дом',
      'f.faction': 'Фракция',
      'hint.house.aria': 'Что это за аукционные дома?',
      'hint.house': '<b>Что это за дома?</b> Blizzard отдаёт 15 аукционов WoW Forever (EU) без названий серверов — '
        + 'только фракцию и внутренний номер. Каждый дом — отдельный рынок со своими ценами: даже два крупнейших дома '
        + 'Альянса расходятся в среднем на 15%, небольшие — на 30–50%, поэтому в одну цену их не сводим.<br>'
        + '<b>Как выбрать:</b> сначала свою фракцию, потом дом своего сервера. Чем больше лотов, тем населённее сервер. '
        + 'Не уверен, какой твой? Сравни цены пары ходовых товаров (слитки, ткань) с игровым аукционом.<br>'
        + '<b>Черноводье</b> — нейтральный аукцион (Пиратская Бухта, Прибамбасск, Круговзор), общий для обеих фракций.',
      'fac.alliance': 'Альянс',
      'fac.horde': 'Орда',
      'fac.blackwater': 'Черноводье (нейтральный)',
      'fac.other': 'Другое',
      'house.lots': (n) => `${n} лотов`,
      'house.empty': 'пусто',
      'house.none': 'нет данных',
      'f.profs': 'Профессии',
      'f.search': 'Поиск',
      'f.search.ph': 'название предмета',
      'f.skill': 'Навык',
      'f.from': 'от',
      'f.to': 'до',
      'f.skill.min': 'Навык от',
      'f.skill.max': 'Навык до',
      'f.price': 'Цена на аукционе, з',
      'f.price.min': 'Цена на аукционе от, золото',
      'f.price.max': 'Цена на аукционе до, золото',
      'f.profit': 'Прибыль от, з',
      'f.profit.ph': 'любая',
      'f.profit.aria': 'Минимальная прибыль, золото',
      'f.variant.aria': 'Способ крафта',
      'v.craft': 'делаю из сырья',
      'v.buy': 'покупаю реагенты',
      'v.best': 'что выгоднее',
      'f.onah': 'только то, что есть на аукционе',
      'f.reset': 'Сбросить',
      saved: 'Мои выборки',
      'sv.list': 'Сохранённые выборки',
      'sv.pick': '— выбрать —',
      'sv.name.ph': 'название',
      'sv.name.aria': 'Название выборки',
      'sv.save': 'Сохранить текущую',
      'sv.delete': 'Удалить',
      'sv.confirm': (n) => `Точно удалить «${n}»?`,
      'sv.loadFail': (e) => `не удалось загрузить выборки: ${e}`,
      'prefs.loadFail': (e) => `не удалось загрузить фильтры из аккаунта: ${e}`,
      'prefs.saveFail': (e) => `не удалось сохранить фильтры в аккаунт: ${e}`,
      'sv.broken': (n) => `выборка «${n}» повреждена, фильтры не изменены`,
      'sv.empty': (n) => `в выборке «${n}» нет подходящих полей, фильтры не изменены`,
      'sv.applied': (n) => `применена выборка «${n}»`,
      'sv.noName': 'введите название выборки',
      'sv.tooLong': 'название длиннее 80 символов',
      'sv.saveFail': (e) => `не удалось сохранить: ${e}`,
      'sv.overwritten': (n) => `выборка «${n}» перезаписана`,
      'sv.saved': (n) => `выборка «${n}» сохранена`,
      'sv.deleteFail': (e) => `не удалось удалить: ${e}`,
      'sv.deleted': (n) => `выборка «${n}» удалена`,
      legend: '<b>Из сырья</b> — промежуточные реагенты (слитки, рулоны ткани, эссенции…) делаешь сам, '
        + 'на аукционе покупаешь только сырьё (руду, ткань, травы). '
        + '<b>Реагенты с аукциона</b> — всё, что просит рецепт, покупаешь на аукционе готовым. '
        + '<b>Прибыль</b> = цена продажи на аукционе − 5% комиссии − себестоимость. '
        + 'Нажми на строку — покажу, из чего складывается себестоимость.',
      'col.name': 'Предмет',
      'col.prof': 'Профессия',
      'col.skill': 'Навык',
      'col.sell': 'Цена на аукционе',
      'col.cost_craft': 'Себестоимость<small>из сырья</small>',
      'col.profit_craft': 'Прибыль<small>из сырья</small>',
      'col.cost_buy': 'Себестоимость<small>реагенты с аукциона</small>',
      'col.profit_buy': 'Прибыль<small>реагенты с аукциона</small>',
      'col.recipe': 'Рецепт',
      'tip.skill': 'Уровень навыка, с которого изучается рецепт',
      'tip.sell': 'Сколько стоит результат одного крафта на аукционе (рыночная цена самых дешёвых лотов)',
      'tip.craft': 'Промежуточные реагенты делаешь сам, сырьё покупаешь на аукционе',
      'tip.buy': 'Все реагенты покупаешь на аукционе',
      'tip.recipe': 'Как изучается рецепт и сколько стоит',
      'foot.recipes': 'Рецепты:',
      'foot.prices': 'Цены: Blizzard API, каждые 30 мин',
      'st.noServer': 'Нет связи с сервером',
      'st.unavailable': (e) => `Статус недоступен: ${e}`,
      'st.updated': (a) => `цены обновлены ${a}`,
      'st.notLoaded': 'цены ещё не загружены',
      'st.stale': ' — данные устарели',
      'st.lastCheck': (a) => `последняя проверка: ${a}`,
      'st.error': (e) => `ошибка обновления: ${e}`,
      'st.recipes': (n) => `рецептов: ${n}`,
      'st.version': (v) => ` · версия ${v}`,
      'ago.never': 'никогда',
      'ago.now': 'только что',
      'ago.min': (m) => `${m} мин назад`,
      'ago.hmin': (h, m) => `${h} ч ${m} мин назад`,
      'ago.h': (h) => `${h} ч назад`,
      'ago.d': (d) => `${d} дн назад`,
      shown: (a, b) => `Показано ${a} из ${b}`,
      'rows.fail': (e) => `Не удалось загрузить рецепты: ${e}`,
      'rows.none': 'Ничего не подходит под фильтры',
      'rows.nodata': 'Нет данных',
      'm.noPrices': 'нет данных о цене реагентов',
      'm.notOnAh': (list) => `нет на аукционе: ${list}`,
      'sell.none': 'нет на аукционе',
      'sell.unit': (v) => `за шт: ${v}`,
      'sell.min': (v) => `самый дешёвый лот: ${v}`,
      'sell.qty': (n) => `выставлено: ${n} шт`,
      'sell.perCraft': (q, v) => `за крафт (${q} шт): ${v}`,
      'profit.noSell': 'нет цены продажи на аукционе',
      'skill.approx': (y) => `навык для изучения неизвестен; жёлтый с ${y}`,
      'skill.unknown': 'навык неизвестен',
      'rp.auto': 'сразу',
      'rp.auto.tip': 'изучается автоматически',
      'rp.scroll': 'свиток',
      'rp.scroll.tip': (n) => (n ? `Свиток: ${n}` : 'Свиток рецепта'),
      'rp.scroll.none': 'свиток, нет на аукционе',
      'rp.scroll.noneTip': ' — нет на аукционе',
      'rp.scroll.minTip': ' (мин. цена на аукционе)',
      'rp.trainer': 'тренер',
      'rp.trainer.tip': 'цена у тренера',
      'rp.trainer.unknown': 'тренер, цена ?',
      'rp.trainer.unknownTip': 'цены обучения у тренера нет в открытых данных',
      'rp.unknown': 'квест/дроп',
      'rp.unknown.tip': 'источник рецепта не указан в данных',
      'badge.new': 'новое',
      'badge.new.tip': 'новое в WoW Forever',
      'ch.craft': 'крафт',
      'ch.ah': 'покупка на аукционе',
      'ch.missing': 'нет цены',
      'node.ah': 'аукцион',
      'node.craft': 'крафт',
      'node.notOnAh': 'нет на аукционе',
      'node.noCraft': 'не крафтится или нет цен',
      'node.vals': (u, t) => `за шт ${u} · итого ${t}`,
      'tree.head': (n, q) => `Из чего складывается себестоимость (из сырья): ${n} ×${q}`,
      'tree.total': (t) => `· итого ${t}`,
      'tree.loading': 'Загрузка разбора…',
      'tree.fail': (e) => `Не удалось загрузить разбор: ${e}`,
      unknownError: 'неизвестная ошибка',
    },
  };

  const PROF_NAMES = {
    en: {
      alchemy: 'Alchemy', blacksmithing: 'Blacksmithing', enchanting: 'Enchanting', engineering: 'Engineering',
      leatherworking: 'Leatherworking', tailoring: 'Tailoring', mining: 'Mining', cooking: 'Cooking',
      first_aid: 'First Aid', herbalism: 'Herbalism', skinning: 'Skinning', fishing: 'Fishing',
    },
    ru: {
      alchemy: 'Алхимия', blacksmithing: 'Кузнечное дело', enchanting: 'Наложение чар', engineering: 'Инженерное дело',
      leatherworking: 'Кожевничество', tailoring: 'Портняжное дело', mining: 'Горное дело', cooking: 'Кулинария',
      first_aid: 'Первая помощь', herbalism: 'Травничество', skinning: 'Снятие шкур', fishing: 'Рыбная ловля',
    },
  };
  const PROF = PROF_NAMES.en; // список известных профессий (ключи)
  const LOCALE = { en: 'en-US', ru: 'ru-RU' };
  const COIN = { en: ['g', 's', 'c'], ru: ['з', 'с', 'м'] };
  const LANGS = Object.keys(I18N);

  const FACTIONS = [
    { key: 'alliance', re: /альянс|alliance/i },
    { key: 'horde', re: /орд|horde/i },
    { key: 'blackwater', re: /черновод|blackwater/i },
  ];
  const LS_HOUSE = 'forever-craft:house';
  const DEFAULT_HOUSE = 110; // Альянс, совпал по ценам с игровым аукционом (проверено 2026-11-08)
  const LS_LANG = 'forever-craft:lang';
  const STALE_MIN = 75;
  const STATUS_EVERY_MS = 5 * 60 * 1000;
  const G = 10000;
  const COLS = 9;
  const SUPABASE_ESM = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/+esm';
  const SAVED_TABLE = 'saved_filters';
  const PREFS_TABLE = 'user_filters'; // текущие фильтры аккаунта, одна строка на пользователя
  const PREFS_SAVE_MS = 800;
  const FILTERS_V = 1;
  const VARIANTS = new Set(['craft', 'buy', 'best']);

  const $ = (sel) => document.querySelector(sel);
  const el = {
    status: $('#status'),
    faction: $('#f-faction'),
    house: $('#f-house'),
    hintBtn: $('#house-hint-btn'),
    hint: $('#house-hint'),
    filters: $('#filters'),
    q: $('#f-q'),
    skillMin: $('#f-skill-min'),
    skillMax: $('#f-skill-max'),
    priceMin: $('#f-price-min'),
    priceMax: $('#f-price-max'),
    profitMin: $('#f-profit-min'),
    variant: $('#f-variant'),
    onAh: $('#f-onah'),
    reset: $('#f-reset'),
    summary: $('#summary'),
    thead: $('#grid thead'),
    tbody: $('#rows'),
    auth: $('#auth'),
    authLogin: $('#auth-login'),
    authUser: $('#auth-user'),
    authEmail: $('#auth-email'),
    authLogout: $('#auth-logout'),
    authMsg: $('#auth-msg'),
    saved: $('#saved'),
    svList: $('#sv-list'),
    svName: $('#sv-name'),
    svSave: $('#sv-save'),
    svDelete: $('#sv-delete'),
    svMsg: $('#sv-msg'),
  };

  // Вход и «Мои выборки» (Supabase). Пусто, пока /api/config не вернул настройки.
  const auth = {
    sb: null,
    session: null,
    userId: null,
    subscription: null,
    saved: [],
    deleteArmed: null,
    deleteTimer: null,
    prefsReady: false,     // фильтры аккаунта загружены — можно сохранять (иначе затрём их значениями по умолчанию)
    prefsTimer: null,
    prefsLast: null,       // последний сохранённый снимок (JSON), чтобы не писать одно и то же
    prefsErr: false,       // на экране наша ошибка сохранения — убрать после удачного сохранения
  };

  // Первый успешный /api/status: до него список домов пуст и дом из аккаунта не применить.
  let resolveFirstStatus;
  const firstStatus = new Promise((r) => { resolveFirstStatus = r; });

  const state = {
    lang: 'en',
    status: null,
    clockSkew: 0,          // серверное время - локальное, мс
    houseId: null,
    dataVersion: null,
    rows: [],
    view: [],
    sort: { key: 'profit_craft', dir: -1 },
    expanded: new Set(),
    trees: new Map(),      // `${house}:${version}:${id}` -> tree | {error}
    loadSeq: 0,
    rowsError: null,
    loading: false,
  };

  // ---------- утилиты ----------

  function t(key, ...args) {
    if (key.startsWith('prof.')) return profName(key.slice(5));
    const v = I18N[state.lang][key] ?? I18N.en[key];
    if (v == null) return key;
    return typeof v === 'function' ? v(...args) : v;
  }

  function profName(p) {
    return PROF_NAMES[state.lang][p] || p;
  }

  // Имя объекта на текущем языке: name — русское, name_en — английское (у дерева ещё recipe_name / recipe_name_en).
  function nm(o, base = 'name') {
    if (!o) return null;
    return state.lang === 'en' ? (o[`${base}_en`] || o[base]) : (o[base] || o[`${base}_en`]);
  }

  function fmtInt(n) {
    return Number(n || 0).toLocaleString(LOCALE[state.lang]);
  }

  function esc(s) {
    return String(s ?? '').replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    }[c]));
  }

  function norm(s) {
    return String(s ?? '').toLowerCase().replace(/ё/g, 'е');
  }

  function coins(c) {
    const [gs, ss, cs] = COIN[state.lang];
    const v = Math.round(Math.abs(c));
    const g = Math.floor(v / 10000);
    const s = Math.floor((v % 10000) / 100);
    const cu = v % 100;
    const parts = [];
    if (g) parts.push(['g', `${fmtInt(g)}${gs}`]);
    if (s) parts.push(['s', `${s}${ss}`]);
    if (cu || !parts.length) parts.push(['c', `${cu}${cs}`]);
    return parts;
  }

  function moneyText(c) {
    if (c == null) return '—';
    return (c < 0 ? '−' : '') + coins(c).map((p) => p[1]).join(' ');
  }

  function money(c, title) {
    const tt = title ? ` title="${esc(title)}"` : '';
    if (c == null) return `<span class="na"${tt}>—</span>`;
    const neg = c < 0;
    const inner = coins(c).map(([cls, txt]) => `<span class="${cls}">${txt}</span>`).join(' ');
    return `<span class="money${neg ? ' neg' : ''}"${tt}>${neg ? '−' : ''}${inner}</span>`;
  }

  function fmtQty(q) {
    if (q == null) return '';
    return Number.isInteger(q) ? String(q) : q.toFixed(2).replace(/\.?0+$/, '');
  }

  function parseNum(input) {
    const v = input.value.trim().replace(/\s/g, '').replace(',', '.');
    if (v === '') return null;
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  }

  function debounce(fn, ms) {
    let tm = null;
    return (...args) => {
      clearTimeout(tm);
      tm = setTimeout(() => fn(...args), ms);
    };
  }

  function lsGet(key) {
    try { return window.localStorage.getItem(key); } catch (e) { return null; }
  }

  function lsSet(key, value) {
    try { window.localStorage.setItem(key, value); } catch (e) { /* приватный режим и т.п. */ }
  }

  async function getJSON(url) {
    const r = await fetch(url, { headers: { Accept: 'application/json' } });
    let body = null;
    try { body = await r.json(); } catch (e) { body = null; }
    if (!r.ok) {
      const detail = body && body.detail ? body.detail : `HTTP ${r.status}`;
      throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    }
    return body;
  }

  function nowServer() {
    return Date.now() + state.clockSkew;
  }

  function minutesAgo(iso) {
    if (!iso) return null;
    const ts = Date.parse(iso);
    if (Number.isNaN(ts)) return null;
    return Math.max(0, Math.round((nowServer() - ts) / 60000));
  }

  function agoText(min) {
    if (min == null) return t('ago.never');
    if (min < 1) return t('ago.now');
    if (min < 60) return t('ago.min', min);
    const h = Math.floor(min / 60);
    const m = min % 60;
    if (h < 24) return m ? t('ago.hmin', h, m) : t('ago.h', h);
    return t('ago.d', Math.floor(h / 24));
  }

  // ---------- статичные тексты страницы ----------

  function applyStatic() {
    document.documentElement.lang = state.lang;
    document.title = t('title');
    document.querySelectorAll('[data-i18n]').forEach((n) => { n.textContent = t(n.dataset.i18n); });
    // только свои строки из I18N, без пользовательских данных
    document.querySelectorAll('[data-i18n-html]').forEach((n) => { n.innerHTML = t(n.dataset.i18nHtml); });
    document.querySelectorAll('[data-i18n-ph]').forEach((n) => { n.placeholder = t(n.dataset.i18nPh); });
    document.querySelectorAll('[data-i18n-aria]').forEach((n) => { n.setAttribute('aria-label', t(n.dataset.i18nAria)); });
    document.querySelectorAll('[data-i18n-title]').forEach((n) => { n.title = t(n.dataset.i18nTitle); });
    document.querySelectorAll('button[data-lang]').forEach((b) => {
      b.setAttribute('aria-pressed', String(b.dataset.lang === state.lang));
    });
  }

  function setLang(lang, persist = true) {
    if (!LANGS.includes(lang)) return;
    state.lang = lang;
    if (persist) lsSet(LS_LANG, lang);
    applyStatic();
    renderHouseSelects();
    renderStatus();
    renderAuth();
    renderSaved();
    sortView();
    render();
  }

  // ---------- аукционные дома: сначала фракция, потом дом ----------

  function factionKey(h) {
    const f = FACTIONS.find((x) => x.re.test((h && h.name) || ''));
    return f ? f.key : 'other';
  }

  function factionOrder(key) {
    const i = FACTIONS.findIndex((f) => f.key === key);
    return i < 0 ? 99 : i;
  }

  function allHouses() {
    return (state.status && state.status.houses) || [];
  }

  // Внутри фракции: сначала непустые, крупные выше.
  function housesOf(fkey) {
    return allHouses()
      .filter((h) => factionKey(h) === fkey)
      .sort((a, b) => (b.lots || 0) - (a.lots || 0) || a.id - b.id);
  }

  function biggestHouse(houses) {
    return houses.find((h) => h.lots) || houses[0] || null;
  }

  function currentHouse() {
    return allHouses().find((h) => h.id === state.houseId) || null;
  }

  function houseLabel(h) {
    const lots = h.lots ? t('house.lots', fmtInt(h.lots)) : t('house.empty');
    return `#${h.id} · ${lots}`;
  }

  function renderHouseSelects() {
    const houses = allHouses();
    if (!houses.length) {
      const none = `<option value="">${esc(t('house.none'))}</option>`;
      el.faction.innerHTML = none;
      el.house.innerHTML = none;
      return;
    }
    const cur = currentHouse();
    const fcur = cur ? factionKey(cur) : null;
    const fkeys = [...new Set(houses.map(factionKey))].sort((a, b) => factionOrder(a) - factionOrder(b));
    el.faction.innerHTML = fkeys
      .map((k) => `<option value="${esc(k)}"${k === fcur ? ' selected' : ''}>${esc(t(`fac.${k}`))}</option>`)
      .join('');
    el.house.innerHTML = (fcur ? housesOf(fcur) : [])
      .map((h) => `<option value="${esc(h.id)}"${h.id === state.houseId ? ' selected' : ''}>${esc(houseLabel(h))}</option>`)
      .join('');
  }

  // Выбрать дом после загрузки статуса: текущий, сохранённый, иначе крупнейший дом Альянса.
  function fillHouses() {
    const houses = allHouses();
    if (!houses.length) {
      state.houseId = null;
      renderHouseSelects();
      return;
    }
    const saved = Number(lsGet(LS_HOUSE));
    const keep = houses.find((h) => h.id === state.houseId);
    const fromLs = houses.find((h) => h.id === saved);
    const firstFaction = [...new Set(houses.map(factionKey))].sort((a, b) => factionOrder(a) - factionOrder(b))[0];
    const preferred = houses.find((h) => h.id === DEFAULT_HOUSE && h.lots);
    const chosen = keep || fromLs || preferred || biggestHouse(housesOf(firstFaction)) || houses[0];
    state.houseId = chosen.id;
    renderHouseSelects();
  }

  // ---------- статус ----------

  function renderStatus() {
    const st = state.status;
    if (!st) {
      if (el.status.dataset.state !== 'error') el.status.innerHTML = `<span>${esc(t('loading'))}</span>`;
      return;
    }
    const parts = [];
    const h = currentHouse();
    if (h) {
      const min = minutesAgo(h.updated_at);
      const stale = min == null || min > STALE_MIN;
      const cls = stale ? 'warn' : 'ok';
      const when = h.updated_at ? t('st.updated', agoText(min)) : t('st.notLoaded');
      const tip = h.checked_at ? t('st.lastCheck', agoText(minutesAgo(h.checked_at))) : '';
      parts.push(`<span class="${cls}" title="${esc(tip)}">${esc(when)}${stale && h.updated_at ? esc(t('st.stale')) : ''}</span>`);
      if (h.last_error) parts.push(`<span class="err" title="${esc(h.last_error)}">${esc(t('st.error', h.last_error.slice(0, 80)))}</span>`);
    }
    const rc = st.recipes || {};
    const ver = rc.version ? t('st.version', rc.version) : '';
    parts.push(`<span>${esc(t('st.recipes', fmtInt(rc.count)) + ver)}</span>`);
    el.status.dataset.state = 'ok';
    el.status.innerHTML = parts.join('');
  }

  async function refreshStatus() {
    let st;
    try {
      st = await getJSON('api/status');
    } catch (e) {
      el.status.dataset.state = 'error';
      el.status.innerHTML = `<span class="err">${esc(state.status ? t('st.unavailable', e.message) : t('st.noServer'))}</span>`;
      return;
    }
    const prevVersion = state.status ? state.status.data_version : null;
    state.status = st;
    const serverNow = Date.parse(st.now);
    state.clockSkew = Number.isNaN(serverNow) ? 0 : serverNow - Date.now();
    const prevHouse = state.houseId;
    fillHouses();
    renderStatus();
    resolveFirstStatus();
    const houseChanged = state.houseId !== prevHouse;
    const versionChanged = prevVersion !== null && st.data_version !== prevVersion && st.data_version !== state.dataVersion;
    if (houseChanged || versionChanged || (!state.rows.length && !state.loading)) {
      await loadRows();
    }
  }

  // ---------- строки ----------

  function prep(r) {
    r._name = norm(`${r.name || ''} ${r.name_en || ''}`); // поиск по обоим языкам
    r._skill = r.learn_skill ?? r.skill_yellow ?? null;
    return r;
  }

  async function loadRows() {
    if (state.houseId == null) {
      state.rows = [];
      applyFilters();
      return;
    }
    const seq = ++state.loadSeq;
    state.loading = true;
    state.rowsError = null;
    if (!state.rows.length) el.tbody.innerHTML = `<tr class="empty"><td colspan="${COLS}">${esc(t('loading'))}</td></tr>`;
    try {
      const d = await getJSON(`api/recipes?house_id=${encodeURIComponent(state.houseId)}`);
      if (seq !== state.loadSeq) return;
      state.dataVersion = d.data_version;
      state.rows = (d.rows || []).map(prep);
      state.expanded.clear();
    } catch (e) {
      if (seq !== state.loadSeq) return;
      state.rows = [];
      state.rowsError = e.message;
    } finally {
      if (seq === state.loadSeq) state.loading = false;
    }
    applyFilters();
  }

  function readFilters() {
    return {
      profs: new Set([...document.querySelectorAll('input[name="prof"]:checked')].map((i) => i.value)),
      q: norm(el.q.value.trim()),
      skillMin: parseNum(el.skillMin),
      skillMax: parseNum(el.skillMax),
      priceMin: parseNum(el.priceMin),
      priceMax: parseNum(el.priceMax),
      profitMin: parseNum(el.profitMin),
      variant: el.variant.value,
      onAh: el.onAh.checked,
    };
  }

  function profitOf(r, variant) {
    if (variant === 'buy') return r.profit_buy;
    if (variant === 'best') {
      const a = r.profit_craft;
      const b = r.profit_buy;
      if (a == null) return b;
      if (b == null) return a;
      return Math.max(a, b);
    }
    return r.profit_craft;
  }

  function applyFilters() {
    const f = readFilters();
    state.view = state.rows.filter((r) => {
      if (!f.profs.has(r.profession)) return false;
      if (f.q && !r._name.includes(f.q)) return false;
      const sk = r._skill;
      if (f.skillMin != null && (sk == null || sk < f.skillMin)) return false;
      if (f.skillMax != null && (sk == null || sk > f.skillMax)) return false;
      if (f.onAh && r.sell_total == null) return false;
      if (f.priceMin != null && (r.sell_total == null || r.sell_total < f.priceMin * G)) return false;
      if (f.priceMax != null && (r.sell_total == null || r.sell_total > f.priceMax * G)) return false;
      if (f.profitMin != null) {
        const p = profitOf(r, f.variant);
        if (p == null || p < f.profitMin * G) return false;
      }
      return true;
    });
    sortView();
    render();
    schedulePrefsSave();
  }

  const SORT_GET = {
    name: (r) => nm(r),
    profession: (r) => profName(r.profession),
    skill: (r) => r._skill,
    sell_total: (r) => r.sell_total,
    cost_craft: (r) => r.cost_craft,
    profit_craft: (r) => r.profit_craft,
    cost_buy: (r) => r.cost_buy,
    profit_buy: (r) => r.profit_buy,
    recipe_price: (r) => (r.recipe_price ? r.recipe_price.amount : null),
  };
  const ASC_FIRST = new Set(['name', 'profession', 'skill']);

  function sortView() {
    const { key, dir } = state.sort;
    const get = SORT_GET[key] || SORT_GET.profit_craft;
    state.view.sort((a, b) => {
      const va = get(a);
      const vb = get(b);
      const na = va == null;
      const nb = vb == null;
      if (na || nb) return na === nb ? a.id - b.id : (na ? 1 : -1); // null всегда внизу
      let c;
      if (typeof va === 'string' || typeof vb === 'string') c = String(va).localeCompare(String(vb), state.lang);
      else c = va - vb;
      return c !== 0 ? c * dir : a.id - b.id;
    });
  }

  function renderSortMarks() {
    el.thead.querySelectorAll('th[data-key]').forEach((th) => {
      if (th.dataset.key === state.sort.key) th.setAttribute('aria-sort', state.sort.dir > 0 ? 'ascending' : 'descending');
      else th.removeAttribute('aria-sort');
    });
  }

  // ---------- рендер ----------

  function missingTitle(list) {
    if (!list || !list.length) return t('m.noPrices');
    return t('m.notOnAh', list.map((m) => nm(m) || `#${m.item_id}`).join(', '));
  }

  function sellTitle(r) {
    if (r.sell_total == null) return t('sell.none');
    const parts = [t('sell.unit', moneyText(r.sell_unit)), t('sell.min', moneyText(r.sell_min_unit)), t('sell.qty', fmtInt(r.ah_quantity))];
    if (r.output_qty && r.output_qty !== 1) parts.push(t('sell.perCraft', fmtQty(r.output_qty), moneyText(r.sell_total)));
    return parts.join('\n');
  }

  function profitTitle(r, cost, missing) {
    if (r.sell_total == null) return t('profit.noSell');
    if (cost == null) return missingTitle(missing);
    return '';
  }

  function skillHtml(r) {
    if (r.learn_skill != null) return esc(r.learn_skill);
    if (r.skill_yellow != null) return `<span class="skill-approx" title="${esc(t('skill.approx', r.skill_yellow))}">~${esc(r.skill_yellow)}</span>`;
    return `<span class="na" title="${esc(t('skill.unknown'))}">—</span>`;
  }

  function recipeHtml(rp) {
    if (!rp) return '<span class="na">—</span>';
    if (rp.source === 'auto') return `<span class="src" title="${esc(t('rp.auto.tip'))}">${esc(t('rp.auto'))}</span>`;
    if (rp.source === 'scroll') {
      const tip = t('rp.scroll.tip', nm(rp));
      if (rp.amount == null) return `<span class="src" title="${esc(tip + t('rp.scroll.noneTip'))}">${esc(t('rp.scroll.none'))}</span>`;
      return `${money(rp.amount, tip + t('rp.scroll.minTip'))}<span class="src">${esc(t('rp.scroll'))}</span>`;
    }
    if (rp.source === 'trainer') {
      if (rp.amount == null) return `<span class="src" title="${esc(t('rp.trainer.unknownTip'))}">${esc(t('rp.trainer.unknown'))}</span>`;
      return `${money(rp.amount, t('rp.trainer.tip'))}<span class="src">${esc(t('rp.trainer'))}</span>`;
    }
    // unknown и всё незнакомое: квест, дроп, особый способ
    return `<span class="src" title="${esc(t('rp.unknown.tip'))}">${esc(t('rp.unknown'))}</span>`;
  }

  function profitCell(r, profit, cost, missing) {
    const cls = profit != null && profit > 0 ? 'num profit-pos' : 'num';
    return `<td class="${cls}">${money(profit, profitTitle(r, cost, missing))}</td>`;
  }

  function rowHtml(r) {
    const open = state.expanded.has(r.id);
    const qty = r.output_qty && r.output_qty !== 1 ? ` <span class="qty">×${fmtQty(r.output_qty)}</span>` : '';
    const badge = r.new_in_forever ? ` <span class="badge" title="${esc(t('badge.new.tip'))}">${esc(t('badge.new'))}</span>` : '';
    return `<tr class="rec${open ? ' open' : ''}" data-id="${esc(r.id)}" tabindex="0" aria-expanded="${open}">`
      + `<td class="name"><span class="caret">▸</span> <span class="nm">${esc(nm(r))}</span>${qty}${badge}</td>`
      + `<td>${esc(profName(r.profession))}</td>`
      + `<td class="num">${skillHtml(r)}</td>`
      + `<td class="num">${money(r.sell_total, sellTitle(r))}</td>`
      + `<td class="num">${money(r.cost_craft, r.cost_craft == null ? missingTitle(r.missing_craft) : '')}</td>`
      + profitCell(r, r.profit_craft, r.cost_craft, r.missing_craft)
      + `<td class="num">${money(r.cost_buy, r.cost_buy == null ? missingTitle(r.missing_buy) : '')}</td>`
      + profitCell(r, r.profit_buy, r.cost_buy, r.missing_buy)
      + `<td class="num recipe">${recipeHtml(r.recipe_price)}</td>`
      + '</tr>';
  }

  function treeKey(id) {
    return `${state.houseId}:${state.dataVersion}:${id}`;
  }

  function nodeHtml(n) {
    const recipe = n.chosen === 'craft' ? nm(n, 'recipe_name') : null;
    const label = ['craft', 'ah', 'missing'].includes(n.chosen) ? t(`ch.${n.chosen}`) : n.chosen;
    const tag = `<span class="tag tag-${esc(n.chosen)}">${esc(label)}${recipe ? ': ' + esc(recipe) : ''}</span>`;
    let cmp = '';
    if (n.buy_unit != null || n.craft_unit != null) {
      const buyCheaper = n.buy_unit != null && n.craft_unit != null && n.buy_unit < n.craft_unit;
      const craftCheaper = n.buy_unit != null && n.craft_unit != null && n.craft_unit < n.buy_unit;
      cmp = `<span class="cmp">${esc(t('node.ah'))} <span class="${buyCheaper ? 'cheaper' : ''}">${money(n.buy_unit, n.buy_unit == null ? t('node.notOnAh') : '')}</span>`
        + ` · ${esc(t('node.craft'))} <span class="${craftCheaper ? 'cheaper' : ''}">${money(n.craft_unit, n.craft_unit == null ? t('node.noCraft') : '')}</span></span>`;
    }
    const kids = n.children && n.children.length ? `<ul>${n.children.map(nodeHtml).join('')}</ul>` : '';
    return `<li><div class="line"><span class="nm">${esc(nm(n) || `#${n.item_id}`)}</span> <span class="qty">×${fmtQty(n.qty)}</span> ${tag}`
      + ` <span class="vals">${t('node.vals', money(n.unit), money(n.total))}</span>${cmp}</div>${kids}</li>`;
  }

  function treeHtml(tr, r) {
    const total = (tr.children || []).reduce((s, c) => (s == null || c.total == null ? null : s + c.total), 0);
    const head = `<div class="tree-head">${esc(t('tree.head', nm(tr) || nm(r), fmtQty(tr.qty)))}`
      + ` <span class="muted">${t('tree.total', money(total))}</span></div>`;
    return `<div class="tree">${head}<ul>${(tr.children || []).map(nodeHtml).join('')}</ul></div>`;
  }

  function detailInner(r) {
    const tr = state.trees.get(treeKey(r.id));
    if (!tr) return `<div class="loading">${esc(t('tree.loading'))}</div>`;
    if (tr.error) return `<div class="error">${esc(t('tree.fail', tr.error))}</div>`;
    return treeHtml(tr, r);
  }

  function detailRowHtml(r) {
    return `<tr class="detail" data-for="${esc(r.id)}"><td colspan="${COLS}">${detailInner(r)}</td></tr>`;
  }

  function render() {
    renderSortMarks();
    const total = state.rows.length;
    el.summary.textContent = total ? t('shown', fmtInt(state.view.length), fmtInt(total)) : '';
    if (state.rowsError) {
      el.tbody.innerHTML = `<tr class="empty"><td colspan="${COLS}" class="error">${esc(t('rows.fail', state.rowsError))}</td></tr>`;
      return;
    }
    if (!state.view.length) {
      const msg = state.loading ? t('loading') : (total ? t('rows.none') : t('rows.nodata'));
      el.tbody.innerHTML = `<tr class="empty"><td colspan="${COLS}">${esc(msg)}</td></tr>`;
      return;
    }
    const out = [];
    for (const r of state.view) {
      out.push(rowHtml(r));
      if (state.expanded.has(r.id)) out.push(detailRowHtml(r));
    }
    el.tbody.innerHTML = out.join('');
    for (const id of state.expanded) ensureTree(id);
  }

  // ---------- дерево ----------

  async function ensureTree(id) {
    const key = treeKey(id);
    if (state.trees.has(key)) return;
    state.trees.set(key, null);
    let tr;
    try {
      tr = await getJSON(`api/recipes/${encodeURIComponent(id)}/tree?house_id=${encodeURIComponent(state.houseId)}`);
    } catch (e) {
      tr = { error: e.message };
    }
    state.trees.set(key, tr);
    const r = state.rows.find((x) => x.id === id);
    const row = el.tbody.querySelector(`tr.detail[data-for="${id}"]`);
    if (r && row && key === treeKey(id)) row.firstElementChild.innerHTML = detailInner(r);
  }

  function toggleRow(tr) {
    const id = Number(tr.dataset.id);
    const r = state.rows.find((x) => x.id === id);
    if (!r) return;
    if (state.expanded.has(id)) {
      state.expanded.delete(id);
      tr.classList.remove('open');
      tr.setAttribute('aria-expanded', 'false');
      const d = tr.nextElementSibling;
      if (d && d.classList.contains('detail')) d.remove();
      return;
    }
    state.expanded.add(id);
    tr.classList.add('open');
    tr.setAttribute('aria-expanded', 'true');
    tr.insertAdjacentHTML('afterend', detailRowHtml(r));
    ensureTree(id);
  }

  // ---------- события ----------

  const applyDebounced = debounce(applyFilters, 150);
  const isHouseControl = (n) => n === el.house || n === el.faction;

  el.filters.addEventListener('input', (e) => {
    if (isHouseControl(e.target)) return;
    applyDebounced();
  });
  el.filters.addEventListener('change', (e) => {
    if (isHouseControl(e.target)) return;
    applyDebounced();
  });

  function switchHouse(id) {
    state.houseId = id;
    lsSet(LS_HOUSE, String(id));
    state.expanded.clear();
    renderHouseSelects();
    renderStatus();
    loadRows();
    schedulePrefsSave();
  }

  el.faction.addEventListener('change', () => {
    const h = biggestHouse(housesOf(el.faction.value));
    if (h) switchHouse(h.id);
  });

  el.house.addEventListener('change', () => {
    const id = Number(el.house.value);
    if (!Number.isFinite(id)) return;
    switchHouse(id);
  });

  function setHint(open) {
    el.hint.hidden = !open;
    el.hintBtn.setAttribute('aria-expanded', String(open));
  }

  el.hintBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    setHint(el.hint.hidden);
  });
  document.addEventListener('click', (e) => {
    if (!el.hint.hidden && !el.hint.contains(e.target)) setHint(false);
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !el.hint.hidden) {
      setHint(false);
      el.hintBtn.focus();
    }
  });

  document.querySelectorAll('button[data-lang]').forEach((b) => {
    b.addEventListener('click', () => setLang(b.dataset.lang));
  });

  el.reset.addEventListener('click', () => {
    document.querySelectorAll('input[name="prof"]').forEach((i) => { i.checked = true; });
    [el.q, el.skillMin, el.skillMax, el.priceMin, el.priceMax, el.profitMin].forEach((i) => { i.value = ''; });
    el.variant.value = 'craft';
    el.onAh.checked = false;
    applyFilters();
  });

  el.thead.addEventListener('click', (e) => {
    const th = e.target.closest('th[data-key]');
    if (!th) return;
    const key = th.dataset.key;
    if (state.sort.key === key) state.sort.dir = -state.sort.dir;
    else state.sort = { key, dir: ASC_FIRST.has(key) ? 1 : -1 };
    sortView();
    render();
    schedulePrefsSave();
  });

  el.tbody.addEventListener('click', (e) => {
    const tr = e.target.closest('tr.rec');
    if (tr) toggleRow(tr);
  });
  el.tbody.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    const tr = e.target.closest('tr.rec');
    if (!tr) return;
    e.preventDefault();
    toggleRow(tr);
  });

  // ---------- сообщения (ненавязчивая строка статуса) ----------

  const msgTimers = new WeakMap();

  function flash(node, text, kind = 'info') {
    clearTimeout(msgTimers.get(node));
    node.textContent = text || '';
    node.dataset.kind = kind;
    if (text && kind !== 'error') msgTimers.set(node, setTimeout(() => { node.textContent = ''; }, 6000));
  }

  function errText(e) {
    if (!e) return t('unknownError');
    return e.message || e.error_description || e.msg || String(e);
  }

  // ---------- сериализация фильтров ----------

  const TEXT_FIELDS = [
    ['skill_min', 'skillMin'],
    ['skill_max', 'skillMax'],
    ['price_min', 'priceMin'],
    ['price_max', 'priceMax'],
    ['profit_min', 'profitMin'],
  ];

  function snapshot() {
    const out = {
      v: FILTERS_V,
      house: state.houseId,
      profs: [...document.querySelectorAll('input[name="prof"]:checked')].map((i) => i.value),
      q: el.q.value,
      variant: el.variant.value,
      on_ah: el.onAh.checked,
      sort: { key: state.sort.key, dir: state.sort.dir },
    };
    for (const [k, node] of TEXT_FIELDS) out[k] = el[node].value;
    return out;
  }

  function isNumText(v) {
    if (typeof v === 'number') return Number.isFinite(v);
    if (typeof v !== 'string' || v.length > 32) return false;
    const s = v.trim().replace(/\s/g, '').replace(',', '.');
    return s === '' || Number.isFinite(Number(s));
  }

  // Неизвестные и битые поля игнорируются; отсутствующие оставляют текущее значение.
  // Возвращает false, если это не объект, иначе — сколько полей применено.
  function applySnapshot(f) {
    if (!f || typeof f !== 'object' || Array.isArray(f)) return false;
    const has = (k) => Object.prototype.hasOwnProperty.call(f, k);
    let applied = 0;
    if (Array.isArray(f.profs)) {
      const known = f.profs.filter((p) => typeof p === 'string' && Object.prototype.hasOwnProperty.call(PROF, p));
      if (known.length || f.profs.length === 0) {
        document.querySelectorAll('input[name="prof"]').forEach((i) => { i.checked = known.includes(i.value); });
        applied++;
      }
    }
    if (typeof f.q === 'string' && f.q.length <= 200) { el.q.value = f.q; applied++; }
    for (const [k, node] of TEXT_FIELDS) {
      if (has(k) && isNumText(f[k])) { el[node].value = String(f[k]); applied++; }
    }
    if (VARIANTS.has(f.variant)) { el.variant.value = f.variant; applied++; }
    if (typeof f.on_ah === 'boolean') { el.onAh.checked = f.on_ah; applied++; }
    if (f.sort && typeof f.sort === 'object' && Object.prototype.hasOwnProperty.call(SORT_GET, f.sort.key)
      && (f.sort.dir === 1 || f.sort.dir === -1)) {
      state.sort = { key: f.sort.key, dir: f.sort.dir };
      applied++;
    }
    const hid = Number(f.house);
    const houseOk = f.house != null && Number.isInteger(hid) && allHouses().some((h) => h.id === hid);
    if (houseOk) applied++;
    if (houseOk && hid !== state.houseId) {
      switchHouse(hid); // loadRows сам применит фильтры
    } else {
      applyFilters();
    }
    return applied;
  }

  // ---------- вход (Supabase) ----------

  function renderAuth() {
    const logged = !!auth.userId;
    el.auth.hidden = !auth.sb;
    el.authLogin.hidden = logged || !auth.sb;
    el.authUser.hidden = !logged;
    el.authEmail.textContent = logged ? ((auth.session.user && auth.session.user.email) || t('auth.signed')) : '';
    el.authEmail.title = el.authEmail.textContent;
    el.saved.hidden = !logged;
  }

  function setSession(session) {
    const uid = session && session.user && session.user.id ? session.user.id : null;
    auth.session = uid ? session : null;
    const changed = uid !== auth.userId;
    auth.userId = uid;
    renderAuth();
    if (changed) {
      auth.saved = [];
      el.svName.value = '';
      flash(el.svMsg, '');
      renderSaved();
      clearTimeout(auth.prefsTimer);
      auth.prefsTimer = null;
      auth.prefsReady = false;
      auth.prefsLast = null;
      if (uid) {
        loadSaved();
        loadPrefs();
      }
    }
  }

  function attachSupabase(sb) {
    if (auth.subscription) {
      try { auth.subscription.unsubscribe(); } catch (e) { /* старый клиент */ }
    }
    auth.sb = sb || null;
    auth.subscription = null;
    auth.session = null;
    auth.userId = null;
    auth.saved = [];
    renderAuth();
    renderSaved();
    if (!sb) return;
    try {
      // Внутри колбэка нельзя ждать других вызовов supabase — откладываем.
      const res = sb.auth.onAuthStateChange((event, session) => { setTimeout(() => setSession(session), 0); });
      auth.subscription = (res && res.data && res.data.subscription) || null;
    } catch (e) {
      flash(el.authMsg, t('auth.unavailable', errText(e)), 'error');
    }
    Promise.resolve()
      .then(() => sb.auth.getSession())
      .then((res) => { if (auth.sb === sb) setSession(res && res.data ? res.data.session : null); })
      .catch((e) => flash(el.authMsg, t('auth.session', errText(e)), 'error'));
  }

  async function initAuth() {
    let cfg;
    try {
      cfg = await getJSON('api/config');
    } catch (e) {
      return; // нет конфига — входа нет, остальное работает
    }
    const url = cfg && typeof cfg.supabase_url === 'string' ? cfg.supabase_url.trim() : '';
    const key = cfg && typeof cfg.supabase_anon_key === 'string' ? cfg.supabase_anon_key.trim() : '';
    if (!url || !key) return;
    let mod;
    try {
      mod = await import(SUPABASE_ESM);
    } catch (e) {
      el.auth.hidden = false;
      flash(el.authMsg, t('auth.nolib'), 'error');
      return;
    }
    if (auth.sb) return; // уже подставлен через отладочный хук
    try {
      attachSupabase(mod.createClient(url, key));
    } catch (e) {
      el.auth.hidden = false;
      flash(el.authMsg, t('auth.unavailable', errText(e)), 'error');
    }
  }

  el.authLogin.addEventListener('click', async () => {
    if (!auth.sb) return;
    el.authLogin.disabled = true;
    flash(el.authMsg, '');
    try {
      const res = await auth.sb.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo: location.origin + location.pathname },
      });
      if (res && res.error) flash(el.authMsg, t('auth.loginFail', errText(res.error)), 'error');
    } catch (e) {
      flash(el.authMsg, t('auth.loginFail', errText(e)), 'error');
    } finally {
      el.authLogin.disabled = false;
    }
  });

  el.authLogout.addEventListener('click', async () => {
    if (!auth.sb) return;
    el.authLogout.disabled = true;
    try {
      const res = await auth.sb.auth.signOut();
      if (res && res.error) flash(el.authMsg, t('auth.logoutFail', errText(res.error)), 'error');
      else setSession(null);
    } catch (e) {
      flash(el.authMsg, t('auth.logoutFail', errText(e)), 'error');
    } finally {
      el.authLogout.disabled = false;
    }
  });

  // ---------- текущие фильтры аккаунта ----------
  // У вошедшего пользователя фильтры, дом и сортировка живут в аккаунте (public.user_filters):
  // при входе применяются, при каждом изменении сохраняются (с задержкой PREFS_SAVE_MS).

  async function loadPrefs() {
    if (!auth.sb || !auth.userId) return;
    const uid = auth.userId;
    let res;
    try {
      res = await auth.sb.from(PREFS_TABLE).select('filters').maybeSingle();
    } catch (e) {
      res = { error: e };
    }
    if (uid !== auth.userId) return;
    if (res && res.error) {
      // prefsReady остаётся false: лучше не сохранять, чем затереть фильтры аккаунта текущими
      flash(el.authMsg, t('prefs.loadFail', errText(res.error)), 'error');
      return;
    }
    const filters = res && res.data ? res.data.filters : null;
    await firstStatus;
    if (uid !== auth.userId) return;
    if (filters) applySnapshot(filters);
    auth.prefsLast = filters ? JSON.stringify(snapshot()) : null;
    auth.prefsReady = true;
    if (!filters) schedulePrefsSave(); // новый аккаунт: сохранить то, что сейчас на экране
  }

  function schedulePrefsSave() {
    if (!auth.sb || !auth.userId || !auth.prefsReady) return;
    clearTimeout(auth.prefsTimer);
    auth.prefsTimer = setTimeout(savePrefs, PREFS_SAVE_MS);
  }

  async function savePrefs() {
    clearTimeout(auth.prefsTimer);
    auth.prefsTimer = null;
    if (!auth.sb || !auth.userId || !auth.prefsReady) return;
    const uid = auth.userId;
    const filters = snapshot();
    const json = JSON.stringify(filters);
    if (json === auth.prefsLast) return;
    let res;
    try {
      res = await auth.sb.from(PREFS_TABLE).upsert(
        { filters, updated_at: new Date().toISOString() },
        { onConflict: 'user_id' },
      );
    } catch (e) {
      res = { error: e };
    }
    if (uid !== auth.userId) return;
    if (res && res.error) {
      flash(el.authMsg, t('prefs.saveFail', errText(res.error)), 'error');
      auth.prefsErr = true;
      return;
    }
    auth.prefsLast = json;
    if (auth.prefsErr) {
      auth.prefsErr = false;
      flash(el.authMsg, '');
    }
  }

  // Уходят со страницы — не ждать задержки.
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden' && auth.prefsTimer) savePrefs();
  });

  // ---------- «Мои выборки» ----------

  function selectedSaved() {
    const id = el.svList.value;
    return id ? auth.saved.find((s) => String(s.id) === id) || null : null;
  }

  function disarmDelete() {
    clearTimeout(auth.deleteTimer);
    auth.deleteArmed = null;
    el.svDelete.textContent = t('sv.delete');
    el.svDelete.classList.remove('danger');
  }

  function renderSaved(selectName) {
    const keepId = el.svList.value;
    el.svList.innerHTML = `<option value="">${esc(t('sv.pick'))}</option>`
      + auth.saved.map((s) => `<option value="${esc(s.id)}">${esc(s.name)}</option>`).join('');
    const target = selectName != null
      ? auth.saved.find((s) => s.name === selectName)
      : auth.saved.find((s) => String(s.id) === keepId);
    el.svList.value = target ? String(target.id) : '';
    el.svDelete.disabled = !el.svList.value;
    disarmDelete();
  }

  async function loadSaved(selectName) {
    if (!auth.sb || !auth.userId) return;
    const uid = auth.userId;
    let res;
    try {
      res = await auth.sb.from(SAVED_TABLE).select('id,name,filters,updated_at').order('name');
    } catch (e) {
      if (uid === auth.userId) flash(el.svMsg, t('sv.loadFail', errText(e)), 'error');
      return;
    }
    if (uid !== auth.userId) return;
    if (res && res.error) {
      flash(el.svMsg, t('sv.loadFail', errText(res.error)), 'error');
      return;
    }
    const data = res && Array.isArray(res.data) ? res.data : [];
    auth.saved = data.filter((s) => s && s.id != null && typeof s.name === 'string');
    renderSaved(selectName);
  }

  el.svList.addEventListener('change', () => {
    disarmDelete();
    const s = selectedSaved();
    el.svDelete.disabled = !s;
    if (!s) return;
    el.svName.value = s.name;
    const n = applySnapshot(s.filters);
    if (n === false) flash(el.svMsg, t('sv.broken', s.name), 'error');
    else if (n === 0) flash(el.svMsg, t('sv.empty', s.name), 'error');
    else flash(el.svMsg, t('sv.applied', s.name), 'ok');
  });

  el.svSave.addEventListener('click', async () => {
    if (!auth.sb || !auth.userId) return;
    const name = el.svName.value.trim();
    if (!name) {
      flash(el.svMsg, t('sv.noName'), 'error');
      el.svName.focus();
      return;
    }
    if (name.length > 80) {
      flash(el.svMsg, t('sv.tooLong'), 'error');
      return;
    }
    const exists = auth.saved.some((s) => s.name === name);
    el.svSave.disabled = true;
    try {
      const res = await auth.sb.from(SAVED_TABLE).upsert(
        { name, filters: snapshot(), updated_at: new Date().toISOString() },
        { onConflict: 'user_id,name' },
      );
      if (res && res.error) {
        flash(el.svMsg, t('sv.saveFail', errText(res.error)), 'error');
        return;
      }
      el.svName.value = name;
      await loadSaved(name);
      flash(el.svMsg, exists ? t('sv.overwritten', name) : t('sv.saved', name), 'ok');
    } catch (e) {
      flash(el.svMsg, t('sv.saveFail', errText(e)), 'error');
    } finally {
      el.svSave.disabled = false;
    }
  });

  el.svDelete.addEventListener('click', async () => {
    const s = selectedSaved();
    if (!s || !auth.sb) return;
    const id = String(s.id);
    if (auth.deleteArmed !== id) { // первое нажатие — подтверждение
      disarmDelete();
      auth.deleteArmed = id;
      el.svDelete.textContent = t('sv.confirm', s.name);
      el.svDelete.classList.add('danger');
      auth.deleteTimer = setTimeout(disarmDelete, 5000);
      return;
    }
    disarmDelete();
    el.svDelete.disabled = true;
    try {
      const res = await auth.sb.from(SAVED_TABLE).delete().eq('id', s.id);
      if (res && res.error) {
        flash(el.svMsg, t('sv.deleteFail', errText(res.error)), 'error');
        el.svDelete.disabled = false;
        return;
      }
      el.svList.value = '';
      el.svName.value = '';
      await loadSaved();
      flash(el.svMsg, t('sv.deleted', s.name), 'ok');
    } catch (e) {
      flash(el.svMsg, t('sv.deleteFail', errText(e)), 'error');
      el.svDelete.disabled = !el.svList.value;
    }
  });

  // ---------- старт ----------

  const savedLang = lsGet(LS_LANG);
  state.lang = LANGS.includes(savedLang) ? savedLang : 'en';
  applyStatic();
  renderHouseSelects();
  refreshStatus();
  initAuth();
  setInterval(refreshStatus, STATUS_EVERY_MS);
  setInterval(renderStatus, 60 * 1000);

  // Отладка из консоли: forevercraft.refresh(); setLang('ru'); __setSupabase(client) подставляет клиент Supabase (для тестов).
  window.forevercraft = { refresh: refreshStatus, setLang, __setSupabase: attachSupabase };
})();
