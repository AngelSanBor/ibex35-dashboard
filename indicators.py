import pandas as pd
import numpy as np


def _rsi(s, p=14):
    d = s.diff()
    g = d.clip(lower=0).ewm(com=p-1, min_periods=p).mean()
    l = (-d.clip(upper=0)).ewm(com=p-1, min_periods=p).mean()
    return 100 - 100 / (1 + g / l.replace(0, np.nan))


def _macd(s, fast=12, slow=26, sig=9):
    m = s.ewm(span=fast, adjust=False).mean() - s.ewm(span=slow, adjust=False).mean()
    return m, m.ewm(span=sig, adjust=False).mean()


def _bb(s, p=20, n=2):
    sma = s.rolling(p).mean()
    sd  = s.rolling(p).std()
    return sma + n*sd, sma, sma - n*sd


def add_indicators(df):
    df = df.copy()
    c  = df["Close"].squeeze()
    h  = df["High"].squeeze()
    lo = df["Low"].squeeze()
    v  = df["Volume"].squeeze() if "Volume" in df.columns else pd.Series(dtype=float)
    df["EMA9"]  = c.ewm(span=9, adjust=False).mean()
    df["SMA20"] = c.rolling(20).mean()
    df["SMA50"] = c.rolling(50).mean()
    df["BB_up"], df["BB_mid"], df["BB_lo"] = _bb(c)
    df["RSI"]   = _rsi(c)
    df["MACD"], df["MACD_sig"] = _macd(c)
    tr = pd.concat([(h-lo), (h-c.shift()).abs(), (lo-c.shift()).abs()], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(14).mean()
    if not v.empty:
        df["Vol_SMA20"] = v.rolling(20).mean()
    if not v.empty:
        # VWAP reiniciado por sesión (cada día), no acumulado sobre todo el histórico
        typical = (h + lo + c) / 3
        grp = df.index.normalize()
        df["VWAP"] = (typical * v).groupby(grp).cumsum() / v.replace(0, np.nan).groupby(grp).cumsum()
    return df


def _pivot_idx(arr, k=2, kind="low"):
    """Índices de pivotes locales: un punto que es el mínimo/máximo de su ventana ±k."""
    out = []
    n   = len(arr)
    for i in range(k, n - k):
        if np.isnan(arr[i]):
            continue
        win = arr[i-k:i+k+1]
        if kind == "low" and arr[i] == np.nanmin(win):
            out.append(i)
        elif kind == "high" and arr[i] == np.nanmax(win):
            out.append(i)
    return out


def detect_rsi_divergence(df, lookback=40):
    """Divergencia entre precio y RSI usando pivotes reales (no extremos del rango)."""
    if len(df) < lookback + 2:
        return None
    sub   = df.tail(lookback)
    close = sub["Close"].squeeze().to_numpy(dtype=float)
    rsi   = sub["RSI"].squeeze().to_numpy(dtype=float)
    if np.isnan(rsi).sum() > lookback * 0.5:
        return None

    lows  = _pivot_idx(close, 2, "low")
    highs = _pivot_idx(close, 2, "high")

    # Divergencia alcista: precio hace mínimo más bajo pero RSI mínimo más alto
    if len(lows) >= 2:
        a, b = lows[-2], lows[-1]
        if (not np.isnan(rsi[a]) and not np.isnan(rsi[b])
                and close[b] < close[a] and rsi[b] > rsi[a]):
            return "bullish"
    # Divergencia bajista: precio hace máximo más alto pero RSI máximo más bajo
    if len(highs) >= 2:
        a, b = highs[-2], highs[-1]
        if (not np.isnan(rsi[a]) and not np.isnan(rsi[b])
                and close[b] > close[a] and rsi[b] < rsi[a]):
            return "bearish"
    return None
