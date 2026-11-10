"""SimExchange: same method names and signatures as optibook.synchronous_client.Exchange.

Write strategies against this, then swap in the real Exchange on the day with no code changes.
"""
import copy
from typing import Dict, List

from .types import InsertOrderResponse, OrderStatus, PriceBook, PriceVolume, TradeTick


class SimExchange:
    def __init__(self, market, owner: str):
        self.m = market
        self.owner = owner
        self.last_response = None  # sim only: inspect reject reasons

    # ---- connection (no-ops in sim) ----
    def connect(self):
        return True

    def disconnect(self):
        return True

    def is_connected(self):
        return True

    # ---- reference data ----
    def get_instruments(self):
        return {k: copy.copy(v) for k, v in self.m.instruments.items()}

    # ---- market data ----
    def get_last_price_book(self, instrument_id: str, depth: int = 10) -> PriceBook:
        b = self.m.books[instrument_id]
        tp = lambda t: self.m.to_price(instrument_id, t)
        return PriceBook(
            instrument_id, self.m.t,
            bids=[PriceVolume(tp(p), v) for p, v in b.depth("bid", depth)],
            asks=[PriceVolume(tp(p), v) for p, v in b.depth("ask", depth)],
        )

    def poll_new_trade_ticks(self, instrument_id: str) -> List[TradeTick]:
        acc = self.m.accounts[self.owner]
        ticks = self.m.ticks[instrument_id]
        out = ticks[acc.tick_cursor[instrument_id]:]
        acc.tick_cursor[instrument_id] = len(ticks)
        return list(out)

    def get_trade_tick_history(self, instrument_id: str) -> List[TradeTick]:
        return list(self.m.ticks[instrument_id][-1000:])

    # ---- own state ----
    def get_positions(self) -> Dict[str, int]:
        acc = self.m.accounts[self.owner]
        return {i: acc.position[i] for i in self.m.instruments}

    def get_positions_and_cash(self):
        acc = self.m.accounts[self.owner]
        out = {i: {"volume": acc.position[i], "cash": 0.0} for i in self.m.instruments}
        out["cash"] = acc.cash  # sim simplification: one cash total
        return out

    def get_pnl(self) -> float:
        return self.m.pnl(self.owner, mark="mid")

    def get_outstanding_orders(self, instrument_id: str) -> Dict[int, OrderStatus]:
        return {
            o.order_id: OrderStatus(o.order_id, instrument_id, self.m.to_price(instrument_id, o.price), o.volume, o.side)
            for o in self.m.resting(self.owner, instrument_id)
        }

    def poll_new_trades(self, instrument_id: str):
        acc = self.m.accounts[self.owner]
        out = acc.new_trades[instrument_id]
        acc.new_trades[instrument_id] = []
        return out

    def get_trade_history(self, instrument_id: str):
        return list(self.m.accounts[self.owner].trade_history[instrument_id])

    # ---- order entry ----
    def insert_order(self, instrument_id: str, *, price: float, volume: int, side: str,
                     order_type: str = "limit") -> InsertOrderResponse:
        tick = self.m.tick(instrument_id)
        ticks = round(price / tick)
        if abs(ticks * tick - price) > 1e-6:
            r = InsertOrderResponse(False, None, f"price {price} not on tick grid {tick}")
            self.m.accounts[self.owner].n_rejects["off_tick"] += 1
        else:
            oid, reason = self.m.submit(self.owner, instrument_id, side, ticks, int(volume),
                                        ioc=(order_type == "ioc"))
            r = InsertOrderResponse(oid is not None, oid, reason)
        self.last_response = r
        return r

    def amend_order(self, instrument_id: str, *, order_id: int, volume: int):
        return self.m.amend(self.owner, instrument_id, order_id, int(volume))

    def delete_order(self, instrument_id: str, *, order_id: int):
        return self.m.cancel(self.owner, instrument_id, order_id)

    def delete_orders(self, instrument_id: str):
        return self.m.cancel_all(self.owner, instrument_id)
