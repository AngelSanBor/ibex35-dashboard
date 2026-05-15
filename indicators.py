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
        typical = (h + lo + c) / 3
        df["VWAP"] = (typical * v).cumsum() / v.replace(0, np.nan).cumsum()
    return df


def detect_rsi_divergence(df, lookback=14):
    if len(df) < lookback + 2:
        return None
    close = df["Close"].squeeze().tail(lookback)
    rsi   = df["RSI"].squeeze().tail(lookback).dropna()
    if len(rsi) < 4:
        return None
    price_up = close.iloc[-1] > close.iloc[0]
    rsi_up   = rsi.iloc[-1]   > rsi.iloc[0]
    if price_up and not rsi_up:
        return "bearish"
    if not price_up and rsi_up:
        return "bullish"
    return None
