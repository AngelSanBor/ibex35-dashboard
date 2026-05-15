"""
Backtester point-in-time sobre datos diarios.

Para cada fecha del histórico (tras un periodo de calentamiento), calcula el score
con los mismos indicadores que el análisis en vivo, registra la señal y comprueba
qué hizo el precio en los `forward_days` siguientes.

Solo usa el timeframe diario — el horario e intraday no tienen histórico suficiente
en yfinance para un backtest fiable.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from indicators import add_indicators

_WARMUP = 55  # mínimo de barras para que SMA50 y todos los indicadores sean fiables


def _score_slice(df_slice):
    """Replica el scoring del timeframe diario sobre un slice de datos."""
    if len(df_slice) < _WARMUP:
        return None
    df = add_indicators(df_slice.dropna(subset=["Close"]))
    c  = df["Close"].squeeze()
    price = float(c.iloc[-1])

    def safe(col, idx=-1):
        v = df[col].iloc[idx]
        return float(v) if not pd.isna(v) else None

    rsi    = safe("RSI")
    macd   = safe("MACD");     macd_p = safe("MACD",     -2)
    msig   = safe("MACD_sig"); msig_p = safe("MACD_sig", -2)
    bb_up  = safe("BB_up");    bb_lo  = safe("BB_lo");   bb_mid = safe("BB_mid")
    sma20  = safe("SMA20");    sma50  = safe("SMA50")

    score = 0.0

    if rsi:
        if rsi < 30:   score += 2.0
        elif rsi < 40: score += 1.0
        elif rsi > 70: score -= 2.0
        elif rsi > 60: score -= 1.0

    if all(v is not None for v in [macd, msig, macd_p, msig_p]):
        if macd_p < msig_p and macd >= msig:   score += 2.0
        elif macd_p > msig_p and macd <= msig: score -= 2.0
        elif macd > msig:                       score += 0.5
        else:                                   score -= 0.5

    if bb_up and bb_lo and bb_mid:
        if price <= bb_lo:   score += 1.5
        elif price >= bb_up: score -= 1.5
        elif price < bb_mid: score += 0.5

    if sma20: score += 0.5 if price > sma20 else -0.5
    if sma50: score += 0.5 if price > sma50 else -0.5

    return score


_WATCH_THRESHOLD = 1.5  # umbral fijo para señales VIGILAR (por debajo de COMPRAR)


def run_backtest(ticker, period="2y", forward_days=5,
                 buy_threshold=2.2, sell_threshold=-1.8):
    """
    Descarga `period` de datos diarios y corre el backtest point-in-time.

    Returns
    -------
    dict con claves:
        ticker, forward_days, n_signals,
        buy   → {n, win_rate, avg_ret, best, worst},
        watch → {n, win_rate, avg_ret, best, worst},
        sell  → {n, win_rate, avg_ret, best, worst},
        detail → DataFrame con todas las señales
    None si no hay suficientes datos.
    """
    df = yf.download(ticker, period=period, interval="1d",
                     auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if df.empty or len(df) < _WARMUP + forward_days + 1:
        return None

    df    = df.dropna(subset=["Close"])
    close = df["Close"].squeeze()
    records = []

    for i in range(_WARMUP, len(df) - forward_days):
        score = _score_slice(df.iloc[:i + 1])
        if score is None:
            continue
        if score >= buy_threshold:
            signal = "COMPRAR"
        elif buy_threshold > _WATCH_THRESHOLD and score >= _WATCH_THRESHOLD:
            signal = "VIGILAR"
        elif score <= sell_threshold:
            signal = "VENDER"
        else:
            continue  # solo registrar señales reales

        entry   = float(close.iloc[i])
        exit_   = float(close.iloc[i + forward_days])
        fwd_ret = (exit_ / entry - 1) * 100
        correct = (signal == "COMPRAR" and fwd_ret > 0) or (signal == "VENDER" and fwd_ret < 0)

        records.append({
            "Fecha":             df.index[i].strftime("%d/%m/%Y"),
            "Señal":             signal,
            "Score":             round(score, 2),
            "Entrada (€)":       round(entry, 3),
            f"Salida +{forward_days}d (€)": round(exit_, 3),
            f"Retorno {forward_days}d (%)": round(fwd_ret, 2),
            "Correcto":          correct,
        })

    if not records:
        return {"n_signals": 0, "ticker": ticker, "forward_days": forward_days}

    detail = pd.DataFrame(records)
    ret_col = f"Retorno {forward_days}d (%)"

    def _stats(sub):
        if sub.empty:
            return {"n": 0, "win_rate": 0.0, "avg_ret": 0.0, "best": 0.0, "worst": 0.0}
        n = len(sub)
        return {
            "n":        n,
            "win_rate": round(sub["Correcto"].sum() / n * 100, 1),
            "avg_ret":  round(sub[ret_col].mean(), 2),
            "best":     round(sub[ret_col].max(), 2),
            "worst":    round(sub[ret_col].min(), 2),
        }

    return {
        "ticker":       ticker,
        "forward_days": forward_days,
        "n_signals":    len(records),
        "buy":          _stats(detail[detail["Señal"] == "COMPRAR"]),
        "watch":        _stats(detail[detail["Señal"] == "VIGILAR"]),
        "sell":         _stats(detail[detail["Señal"] == "VENDER"]),
        "detail":       detail,
    }
