"""Engine sanity tests:  python -m pytest -q tests"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optisim import Limits, Market, SimExchange  # noqa: E402


def mk(limits=None):
    m = Market(dt=0.1, seed=1)
    m.add_stock("X", 100.0, 0.0)
    m.add_instrument("X", "X", 0.1)
    m.add_instrument("X_DUAL", "X", 0.1, is_primary=False)
    m.add_account("a", limits or Limits())
    m.add_account("b", limits or Limits())
    return m, SimExchange(m, "a"), SimExchange(m, "b")


def test_price_time_priority_and_partial_fill():
    m, a, b = mk()
    r1 = a.insert_order("X", price=100.0, volume=5, side="bid")
    b.insert_order("X", price=100.0, volume=5, side="bid")
    a.insert_order("X", price=99.9, volume=5, side="bid")
    m.add_account("c")
    c = SimExchange(m, "c")
    c.insert_order("X", price=99.9, volume=7, side="ask", order_type="ioc")
    # a's 100.0 order first (best price, earliest), then 2 lots of b's
    assert a.get_positions()["X"] == 5 and b.get_positions()["X"] == 2
    assert c.get_positions()["X"] == -7
    assert r1.order_id not in a.get_outstanding_orders("X")
    assert list(b.get_outstanding_orders("X").values())[0].volume == 3


def test_ioc_does_not_rest():
    m, a, b = mk()
    a.insert_order("X", price=100.0, volume=5, side="bid", order_type="ioc")
    assert a.get_outstanding_orders("X") == {}
    assert m.books["X"].orders == {}


def test_worst_case_position_limit():
    m, a, b = mk(Limits(position_limit=10))
    assert a.insert_order("X", price=99.0, volume=6, side="bid").success
    r = a.insert_order("X", price=98.0, volume=5, side="bid")
    assert not r.success and "position" in r.reason  # 6 resting + 5 > 10
    assert a.insert_order("X", price=101.0, volume=10, side="ask").success  # other side is independent


def test_self_trade_prevented():
    m, a, b = mk()
    a.insert_order("X", price=100.0, volume=5, side="bid")
    r = a.insert_order("X", price=100.0, volume=5, side="ask")
    assert not r.success and "self" in r.reason


def test_rate_limit_rolls_over():
    m, a, b = mk(Limits(max_ops_per_sec=3))
    for i in range(3):
        assert a.insert_order("X", price=90.0 + i, volume=1, side="bid").success
    assert not a.insert_order("X", price=80.0, volume=1, side="bid").success
    for _ in range(10):
        m.step()  # 1 second later
    assert a.insert_order("X", price=80.0, volume=1, side="bid").success


def test_amend_down_keeps_priority_up_loses_it():
    m, a, b = mk()
    oa = a.insert_order("X", price=100.0, volume=5, side="bid").order_id
    b.insert_order("X", price=100.0, volume=5, side="bid")
    a.amend_order("X", order_id=oa, volume=3)
    m.add_account("c")
    c = SimExchange(m, "c")
    c.insert_order("X", price=100.0, volume=3, side="ask", order_type="ioc")
    assert a.get_positions()["X"] == 3 and b.get_positions()["X"] == 0
    ob = list(b.get_outstanding_orders("X"))[0]
    oa2 = a.insert_order("X", price=100.0, volume=1, side="bid").order_id
    b.amend_order("X", order_id=ob, volume=9)  # increase -> b goes behind a
    c.insert_order("X", price=100.0, volume=1, side="ask", order_type="ioc")
    assert a.get_positions()["X"] == 4


def test_off_tick_rejected():
    m, a, b = mk()
    assert not a.insert_order("X", price=100.05, volume=1, side="bid").success


def test_money_is_conserved_in_full_scenario():
    from optisim import attach, build
    from strategies import QuoteHedge
    m, pairs = build("hard", seed=3)
    attach(m, "us", QuoteHedge(pairs, clock=lambda: m.t))
    for _ in range(2000):
        m.step()
    assert abs(sum(m.pnl(n) for n in m.accounts)) < 1e-6


def test_paused_instrument_rejects_and_clears():
    m, a, b = mk()
    a.insert_order("X", price=99.0, volume=1, side="bid")
    m.pauses.append(("X", 0.0, 10.0))
    m.step()
    assert m.books["X"].orders == {}
    assert not a.insert_order("X", price=99.0, volume=1, side="bid").success
