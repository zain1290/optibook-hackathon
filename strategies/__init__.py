from .cross_arb import CrossArb
from .evolved import Evolved
from .quote_hedge import QuoteHedge

STRATEGIES = {"cross_arb": CrossArb, "quote_hedge": QuoteHedge, "evolved": Evolved}
