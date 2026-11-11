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
    error_reason: Optional[str] = None  # real client field name

    @property
    def reason(self):  # older sim code reads .reason
        return self.error_reason or ""


@dataclass
class AmendOrderResponse:
    success: bool
    error_reason: Optional[str] = None


@dataclass
class DeleteOrderResponse:
    success: bool
    error_reason: Optional[str] = None


@dataclass
class PriceChangeLimit:
    absolute_change: float
    relative_change: float


@dataclass
class SocialMediaFeed:
    """A news post (real client: poll_new_social_media_feeds). meta_data is a free-form dict."""
    timestamp: float = None
    post: str = None
    meta_data: dict = None


@dataclass
class Instrument:
    instrument_id: str
    tick_size: float
    paused: bool = False
    # sim extras: which stock this listing belongs to, and whether it is the liquid primary
    underlying: str = ""
    is_primary: bool = True
    # real client fields (None when not used)
    instrument_type: Optional[str] = None      # STOCK, STOCK_OPTION, STOCK_FUTURE, INDEX_TRACKING_ETF, ...
    price_change_limit: Optional[PriceChangeLimit] = None
    expiry: Optional[float] = None             # sim seconds (real client: datetime)
    option_kind: Optional[str] = None          # 'call' / 'put'
    strike: Optional[float] = None
    base_instrument_id: Optional[str] = None
    interest_rate: Optional[float] = None
    index_constituents: Optional[dict] = None  # ETF / index weights: instrument -> shares
    index_divisor: Optional[float] = None
    etf_cash_comp: Optional[float] = None
    etf_multiplier: Optional[float] = None
    instrument_group: Optional[str] = None
    expired: bool = False
