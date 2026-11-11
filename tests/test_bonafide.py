"""The Bona Fide setup: many stocks, one connection per team, news, derivatives pricing, new strategies."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optisim import SimExchange, attach, build  # noqa: E402
from strategies import STRATEGIES, pricing  # noqa: E402
from strategies.news import instruments_in, sentiment  # noqa: E402


def test_second_connection_kicks_the_first_and_cancels_orders():
    m, _ = build("bonafide_quiet", 0)
    m.add_account("us")
    a = SimExchange(m, "us")
    for _ in range(5):
        m.step()
    b = a.get_last_price_book("NVDA")
    r = a.insert_order("NVDA", price=b.bids[0].price - 0.5, volume=1, side="bid")
    assert r.success and a.get_outstanding_orders("NVDA")
    other = SimExchange(m, "us")  # a teammate's notebook logs in
    assert not a.is_connected() and other.is_connected()
    assert other.get_outstanding_orders("NVDA") == {}  # cancel on disconnect
    try:
        a.insert_order("NVDA", price=100.0, volume=1, side="bid")
        assert False, "kicked client must not trade"
    except ConnectionError:
        pass
    a.connect()
    assert a.is_connected() and not other.is_connected()


def test_market_is_zero_sum_with_news_and_derivatives_through_expiry():
    m, _ = build("bonafide_derivs", 1, n_teams=4)
    attach(m, "us", STRATEGIES["combo"](clock=lambda: m.t))
    for _ in range(int(1260 / m.dt)):  # past the 1200 s expiry
        m.step()
    assert m.news, "news bot should have posted"
    assert any(i.expired for i in m.instruments.values())
    assert abs(sum(m.pnl(n) for n in m.accounts)) < 1e-6


def test_stock_mm_makes_money_on_the_quiet_practice_market():
    m, _ = build("bonafide_quiet", 2)
    attach(m, "us", STRATEGIES["stock_mm"](clock=lambda: m.t))
    for _ in range(3000):
        m.step()
    rep = m.report("us")
    assert rep["pnl_fair"] > 0
    assert max(abs(v) for v in rep["final_positions"].values() or [0]) <= 300
    assert not rep["rejects"].get("position_limit")


def test_news_reader():
    ids = ["NVDA", "AMD", "AVGO", "MU", "SNDK"]
    assert instruments_in("NVDA smashes earnings expectations", ids) == ["NVDA"]
    assert set(instruments_in("Sell-off in memory as demand fears grow", ids)) == {"MU", "SNDK"}
    assert "AMD" in instruments_in("Advanced Micro Devices wins contract", ids)
    assert sentiment("NVDA smashes earnings expectations, raises guidance") > 0
    assert sentiment("AMD misses revenue estimates, shares slide") < 0
    assert sentiment("CEO spotted at coffee shop") == 0


def test_pricing():
    s, k, t, v, r = 100.0, 105.0, 0.5, 0.3, 0.02
    c, p = pricing.bs_price(s, k, t, v, r, "call"), pricing.bs_price(s, k, t, v, r, "put")
    assert abs((c - p) - (s - k * math.exp(-r * t))) < 1e-9  # put-call parity
    assert abs(pricing.implied_vol(c, s, k, t, r, "call") - v) < 1e-4
    g = pricing.bs_greeks(s, k, t, v, r, "call")
    h = 1e-4
    assert abs(g["delta"] - (pricing.bs_price(s + h, k, t, v, r) - pricing.bs_price(s - h, k, t, v, r)) / (2 * h)) < 1e-5
    assert abs(pricing.future_fair_value(100, 0.05, 1.0) - 100 * math.exp(0.05)) < 1e-9
    assert pricing.etf_fair_value({"A": 10, "B": 20}, {"A": 1, "B": 2}, divisor=5) == 10.0


def test_combo_live_settings_reach_the_right_part():
    c = STRATEGIES["combo"](clock=lambda: 0.0)
    for k, v in {"size": 7, "quote_edge": 2.0, "take_edge": 2, "deriv_edge": 6, "hedge_band": 15, "vol": 0.4}.items():
        assert k in c.live_params()
        setattr(c, k, v)
    assert (c.mm.size, c.mm.quote_edge, c.mm.take_edge) == (7, 2.0, 2)
    assert (c.deriv.deriv_edge, c.deriv.hedge_band, c.deriv.vol) == (6, 15, 0.4)
