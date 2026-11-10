"""Data types that mirror the real optibook client, so strategy code ports 1:1.

Real client: from optibook.synchronous_client import Exchange
Attribute names below match what past winning repos read from the real objects.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PriceVolume:
    price: float
    volume: int


@dataclass
class PriceBook:
    instrument_id: str
    timestamp: float
    bids: List[PriceVolume] = field(default_factory=list)  # best (highest) first
    asks: List[PriceVolume] = field(default_factory=list)  # best (lowest) first


@dataclass
class OrderStatus:
    order_id: int
    instrument_id: str
    price: float
    volume: int  # remaining volume
    side: str  # 'bid' or 'ask'


@dataclass
class Trade:
    """One of OUR fills (real client: poll_new_trades / get_trade_history)."""
    order_id: int
    instrument_id: str
    price: float
    volume: int
    side: str


@dataclass
class TradeTick:
    """A public trade on the exchange (real client: poll_new_trade_ticks)."""
    timestamp: float
    instrument_id: str
    price: float
    volume: int
    aggressor_side: str
    buyer: str
    seller: str


@dataclass
class InsertOrderResponse:
    success: bool
    order_id: Optional[int] = None
    reason: str = ""  # sim only: why it was rejected


@dataclass
class Instrument:
    instrument_id: str
    tick_size: float
    paused: bool = False
    # sim extras: which stock this listing belongs to, and whether it is the liquid primary
    underlying: str = ""
    is_primary: bool = True
