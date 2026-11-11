"""SimExchange: same method names and signatures as optibook.synchronous_client.Exchange.

Write strategies against this, then swap in the real Exchange on the day with no code changes.
Mirrors the documented Optibook behaviour:
  - one connection per account: connecting again kicks the previous client,
  - Cancel On Disconnect: every resting order is pulled when a connection drops,
  - trade ticks start empty after connecting (no history snapshot),
  - get_pnl values open positions at the last traded price.
"""
import copy
from typing import Dict, List

from .types import (AmendOrderResponse, DeleteOrderResponse, InsertOrderResponse, OrderStatus, PriceBook,
                    PriceVolume, TradeTick)

SIM_ONLY = ("underlying", "is_primary")  # fields the real client does not have


class NotConnected(ConnectionError):
    pass


class SimExchange:
    def __init__(self, market, owner: str, auto_connect: bool = True):
        self.m = market
        self.owner = owner
        self.last_response = None  # sim only: inspect reject reasons
        self.session = None
        self._feed_cursor = 0
        if auto_connect:
            self.connect()

    # ---- connection ----
    def connect(self):
        self.session = self.m.connect(self.owner)
        self._feed_cursor = len(self.m.news)
        self._feed_start = self._feed_cursor
        return True

    def disconnect(self):
        if self.session is not None:
            self.m.disconnect(self.owner, self.session)
        self.session = None
        return None

    def is_connected(self):
        return self.session is not None and self.m.sessions.get(self.owner) == self.session

    def _check(self):
        if not self.is_connected():
            raise NotConnected("not connected to the exchange (another connection took over, or disconnected)")

    # ---- reference data ----
    def get_instruments(self):
        return {k: copy.copy(v) for k, v in self.m.instruments.items()}

    def get_tradable_instruments(self):
        """Excludes paused and expired instruments, like the real client."""
        return {k: copy.copy(v) for k, v in self.m.instruments.items() if not v.paused and not v.expired}

    # ---- market data ----
    def get_last_price_book(self, instrument_id: str, depth: int = 10) -> PriceBook:
        self._check()
        b = self.m.books[instrument_id]
        tp = lambda t: self.m.to_price(instrument_id, t)
        return PriceBook(
            instrument_id, self.m.t,
            bids=[PriceVolume(tp(p), v) for p, v in b.depth("bid", depth)],
            asks=[PriceVolume(tp(p), v) for p, v in b.depth("ask", depth)],
        )

    def poll_new_trade_ticks(self, instrument_id: str) -> List[TradeTick]:
        self._check()
        acc = self.m.accounts[self.owner]
        ticks = self.m.ticks[instrument_id]
        out = ticks[acc.tick_cursor[instrument_id]:]
        acc.tick_cursor[instrument_id] = len(ticks)
        return list(out)

    def get_trade_tick_history(self, instrument_id: str) -> List[TradeTick]:
        return list(self.m.ticks[instrument_id][-1000:])

    def poll_new_social_media_feeds(self):
        self._check()
        out = self.m.news[self._feed_cursor:]
        self._feed_cursor = len(self.m.news)
        return list(out)

    def get_social_media_feeds_history(self):
        return list(self.m.news[self._feed_start:][-500:])

    # ---- own state ----
    def get_positions(self) -> Dict[str, int]:
        acc = self.m.accounts[self.owner]
        return {i: acc.position[i] for i in self.m.instruments}

    def get_cash(self) -> float:
        return self.m.accounts[self.owner].cash

    def get_positions_and_cash(self):
        acc = self.m.accounts[self.owner]
        out = {i: {"volume": acc.position[i], "cash": 0.0} for i in self.m.instruments}
        out["cash"] = acc.cash  # sim simplification: one cash total
        return out

    def get_pnl(self, valuations: Dict[str, float] = None) -> float:
        """Like the real client: positions at the last traded price unless valuations are given."""
        acc = self.m.accounts[self.owner]
        total = acc.cash
        for i, pos in acc.position.items():
            if pos:
                px = (valuations or {}).get(i)
                if px is None:
                    px = self.m.last_price(i) or self.m.mid(i) or self.m.fv(i)
                total += pos * px
        return total

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
        self._check()
        tick = self.m.tick(instrument_id)
        ticks = round(price / tick)
        if abs(ticks * tick - price) > 1e-6:
            r = InsertOrderResponse(False, None, f"price {price} not on tick grid {tick}")
            self.m.accounts[self.owner].n_rejects["off_tick"] += 1
        else:
            oid, reason = self.m.submit(self.owner, instrument_id, side, ticks, int(volume),
                                        ioc=(order_type == "ioc"))
            r = InsertOrderResponse(oid is not None, oid, reason or None)
        self.last_response = r
        return r

    def amend_order(self, instrument_id: str, *, order_id: int, volume: int):
        self._check()
        ok = self.m.amend(self.owner, instrument_id, order_id, int(volume))
        return AmendOrderResponse(ok, None if ok else "amend failed (unknown order, limit or rate limit)")

    def delete_order(self, instrument_id: str, *, order_id: int):
        self._check()
        ok = self.m.cancel(self.owner, instrument_id, order_id)
        return DeleteOrderResponse(ok, None if ok else "delete failed (unknown order or rate limit)")

    def delete_orders(self, instrument_id: str):
        self._check()
        self.m.cancel_all(self.owner, instrument_id)
        return None
