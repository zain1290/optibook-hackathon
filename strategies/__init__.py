from .combo import Combo
from .cross_arb import CrossArb
from .deriv_arb import DerivArb
from .evolved import Evolved
from .pairs import PairsTrader
from .quote_hedge import QuoteHedge
from .stock_mm import StockMM

STRATEGIES = {"combo": Combo, "stock_mm": StockMM, "deriv_arb": DerivArb, "pairs": PairsTrader,
              "cross_arb": CrossArb, "quote_hedge": QuoteHedge, "evolved": Evolved}
