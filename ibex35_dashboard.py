"""
IBEX 35 · Análisis IA Swing Trading
Multi-timeframe + Backtesting + Noticias + Visión por IA
Rev. 2 — resumen sencillo + fallos técnicos corregidos
"""

import json
import os
from datetime import datetime

import streamlit as st
import yfinance as yf

from analysis import (
    analyze_tf, combined_verdict,
    get_catalyst_data, get_ibex_relative, get_price,
    analyze_screenshot,
)
from backtester import run_backtest
from news import get_news
from ui_components import (
    render_backtest_results, render_catalyst, render_news,
    render_position, render_quick_summary, render_scenarios, render_signal_table,
    render_target_alert, render_tf_block, render_verdict,
)

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="IBEX35 · Análisis IA",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    html, body, [class*="css"], [data-testid="stAppViewContainer"],
    [data-testid="stHeader"], .main {
        background: #03050d !important;
        font-family: 'Inter', sans-serif;
    }
    [data-testid="stSidebar"] {
        background: #060914 !important;
        border-right: 1px solid #0f1426;
    }
    .block-container { padding-top: 1.4rem !important; max-width: 1260px; }

    h1,h2,h3 { color: #eef2ff !important; font-family: 'Inter', sans-serif; font-weight: 800; letter-spacing:-0.02em; }
    p, li, span { font-family: 'Inter', sans-serif; }

    .vcard {
        border-radius: 20px; padding: 36px 42px;
        display: flex; align-items: center; justify-content: space-between;
        flex-wrap: wrap; gap: 28px; position: relative;
    }
    .vcard-buy {
        background: linear-gradient(145deg, #020d05 0%, #030f07 60%, #041209 100%);
        border: 1px solid #14532d;
        box-shadow: 0 0 80px rgba(20,83,45,0.18), 0 0 0 1px rgba(74,222,128,0.06) inset, 0 40px 80px rgba(0,0,0,0.6);
    }
    .vcard-sell {
        background: linear-gradient(145deg, #0c0202 0%, #100303 60%, #130404 100%);
        border: 1px solid #7f1d1d;
        box-shadow: 0 0 80px rgba(127,29,29,0.2), 0 0 0 1px rgba(248,113,113,0.05) inset, 0 40px 80px rgba(0,0,0,0.6);
    }
    .vcard-hold {
        background: linear-gradient(145deg, #080601 0%, #0d0a02 60%, #110d02 100%);
        border: 1px solid #78350f;
        box-shadow: 0 0 60px rgba(120,53,15,0.15), 0 0 0 1px rgba(251,191,36,0.04) inset, 0 40px 80px rgba(0,0,0,0.6);
    }

    .tf-card {
        border-radius: 16px; padding: 22px 24px; margin-bottom: 0;
        border: 1px solid #0d1022; position: relative; overflow: hidden;
    }
    .tf-buy  { background: linear-gradient(160deg, #020b05 0%, #040e07 100%); border-color: #0f3a1f; box-shadow: 0 8px 32px rgba(15,58,31,0.25); }
    .tf-sell { background: linear-gradient(160deg, #0b0202 0%, #0f0303 100%); border-color: #3a0f0f; box-shadow: 0 8px 32px rgba(58,15,15,0.25); }
    .tf-hold { background: linear-gradient(160deg, #090702 0%, #0d0b03 100%); border-color: #3a2808; box-shadow: 0 8px 32px rgba(58,40,8,0.2); }

    .pill {
        display: inline-flex; align-items: center; padding: 5px 14px;
        border-radius: 5px; font-size: 0.7rem; font-weight: 900;
        letter-spacing: .12em; text-transform: uppercase;
    }
    .pill-buy  { background: rgba(20,83,45,0.5);  color: #4ade80; border: 1px solid #15803d; }
    .pill-sell { background: rgba(127,29,29,0.5); color: #fca5a5; border: 1px solid #991b1b; }
    .pill-hold { background: rgba(120,53,15,0.5); color: #fcd34d; border: 1px solid #a16207; }

    .chip {
        display: inline-flex; flex-direction: column; align-items: flex-start;
        background: rgba(255,255,255,0.025); border: 1px solid #0f1428;
        border-radius: 10px; padding: 10px 15px; min-width: 96px; backdrop-filter: blur(8px);
    }
    .chip-label { color: #2d3a5a; font-size: 0.65rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; margin-bottom: 5px; }
    .chip-value { color: #dde5ff; font-size: 1.05rem; font-weight: 700; }

    .sig-bull { background: rgba(10,40,20,0.5); border-left: 2px solid #16a34a; border-radius: 0 8px 8px 0; padding: 7px 14px; margin: 3px 0; color: #86efac; font-size: 0.88rem; }
    .sig-bear { background: rgba(50,8,8,0.5);   border-left: 2px solid #dc2626; border-radius: 0 8px 8px 0; padding: 7px 14px; margin: 3px 0; color: #fca5a5; font-size: 0.88rem; }
    .sig-neut { background: rgba(10,14,28,0.6); border-left: 2px solid #1a2240; border-radius: 0 8px 8px 0; padding: 7px 14px; margin: 3px 0; color: #374151; font-size: 0.88rem; }

    .pos-row { background: rgba(255,255,255,0.02); border: 1px solid #0f1428; border-radius: 14px; padding: 18px 22px; margin: 6px 0; }

    .news-item { background: rgba(255,255,255,0.02); border: 1px solid #0f1428; border-radius: 12px; padding: 15px 20px; margin: 6px 0; transition: border-color 0.15s ease; }
    .news-item:hover { border-color: #1e2c55; background: rgba(255,255,255,0.035); }

    .sec-header {
        color: #1e2c50; font-size: 0.65rem; font-weight: 900; letter-spacing: .18em;
        text-transform: uppercase; margin: 36px 0 14px; padding-bottom: 10px;
        border-bottom: 1px solid #0d1428; display: flex; align-items: center; gap: 10px;
    }

    hr { border-color: #0d1428 !important; }

    [data-testid="stMetricValue"]  { color: #eef2ff !important; font-size: 1.35rem !important; font-weight: 800 !important; letter-spacing: -0.01em; }
    [data-testid="stMetricLabel"]  { color: #2d3a5a !important; font-size: 0.65rem !important; letter-spacing: .1em; text-transform: uppercase; font-weight: 700 !important; }
    [data-testid="stMetricDelta"]  { font-size: 0.8rem !important; }
    [data-testid="metric-container"] { background: rgba(255,255,255,0.02); border: 1px solid #0f1428; border-radius: 14px; padding: 16px 20px !important; }

    .banner-inactive  { background: rgba(10,14,28,0.95); border: 1px solid #1a2240; border-radius: 12px; padding: 16px 22px; }
    .banner-div-tech  { background: rgba(60,15,110,0.15); border: 1px solid #5b21b6; border-radius: 12px; padding: 14px 20px; }
    .level-op  { background: rgba(90,35,5,0.2);  border: 1px solid #7c2d12; border-radius: 14px; padding: 18px 20px; }
    .level-str { background: rgba(255,255,255,0.02); border: 1px solid #0f1428; border-radius: 14px; padding: 18px 20px; }

    /* ═══ MÓVIL / iPHONE ═══════════════════════════════════════════════ */
    @media screen and (max-width: 768px) {
        .block-container { padding: 4.5rem 0.6rem 1rem !important; max-width: 100% !important; }

        /* Fuentes globales más grandes */
        p, li { font-size: 0.98rem !important; line-height: 1.65 !important; }
        h1 { font-size: 1.55rem !important; margin-top: 0 !important; padding-top: 0 !important; }
        h2 { font-size: 1.25rem !important; }
        h3 { font-size: 1.1rem !important; }
        .sec-header { font-size: 0.74rem !important; letter-spacing: .1em !important; margin: 22px 0 10px !important; }

        /* Métricas: números más grandes */
        [data-testid="stMetricValue"]  { font-size: 1.55rem !important; }
        [data-testid="stMetricLabel"]  { font-size: 0.74rem !important; }
        [data-testid="stMetricDelta"]  { font-size: 0.88rem !important; }
        [data-testid="metric-container"] { padding: 12px 14px !important; }

        /* Tarjeta veredicto: apilada verticalmente */
        .vcard { flex-direction: column !important; padding: 18px 14px !important; gap: 14px !important; align-items: flex-start !important; }
        .vcard > div:first-child  { min-width: unset !important; width: 100% !important; }
        .vcard > div:last-child   { min-width: unset !important; width: 100% !important; flex-direction: row !important; flex-wrap: wrap !important; align-items: flex-start !important; gap: 10px !important; }

        /* Texto COMPRAR/VENDER: más grande aún */
        .vcard div[style*="3.4rem"] { font-size: 2.8rem !important; }

        /* Chips: 2 por fila */
        .chip { min-width: calc(50% - 8px) !important; flex: 1 1 calc(50% - 8px) !important; padding: 10px 10px !important; }
        .chip-label { font-size: 0.70rem !important; }
        .chip-value { font-size: 1.0rem !important; }

        /* Pills */
        .pill { font-size: 0.80rem !important; padding: 6px 14px !important; }

        /* TF cards */
        .tf-card { padding: 14px 12px !important; }

        /* Señales técnicas */
        .sig-bull, .sig-bear, .sig-neut { font-size: 0.92rem !important; padding: 8px 12px !important; }

        /* Tablas: scroll horizontal en pantalla pequeña */
        table { display: block !important; overflow-x: auto !important; -webkit-overflow-scrolling: touch !important; font-size: 0.86rem !important; white-space: nowrap !important; }

        /* Noticias */
        .news-item { padding: 12px 12px !important; }
        .news-item a { font-size: 1.0rem !important; line-height: 1.5 !important; }

        /* Filas de posición */
        .pos-row { padding: 12px 12px !important; }

        /* Botones táctiles más grandes */
        [data-testid="stButton"] button { font-size: 1rem !important; min-height: 48px !important; }

        /* Niveles clave */
        .level-op, .level-str { padding: 14px 14px !important; }

        /* Sidebar más ancha en móvil para mejor usabilidad */
        [data-testid="stSidebar"] { min-width: 280px !important; }
        [data-testid="stSidebar"] label { font-size: 0.95rem !important; }
        [data-testid="stSidebar"] input { font-size: 0.95rem !important; min-height: 44px !important; }
        [data-testid="stSidebar"] select { font-size: 0.95rem !important; min-height: 44px !important; }
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────
IBEX35_NAMES = {
    "IDR.MC": "Indra Sistemas",    "SAN.MC": "Santander",
    "BBVA.MC": "BBVA",             "TEF.MC": "Telefónica",
    "IBE.MC": "Iberdrola",         "REP.MC": "Repsol",
    "AMS.MC": "Amadeus",           "ACS.MC": "ACS",
    "FER.MC": "Ferrovial",         "ITX.MC": "Inditex",
    "AENA.MC": "AENA",             "ENG.MC": "Enagás",
    "REE.MC": "Red Eléctrica",     "MAP.MC": "Mapfre",
    "GRF.MC": "Grifols",           "SAB.MC": "Sabadell",
    "CABK.MC": "CaixaBank",        "BKT.MC": "Bankinter",
    "CLNX.MC": "Cellnex",          "MTS.MC": "ArcelorMittal",
    "PHM.MC": "Pharma Mar",        "ACX.MC": "Acerinox",
    "ANA.MC": "Acciona",           "NTGY.MC": "Naturgy",
    "COL.MC": "Inmobiliaria Colonial", "MRL.MC": "Merlin Properties",
    "LOGN.MC": "Logista",          "PUIG.MC": "Puig",
    "SOL.MC": "Solaria",           "VIS.MC": "Viscofan",
    "IAG.MC": "IAG",               "ELE.MC": "Endesa",
    "ROVI.MC": "Lab. Rovi",        "UNI.MC": "Unicaja",
    "CIE.MC": "CIE Automotive",
}

# Fechas de resultados trimestrales — actualizar manualmente
EARNINGS_DATES = {
    "IDR.MC": [
        {"quarter": "Q3 2024", "date": "2024-10-31"},
        {"quarter": "Q4 2024", "date": "2025-02-26"},
        {"quarter": "Q1 2025", "date": "2025-04-30"},
        {"quarter": "Q2 2025", "date": "2025-07-30"},
        {"quarter": "Q3 2025", "date": "2025-10-30"},
        {"quarter": "Q4 2025", "date": "2026-02-27"},
        {"quarter": "Q1 2026", "date": "2026-04-29"},
    ]
}

TIMEFRAMES = [
    {"label": "Tendencia  (Diario · 6 meses)",  "period": "6mo", "interval": "1d",  "weight": 3},
    {"label": "Swing      (1 hora · 1 mes)",     "period": "1mo", "interval": "1h",  "weight": 2},
    {"label": "Entrada    (15 min · 5 días)",    "period": "5d",  "interval": "15m", "weight": 1},
]

MARKET_TICKERS = {
    "BZ=F":  {"name": "Brent",      "icon": "🛢"},
    "^VIX":  {"name": "VIX índice",  "icon": "😨"},
    "NQ=F":  {"name": "Nasdaq Fut", "icon": "📈"},
    "YM=F":  {"name": "Dow Fut",    "icon": "📊"},
}

BRENT_ALERT_PCT = 1.5


@st.cache_data(ttl=900)
def get_market_context():
    import pytz
    today_et = datetime.now(pytz.timezone("America/New_York")).date()
    result = {}
    for sym in MARKET_TICKERS:
        try:
            tk    = yf.Ticker(sym)
            price = float(tk.fast_info.last_price)
            df    = tk.history(period="5d", interval="1d")
            if df is None or len(df) < 2:
                result[sym] = None
                continue
            # Convertir índice del histórico a ET para comparar fechas correctamente
            last_date = df.index[-1].tz_convert("America/New_York").date()
            if last_date >= today_et:
                prev_close = float(df["Close"].iloc[-2])
            else:
                prev_close = float(df["Close"].iloc[-1])
            chg = ((price - prev_close) / prev_close * 100) if prev_close else 0.0
            result[sym] = {"price": price, "prev": prev_close, "chg_pct": chg}
        except Exception:
            result[sym] = None
    return result


def _market_sentiment(ctx):
    vix_d  = ctx.get("^VIX")
    nq_d   = ctx.get("NQ=F")
    ym_d   = ctx.get("YM=F")
    vix    = vix_d["price"] if vix_d else None
    fut_avg = ((nq_d["chg_pct"] if nq_d else 0) + (ym_d["chg_pct"] if ym_d else 0)) / 2

    if vix is None:
        return "DESCONOCIDO", "⚪", "#6b7280", "Sin datos de VIX disponibles"
    if vix > 35:
        return "PÁNICO", "🔴", "#f87171", f"VIX {vix:.1f} — miedo extremo en el mercado"
    if vix > 25:
        return "TEMEROSO", "🔴", "#fca5a5", f"VIX {vix:.1f} — alta volatilidad, precaución"
    if vix > 20:
        label = "NEGATIVO" if fut_avg < -0.3 else "PRECAUCIÓN"
        clr   = "#f87171" if fut_avg < -0.3 else "#fbbf24"
        return label, "🟡", clr, f"VIX {vix:.1f} — incertidumbre, futuros {fut_avg:+.1f}%"
    if vix < 15:
        if fut_avg > 0.2:
            return "POSITIVO", "🟢", "#4ade80", f"VIX {vix:.1f} bajo · futuros alcistas {fut_avg:+.1f}%"
        return "NEUTRAL", "🟡", "#fbbf24", f"VIX {vix:.1f} bajo pero futuros sin dirección clara"
    # VIX 15-20
    if fut_avg > 0.3:
        return "MOD. POSITIVO", "🟢", "#86efac", f"VIX {vix:.1f} controlado · futuros {fut_avg:+.1f}%"
    if fut_avg < -0.3:
        return "MOD. NEGATIVO", "🟡", "#fbbf24", f"VIX {vix:.1f} · futuros a la baja {fut_avg:+.1f}%"
    return "NEUTRAL", "🟡", "#fbbf24", f"VIX {vix:.1f} — sin señal clara de dirección"


def render_market_panel():
    ctx = get_market_context()
    sentiment, sem_icon, sem_clr, sem_desc = _market_sentiment(ctx)

    def _asset_html(sym):
        d = ctx.get(sym)
        meta = MARKET_TICKERS[sym]
        if d is None:
            return (
                f'<div style="display:flex;flex-direction:column;gap:3px;min-width:130px">'
                f'<span style="color:#1e2c50;font-size:0.6rem;font-weight:900;letter-spacing:.1em;'
                f'text-transform:uppercase">{meta["icon"]} {meta["name"]}</span>'
                f'<span style="color:#374151;font-size:0.82rem">N/D</span></div>'
            )
        chg    = d["chg_pct"]
        clr    = "#4ade80" if chg > 0 else "#f87171" if chg < 0 else "#6b7280"
        arrow  = "▲" if chg > 0 else "▼" if chg < 0 else "▸"
        is_brent = sym == "BZ=F"
        fast   = is_brent and abs(chg) >= BRENT_ALERT_PCT
        fast_tag = (
            f'<span style="background:rgba(251,191,36,0.15);border:1px solid #92400e;'
            f'border-radius:4px;padding:1px 6px;font-size:0.6rem;font-weight:900;'
            f'color:#fbbf24;margin-left:6px;letter-spacing:.06em">⚡ RÁPIDO</span>'
            if fast else ""
        )
        price_fmt = f"${d['price']:.2f}" if is_brent else f"{d['price']:,.1f}" if d['price'] > 1000 else f"{d['price']:.2f}"
        return (
            f'<div style="display:flex;flex-direction:column;gap:6px;min-width:150px">'
            f'<span style="color:#2d3a5a;font-size:1.1rem;font-weight:900;letter-spacing:.06em;'
            f'text-transform:uppercase">{meta["icon"]} {meta["name"]}{fast_tag}</span>'
            f'<div style="display:flex;align-items:baseline;gap:8px;flex-wrap:wrap">'
            f'<span style="color:#eef2ff;font-size:1.9rem;font-weight:800;letter-spacing:-0.02em;line-height:1">{price_fmt}</span>'
            f'<span style="color:{clr};font-size:1.4rem;font-weight:800">{arrow} {chg:+.2f}%</span>'
            f'</div></div>'
        )

    assets_html = "".join(_asset_html(s) for s in MARKET_TICKERS)
    st.markdown(
        f'<div style="background:rgba(255,255,255,0.018);border:1px solid #0f1428;'
        f'border-radius:14px;padding:14px 20px;margin-bottom:16px">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'flex-wrap:wrap;gap:16px">'
        f'<div style="display:flex;flex-wrap:wrap;gap:28px">{assets_html}</div>'
        f'<div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;'
        f'padding-left:20px;border-left:1px solid #0f1428">'
        f'<div style="display:flex;align-items:center;gap:10px">'
        f'<span style="font-size:2.6rem;line-height:1">{sem_icon}</span>'
        f'<span style="color:{sem_clr};font-size:2.0rem;font-weight:900;letter-spacing:-0.02em;line-height:1">'
        f'{sentiment}</span></div>'
        f'<span style="color:#374151;font-size:0.85rem;text-align:right;max-width:220px;margin-top:4px">'
        f'{sem_desc}</span>'
        f'<span style="color:#1e2c50;font-size:0.65rem;letter-spacing:.08em;margin-top:2px">SENTIMIENTO DE MERCADO</span>'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# ESTADO DE SESIÓN
# ─────────────────────────────────────────────
if "analysis" not in st.session_state:
    st.session_state.analysis = None


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("🔍 IBEX 35 · Análisis IA")
    st.divider()

    # ── Selector de ticker
    ticker_options = list(IBEX35_NAMES.keys())
    ticker = st.selectbox(
        "Valor a analizar",
        options=ticker_options,
        index=ticker_options.index("IDR.MC"),
        format_func=lambda t: f"{t}  ·  {IBEX35_NAMES[t]}",
        key="ticker_select",
    )
    custom = st.text_input(
        "O introduce un ticker personalizado",
        placeholder="p.ej. AENA.MC",
        key="ticker_custom",
    )
    if custom.strip():
        ticker = custom.strip().upper()
    nombre = IBEX35_NAMES.get(ticker, ticker)

    # Reset análisis al cambiar de ticker
    if "prev_ticker" not in st.session_state:
        st.session_state.prev_ticker = ticker
    if st.session_state.prev_ticker != ticker:
        st.session_state.analysis    = None
        st.session_state.prev_ticker = ticker

    st.caption(f"`{ticker}` · IBEX 35")
    st.divider()

    # ── Precio manual
    manual_price = st.number_input(
        "Precio actual (manual)", min_value=0.0, value=0.0, step=0.01, format="%.3f",
        key="manual_price",
        help="Deja en 0 para usar Yahoo Finance (~15 min retraso). Introduce el precio real si lo tienes.",
    )
    if manual_price > 0:
        st.markdown(
            f'<div style="color:#fbbf24;font-size:0.75rem;margin-top:-8px;margin-bottom:4px">'
            f'✎ Precio manual activo: <strong>{manual_price:.3f}€</strong></div>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.subheader("Mi posición")
    n_ent = st.number_input("Número de entradas", 1, 5, 3, 1)
    # Defaults solo para IDR.MC (posición real del usuario)
    _idr_defaults = [(197.0, 58.30), (187.0, 53.35), (223.18, 46.60)]
    entries = []
    for i in range(int(n_ent)):
        d_sh, d_pr = (_idr_defaults[i] if ticker == "IDR.MC" and i < len(_idr_defaults)
                      else (0.0, 0.0))
        ca, cb = st.columns(2)
        sh = ca.number_input(f"#{i+1} Acc.", 0.0, value=d_sh, step=1.0,  key=f"sh{i}", format="%.2f")
        pr = cb.number_input(f"#{i+1} €",   0.0, value=d_pr, step=0.01, key=f"pr{i}", format="%.2f")
        if sh > 0 and pr > 0:
            entries.append({"shares": sh, "price": pr})

    st.divider()

    # ── Volumen manual
    _prev = st.session_state.get("analysis")
    _nd_intervals = [
        r["interval"] for r in (_prev or {}).get("tf_results", [])
        if r and r["interval"] in ("1h", "15m")
        and r.get("vol_ratio") is None and not r.get("vol_manual")
    ]
    if _nd_intervals:
        st.markdown(
            '<div style="background:rgba(120,53,15,0.3);border:1px solid #92400e;'
            'border-radius:8px;padding:10px 12px;font-size:0.78rem;color:#fcd34d;'
            'line-height:1.5;margin-bottom:8px">'
            '📊 <strong>Volumen N/D.</strong> Introduce los datos de tu plataforma '
            'y pulsa <strong>ANALIZAR</strong> de nuevo.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="color:#4b5563;font-size:0.75rem;font-weight:600;'
            'margin-bottom:4px">📊 Volumen manual</div>',
            unsafe_allow_html=True,
        )

    mv_act = st.number_input("Volumen actual (acciones)", min_value=0.0, value=0.0,
                             step=1000.0, format="%.0f", key="mv_actual",
                             help="Número de acciones negociadas hoy.")
    mv_med = st.number_input("Media vol. (acciones, referencia)", min_value=0.0, value=0.0,
                             step=1000.0, format="%.0f", key="mv_media",
                             help="Media de volumen de referencia.")
    if mv_act > 0 and mv_med > 0:
        _computed_ratio = mv_act / mv_med
        _ratio_clr = "#4ade80" if _computed_ratio >= 1.3 else "#fbbf24" if _computed_ratio >= 0.7 else "#f87171"
        st.markdown(
            f'<div style="background:#0a0c18;border:1px solid #1e2235;border-radius:6px;'
            f'padding:8px 12px;font-size:0.82rem;margin-top:4px">'
            f'Ratio calculado: <strong style="color:{_ratio_clr}">{_computed_ratio:.2f}×</strong>'
            f'<span style="color:#374151;font-size:0.75rem;margin-left:8px">'
            f'({mv_act:,.0f} / {mv_med:,.0f})</span></div>',
            unsafe_allow_html=True,
        )
        manual_vol_1h  = _computed_ratio
        manual_vol_15m = _computed_ratio
    else:
        manual_vol_1h  = 0.0
        manual_vol_15m = 0.0

    st.divider()
    st.subheader("Análisis de captura")
    api_key  = st.text_input(
        "Anthropic API Key", type="password",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        help="Necesaria para analizar capturas con IA",
    )
    uploaded = st.file_uploader(
        "Gráfico de Investing.com",
        type=["png", "jpg", "jpeg"],
        help="Sube la captura y pulsa 'Analizar ahora'",
    )

    st.divider()
    st.markdown(
        '<div style="background:rgba(17,24,39,0.8);border:1px solid #374151;border-radius:8px;'
        'padding:10px 12px;font-size:0.75rem;color:#6b7280;line-height:1.5">'
        '⚠️ <strong style="color:#4b5563">Limitación conocida:</strong> el volumen en 1H y 15min '
        'puede contener artefactos de Yahoo Finance para valores del mercado continuo español. '
        'Se filtra automáticamente si es &lt; 15% de la media 20d.</div>',
        unsafe_allow_html=True,
    )
    st.caption("Datos: Yahoo Finance · IA: Claude Sonnet")


# ─────────────────────────────────────────────
# CABECERA
# ─────────────────────────────────────────────
st.markdown(f"# 🔍 {nombre} &nbsp; `{ticker}`")

_yf_price, prev = get_price(ticker)
price     = manual_price if manual_price > 0 else _yf_price
price_src = "✎ manual" if manual_price > 0 else "Yahoo Finance (~15 min retraso)"
chg       = price - prev
chg_pct   = (chg / prev) * 100

_chg_clr   = "#4ade80" if chg >= 0 else "#f87171"
_chg_bg    = "rgba(20,83,45,0.3)" if chg >= 0 else "rgba(127,29,29,0.3)"
_chg_arrow = "▲" if chg >= 0 else "▼"
_src_txt   = f"✎ manual" if manual_price > 0 else f"Yahoo Finance · {datetime.now().strftime('%H:%M')}"
st.markdown(
    f'<div style="display:flex;align-items:flex-end;gap:32px;flex-wrap:wrap;margin-bottom:4px">'
    f'<div>'
    f'<div style="color:#2d3a5a;font-size:0.6rem;font-weight:900;letter-spacing:.12em;text-transform:uppercase;margin-bottom:4px">PRECIO ACTUAL</div>'
    f'<div style="color:#eef2ff;font-size:2.1rem;font-weight:800;letter-spacing:-0.02em;line-height:1">{price:.3f} €</div>'
    f'<div style="display:inline-block;background:{_chg_bg};border-radius:6px;padding:3px 10px;margin-top:6px">'
    f'<span style="color:{_chg_clr};font-size:0.88rem;font-weight:700">'
    f'{_chg_arrow} {chg:+.3f} € ({chg_pct:+.2f}%)</span></div>'
    f'</div>'
    f'<div style="padding-bottom:4px">'
    f'<div style="color:#2d3a5a;font-size:0.6rem;font-weight:900;letter-spacing:.12em;text-transform:uppercase;margin-bottom:4px">CIERRE ANTERIOR</div>'
    f'<div style="color:#9ca3af;font-size:1.4rem;font-weight:700;line-height:1">{prev:.3f} €</div>'
    f'</div>'
    f'</div>',
    unsafe_allow_html=True,
)

st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PANEL DE MERCADO (siempre visible)
# ─────────────────────────────────────────────
_rc1, _rc2 = st.columns([5, 1])
with _rc2:
    if st.button("🔄 Actualizar", use_container_width=True, help="Refresca precios de mercado"):
        get_market_context.clear()
        st.rerun()
render_market_panel()
st.caption(f"Fuente precio: {price_src}  ·  Cargado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# ─────────────────────────────────────────────
# POSICIÓN — cálculo previo (sin renderizar)
# ─────────────────────────────────────────────
if entries:
    _ts = sum(e["shares"] for e in entries)
    _tc = sum(e["shares"] * e["price"] for e in entries)
    _ap = _tc / _ts
    _cv = _ts * price
    position = {"shares": _ts, "avg_price": _ap, "total_cost": _tc,
                "pnl_eur": _cv - _tc, "pnl_pct": (_cv / _tc - 1) * 100}
else:
    position = {"shares": 0, "avg_price": 0, "total_cost": 0, "pnl_eur": 0, "pnl_pct": 0}

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab_analysis, tab_position, tab_backtest = st.tabs(["📊 Análisis", "💼 Mi Posición", "📈 Backtesting"])


# ═══════════════════════════════════════════════
# TAB 1 — ANÁLISIS
# ═══════════════════════════════════════════════
with tab_analysis:

    bc1, bc2 = st.columns([1, 3])
    with bc1:
        run = st.button("🔍  ANALIZAR AHORA", type="primary", use_container_width=True)
    with bc2:
        st.caption(
            "Lanza análisis técnico multi-timeframe (Diario · 1H · 15min) + noticias."
            + ("  |  📎 Captura cargada — se analizará también." if uploaded else "")
        )

    # ── Ejecutar análisis
    if run:
        tf_results     = []
        chart_analysis = None
        img_bytes_save = uploaded.getvalue() if uploaded else None

        with st.status(f"🔍 Analizando {nombre}...", expanded=True) as status:
            _manual_vols = {"1h": manual_vol_1h or None, "15m": manual_vol_15m or None}
            for tf in TIMEFRAMES:
                st.write(f"📊 Descargando datos {tf['label']}...")
                r = analyze_tf(ticker, tf["label"], tf["period"], tf["interval"],
                               manual_vol_ratio=_manual_vols.get(tf["interval"]))
                tf_results.append(r)
                v    = r["verdict"] if r else "Sin datos"
                icon = {"COMPRAR": "🟢", "VENDER": "🔴", "ESPERAR": "🟡"}.get(v, "⚪")
                st.write(f"   {icon} {tf['label']} → **{v}**"
                         + (f"  ·  RSI {r['rsi']:.0f}  ·  Score {r['score']:+.1f}" if r else ""))

            st.write("⚖️ Calculando veredicto combinado...")
            verdict, score, context, meta = combined_verdict(tf_results, position)
            icon_v = {"COMPRAR": "🟢", "VENDER": "🔴", "MANTENER": "🟡"}.get(verdict, "🟡")
            st.write(f"   {icon_v} Veredicto: **{verdict}**  ·  Score ponderado: **{score:+.2f}**"
                     + (f"  ·  {meta['vol_valid_count']}/{meta['n_tf']} TF con volumen válido" if meta else ""))

            st.write("📰 Cargando noticias...")
            news, news_src = get_news(ticker, force_refresh=True)
            st.write(f"   ✅ {len(news)} noticias · {news_src}")

            if uploaded:
                st.write("🖼️ Claude analizando el gráfico subido...")
                mime = "image/jpeg" if uploaded.name.lower().endswith((".jpg", ".jpeg")) else "image/png"
                pos_ctx = (
                    "\n".join(f"  · Entrada #{i+1}: {e['shares']:.2f} acc @ {e['price']:.2f}€"
                              for i, e in enumerate(entries))
                    + f"\n  · Precio medio: {position['avg_price']:.2f}€"
                    + f"\n  · P&L actual: {position['pnl_eur']:+,.2f}€ ({position['pnl_pct']:+.1f}%)"
                    + f"\n  · Precio ahora: {price:.3f}€"
                )
                chart_analysis = analyze_screenshot(img_bytes_save, mime, api_key, pos_ctx,
                                                    nombre, ticker)
                st.write("   ✅ Análisis de captura completado")

            status.update(label="✅ Análisis completado", state="complete", expanded=False)

        st.session_state.analysis = {
            "tf_results": tf_results,
            "verdict":    verdict,
            "score":      score,
            "context":    context,
            "meta":       meta,
            "news":       news,
            "news_src":   news_src,
            "chart":      chart_analysis,
            "ts":         datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "img_bytes":  img_bytes_save,
        }

    # ── Mostrar resultados
    a = st.session_state.analysis

    if a is None:
        st.markdown(
            '<div style="background:rgba(255,255,255,0.015);border:1px dashed #0f1a36;border-radius:20px;'
            'padding:56px 40px;text-align:center;margin-top:28px">'
            '<div style="color:#0f1a36;font-size:3rem;margin-bottom:16px">◈</div>'
            '<div style="color:#1e2c50;font-size:0.65rem;font-weight:900;letter-spacing:.2em;'
            'text-transform:uppercase;margin-bottom:10px">Sin análisis</div>'
            '<div style="color:#374151;font-size:0.95rem;line-height:1.6">'
            'Pulsa <strong style="color:#dde5ff">ANALIZAR AHORA</strong> para obtener el análisis '
            'técnico multi-timeframe y la recomendación de swing trading.'
            '</div></div>',
            unsafe_allow_html=True,
        )
    else:
        verdict = a["verdict"]
        meta    = a.get("meta", {})

        if verdict == "COMPRAR":
            st.toast(f"Señal de COMPRA detectada en {nombre}", icon="🟢")
        elif verdict == "VENDER":
            st.toast(f"Señal de VENTA detectada en {nombre}", icon="🔴")
        elif verdict == "MANTENER CON ALERTA":
            st.toast("Divergencia bajista cerca de resistencia — señal degradada", icon="⚠️")

        _nd_now = [
            r["label"] for r in a.get("tf_results", [])
            if r and r["interval"] in ("1h", "15m") and r.get("vol_ratio") is None and not r.get("vol_manual")
        ]
        if _nd_now:
            st.info(
                f"📊 **Volumen N/D** en: {', '.join(_nd_now)}. "
                "Busca el ratio Vol/Media20d en tu plataforma, introdúcelo en la barra lateral "
                "(**Volumen manual**) y pulsa **ANALIZAR** de nuevo.",
                icon="📊",
            )

        day_r     = a["tf_results"][0]
        intra_tfs = [r for r in a["tf_results"][1:] if r]
        cur_price = day_r["price"] if day_r else price
        op_sups   = [r["support"]    for r in intra_tfs if r.get("support")    and r["support"]    < cur_price]
        op_ress   = [r["resistance"] for r in intra_tfs if r.get("resistance") and r["resistance"] > cur_price]
        op_sup_v  = max(op_sups) if op_sups else (day_r["support"]    if day_r else None)
        op_res_v  = min(op_ress) if op_ress else (day_r["resistance"] if day_r else None)
        _s = f"{op_sup_v:.2f}€" if op_sup_v else "soporte op."
        _r = f"{op_res_v:.2f}€" if op_res_v else "resistencia"

        if verdict == "COMPRAR":
            exec_line = f"Mantener posición. Escenario bajista si cierra bajo {_s} con Vol ≥ 0.7×."
        elif verdict == "VENDER":
            exec_line = f"Reducir exposición. Stop operativo en {_s} — no esperar rebote sin volumen."
        elif verdict == "MANTENER CON ALERTA":
            exec_line = f"No añadir posición. Esperar cierre sobre {_r} con volumen o vigilar {_s} como stop."
        elif meta.get("inactive"):
            exec_line = f"No operar. Mercado inactivo. Vigilar cierre sobre {_r} o bajo {_s}."
        else:
            exec_line = f"No tocar la posición hasta cierre sobre {_r} con volumen o pérdida de {_s}."

        # ═══ RESUMEN RÁPIDO (siempre visible) ═══
        atr_day = day_r.get("atr") if day_r else None
        day_rsi = day_r.get("rsi") if day_r else None
        _trend  = "alcista" if (day_r and day_r.get("sma20") and cur_price > day_r["sma20"]) else "bajista"

        _buy  = op_sup_v
        _tgt  = op_res_v
        _stop = (op_sup_v - atr_day) if (op_sup_v and atr_day) else (cur_price - 2 * atr_day if atr_day else None)

        def _eur(v):
            return f"{v:.2f}€" if v else "—"

        _amap = {
            "COMPRAR":             ("COMPRAR",  "🟢", "#4ade80", "rgba(74,222,128,0.08)"),
            "VENDER":              ("VENDER",   "🔴", "#f87171", "rgba(248,113,113,0.08)"),
            "MANTENER":            ("MANTENER", "🟡", "#fbbf24", "rgba(245,158,11,0.07)"),
            "MANTENER CON ALERTA": ("MANTENER", "⚠️", "#fbbf24", "rgba(245,158,11,0.07)"),
        }
        _aw, _ai, _aclr, _adim = _amap.get(verdict, ("ESPERAR", "🟡", "#fbbf24", "rgba(245,158,11,0.07)"))
        if verdict == "MANTENER" and position["shares"] == 0:
            _aw, _ai = "ESPERAR", "⏳"

        _rsi_txt = f"RSI {day_rsi:.0f}" if day_rsi else "RSI n/d"
        _pnl_txt = f" Llevas {position['pnl_pct']:+.1f}% en esta posición." if position["shares"] > 0 else ""
        if meta.get("inactive"):
            _why = ("El mercado está sin volumen ahora mismo, así que las señales no son fiables. "
                    "Mejor esperar a que haya movimiento real antes de tocar nada." + _pnl_txt)
        elif verdict == "COMPRAR":
            _why = (f"Los indicadores apuntan al alza (tendencia {_trend}, {_rsi_txt}). "
                    f"Buen momento para comprar o ampliar." + _pnl_txt)
        elif verdict == "VENDER":
            _why = (f"Señales de debilidad (tendencia {_trend}, {_rsi_txt}). Mejor reducir o salir." + _pnl_txt)
        elif verdict == "MANTENER CON ALERTA":
            _why = ("Hay señal de agotamiento cerca de resistencia. Mantén lo que tienes "
                    "pero NO compres más hasta que confirme." + _pnl_txt)
        elif position["shares"] == 0:
            _why = (f"Todavía no hay señal clara para entrar (tendencia {_trend}, {_rsi_txt}). "
                    f"Espera a que baje a la zona de compra o a que rompa la resistencia con fuerza.")
        else:
            _why = (f"Sin señal clara de cambio (tendencia {_trend}, {_rsi_txt}). "
                    f"Mantén la posición y espera confirmación." + _pnl_txt)

        if verdict == "VENDER":
            _chips = [
                ("🔴", "Vender cerca de",  _eur(cur_price), "#f87171"),
                ("🛑", "Stop si aguantas", _eur(_stop),     "#fca5a5"),
                ("👁", "Soporte clave",    _eur(_buy),      "#7dd3fc"),
            ]
        elif verdict in ("MANTENER", "MANTENER CON ALERTA") and position["shares"] > 0:
            _chips = [
                ("🚪", "No añadir hasta", _eur(_tgt),  "#fda4af"),
                ("👁", "Aviso, vigilar",  _eur(_buy),  "#fcd34d"),
                ("🛑", "Stop proteger",   _eur(_stop), "#fca5a5"),
            ]
        else:
            _chips = [
                ("🟢", "Comprar cerca de",  _eur(_buy),  "#4ade80"),
                ("🎯", "Objetivo (vender)", _eur(_tgt),  "#86efac"),
                ("🛑", "Stop (proteger)",   _eur(_stop), "#fca5a5"),
            ]

        _sent_lbl, _, _, _ = _market_sentiment(get_market_context())
        if _sent_lbl in ("TEMEROSO", "PÁNICO", "NEGATIVO"):
            _risk = f"⚠️ Cuidado: el mercado global está nervioso hoy ({_sent_lbl}). Hay más riesgo de lo normal al operar."
        elif _sent_lbl in ("POSITIVO", "MOD. POSITIVO"):
            _risk = f"✅ El mercado global acompaña hoy ({_sent_lbl}), buen viento de cola."
        else:
            _risk = None

        render_quick_summary(_aw, _ai, _aclr, _adim, _why, _chips, _risk)

        if entries and atr_day:
            render_target_alert(position, cur_price, atr_day)

        # ═══ DETALLE PLEGABLE ═══
        with st.expander("📊 Ver análisis técnico detallado"):
            render_verdict(verdict, a["score"], a["context"], exec_line)
            render_scenarios(day_r, intra_tfs, cur_price)
            render_signal_table(a["tf_results"], meta)
            st.markdown('<div class="sec-header">DETALLE POR TEMPORALIDAD</div>', unsafe_allow_html=True)
            tc1, tc2, tc3 = st.columns(3)
            for col, r in zip([tc1, tc2, tc3], a["tf_results"]):
                with col:
                    render_tf_block(r)

            if day_r:
                st.markdown('<div class="sec-header">NIVELES CLAVE · SOPORTE OPERATIVO Y ESTRUCTURAL</div>', unsafe_allow_html=True)
                cur_price2    = day_r["price"]
                intraday_sups = [r["support"] for r in a["tf_results"][1:]
                                 if r and r.get("support") and r["support"] < cur_price2]
                op_sup   = max(intraday_sups) if intraday_sups else None
                str_sup  = day_r["support"]
                dist_op  = (cur_price2 - op_sup)  / cur_price2 * 100 if op_sup else None
                dist_str = (cur_price2 - str_sup) / cur_price2 * 100
                dist_res = (day_r["resistance"] - cur_price2) / cur_price2 * 100

                nl1, nl2, nl3 = st.columns(3)
                if op_sup:
                    nl1.markdown(
                        f'<div class="level-op">'
                        f'<div style="color:#92400e;font-size:0.7rem;font-weight:700;text-transform:uppercase;margin-bottom:4px">Soporte operativo (intraday)</div>'
                        f'<div style="color:#fcd34d;font-size:1.4rem;font-weight:700">{op_sup:.3f} €</div>'
                        f'<div style="color:#78350f;font-size:0.8rem;margin-top:4px">−{dist_op:.1f}% desde precio actual</div>'
                        f'<div style="color:#92400e;font-size:0.78rem;margin-top:6px">⚠️ Pérdida activa escenario bajista</div>'
                        f'</div>', unsafe_allow_html=True,
                    )
                else:
                    nl1.markdown(
                        '<div class="level-str"><div style="color:#4b5563;font-size:0.7rem;font-weight:700;text-transform:uppercase;margin-bottom:4px">Soporte operativo</div>'
                        '<div style="color:#6b7280;font-size:0.9rem">Sin datos intraday</div></div>',
                        unsafe_allow_html=True,
                    )
                nl2.markdown(
                    f'<div class="level-str">'
                    f'<div style="color:#374151;font-size:0.7rem;font-weight:700;text-transform:uppercase;margin-bottom:4px">Soporte estructural (diario)</div>'
                    f'<div style="color:#7dd3fc;font-size:1.4rem;font-weight:700">{str_sup:.3f} €</div>'
                    f'<div style="color:#374151;font-size:0.8rem;margin-top:4px">−{dist_str:.1f}% desde precio actual</div>'
                    f'<div style="color:#1e3a5f;font-size:0.78rem;margin-top:6px">Invalidaría tesis a medio plazo</div>'
                    f'</div>', unsafe_allow_html=True,
                )
                nl3.markdown(
                    f'<div class="level-str">'
                    f'<div style="color:#374151;font-size:0.7rem;font-weight:700;text-transform:uppercase;margin-bottom:4px">Resistencia (diario)</div>'
                    f'<div style="color:#fda4af;font-size:1.4rem;font-weight:700">{day_r["resistance"]:.3f} €</div>'
                    f'<div style="color:#374151;font-size:0.8rem;margin-top:4px">+{dist_res:.1f}% hasta nivel</div>'
                    f'<div style="color:#1e3a5f;font-size:0.78rem;margin-top:6px">Ruptura confirma escenario alcista</div>'
                    f'</div>', unsafe_allow_html=True,
                )

                st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
                mc1, mc2, mc3, mc4, mc5, mc6 = st.columns(6)
                if day_r.get("sma20"): mc1.metric("SMA 20",      f"{day_r['sma20']:.3f} €")
                if day_r.get("sma50"): mc2.metric("SMA 50",      f"{day_r['sma50']:.3f} €")
                if day_r.get("bb_lo"): mc3.metric("BB Inferior", f"{day_r['bb_lo']:.3f} €")
                if day_r.get("atr"):   mc4.metric("ATR (14d)",   f"{day_r['atr']:.3f} €")
                if day_r.get("atr") and day_r["atr"] > 0:
                    atr       = day_r["atr"]
                    stop_px   = cur_price2 - 1.0 * atr
                    target_px = cur_price2 + 2.0 * atr
                    rr        = (target_px - cur_price2) / (cur_price2 - stop_px) if cur_price2 > stop_px else 0
                    rr_str    = f"{rr:.1f}:1" + ("" if rr >= 1.5 else " ⚠️")
                    mc5.metric("Stop (1×ATR)",     f"{stop_px:.3f} €")
                    mc6.metric("Objetivo (2×ATR)", f"{target_px:.3f} €", rr_str,
                               delta_color="normal" if rr >= 1.5 else "inverse")

        # Rendimiento relativo vs IBEX 35
        idr_ret, ibex_ret = get_ibex_relative(ticker)
        if idr_ret is not None:
            diff = idr_ret - ibex_ret
            with st.expander(f"📈 Fuerza vs IBEX 35  ·  {'🟢 más fuerte' if diff >= 0 else '🔴 más débil'} ({diff:+.1f}%)"):
                rc1, rc2, rc3 = st.columns(3)
                rc1.metric(f"{ticker} (20d)", f"{idr_ret:+.2f}%", delta_color="normal" if idr_ret >= 0 else "inverse")
                rc2.metric("IBEX 35 (20d)",   f"{ibex_ret:+.2f}%", delta_color="normal" if ibex_ret >= 0 else "inverse")
                rc3.metric("Diferencia",      f"{diff:+.2f}%",
                           "🟢 Fortaleza" if diff >= 0 else "🔴 Debilidad",
                           delta_color="normal" if diff >= 0 else "inverse")

        # Catalizador + noticias
        with st.expander(f"📅 Catalizador y noticias  ·  {len(a.get('news', []))} titulares"):
            st.markdown('<div class="sec-header">CATALIZADOR RECIENTE · ÚLTIMOS 45 DÍAS</div>', unsafe_allow_html=True)
            earnings_json = json.dumps(EARNINGS_DATES.get(ticker, []))
            render_catalyst(get_catalyst_data(ticker, earnings_json))
            st.markdown(
                f'<div class="sec-header">NOTICIAS RECIENTES · {nombre.upper()}'
                f'<span style="font-weight:400;color:#374151;margin-left:12px">'
                f'📡 {a.get("news_src","")}</span></div>',
                unsafe_allow_html=True,
            )
            render_news(a["news"])

        # Análisis de captura (IA)
        if a.get("chart"):
            with st.expander("🖼️ Análisis del gráfico por IA"):
                if a.get("img_bytes"):
                    st.image(a["img_bytes"], caption="Gráfico analizado", use_container_width=True)
                st.markdown(
                    f'<div style="background:rgba(255,255,255,0.02);border:1px solid #0f1428;'
                    f'border-radius:16px;padding:22px 24px;font-size:0.92rem;color:#9ca3af;'
                    f'line-height:1.75">{a["chart"]}</div>',
                    unsafe_allow_html=True,
                )

        st.markdown(
            f'<div style="color:#0f1428;font-size:0.7rem;text-align:right;margin-top:24px;letter-spacing:.04em">'
            f'⚠️ Análisis orientativo · No es asesoramiento financiero · {a["ts"]}</div>',
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════
# TAB 2 — MI POSICIÓN
# ═══════════════════════════════════════════════
with tab_position:
    st.subheader(f"💼 Mi posición en {nombre}")
    render_position(entries, price)

    # Alerta stop/objetivo si hay análisis previo con ATR
    a_pos = st.session_state.analysis
    if a_pos and entries:
        day_r_pos = a_pos["tf_results"][0] if a_pos.get("tf_results") else None
        atr_pos   = day_r_pos.get("atr") if day_r_pos else None
        cur_p_pos = day_r_pos["price"] if day_r_pos else price
        if atr_pos:
            st.divider()
            render_target_alert(position, cur_p_pos, atr_pos)
    elif entries and not a_pos:
        st.info(
            "Pulsa **ANALIZAR AHORA** en la pestaña 📊 Análisis para calcular "
            "el stop y el objetivo basados en el ATR.",
            icon="ℹ️",
        )


# ═══════════════════════════════════════════════
# TAB 3 — BACKTESTING
# ═══════════════════════════════════════════════
with tab_backtest:
    st.markdown(
        f'<div style="color:#374151;font-size:0.92rem;line-height:1.7;margin-bottom:20px">'
        f'Valida si las señales del sistema han tenido edge histórico en <strong style="color:#dde5ff">{nombre}</strong>. '
        f'Corre el scoring diario sobre cada sesión del histórico y comprueba qué hizo el precio '
        f'en los días siguientes. Solo usa el timeframe diario (1D).</div>',
        unsafe_allow_html=True,
    )

    bc1, bc2, bc3, bc4 = st.columns(4)
    with bc1:
        bt_period = st.selectbox("Período histórico", ["1y", "2y", "3y", "5y"], index=1)
    with bc2:
        bt_fwd = st.slider("Días de retorno", min_value=3, max_value=15, value=5, step=1)
    with bc3:
        bt_buy_t = st.slider(
            "Umbral COMPRAR (score ≥)",
            min_value=1.0, max_value=4.0, value=2.2, step=0.1,
            help="Score mínimo para emitir señal de compra. Sube para señales más selectivas.",
        )
    with bc4:
        bt_sell_t = st.slider(
            "Umbral VENDER (score ≤)",
            min_value=-4.0, max_value=-1.0, value=-2.5, step=0.1,
            help="Score máximo para emitir señal de venta. Bájalo (más negativo) para señales más selectivas.",
        )

    run_bt = st.button("▶  EJECUTAR BACKTEST", type="primary", use_container_width=True)

    if run_bt:
        with st.spinner(f"Descargando {bt_period} de histórico para {ticker} y calculando señales..."):
            bt_result = run_backtest(ticker, period=bt_period, forward_days=bt_fwd,
                                     buy_threshold=bt_buy_t, sell_threshold=bt_sell_t)
        render_backtest_results(bt_result)
    else:
        st.markdown(
            '<div style="background:rgba(255,255,255,0.015);border:1px dashed #0f1a36;'
            'border-radius:16px;padding:40px;text-align:center;margin-top:20px">'
            '<div style="color:#1e2c50;font-size:0.65rem;font-weight:900;letter-spacing:.2em;'
            'text-transform:uppercase;margin-bottom:10px">Configura y lanza el backtest</div>'
            '<div style="color:#374151;font-size:0.9rem">Elige el período y los días de retorno, '
            'luego pulsa <strong style="color:#dde5ff">EJECUTAR BACKTEST</strong>.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
