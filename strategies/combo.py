"""Everything in one bot, on one exchange connection (Optibook allows only one per team):
  - stock_mm on every stock (quotes inside the exchange maker, picks off stale quotes, reacts to news)
  - deriv_arb on options / futures / ETFs, if the exchange lists any (does nothing otherwise)
  - pairs trading, only if switched on (pairs=True)
They share one order budget. Delta from derivatives is handed to stock_mm, which leans its quotes to
work it off patiently; deriv_arb only hedges immediately beyond its (wider) band.
Parameters: anything stock_mm takes, plus deriv_edge, deriv_size, vol, hedge_band, use_pairs, entry_z.
"""
import time

from .common import RateBudget
from .deriv_arb import DerivArb
from .pairs import PairsTrader
from .stock_mm import StockMM


class Combo:
    name = "combo"

    def __init__(self, pairs=None, deriv_edge=3, deriv_size=10, vol=None, hedge_band=40, use_pairs=False,
                 stock_pairs="MU:SNDK,NVDA:AMD,CRWV:NBIS", entry_z=2.5, max_ops_per_sec=20, clock=None,
                 hedge_cooldown=0.0, **mm_params):
        self.clock = clock or time.monotonic
        self.budget = RateBudget(max_ops_per_sec, self.clock, reserve=mm_params.get("reserve_ops", 6))
        self.mm = StockMM(clock=clock, max_ops_per_sec=max_ops_per_sec, **mm_params)
        self.mm.budget = self.budget
        self.deriv = DerivArb(deriv_edge=deriv_edge, deriv_size=deriv_size, vol=vol, hedge_band=hedge_band,
                              position_limit=self.mm.position_limit, clock=clock, budget=self.budget)
        self.pairs = PairsTrader(stock_pairs=stock_pairs, entry_z=entry_z, position_limit=self.mm.position_limit,
                                 clock=clock, budget=self.budget) if use_pairs else None
        self.use_pairs = use_pairs
        self.end_time = None

    # live settings: stock_mm's attributes are exposed directly on the combo
    def __getattr__(self, k):
        if k in ("mm", "deriv", "pairs", "__setstate__", "__getstate__"):
            raise AttributeError(k)
        return getattr(self.mm, k)

    def __setattr__(self, k, v):
        if k == "end_time" and "mm" in self.__dict__:
            self.mm.end_time = v
        if k in ("deriv_edge", "deriv_size", "hedge_band", "vol"):
            if k == "vol":
                self.deriv.vol = v
                return
            object.__setattr__(self, k, v)  # goes through the property
            return
        if "mm" in self.__dict__ and k not in self.__dict__ and hasattr(self.mm, k) and k not in ("budget", "clock"):
            setattr(self.mm, k, v)
            return
        object.__setattr__(self, k, v)

    @property
    def limit(self):
        return self.mm.position_limit

    @property
    def deriv_edge(self):
        return self.deriv.deriv_edge

    @deriv_edge.setter
    def deriv_edge(self, v):
        self.deriv.deriv_edge = v

    @property
    def deriv_size(self):
        return self.deriv.deriv_size

    @deriv_size.setter
    def deriv_size(self, v):
        self.deriv.deriv_size = v

    @property
    def hedge_band(self):
        return self.deriv.hedge_band

    @hedge_band.setter
    def hedge_band(self, v):
        self.deriv.hedge_band = v

    def step(self, e):
        self.deriv.step(e)
        if self.deriv.deltas:  # derivative delta per stock, excluding the stock position itself
            pos = e.get_positions()
            extra = {}
            for i, d in self.deriv.deltas.items():
                for s, dd in d.items():
                    extra[s] = extra.get(s, 0.0) + pos.get(i, 0) * dd
            self.mm.extra_delta = extra
        self.mm.step(e)
        if self.pairs is not None:
            self.pairs.step(e)

    def live_params(self):
        out = self.mm.live_params()
        out.update({"deriv_edge": self.deriv.deriv_edge, "deriv_size": self.deriv.deriv_size,
                    "hedge_band": self.deriv.hedge_band, "vol": self.deriv.vol})
        return out
