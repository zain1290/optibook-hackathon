"""Price-time priority limit order book. Prices are stored as integer ticks to avoid float bugs."""
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class Order:
    order_id: int
    owner: str
    instrument_id: str
    side: str  # 'bid' | 'ask'
    price: int  # ticks
    volume: int  # remaining
    seq: int  # time priority


@dataclass
class Fill:
    resting: Order
    price: int
    volume: int


class OrderBook:
    def __init__(self, instrument_id: str):
        self.instrument_id = instrument_id
        self.levels: Dict[str, Dict[int, deque]] = {"bid": {}, "ask": {}}
        self.orders: Dict[int, Order] = {}

    # ---------- queries ----------
    def best(self, side: str):
        lv = self.levels[side]
        if not lv:
            return None
        return max(lv) if side == "bid" else min(lv)

    def depth(self, side: str, n: int = 5) -> List[Tuple[int, int]]:
        lv = self.levels[side]
        prices = sorted(lv, reverse=(side == "bid"))[:n]
        return [(p, sum(o.volume for o in lv[p])) for p in prices]

    def crosses(self, side: str, price: int, level_price: int) -> bool:
        return level_price <= price if side == "bid" else level_price >= price

    def own_would_cross(self, owner: str, side: str, price: int) -> bool:
        opp = "ask" if side == "bid" else "bid"
        for p, q in self.levels[opp].items():
            if self.crosses(side, price, p) and any(o.owner == owner for o in q):
                return True
        return False

    # ---------- mutations ----------
    def match(self, side: str, price: int, volume: int) -> Tuple[List[Fill], int]:
        """Match an incoming order against the opposite side. Returns fills and remaining volume."""
        opp = "ask" if side == "bid" else "bid"
        fills: List[Fill] = []
        lv = self.levels[opp]
        while volume > 0 and lv:
            bp = min(lv) if opp == "ask" else max(lv)
            if not self.crosses(side, price, bp):
                break
            q = lv[bp]
            while volume > 0 and q:
                o = q[0]
                v = min(volume, o.volume)
                fills.append(Fill(o, bp, v))
                o.volume -= v
                volume -= v
                if o.volume == 0:
                    q.popleft()
                    del self.orders[o.order_id]
            if not q:
                del lv[bp]
        return fills, volume

    def add(self, order: Order):
        self.levels[order.side].setdefault(order.price, deque()).append(order)
        self.orders[order.order_id] = order

    def remove(self, order_id: int) -> bool:
        o = self.orders.pop(order_id, None)
        if o is None:
            return False
        q = self.levels[o.side][o.price]
        q.remove(o)
        if not q:
            del self.levels[o.side][o.price]
        return True

    def requeue(self, order: Order):
        """Send an order to the back of its price level (loses time priority)."""
        q = self.levels[order.side][order.price]
        q.remove(order)
        q.append(order)

    def clear(self):
        self.levels = {"bid": {}, "ask": {}}
        self.orders = {}
