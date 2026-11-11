"""Fair values for derivatives: options (Black-Scholes + Greeks), futures, index-tracking ETFs.

Pure maths, standard library only. Used by the strategies AND by the simulator (one source of truth).
Assumptions to re-check against the challenge brief on the day are marked ASSUMPTION.
"""
import datetime as _dt
import math

SECONDS_PER_YEAR = 365.0 * 24 * 3600
# In the simulator a 10-minute round would leave options with no time value at real-world scale,
# so sim expiries run on a compressed clock: 1 sim hour = 1 year.
SECONDS_PER_YEAR_SIM = 3600.0


def _ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _npdf(x):
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def time_to_expiry(expiry, now=None, sim=False):
    """Years until expiry. expiry may be a datetime (real client) or sim seconds (simulator)."""
    if expiry is None:
        return 0.0
    if isinstance(expiry, _dt.datetime):
        now = now or _dt.datetime.now(expiry.tzinfo)
        return max(0.0, (expiry - now).total_seconds() / SECONDS_PER_YEAR)
    return max(0.0, (float(expiry) - float(now or 0.0)) / (SECONDS_PER_YEAR_SIM if sim else SECONDS_PER_YEAR))


def _kind(kind):
    k = str(kind or "call").lower()
    return "put" if "put" in k else "call"


def bs_price(s, k, tau, vol, r=0.0, kind="call"):
    """European option price. tau in years, vol and r annualised (0.3 = 30%)."""
    kind = _kind(kind)
    if tau <= 0 or vol <= 0:
        intrinsic = max(0.0, s - k) if kind == "call" else max(0.0, k - s)
        return intrinsic
    sq = vol * math.sqrt(tau)
    d1 = (math.log(s / k) + (r + 0.5 * vol * vol) * tau) / sq
    d2 = d1 - sq
    if kind == "call":
        return s * _ncdf(d1) - k * math.exp(-r * tau) * _ncdf(d2)
    return k * math.exp(-r * tau) * _ncdf(-d2) - s * _ncdf(-d1)


def bs_greeks(s, k, tau, vol, r=0.0, kind="call"):
    """delta (per 1 unit of stock), gamma, vega (per 1.00 of vol, i.e. per 100 vol points),
    theta (per year), rho. Divide vega by 100 for 'per vol point'."""
    kind = _kind(kind)
    if tau <= 0 or vol <= 0:
        itm = (s > k) if kind == "call" else (s < k)
        return {"delta": (1.0 if itm else 0.0) * (1 if kind == "call" else -1), "gamma": 0.0, "vega": 0.0,
                "theta": 0.0, "rho": 0.0}
    sq = vol * math.sqrt(tau)
    d1 = (math.log(s / k) + (r + 0.5 * vol * vol) * tau) / sq
    d2 = d1 - sq
    disc = math.exp(-r * tau)
    gamma = _npdf(d1) / (s * sq)
    vega = s * _npdf(d1) * math.sqrt(tau)
    if kind == "call":
        delta = _ncdf(d1)
        theta = -s * _npdf(d1) * vol / (2 * math.sqrt(tau)) - r * k * disc * _ncdf(d2)
        rho = k * tau * disc * _ncdf(d2)
    else:
        delta = _ncdf(d1) - 1.0
        theta = -s * _npdf(d1) * vol / (2 * math.sqrt(tau)) + r * k * disc * _ncdf(-d2)
        rho = -k * tau * disc * _ncdf(-d2)
    return {"delta": delta, "gamma": gamma, "vega": vega, "theta": theta, "rho": rho}


def implied_vol(price, s, k, tau, r=0.0, kind="call", lo=1e-4, hi=5.0, tol=1e-6):
    """Vol that makes bs_price match `price` (bisection; None if price is outside no-arbitrage bounds)."""
    if tau <= 0:
        return None
    if price < bs_price(s, k, tau, lo, r, kind) - tol or price > bs_price(s, k, tau, hi, r, kind) + tol:
        return None
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if bs_price(s, k, tau, mid, r, kind) > price:
            hi = mid
        else:
            lo = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


def future_fair_value(s, r, tau):
    """Cost of carry, no dividends: F = S * exp(r * tau)."""
    return s * math.exp(r * tau)


def etf_fair_value(prices, constituents, divisor=1.0, cash_comp=0.0, multiplier=1.0):
    """ASSUMPTION (re-check the brief): ETF = multiplier * sum(shares_i * price_i) / divisor + cash_comp."""
    basket = sum(constituents[i] * prices[i] for i in constituents)
    return multiplier * basket / (divisor or 1.0) + (cash_comp or 0.0)


def realised_vol(prices, dt_seconds, sim=False):
    """Annualised volatility from a list of prices sampled every dt_seconds."""
    rets = [math.log(b / a) for a, b in zip(prices, prices[1:]) if a > 0 and b > 0]
    if len(rets) < 3:
        return None
    mu = sum(rets) / len(rets)
    var = sum((x - mu) ** 2 for x in rets) / (len(rets) - 1)
    year = SECONDS_PER_YEAR_SIM if sim else SECONDS_PER_YEAR
    return math.sqrt(var * year / dt_seconds)
