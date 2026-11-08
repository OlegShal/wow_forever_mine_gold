from app.pricing import aggregate, unit_lots


def test_buyout_is_per_lot_and_bid_only_is_skipped():
    auctions = {"auctions": [
        {"id": 1, "item": {"id": 1}, "quantity": 5, "buyout": 500, "time_left": "LONG"},
        {"id": 2, "item": {"id": 1}, "quantity": 1, "buyout": 80, "time_left": "LONG"},
        {"id": 3, "item": {"id": 1}, "quantity": 2, "bid": 10, "time_left": "SHORT"},
    ]}
    lots = unit_lots(auctions, None)
    assert sorted(lots[1]) == [(80.0, 1), (100.0, 5)]


def test_commodities_use_unit_price():
    commodities = {"auctions": [
        {"id": 10, "item": {"id": 2}, "quantity": 100, "unit_price": 7, "time_left": "LONG"},
        {"id": 11, "item": {"id": 2}, "quantity": 20, "unit_price": 5, "time_left": "LONG"},
    ]}
    prices = aggregate(unit_lots(None, commodities))
    assert prices[2].min_unit == 5
    assert prices[2].market_unit == 5        # 15% от 120 = 18 шт, все по 5
    assert prices[2].quantity == 120
    assert prices[2].auctions == 2


def test_market_price_averages_cheapest_share():
    lots = {3: [(20.0, 9), (10.0, 1)]}
    p = aggregate(lots, share=0.15)[3]
    assert p.min_unit == 10
    assert p.market_unit == 15               # ceil(10*0.15)=2 шт: 10 + 20


def test_empty_house_without_auctions_field():
    assert unit_lots({"id": 112, "name": "x"}, {}) == {}
