import base64
import json
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

from indicators import add_indicators, detect_rsi_divergence

try:
    import anthropic
    _ANTHROPIC_OK = True
except ImportError:
    _ANTHROPIC_OK = False


# Umbrales únicos de decisión (coherentes en todos los timeframes y en el combinado)
BUY_THRESHOLD  = 2.2
SELL_THRESHOLD = -1.8


def _key_levels(df, price, k=3):
    """Soporte y resistencia basados en pivotes reales cercanos al precio,
    no en el mínimo/máximo absoluto (que puede ser una mecha puntual)."""
    hi = df["High"].squeeze().to_numpy(dtype=float)
    lo = df["Low"].squeeze().to_numpy(dtype=float)
    n  = len(df)
    low_piv, high_piv = [], []
    for i in range(k, n - k):
        if lo[i] == np.nanmin(lo[i-k:i+k+1]):
            low_piv.append(lo[i])
        if hi[i] == np.nanmax(hi[i-k:i+k+1]):
            high_piv.append(hi[i])
    sups = [x for x in low_piv  if x < price]
    ress = [x for x in high_piv if x > price]
    support    = max(sups) if sups else float(np.nanmin(lo))
    resistance = min(ress) if ress else float(np.nanmax(hi))
    return support, resistance


# ─────────────────────────────────────────────
# PRECIO
# ─────────────────────────────────────────────
@st.cache_data(ttl=30)
def get_price(ticker):
    try:
        fi = yf.Ticker(ticker).fast_info
        return float(fi.last_price), float(fi.previous_close)
    except Exception:
        df = yf.download(ticker, period="2d", interval="1d", progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        c = df["Close"].squeeze()
        return float(c.iloc[-1]), float(c.iloc[-2])


# ─────────────────────────────────────────────
# RENDIMIENTO RELATIVO vs IBEX 35
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_ibex_relative(ticker):
    try:
        stock = yf.download(ticker,  period="2mo", interval="1d", auto_adjust=True, progress=False)
        ibex  = yf.download("^IBEX", period="2mo", interval="1d", auto_adjust=True, progress=False)
        for d in [stock, ibex]:
            if isinstance(d.columns, pd.MultiIndex):
                d.columns = d.columns.get_level_values(0)
        stk_c  = stock["Close"].squeeze().dropna().tail(21)
        ibex_c = ibex["Close"].squeeze().dropna().tail(21)
        if len(stk_c) < 2 or len(ibex_c) < 2:
            return None, None
        return (float((stk_c.iloc[-1] / stk_c.iloc[0] - 1) * 100),
                float((ibex_c.iloc[-1] / ibex_c.iloc[0] - 1) * 100))
    except Exception:
        return None, None


# ─────────────────────────────────────────────
# CATALIZADOR (EARNINGS)
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_catalyst_data(ticker, earnings_dates_json):
    """earnings_dates_json: JSON string of list[{quarter, date}] for this ticker."""
    from datetime import timedelta as _td
    entries = json.loads(earnings_dates_json) if earnings_dates_json else []
    try:
        today  = datetime.now().date()
        cutoff = today - pd.Timedelta(days=45).to_pytimedelta()
        past   = [e for e in entries if datetime.strptime(e["date"], "%Y-%m-%d").date() <= today]
        if not past:
            return {"has_catalyst": False}
        latest    = max(past, key=lambda e: e["date"])
        earn_date = datetime.strptime(latest["date"], "%Y-%m-%d").date()
        quarter   = latest["quarter"]
        if earn_date < cutoff:
            return {"has_catalyst": False, "last_quarter": quarter,
                    "last_date": earn_date.strftime("%d/%m/%Y")}

        reaction_start = earn_date
        while reaction_start.weekday() >= 5:
            reaction_start += _td(days=1)

        df = yf.download(ticker, period="3mo", interval="1d", auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 5:
            return {"has_catalyst": False}

        close = df["Close"].squeeze()
        vol   = df["Volume"].squeeze()
        vsma  = vol.rolling(20).mean()

        rs_ts     = pd.Timestamp(reaction_start)
        idx_dates = df.index.normalize()
        try:
            idx_dates = idx_dates.tz_localize(None)
        except Exception:
            try:
                idx_dates = idx_dates.tz_convert(None)
            except Exception:
                pass
        rs_ts_naive = rs_ts.tz_localize(None) if rs_ts.tzinfo else rs_ts
        mask_before = idx_dates <= rs_ts_naive
        if not mask_before.any():
            return {"has_catalyst": False}
        ev_pos = int(np.where(mask_before)[0][-1])

        price_ev    = float(close.iloc[ev_pos])
        after       = df.iloc[ev_pos + 1 : ev_pos + 4]
        if after.empty:
            return {"has_catalyst": False}
        price_after  = float(after["Close"].squeeze().iloc[-1])
        pct_rx       = (price_after / price_ev - 1) * 100
        vol_after_m  = float(after["Volume"].squeeze().mean())
        vsma_ev      = float(vsma.iloc[ev_pos]) if not pd.isna(vsma.iloc[ev_pos]) else None
        vol_ratio_rx = (vol_after_m / vsma_ev) if vsma_ev and vsma_ev > 0 else None

        if abs(pct_rx) < 1.5:
            conclusion = "sin reacción clara"
        elif pct_rx > 0 and vol_ratio_rx and vol_ratio_rx >= 1.0:
            conclusion = "descontó positivamente con convicción (volumen confirma)"
        elif pct_rx > 0:
            conclusion = "reacción alcista leve — sin convicción de volumen"
        elif pct_rx < 0 and vol_ratio_rx and vol_ratio_rx >= 1.0:
            conclusion = "descontó negativamente con convicción (volumen confirma)"
        else:
            conclusion = "reacción bajista leve — sin convicción de volumen"

        return {
            "has_catalyst": True,
            "quarter":      quarter,
            "date":         earn_date.strftime("%d/%m/%Y"),
            "pct_rx":       pct_rx,
            "vol_ratio":    vol_ratio_rx,
            "conclusion":   conclusion,
            "price_ev":     price_ev,
            "price_after":  price_after,
        }
    except Exception:
        return {"has_catalyst": False}


# ─────────────────────────────────────────────
# ANÁLISIS POR TIMEFRAME
# ─────────────────────────────────────────────
@st.cache_data(ttl=180, show_spinner=False)
def analyze_tf(ticker, label, period, interval, manual_vol_ratio=None):
    df = yf.download(ticker, period=period, interval=interval,
                     auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if df.empty or len(df) < 22:
        return None

    df    = add_indicators(df.dropna(subset=["Close"]))
    close = df["Close"].squeeze()
    price = float(close.iloc[-1])

    def safe(col, idx=-1):
        v = df[col].iloc[idx]
        return float(v) if not pd.isna(v) else None

    rsi    = safe("RSI")
    macd   = safe("MACD");     macd_p = safe("MACD",     -2)
    msig   = safe("MACD_sig"); msig_p = safe("MACD_sig", -2)
    bb_up  = safe("BB_up");    bb_lo  = safe("BB_lo");   bb_mid = safe("BB_mid")
    sma20  = safe("SMA20");    sma50  = safe("SMA50")
    atr    = safe("ATR") or price * 0.01

    vol_current = float(df["Volume"].iloc[-1]) if "Volume" in df.columns else None
    vol_sma20   = safe("Vol_SMA20")
    vol_ratio   = (vol_current / vol_sma20) if (vol_current and vol_sma20 and vol_sma20 > 0) else None
    if vol_ratio is not None and interval in ("1h", "15m") and vol_ratio < 0.15:
        vol_ratio = None
    vol_manual = False
    if vol_ratio is None and manual_vol_ratio and manual_vol_ratio > 0:
        vol_ratio  = float(manual_vol_ratio)
        vol_manual = True
    vwap    = safe("VWAP") if interval == "15m" else None
    rsi_div = detect_rsi_divergence(df)

    score   = 0.0
    signals = []

    if rsi:
        if rsi < 30:
            score += 2.0; signals.append(("bull", f"RSI {rsi:.0f} — sobrevendido · rebote probable"))
        elif rsi < 40:
            score += 1.0; signals.append(("bull", f"RSI {rsi:.0f} — zona de interés comprador"))
        elif rsi > 70:
            score -= 2.0; signals.append(("bear", f"RSI {rsi:.0f} — sobrecomprado · riesgo de corrección"))
        elif rsi > 60:
            score -= 1.0; signals.append(("bear", f"RSI {rsi:.0f} — zona de precaución"))
        else:
            signals.append(("neut", f"RSI {rsi:.0f} — zona neutral (30-60)"))

    if all(v is not None for v in [macd, msig, macd_p, msig_p]):
        if macd_p < msig_p and macd >= msig:
            score += 2.0; signals.append(("bull", "MACD cruce alcista ↑ — señal de entrada fresca"))
        elif macd_p > msig_p and macd <= msig:
            score -= 2.0; signals.append(("bear", "MACD cruce bajista ↓ — señal de salida fresca"))
        elif macd > msig:
            score += 0.5; signals.append(("bull", f"MACD sobre señal — momentum positivo ({macd:.4f})"))
        else:
            score -= 0.5; signals.append(("bear", f"MACD bajo señal — momentum negativo ({macd:.4f})"))

    if bb_up and bb_lo and bb_mid:
        if price <= bb_lo:
            score += 1.5; signals.append(("bull", f"Precio en banda inferior BB ({bb_lo:.2f}€) — zona de rebote"))
        elif price >= bb_up:
            score -= 1.5; signals.append(("bear", f"Precio en banda superior BB ({bb_up:.2f}€) — zona sobrecomprada"))
        elif price < bb_mid:
            score += 0.5; signals.append(("bull", f"Precio bajo media BB ({bb_mid:.2f}€) — zona neutra-alcista"))
        else:
            signals.append(("neut", "Precio en mitad alta BB — sin señal clara"))

    if sma20:
        if price > sma20:
            score += 0.5; signals.append(("bull", f"Precio ({price:.2f}€) sobre SMA20 ({sma20:.2f}€) — tendencia alcista"))
        else:
            score -= 0.5; signals.append(("bear", f"Precio ({price:.2f}€) bajo SMA20 ({sma20:.2f}€) — tendencia bajista"))
    if sma50:
        if price > sma50:
            score += 0.5; signals.append(("bull", f"Precio sobre SMA50 ({sma50:.2f}€) — estructura alcista"))
        else:
            score -= 0.5; signals.append(("bear", f"Precio bajo SMA50 ({sma50:.2f}€) — estructura bajista"))

    vol_tag = " (manual)" if vol_manual else ""
    if vol_ratio is not None:
        if vol_ratio >= 1.5:
            signals.append(("bull", f"Volumen {vol_ratio:.1f}× media 20d{vol_tag} — confirmación fuerte · señal válida"))
        elif vol_ratio >= 1.1:
            signals.append(("neut", f"Volumen {vol_ratio:.1f}× media 20d{vol_tag} — actividad normal"))
        elif vol_ratio < 0.7:
            signals.append(("neut", f"Volumen {vol_ratio:.1f}× media 20d{vol_tag} — sin convicción · señal débil"))
        else:
            signals.append(("neut", f"Volumen {vol_ratio:.1f}× media 20d{vol_tag}"))
    else:
        signals.append(("neut", "Volumen: dato no disponible — análisis condicionado"))

    if vwap and interval == "15m":
        if price > vwap:
            score += 0.3; signals.append(("bull", f"Precio sobre VWAP ({vwap:.2f}€) — sesión con sesgo alcista"))
        else:
            score -= 0.3; signals.append(("bear", f"Precio bajo VWAP ({vwap:.2f}€) — sesión con sesgo bajista"))

    if rsi_div == "bullish":
        score += 1.5; signals.append(("bull", "Divergencia alcista RSI — precio baja, RSI sube · posible giro al alza"))
    elif rsi_div == "bearish":
        score -= 1.5; signals.append(("bear", "Divergencia bajista RSI — precio sube, RSI baja · señal de agotamiento"))
    else:
        signals.append(("neut", "Sin divergencia RSI detectada"))

    n_back            = min(60, max(20, len(df) // 2))
    support, resistance = _key_levels(df.tail(n_back), price)

    if score >= BUY_THRESHOLD:
        verdict = "COMPRAR"
    elif score <= SELL_THRESHOLD:
        verdict = "VENDER"
    else:
        verdict = "ESPERAR"

    return {
        "label": label, "interval": interval,
        "score": score,  "verdict": verdict,
        "signals": signals, "price": price,
        "rsi": rsi, "atr": atr,
        "vol_ratio": vol_ratio, "vol_manual": vol_manual,
        "vwap": vwap, "rsi_div": rsi_div,
        "support": support, "resistance": resistance,
        "sma20": sma20, "sma50": sma50,
        "bb_up": bb_up, "bb_lo": bb_lo,
    }


# ─────────────────────────────────────────────
# VEREDICTO COMBINADO
# ─────────────────────────────────────────────
def combined_verdict(results, position):
    valid = [r for r in results if r]
    if not valid:
        return "ESPERAR", 0.0, "Sin datos suficientes.", {}

    base_weights    = {"1d": 3, "1h": 2, "15m": 1}
    vol_valid_count = 0
    adj_weights     = {}

    for r in valid:
        w  = base_weights.get(r["interval"], 1)
        vr = r.get("vol_ratio")
        if vr is not None:
            if vr < 0.4:    w *= 0.25
            elif vr < 0.7:  w *= 0.5
            elif vr >= 1.3: w *= 1.2
            if vr >= 0.7:
                vol_valid_count += 1
        adj_weights[r["interval"]] = w

    w_score_sum = sum(r["score"] * adj_weights.get(r["interval"], 1) for r in valid)
    w_total     = sum(adj_weights.get(r["interval"], 1) for r in valid)
    avg_score   = w_score_sum / w_total if w_total > 0 else 0.0

    n_buy  = sum(1 for r in valid if r["verdict"] == "COMPRAR")
    n_sell = sum(1 for r in valid if r["verdict"] == "VENDER")

    if   n_buy >= 2 and n_sell == 0:    verdict = "COMPRAR"
    elif n_sell >= 2 and n_buy == 0:    verdict = "VENDER"
    elif avg_score >= BUY_THRESHOLD:    verdict = "COMPRAR"
    elif avg_score <= SELL_THRESHOLD:   verdict = "VENDER"
    else:                               verdict = "MANTENER"

    div_alert = False
    for r in valid:
        if r["interval"] == "15m" and r.get("rsi_div") == "bearish":
            res = r.get("resistance")
            prc = r.get("price")
            if res and prc and prc >= res * 0.98:
                div_alert = True
                if verdict == "COMPRAR":
                    verdict = "MANTENER CON ALERTA"
                break

    price   = valid[0]["price"]
    atr_day = next((r.get("atr") for r in valid if r["interval"] == "1d"), None)
    pnl_pct = (price / position["avg_price"] - 1) * 100 if position["avg_price"] else 0

    if verdict == "COMPRAR" and position["shares"] > 0:
        context = (f"Ya tienes {position['shares']:.0f} acciones abiertas. "
                   "Los indicadores apoyan la continuación alcista — posible ampliación de posición.")
    elif verdict == "MANTENER CON ALERTA":
        context = (f"Señal alcista degradada por divergencia bajista RSI en 15min cerca de resistencia. "
                   f"Posición {pnl_pct:+.1f}% — mantén pero no añadas hasta confirmación de ruptura.")
    elif verdict == "VENDER" and pnl_pct > 0:
        context = (f"Estás en beneficio ({pnl_pct:+.1f}%). "
                   "Señal de salida activa — considera recoger beneficios parciales o totales.")
    elif verdict == "VENDER" and pnl_pct < 0:
        context = (f"Estás en pérdidas ({pnl_pct:+.1f}%). "
                   "Señal de alerta — evalúa reducir exposición o activar stop loss.")
    elif verdict == "MANTENER":
        context = (f"Posición abierta a {position['avg_price']:.2f}€ · precio actual {price:.2f}€ "
                   f"({pnl_pct:+.1f}%). Sin señal clara de cambio — mantén y espera confirmación.")
    else:
        context = ""

    all_vols    = [r.get("vol_ratio") for r in valid if r.get("vol_ratio") is not None]
    all_low_vol = len(all_vols) > 0 and all(v < 0.5 for v in all_vols)

    if vol_valid_count == 0:
        verdict   = "MANTENER"
        intra_res = [r["resistance"] for r in valid
                     if r["interval"] in ("1h", "15m") and r.get("resistance") and r["resistance"] > price]
        intra_sup = [r["support"] for r in valid
                     if r["interval"] in ("1h", "15m") and r.get("support") and r["support"] < price]
        day_res   = next((r["resistance"] for r in valid if r["interval"] == "1d"), None)
        day_sup   = next((r["support"]    for r in valid if r["interval"] == "1d"), None)
        bull_lv   = min(intra_res) if intra_res else day_res
        bear_lv   = max(intra_sup) if intra_sup else day_sup
        act_bull  = (f"\n🟢 Activación alcista: cierre sobre {bull_lv:.2f}€ con Vol ≥ 1× "
                     "confirma escenario alcista.") if bull_lv else ""
        act_bear  = (f"\n🔴 Activación bajista: cierre bajo {bear_lv:.2f}€ con Vol ≥ 0.7× "
                     "activa escenario bajista.") if bear_lv else ""
        context   = (
            "MERCADO INACTIVO. Sin volumen en ningún timeframe: las señales técnicas no tienen "
            "validez. Esperar sesión con Vol/20d ≥ 0.7× antes de tomar cualquier decisión."
            + act_bull + act_bear
        )
    elif all_low_vol:
        context += (
            " ⚠️ Volumen < 50% de la media en todos los timeframes: mercado sin participantes "
            "activos. Los movimientos de precio son ruido, no señal. No actuar hasta "
            "confirmación de volumen."
        )

    if (vol_valid_count > 0 and atr_day and position["avg_price"]
            and position["shares"] > 0 and atr_day > 0):
        loss_atr = (position["avg_price"] - price) / atr_day
        if loss_atr >= 1.0:
            supp_day  = next((r.get("support") for r in valid if r["interval"] == "1d"), None)
            warn_supp = f" Vigilar soporte en {supp_day:.2f}€." if supp_day else ""
            context  += (f" ⚠️ Posición fuera del rango de ruido normal "
                         f"({loss_atr:.1f}×ATR de pérdida).{warn_supp}")

    meta = {
        "vol_valid_count": vol_valid_count,
        "n_tf":            len(valid),
        "div_alert":       div_alert,
        "all_low_vol":     all_low_vol,
        "inactive":        vol_valid_count == 0,
        "adj_weights":     adj_weights,
    }
    return verdict, avg_score, context, meta


# ─────────────────────────────────────────────
# ANÁLISIS DE CAPTURA CON CLAUDE VISION
# ─────────────────────────────────────────────
def analyze_screenshot(img_bytes, mime, api_key, pos_ctx, nombre, ticker):
    if not _ANTHROPIC_OK:
        return "❌ Instala el paquete `anthropic` (`pip install anthropic`) para usar esta función."
    if not api_key:
        return "❌ Introduce tu Anthropic API Key en la barra lateral."
    try:
        client  = anthropic.Anthropic(api_key=api_key)
        img_b64 = base64.standard_b64encode(img_bytes).decode()
        prompt  = f"""Eres un analista técnico experto en renta variable española (IBEX 35).

Analiza este gráfico de {nombre} ({ticker}) capturado de Investing.com.

CONTEXTO DE LA POSICIÓN DEL INVERSOR:
{pos_ctx}

ANÁLISIS REQUERIDO — responde TODOS los puntos. Si un dato no es visible en el gráfico, indícalo como "no visible en el gráfico":

1. **Tendencia principal** visible (alcista / bajista / lateral)
2. **Soportes clave**: niveles donde el valor ha rebotado o podría rebotar
3. **Resistencias clave**: niveles donde el valor ha frenado o podría frenar
4. **Volumen** (CRÍTICO): ¿confirma o contradice la señal técnica visible? ¿Por encima o debajo de la media?
5. **ATR / volatilidad implícita**: rango de velas, stop y objetivo proporcionales
6. **Divergencias RSI** (CRÍTICO): precio vs RSI — alcista, bajista o ninguna
7. **Patrones técnicos**: figuras de velas o pautas de continuación / reversión
8. **Indicadores visibles**: RSI, MACD, medias — relaciónalos siempre con el volumen
9. **Rendimiento relativo**: fortaleza o debilidad vs índice/sector si es visible
10. **Recomendación concreta**: COMPRAR MÁS / MANTENER / REDUCIR / VENDER con precios de entrada, stop (€) y objetivo (€)

Sé directo. Adapta la recomendación a que el inversor YA TIENE posición abierta."""

        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1400,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64",
                                             "media_type": mime,
                                             "data": img_b64}},
                {"type": "text",  "text": prompt},
            ]}],
        )
        return resp.content[0].text
    except Exception as e:
        return f"❌ Error al analizar: {e}"
