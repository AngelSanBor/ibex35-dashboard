import streamlit as st
import pandas as pd
import requests
import io
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator
from datetime import datetime, timedelta

st.set_page_config(page_title="IBEX 35 · Trading Desk", page_icon="📈", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
.block-container { padding: 1.5rem 2rem; }
.dash-header { display: flex; align-items: baseline; gap: 16px; margin-bottom: 2rem; }
.dash-title { font-family: 'Syne', sans-serif; font-size: 2rem; font-weight: 800; color: #f0f0f0; letter-spacing: -1px; margin: 0; }
.dash-sub { font-family: 'DM Mono', monospace; font-size: 0.75rem; color: #555; letter-spacing: 2px; text-transform: uppercase; }
.metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1px; background: #1a1a24; border: 1px solid #1a1a24; border-radius: 12px; overflow: hidden; margin-bottom: 1.5rem; }
.metric-card { background: #0f0f18; padding: 1.2rem 1.4rem; }
.metric-label { font-family: 'DM Mono', monospace; font-size: 0.65rem; color: #444; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 6px; }
.metric-value { font-family: 'DM Mono', monospace; font-size: 1.5rem; font-weight: 500; color: #e8e8e8; }
.metric-value.positive { color: #00e5a0; }
.metric-value.negative { color: #ff4d6d; }
.pos-banner { background: linear-gradient(135deg, #0f1f17 0%, #0a0f1a 100%); border: 1px solid #1a3a28; border-left: 3px solid #00e5a0; border-radius: 8px; padding: 1rem 1.4rem; margin-bottom: 1.5rem; display: flex; gap: 2rem; align-items: center; flex-wrap: wrap; }
.pos-banner.neg { border-left-color: #ff4d6d; background: linear-gradient(135deg, #1f0f0f 0%, #0a0a1a 100%); border-color: #3a1a1a; }
.pos-label { font-family: 'DM Mono', monospace; font-size: 0.65rem; color: #3a7a5a; text-transform: uppercase; letter-spacing: 2px; }
.pos-value { font-family: 'DM Mono', monospace; font-size: 1rem; color: #00e5a0; font-weight: 500; }
.pos-value.neg { color: #ff4d6d; }
.monitor-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 1px; background: #1a1a24; border: 1px solid #1a1a24; border-radius: 12px; overflow: hidden; margin-top: 1rem; }
.monitor-cell { background: #0f0f18; padding: 1rem; }
.monitor-ticker { font-family: 'DM Mono', monospace; font-size: 0.65rem; color: #444; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 4px; }
.monitor-price { font-family: 'DM Mono', monospace; font-size: 1.1rem; color: #e8e8e8; font-weight: 500; }
.monitor-chg.up { color: #00e5a0; font-size: 0.8rem; }
.monitor-chg.dn { color: #ff4d6d; font-size: 0.8rem; }
section[data-testid="stSidebar"] { background: #0f0f18 !important; border-right: 1px solid #1a1a24; }
section[data-testid="stSidebar"] * { color: #aaa !important; }
.stNumberInput input { background: #1a1a24 !important; border: 1px solid #2a2a38 !important; color: #e8e8e8 !important; border-radius: 6px !important; font-family: 'DM Mono', monospace !important; }
.stButton button { background: #00e5a0 !important; color: #0a0a0f !important; font-family: 'Syne', sans-serif !important; font-weight: 700 !important; border: none !important; border-radius: 6px !important; }
hr { border-color: #1a1a24 !important; }
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

IBEX_TICKERS = {
    "Indra":      "IDR.MC", "Santander": "SAN.MC", "BBVA":       "BBVA.MC",
    "Inditex":    "ITX.MC", "Iberdrola": "IBE.MC", "Repsol":     "REP.MC",
    "Telefónica": "TEF.MC", "CaixaBank": "CABK.MC","Amadeus":    "AMS.MC",
    "ACS":        "ACS.MC", "Acciona":   "ANA.MC", "Naturgy":    "NTGY.MC",
    "Endesa":     "ELE.MC", "Mapfre":    "MAP.MC", "Sabadell":   "SAB.MC",
}

NIVELES = {
    "IDR.MC": {"soportes": [47.00, 47.28], "resistencias": [52.64, 53.00, 54.32], "ma200": 54.82},
}

PERIODO_DIAS = {
    "1sem": 7, "1mes": 32, "3mes": 95, "6mes": 185, "1año": 366, "2años": 730
}

@st.cache_data(ttl=300)
def cargar_stooq(ticker, dias):
    end = datetime.today()
    start = end - timedelta(days=dias)
    s = start.strftime("%Y%m%d")
    e = end.strftime("%Y%m%d")
    t = ticker.lower().replace(".mc", ".mc")
    url = f"https://stooq.com/q/d/l/?s={t}&d1={s}&d2={e}&i=d"
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        df = pd.read_csv(io.StringIO(r.text), parse_dates=["Date"], index_col="Date")
        df = df.sort_index()
        df.dropna(inplace=True)
        if df.empty or len(df) < 2:
            return None
        return df
    except Exception:
        return None

with st.sidebar:
    st.markdown("### 📊 CONFIGURACIÓN")
    ticker_nombre = st.selectbox("Acción", list(IBEX_TICKERS.keys()))
    ticker = IBEX_TICKERS[ticker_nombre]
    periodo = st.selectbox("Periodo", list(PERIODO_DIAS.keys()), index=2)
    tipo_grafico = st.radio("Gráfico", ["Velas", "Línea"])
    st.markdown("---")
    st.markdown("### 📐 INDICADORES")
    mostrar_sma20   = st.checkbox("SMA 20",           value=True)
    mostrar_ema20   = st.checkbox("EMA 20",           value=True)
    mostrar_rsi     = st.checkbox("RSI 14",           value=True)
    mostrar_macd    = st.checkbox("MACD",             value=False)
    mostrar_niveles = st.checkbox("Niveles técnicos", value=True)
    st.markdown("---")
    if st.button("🔄 Actualizar"):
        st.cache_data.clear()

st.markdown("""
<div class="dash-header">
    <h1 class="dash-title">IBEX 35 · TRADING DESK</h1>
    <span class="dash-sub">datos en tiempo real · Stooq</span>
</div>
""", unsafe_allow_html=True)

dias = PERIODO_DIAS[periodo]
df = cargar_stooq(ticker, dias)

if df is None or df.empty:
    st.error(f"No se pudieron cargar datos para {ticker_nombre}. Prueba otro periodo.")
    st.stop()

precio_actual  = float(df["Close"].iloc[-1])
precio_inicial = float(df["Close"].iloc[0])
cambio_pct     = ((precio_actual - precio_inicial) / precio_inicial) * 100
maximo         = float(df["High"].max())
minimo         = float(df["Low"].min())
volumen_medio  = int(df["Volume"].mean()) if "Volume" in df.columns else 0

chg_class = "positive" if cambio_pct >= 0 else "negative"
chg_sign  = "▲" if cambio_pct >= 0 else "▼"

st.markdown(f"""
<div class="metric-grid">
    <div class="metric-card"><div class="metric-label">Acción</div><div class="metric-value">{ticker_nombre}</div></div>
    <div class="metric-card"><div class="metric-label">Precio actual</div><div class="metric-value">{precio_actual:.2f} €</div></div>
    <div class="metric-card"><div class="metric-label">Variación ({periodo})</div><div class="metric-value {chg_class}">{chg_sign} {abs(cambio_pct):.2f}%</div></div>
    <div class="metric-card"><div class="metric-label">Máximo</div><div class="metric-value">{maximo:.2f} €</div></div>
    <div class="metric-card"><div class="metric-label">Mínimo</div><div class="metric-value">{minimo:.2f} €</div></div>
    <div class="metric-card"><div class="metric-label">Vol. medio</div><div class="metric-value">{volumen_medio:,}</div></div>
</div>
""", unsafe_allow_html=True)

st.markdown("#### 💼 Mi posición en esta acción")
col_a, col_b, _ = st.columns([1, 1, 2])
with col_a:
    acciones_input = st.number_input("Nº de acciones", min_value=0, value=0, step=1)
with col_b:
    entrada_input  = st.number_input("Precio de entrada (€)", min_value=0.0, value=0.0, step=0.01, format="%.2f")

if acciones_input > 0 and entrada_input > 0:
    pl_eur       = (precio_actual - entrada_input) * acciones_input
    pl_pct       = ((precio_actual - entrada_input) / entrada_input) * 100
    inversion    = entrada_input * acciones_input
    valor_actual = precio_actual * acciones_input
    pos_class    = "pos-value" if pl_eur >= 0 else "pos-value neg"
    ban_class    = "pos-banner" if pl_eur >= 0 else "pos-banner neg"
    signo        = "▲" if pl_eur >= 0 else "▼"
    st.markdown(f"""
    <div class="{ban_class}">
        <div><div class="pos-label">Inversión</div><div class="pos-value">{inversion:,.0f} €</div></div>
        <div><div class="pos-label">Valor actual</div><div class="pos-value">{valor_actual:,.0f} €</div></div>
        <div><div class="pos-label">P&L €</div><div class="{pos_class}">{signo} {abs(pl_eur):,.0f} €</div></div>
        <div><div class="pos-label">P&L %</div><div class="{pos_class}">{signo} {abs(pl_pct):.2f}%</div></div>
        <div><div class="pos-label">Acciones</div><div class="pos-value">{acciones_input:,}</div></div>
        <div><div class="pos-label">Entrada</div><div class="pos-value">{entrada_input:.2f} €</div></div>
    </div>
    """, unsafe_allow_html=True)

close = df["Close"]
if len(close) >= 20:
    df["SMA20"] = SMAIndicator(close, window=20).sma_indicator()
    df["EMA20"] = EMAIndicator(close, window=20).ema_indicator()
if len(close) >= 14:
    df["RSI14"] = RSIIndicator(close, window=14).rsi()
if len(close) >= 26:
    macd_obj     = MACD(close)
    df["MACD"]   = macd_obj.macd()
    df["Signal"] = macd_obj.macd_signal()
    df["Hist"]   = macd_obj.macd_diff()

n_filas = 1
row_heights = [0.65]
if mostrar_rsi:  n_filas += 1; row_heights.append(0.2)
if mostrar_macd: n_filas += 1; row_heights.append(0.15)

fig = make_subplots(rows=n_filas, cols=1, shared_xaxes=True,
                    vertical_spacing=0.03, row_heights=row_heights)

if tipo_grafico == "Velas":
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name=ticker_nombre,
        increasing_line_color="#00e5a0", increasing_fillcolor="#00e5a0",
        decreasing_line_color="#ff4d6d", decreasing_fillcolor="#ff4d6d"
    ), row=1, col=1)
else:
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name=ticker_nombre,
        line=dict(color="#00e5a0", width=2), fill="tozeroy", fillcolor="rgba(0,229,160,0.05)"
    ), row=1, col=1)

if mostrar_sma20 and "SMA20" in df.columns:
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA20"], mode="lines",
        name="SMA 20", line=dict(color="#f59e0b", width=1.5, dash="dot")), row=1, col=1)
if mostrar_ema20 and "EMA20" in df.columns:
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA20"], mode="lines",
        name="EMA 20", line=dict(color="#a78bfa", width=1.5, dash="dash")), row=1, col=1)

if acciones_input > 0 and entrada_input > 0:
    fig.add_hline(y=entrada_input, line_color="#00e5a0", line_width=1.5,
        annotation_text=f"Mi entrada {entrada_input:.2f}€",
        annotation_font_color="#00e5a0", annotation_position="right", row=1, col=1)

if mostrar_niveles and ticker in NIVELES:
    niv = NIVELES[ticker]
    for s in niv["soportes"]:
        fig.add_hline(y=s, line_color="#00e5a0", line_dash="dot", line_width=1,
            annotation_text=f"Soporte {s:.2f}€", annotation_font_color="#00e5a0",
            annotation_position="right", row=1, col=1)
    for r in niv["resistencias"]:
        fig.add_hline(y=r, line_color="#ff4d6d", line_dash="dot", line_width=1,
            annotation_text=f"Resistencia {r:.2f}€", annotation_font_color="#ff4d6d",
            annotation_position="right", row=1, col=1)
    fig.add_hline(y=niv["ma200"], line_color="#f59e0b", line_dash="longdash", line_width=1.5,
        annotation_text=f"MA200 {niv['ma200']:.2f}€", annotation_font_color="#f59e0b",
        annotation_position="right", row=1, col=1)

fila_actual = 2
if mostrar_rsi and "RSI14" in df.columns:
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI14"], mode="lines",
        name="RSI 14", line=dict(color="#f472b6", width=1.5)), row=fila_actual, col=1)
    fig.add_hline(y=70, line_color="#ff4d6d", line_dash="dot", line_width=1, row=fila_actual, col=1)
    fig.add_hline(y=30, line_color="#00e5a0", line_dash="dot", line_width=1, row=fila_actual, col=1)
    fig.update_yaxes(title_text="RSI", range=[0,100], row=fila_actual, col=1, tickfont_color="#444")
    fila_actual += 1

if mostrar_macd and "MACD" in df.columns:
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], mode="lines",
        name="MACD", line=dict(color="#60a5fa", width=1.5)), row=fila_actual, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["Signal"], mode="lines",
        name="Señal", line=dict(color="#f59e0b", width=1.5)), row=fila_actual, col=1)
    colores = ["#00e5a0" if v >= 0 else "#ff4d6d" for v in df["Hist"].fillna(0)]
    fig.add_trace(go.Bar(x=df.index, y=df["Hist"], name="Histograma",
        marker_color=colores, opacity=0.6), row=fila_actual, col=1)
    fig.update_yaxes(title_text="MACD", row=fila_actual, col=1, tickfont_color="#444")

fig.update_layout(
    height=620, paper_bgcolor="#0a0a0f", plot_bgcolor="#0f0f18",
    font=dict(family="DM Mono", color="#555"),
    xaxis_rangeslider_visible=False,
    legend=dict(orientation="h", y=1.02, x=0, bgcolor="rgba(0,0,0,0)", font=dict(color="#555", size=11)),
    margin=dict(l=10, r=140, t=30, b=10),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#1a1a24", font_color="#e8e8e8", bordercolor="#2a2a38")
)
fig.update_xaxes(showgrid=True, gridcolor="#1a1a24", zeroline=False, tickfont=dict(color="#444"))
fig.update_yaxes(showgrid=True, gridcolor="#1a1a24", zeroline=False, tickfont=dict(color="#444"))
fig.update_yaxes(title_text="Precio (€)", row=1, col=1)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("#### 🌐 Monitor IBEX 35")

@st.cache_data(ttl=300)
def precios_ibex(tickers_dict):
    resultados = {}
    end = datetime.today()
    start = end - timedelta(days=7)
    s = start.strftime("%Y%m%d")
    e = end.strftime("%Y%m%d")
    for nombre, t in tickers_dict.items():
        try:
            url = f"https://stooq.com/q/d/l/?s={t.lower()}&d1={s}&d2={e}&i=d"
            r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
            d = pd.read_csv(io.StringIO(r.text), parse_dates=["Date"], index_col="Date")
            d = d.sort_index().dropna()
            if len(d) >= 2:
                precio   = float(d["Close"].iloc[-1])
                anterior = float(d["Close"].iloc[-2])
                cambio   = ((precio - anterior) / anterior) * 100
                resultados[nombre] = (precio, cambio)
        except Exception:
            pass
    return resultados

with st.spinner(""):
    precios = precios_ibex(IBEX_TICKERS)

if precios:
    cells = ""
    for nombre, (precio, cambio) in precios.items():
        chg_cls = "up" if cambio >= 0 else "dn"
        signo   = "▲" if cambio >= 0 else "▼"
        cells += f"""<div class="monitor-cell">
            <div class="monitor-ticker">{nombre}</div>
            <div class="monitor-price">{precio:.2f}€</div>
            <div class="monitor-chg {chg_cls}">{signo} {abs(cambio):.2f}%</div>
        </div>"""
    st.markdown(f'<div class="monitor-grid">{cells}</div>', unsafe_allow_html=True)

st.markdown("---")
with st.expander("📋 Datos históricos"):
    cols_show = [c for c in ["Open","High","Low","Close"] if c in df.columns]
    df_mostrar = df[cols_show].copy()
    st.dataframe(df_mostrar.round(2).iloc[::-1], use_container_width=True)
