import pytest

from app.calc import Calculator, Reagent, Recipe
from app.config import CRAFTABLE_PROFESSIONS
from app.pricing import ItemPrice

ORE, BAR, TIN_ORE, TIN_BAR, BRONZE, VIAL, HERB, POTION, BELT = range(1, 10)
WATER, UNDEATH = 10, 11
PATTERN = 50


def p(market, min_unit=None):
    return ItemPrice(min_unit=min_unit or market, market_unit=market, quantity=100, auctions=5)


RECIPES = [
    Recipe(1, "mining", "Smelt Copper", BAR, 1, (Reagent(ORE, 1),)),
    Recipe(2, "mining", "Smelt Tin", TIN_BAR, 1, (Reagent(TIN_ORE, 1),)),
    Recipe(3, "mining", "Smelt Bronze", BRONZE, 2, (Reagent(BAR, 1), Reagent(TIN_BAR, 1))),
    Recipe(4, "blacksmithing", "Bronze Belt", BELT, 1, (Reagent(BRONZE, 3),),
           learn_skill=100, source_type="scroll", recipe_item_id=PATTERN),
    Recipe(5, "alchemy", "Potion", POTION, 1, (Reagent(HERB, 2), Reagent(VIAL, 1)),
           learn_skill=1, source_type="trainer", source_cost=500),
    Recipe(6, "alchemy", "Transmute Water to Undeath", UNDEATH, 1, (Reagent(WATER, 1),)),
    Recipe(7, "alchemy", "Transmute Undeath to Water", WATER, 1, (Reagent(UNDEATH, 1),)),
    Recipe(8, "alchemy", "Unknown reagent", POTION, 1, (Reagent(HERB, 1), Reagent(99, 1)), source_type="auto"),
]

AH = {
    ORE: p(10), BAR: p(30), TIN_ORE: p(20), TIN_BAR: p(50), BRONZE: p(70),
    VIAL: p(6), HERB: p(15), POTION: p(100), BELT: p(500),
    WATER: p(100), UNDEATH: p(40), PATTERN: p(2000, min_unit=1234),
}


@pytest.fixture
def calc():
    return Calculator(RECIPES, AH, CRAFTABLE_PROFESSIONS)


def by_id(calc, rid):
    return calc.evaluate(calc.recipes[rid])


def test_self_craft_goes_down_to_ore(calc):
    row = by_id(calc, 4)
    # бронза своим крафтом: (медь 10 + олово 20) / 2 слитка = 15; пояс = 3 * 15
    assert row["cost_craft"] == 45
    assert row["cost_buy"] == 3 * 70
    assert row["profit_craft"] == round(500 * 0.95 - 45)
    assert row["profit_buy"] == round(500 * 0.95 - 210)


def test_all_reagents_priced_from_ah_only(calc):
    row = by_id(calc, 5)
    assert row["cost_buy"] == 2 * 15 + 6
    vial = next(r for r in row["reagents"] if r["item_id"] == VIAL)
    assert vial["buy_unit"] == 6
    assert vial["self_source"] == "ah"


def test_output_qty_multiplies_sell_side(calc):
    row = by_id(calc, 3)
    assert row["sell_total"] == 140
    assert row["cost_craft"] == 30
    assert row["profit_craft"] == round(140 * 0.95 - 30)


def test_transmute_cycle_terminates(calc):
    row = by_id(calc, 6)
    # вода своим крафтом = трансмут из нежити, нежить уже выше по дереву -> покупаем её (40)
    assert row["cost_craft"] == 40
    assert row["cost_buy"] == 100


def test_missing_reagent_price(calc):
    row = by_id(calc, 8)
    assert row["cost_buy"] is None
    assert row["cost_craft"] is None
    assert row["profit_buy"] is None
    assert row["missing_buy"] == [99]


def test_recipe_price_sources(calc):
    assert by_id(calc, 5)["recipe_price"] == {"amount": 500, "source": "trainer", "item_id": None}
    assert by_id(calc, 4)["recipe_price"] == {"amount": 1234, "source": "scroll", "item_id": PATTERN}
    assert by_id(calc, 8)["recipe_price"] == {"amount": 0, "source": "auto", "item_id": None}
    # тренер без известной цены
    assert by_id(calc, 1)["recipe_price"] == {"amount": None, "source": "trainer", "item_id": None}


def test_unknown_recipe_source():
    r = Recipe(20, "mining", "Smelt Dark Iron", BAR, 1, (Reagent(ORE, 8),), source_type="unknown")
    calc = Calculator([r], AH, CRAFTABLE_PROFESSIONS)
    assert calc.evaluate(r)["recipe_price"] == {"amount": None, "source": "unknown", "item_id": None}


def test_scroll_not_on_ah():
    calc = Calculator(RECIPES, {k: v for k, v in AH.items() if k != PATTERN}, CRAFTABLE_PROFESSIONS)
    assert calc.evaluate(calc.recipes[4])["recipe_price"] == {"amount": None, "source": "scroll", "item_id": PATTERN}


def test_no_sell_price_means_no_profit():
    calc = Calculator(RECIPES, {k: v for k, v in AH.items() if k != BELT}, CRAFTABLE_PROFESSIONS)
    row = calc.evaluate(calc.recipes[4])
    assert row["sell_total"] is None
    assert row["profit_craft"] is None
    assert row["cost_craft"] == 45


def test_tree_matches_self_craft_cost(calc):
    tree = calc.tree(calc.recipes[4])
    assert sum(c["total"] for c in tree["children"]) == by_id(calc, 4)["cost_craft"]
    bronze = tree["children"][0]
    assert bronze["chosen"] == "craft"
    assert bronze["buy_unit"] == 70
    # 3 бронзы = 1.5 крафта бронзы = 1.5 медных + 1.5 оловянных слитка
    assert [c["qty"] for c in bronze["children"]] == [1.5, 1.5]
    assert bronze["children"][0]["children"][0]["item_id"] == ORE


def test_not_craftable_profession_is_bought():
    recipes = RECIPES + [Recipe(9, "tailoring", "Bolt", BAR, 1, (Reagent(ORE, 100),))]
    calc = Calculator(recipes, AH, CRAFTABLE_PROFESSIONS)
    # портняжный рецепт не используется для промежуточных: медь всё так же из плавки
    assert calc.craft(BAR).recipe_id == 1
