import json
from datetime import datetime
from pathlib import Path
import yfinance as yf

NEWS_CACHE = Path(__file__).parent / "news_cache.json"


def load_news_cache():
    if NEWS_CACHE.exists():
        try:
            data = json.loads(NEWS_CACHE.read_text(encoding="utf-8"))
            return data.get("news", []), data.get("fetched_at", "")
        except Exception:
            pass
    return [], ""


def _parse_news_items(raw, limit=20):
    out = []
    for item in raw[:limit]:
        c         = item.get("content", item)
        title     = (c.get("title") or item.get("title") or "").strip()
        if not title:
            continue
        provider  = c.get("provider", {})
        publisher = provider.get("displayName") or item.get("publisher") or ""
        link      = (c.get("canonicalUrl", {}).get("url") or
                     c.get("clickThroughUrl", {}).get("url") or
                     item.get("link") or "#")
        pub = c.get("pubDate") or c.get("displayTime") or ""
        if pub:
            try:
                dt  = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                fmt = dt.strftime("%d/%m %H:%M")
            except Exception:
                fmt = ""
        else:
            ts  = item.get("providerPublishTime", 0)
            fmt = datetime.fromtimestamp(ts).strftime("%d/%m %H:%M") if ts else ""
        out.append({"title": title, "publisher": publisher, "link": link,
                    "time": fmt, "source": "yfinance"})
    return out


def get_news_live(ticker):
    # Intenta yf.Search primero (permite pedir más noticias)
    try:
        search = yf.Search(ticker, news_count=20, enable_fuzzy_query=False)
        raw    = search.news or []
        if raw:
            return _parse_news_items(raw, limit=20)
    except Exception:
        pass
    # Fallback a yf.Ticker().news
    try:
        raw = yf.Ticker(ticker).news or []
        return _parse_news_items(raw, limit=20)
    except Exception:
        return []


def get_news(ticker, force_refresh=False):
    # Cache was built for IDR.MC; skip it for other tickers or when forced
    if not force_refresh and ticker == "IDR.MC":
        cached, fetched_at = load_news_cache()
        if cached:
            return cached, f"caché actualizado: {fetched_at}"
    live = get_news_live(ticker)
    return live, "tiempo real"
