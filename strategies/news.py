"""Reading social media posts: which instruments a post is about, and whether it is good or bad news.

Deliberately simple (keyword rules), fast and explainable. The lists are plain data: extend them on the
day once you have seen what the real posts look like (they are logged in news.jsonl).
"""
import re

POSITIVE = ["beat", "beats", "smash", "smashes", "raise", "raises", "raised", "upgrade", "upgrades", "breakthrough",
            "record", "surge", "surges", "soar", "soars", "rally", "rallies", "boom", "strong buy", "order",
            "contract", "approval", "approved", "partnership", "buyback", "outperform", "jumps", "wins"]
NEGATIVE = ["miss", "misses", "slide", "slides", "restriction", "restrictions", "resign", "resigns", "short seller",
            "sell-off", "selloff", "fear", "fears", "downgrade", "downgrades", "probe", "lawsuit", "cut", "cuts",
            "plunge", "plunges", "recall", "fraud", "ban", "warns", "warning", "delay", "delays", "underperform",
            "questioning", "falls", "drops", "crash"]

# sector words -> instruments. ASSUMPTION: matches the practice market; edit if the brief differs.
SECTORS = {
    "chip": ["NVDA", "AMD", "AVGO"], "chips": ["NVDA", "AMD", "AVGO"], "semiconductor": ["NVDA", "AMD", "AVGO", "MU"],
    "memory": ["MU", "SNDK"], "storage": ["SNDK", "MU"], "cloud": ["CRWV", "NBIS"], "neocloud": ["CRWV", "NBIS"],
    "data centre": ["VRT", "CRWV", "NBIS"], "data center": ["VRT", "CRWV", "NBIS"], "power": ["VRT"],
}
# company names people write instead of tickers
NAMES = {"nvidia": "NVDA", "advanced micro": "AMD", "broadcom": "AVGO", "coreweave": "CRWV", "micron": "MU",
         "nebius": "NBIS", "sandisk": "SNDK", "vertiv": "VRT"}


def _has(text, word):
    return re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", text) is not None


def sentiment(text):
    """+n for good news, -n for bad, 0 for nothing clear."""
    t = (text or "").lower()
    return sum(_has(t, w) for w in POSITIVE) - sum(_has(t, w) for w in NEGATIVE)


def instruments_in(text, instruments, meta=None):
    """Instruments a post is about: tickers, company names, sector words, or meta_data fields."""
    found = []
    raw = text or ""
    for i in instruments:
        if re.search(r"(?<![A-Za-z0-9_])" + re.escape(i) + r"(?![A-Za-z0-9_])", raw):
            found.append(i)
    low = raw.lower()
    for name, tick in NAMES.items():
        if tick in instruments and tick not in found and _has(low, name):
            found.append(tick)
    for word, insts in SECTORS.items():
        if _has(low, word):
            found += [i for i in insts if i in instruments and i not in found]
    for v in (meta or {}).values():
        if isinstance(v, str) and v in instruments and v not in found:
            found.append(v)
    return found


def read_post(post, instruments):
    """-> (instruments, sentiment, text, timestamp) for a SocialMediaFeed-like object or dict."""
    get = (lambda k: post.get(k)) if isinstance(post, dict) else (lambda k: getattr(post, k, None))
    text = get("post") or ""
    meta = get("meta_data") or {}
    return instruments_in(text, instruments, meta if isinstance(meta, dict) else {}), sentiment(text), text, get("timestamp")
