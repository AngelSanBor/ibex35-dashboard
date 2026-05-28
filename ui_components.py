import streamlit as st


# ─────────────────────────────────────────────
# RESUMEN RÁPIDO — "¿Qué hago hoy?"
# ─────────────────────────────────────────────
def render_quick_summary(action_word, action_icon, clr, dim, why_line, chips, risk_line=None):
    """Tarjeta clara y sencilla: qué hacer hoy + a qué precio + por qué en 1 frase.
    chips: lista de tuplas (emoji, etiqueta, valor, color_valor)."""
    chips_html = ""
    for emoji, label, value, cclr in chips:
        chips_html += (
            f'<div style="flex:1 1 28%;min-width:96px;background:rgba(255,255,255,0.03);'
            f'border:1px solid #0f1428;border-radius:12px;padding:12px 14px">'
            f'<div style="color:#2d3a5a;font-size:0.62rem;font-weight:800;letter-spacing:.06em;'
            f'text-transform:uppercase;margin-bottom:6px">{emoji} {label}</div>'
            f'<div style="color:{cclr};font-size:1.3rem;font-weight:800;line-height:1">{value}</div></div>'
        )
    risk_html = ""
    if risk_line:
        risk_html = (
            f'<div style="margin-top:14px;background:rgba(120,53,15,0.16);border:1px solid #5a3a12;'
            f'border-radius:10px;padding:11px 15px;color:#fcd34d;font-size:0.92rem;line-height:1.5">'
            f'{risk_line}</div>'
        )
    st.markdown(
        f'<div style="background:{dim};border:1.5px solid {clr}55;border-radius:22px;'
        f'padding:24px 26px;margin-bottom:10px;box-shadow:0 24px 60px rgba(0,0,0,0.5)">'
        f'<div style="color:#2d3a5a;font-size:0.62rem;font-weight:900;letter-spacing:.2em;'
        f'text-transform:uppercase;margin-bottom:10px">¿Qué hago hoy?</div>'
        f'<div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;flex-wrap:wrap">'
        f'<span style="font-size:2.8rem;line-height:1">{action_icon}</span>'
        f'<span style="color:{clr};font-size:2.8rem;font-weight:900;letter-spacing:-0.03em;'
        f'line-height:1">{action_word}</span></div>'
        f'<div style="color:#c9d4f0;font-size:1.05rem;line-height:1.6;margin-bottom:18px">{why_line}</div>'
        f'<div style="display:flex;gap:10px;flex-wrap:wrap">{chips_html}</div>'
        f'{risk_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# ALERTA DE OBJETIVO / STOP
# ─────────────────────────────────────────────
def render_target_alert(position, price, atr_day):
    """Muestra alertas visuales cuando el precio alcanza el objetivo (2×ATR) o el stop (1×ATR)."""
    avg = position.get("avg_price", 0)
    shares = position.get("shares", 0)
    if not avg or not shares or not atr_day:
        return

    target   = avg + 2.0 * atr_day
    stop     = avg - 1.0 * atr_day
    dist_tgt = (target - price) / price * 100   # % que falta para el objetivo
    dist_stp = (price - stop)  / price * 100    # % de colchón sobre el stop
    pct_range = (price - stop) / (target - stop) * 100 if target > stop else 50
    pct_range = max(0, min(100, pct_range))

    # ── Color de la barra de progreso según posición
    if price >= target:
        bar_clr = "#4ade80"
    elif price <= stop:
        bar_clr = "#f87171"
    elif pct_range > 70:
        bar_clr = "#86efac"
    elif pct_range < 30:
        bar_clr = "#fca5a5"
    else:
        bar_clr = "#fbbf24"

    # ── Alertas destacadas
    if price >= target:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#020d05,#041209);'
            f'border:1px solid #16a34a;border-radius:16px;padding:20px 28px;margin:14px 0;'
            f'box-shadow:0 0 40px rgba(74,222,128,0.15)">'
            f'<div style="color:#4ade80;font-size:0.65rem;font-weight:900;letter-spacing:.2em;'
            f'text-transform:uppercase;margin-bottom:6px">🎯 OBJETIVO ALCANZADO</div>'
            f'<div style="color:#86efac;font-size:1.1rem;font-weight:700;line-height:1.6">'
            f'El precio ({price:.3f}€) ha superado el objetivo de <strong>{target:.3f}€</strong> '
            f'(entrada media {avg:.2f}€ + 2×ATR {atr_day:.3f}€). '
            f'Considera tomar beneficios parciales o totales.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    elif price <= stop:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#0c0202,#130404);'
            f'border:1px solid #dc2626;border-radius:16px;padding:20px 28px;margin:14px 0;'
            f'box-shadow:0 0 40px rgba(248,113,113,0.15)">'
            f'<div style="color:#f87171;font-size:0.65rem;font-weight:900;letter-spacing:.2em;'
            f'text-transform:uppercase;margin-bottom:6px">🛑 STOP LOSS ACTIVADO</div>'
            f'<div style="color:#fca5a5;font-size:1.1rem;font-weight:700;line-height:1.6">'
            f'El precio ({price:.3f}€) ha perforado el stop de <strong>{stop:.3f}€</strong> '
            f'(entrada media {avg:.2f}€ − 1×ATR {atr_day:.3f}€). '
            f'La pérdida supera el rango de ruido normal — evalúa salir.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Barra de progreso stop → objetivo (siempre visible si hay posición)
    tgt_pnl = (target - avg) / avg * 100
    stp_pnl = (stop   - avg) / avg * 100
    st.markdown(
        f'<div style="background:rgba(255,255,255,0.018);border:1px solid #0f1428;'
        f'border-radius:14px;padding:18px 24px;margin:10px 0">'
        f'<div style="color:#1e2c50;font-size:0.6rem;font-weight:900;letter-spacing:.18em;'
        f'text-transform:uppercase;margin-bottom:14px">POSICIÓN EN RANGO · Stop → Objetivo</div>'
        f'<div style="display:flex;justify-content:space-between;margin-bottom:8px">'
        f'<span style="color:#f87171;font-size:0.82rem;font-weight:700">'
        f'🛑 Stop &nbsp;<strong>{stop:.3f}€</strong>'
        f'<span style="color:#7f1d1d;font-size:0.75rem;margin-left:6px">({stp_pnl:+.1f}%)</span></span>'
        f'<span style="color:#9ca3af;font-size:0.82rem">Entrada media &nbsp;<strong style="color:#dde5ff">{avg:.2f}€</strong></span>'
        f'<span style="color:#4ade80;font-size:0.82rem;font-weight:700">'
        f'<strong>{target:.3f}€</strong> &nbsp;🎯 Objetivo'
        f'<span style="color:#14532d;font-size:0.75rem;margin-left:6px">({tgt_pnl:+.1f}%)</span></span>'
        f'</div>'
        f'<div style="position:relative;height:10px;background:#0a0f1e;border-radius:5px;overflow:visible">'
        f'<div style="width:{pct_range:.1f}%;height:100%;background:{bar_clr};border-radius:5px;'
        f'box-shadow:0 0 8px {bar_clr}88;transition:width 0.4s ease"></div>'
        f'<div style="position:absolute;top:-4px;left:calc({pct_range:.1f}% - 6px);'
        f'width:12px;height:18px;background:{bar_clr};border-radius:3px;'
        f'box-shadow:0 0 10px {bar_clr}">'
        f'</div></div>'
        f'<div style="text-align:center;margin-top:10px">'
        f'<span style="color:{bar_clr};font-size:0.85rem;font-weight:700">'
        f'Precio actual {price:.3f}€ &nbsp;·&nbsp; '
        + (f'Faltan <strong>{dist_tgt:.1f}%</strong> para objetivo'
           if price < target else f'<strong>Objetivo superado +{abs(dist_tgt):.1f}%</strong>')
        + f'&nbsp;·&nbsp; Colchón sobre stop <strong>{dist_stp:.1f}%</strong>'
        f'</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# BARRAS DE SCORE
# ─────────────────────────────────────────────
def _score_bar(score: float) -> str:
    S_MIN, S_MAX  = -5.0, 5.0
    SELL_T, BUY_T = -1.8, 2.2
    sell_w = (-1.8 - S_MIN) / (S_MAX - S_MIN) * 100
    hold_w = (2.2 - (-1.8))  / (S_MAX - S_MIN) * 100
    buy_w  = 100 - sell_w - hold_w
    pos    = max(1.5, min(98.5, (score - S_MIN) / (S_MAX - S_MIN) * 100))
    m_clr  = "#4ade80" if score >= BUY_T else "#f87171" if score <= SELL_T else "#fbbf24"
    return (
        f'<div style="width:230px;user-select:none;margin-top:8px">'
        f'<div style="color:#1e2c50;font-size:0.6rem;font-weight:800;letter-spacing:.14em;'
        f'text-transform:uppercase;margin-bottom:6px">Score interno</div>'
        f'<div style="position:relative;height:6px;margin-bottom:4px">'
        f'<div style="position:absolute;left:{pos:.1f}%;transform:translateX(-50%);'
        f'color:{m_clr};font-size:0.6rem;line-height:1">▼</div>'
        f'</div>'
        f'<div style="display:flex;height:6px;border-radius:3px;overflow:hidden">'
        f'<div style="width:{sell_w:.1f}%;background:linear-gradient(to right,#450a0a,#dc2626)"></div>'
        f'<div style="width:{hold_w:.1f}%;background:linear-gradient(to right,#78350f,#f59e0b)"></div>'
        f'<div style="width:{buy_w:.1f}%;background:linear-gradient(to right,#14532d,#4ade80)"></div>'
        f'</div>'
        f'<div style="position:relative;height:12px;margin-top:1px">'
        f'<div style="position:absolute;left:{sell_w:.1f}%;transform:translateX(-50%);'
        f'color:#1e2c50;font-size:0.58rem;font-weight:700">{SELL_T}</div>'
        f'<div style="position:absolute;left:{sell_w+hold_w:.1f}%;transform:translateX(-50%);'
        f'color:#1e2c50;font-size:0.58rem;font-weight:700">+{BUY_T}</div>'
        f'</div>'
        f'<div style="display:flex;font-size:0.58rem;font-weight:800;letter-spacing:.06em;margin-top:1px">'
        f'<div style="width:{sell_w:.1f}%;color:#f87171;text-align:center">VENDER</div>'
        f'<div style="width:{hold_w:.1f}%;color:#f59e0b;text-align:center">MANTENER</div>'
        f'<div style="width:{buy_w:.1f}%;color:#4ade80;text-align:center">COMPRAR</div>'
        f'</div>'
        f'</div>'
    )


def _score_bar_010(score: float) -> str:
    S_MIN, S_MAX  = -5.0, 5.0
    BUY_T, SELL_T = 2.2, -1.8
    val    = (score - S_MIN) / (S_MAX - S_MIN) * 10
    filled = max(0, min(10, round(val)))
    m_clr  = "#4ade80" if score >= BUY_T else "#f87171" if score <= SELL_T else "#f59e0b"
    blocks = ""
    for i in range(10):
        if   i < 3: on_clr, glow = "#ef4444", "#ef444466"
        elif i < 6: on_clr, glow = "#f59e0b", "#f59e0b55"
        else:       on_clr, glow = "#22c55e", "#22c55e55"
        is_on  = i < filled
        ht     = 24 if is_on else 14
        mt     = (24 - ht) // 2
        shadow = f"0 0 8px {glow}, 0 0 2px {on_clr}" if is_on else "none"
        bg     = on_clr if is_on else "#0a0f1e"
        brd    = on_clr if is_on else "#0f1632"
        blocks += (
            f'<div style="flex:1;height:{ht}px;margin-top:{mt}px;border-radius:3px;'
            f'background:{bg};border:1px solid {brd};box-shadow:{shadow}"></div>'
        )
    return (
        f'<div style="width:180px;user-select:none;text-align:right">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:8px">'
        f'<span style="color:#1e2c50;font-size:0.6rem;font-weight:900;letter-spacing:.14em;'
        f'text-transform:uppercase">Índice</span>'
        f'<span style="color:{m_clr};font-size:2rem;font-weight:900;line-height:1;letter-spacing:-0.03em">'
        f'{val:.1f}<span style="color:#1e2c50;font-size:0.8rem;font-weight:600">/10</span></span>'
        f'</div>'
        f'<div style="display:flex;gap:4px;height:24px;align-items:center">{blocks}</div>'
        f'<div style="display:flex;justify-content:space-between;margin-top:5px">'
        f'<span style="color:#1e2c50;font-size:0.58rem;font-weight:700;letter-spacing:.06em">BAJISTA</span>'
        f'<span style="color:#1e2c50;font-size:0.58rem;font-weight:700;letter-spacing:.06em">ALCISTA</span>'
        f'</div>'
        f'</div>'
    )


# ─────────────────────────────────────────────
# RENDER VEREDICTO PRINCIPAL
# ─────────────────────────────────────────────
def render_verdict(verdict, score, context, exec_line=""):
    vc   = {"COMPRAR": "vcard-buy",  "VENDER": "vcard-sell"}.get(verdict, "vcard-hold")
    pc   = {"COMPRAR": "pill-buy",   "VENDER": "pill-sell"}.get(verdict,  "pill-hold")
    clr  = {"COMPRAR": "#4ade80",    "VENDER": "#f87171"}.get(verdict,    "#f59e0b")
    dim  = {"COMPRAR": "rgba(74,222,128,0.08)", "VENDER": "rgba(248,113,113,0.08)"}.get(verdict, "rgba(245,158,11,0.06)")
    lbl  = {"COMPRAR": "SEÑAL DE ENTRADA", "VENDER": "SEÑAL DE SALIDA"}.get(verdict, "SIN SEÑAL CLARA")
    sb010 = _score_bar_010(score)
    sbint = _score_bar(score)
    exec_html = (
        f'<div style="background:{dim};border:1px solid {clr}22;'
        f'border-radius:8px;padding:10px 16px;margin-bottom:16px;'
        f'color:{clr};font-size:0.88rem;font-weight:600;line-height:1.5">'
        f'<span style="opacity:0.6;margin-right:6px">QUÉ HACER HOY</span>{exec_line}</div>'
        if exec_line else ""
    )
    st.markdown(
        f'<div class="vcard {vc}">'
        f'<div style="flex:1;min-width:280px">'
        f'<div style="color:{clr};font-size:0.6rem;font-weight:900;letter-spacing:.2em;'
        f'text-transform:uppercase;opacity:0.7;margin-bottom:10px">{lbl}</div>'
        f'<div style="color:{clr};font-size:3.4rem;font-weight:900;line-height:0.95;'
        f'letter-spacing:-0.03em;margin-bottom:18px">{verdict}</div>'
        f'{exec_html}'
        f'<div style="color:#4b5563;font-size:0.9rem;max-width:560px;line-height:1.65">{context}</div>'
        f'</div>'
        f'<div style="display:flex;flex-direction:column;align-items:flex-end;gap:16px;min-width:200px">'
        f'{sb010}'
        f'<div style="border-top:1px solid #0f1428;width:100%;padding-top:14px">'
        f'<div style="color:#1e2c50;font-size:0.58rem;font-weight:900;letter-spacing:.14em;'
        f'text-transform:uppercase;text-align:right;margin-bottom:4px">Score ponderado</div>'
        f'<div style="color:{clr};font-size:2.4rem;font-weight:900;letter-spacing:-0.04em;'
        f'text-align:right;line-height:1">{score:+.2f}</div>'
        f'{sbint}'
        f'</div>'
        f'<span class="pill {pc}">{verdict}</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# TABLA DE VALIDACIÓN DE SEÑALES
# ─────────────────────────────────────────────
def render_signal_table(tf_results, meta):
    rows = []
    for r in tf_results:
        if r is None:
            continue
        vr  = r.get("vol_ratio")
        div = r.get("rsi_div")

        if vr is None:
            validez, val_clr = "⚠️ Vol N/D", "#fbbf24"
        elif vr < 0.4:
            validez, val_clr = "❌ Inválida", "#f87171"
        elif vr < 0.7:
            validez, val_clr = "⚠️ Débil", "#fbbf24"
        else:
            validez, val_clr = "✅ Válida", "#4ade80"

        div_txt = "↑ Alcista" if div == "bullish" else "↓ Bajista" if div == "bearish" else "—"
        div_clr = "#4ade80" if div == "bullish" else "#f87171" if div == "bearish" else "#374151"
        v       = r["verdict"]
        v_clr   = "#4ade80" if v == "COMPRAR" else "#f87171" if v == "VENDER" else "#fbbf24"
        vol_clr = "#4ade80" if vr and vr >= 1.3 else "#fbbf24" if vr and vr >= 0.7 else "#f87171"
        vol_str = f"{vr:.2f}×" if vr is not None else "N/D"

        if vr is None:
            accion, accion_clr = "Sin vol. verificable — no operar", "#4b5563"
        elif vr < 0.4:
            accion, accion_clr = "Ignorar señal", "#f87171"
        elif vr < 0.7:
            accion, accion_clr = "Esperar confirmación", "#fbbf24"
        else:
            accion, accion_clr = "Señal válida", "#4ade80"

        rows.append(
            f"<tr style='border-bottom:1px solid #090e1e'>"
            f"<td style='padding:10px 12px;color:#4b5563;font-size:0.82rem'>{r['label']}</td>"
            f"<td style='padding:10px 12px;color:{v_clr};font-weight:800;font-size:0.82rem;letter-spacing:.04em'>{v}</td>"
            f"<td style='padding:10px 12px;color:{v_clr};font-weight:700;font-size:0.88rem'>{r['score']:+.1f}</td>"
            f"<td style='padding:10px 12px;color:{vol_clr};font-weight:700;font-size:0.88rem'>{vol_str}</td>"
            f"<td style='padding:10px 12px;color:{val_clr};font-size:0.82rem'>{validez}</td>"
            f"<td style='padding:10px 12px;color:{div_clr};font-size:0.82rem'>{div_txt}</td>"
            f"<td style='padding:10px 12px;color:{accion_clr};font-weight:700;font-size:0.82rem'>{accion}</td>"
            f"</tr>"
        )

    n_valid   = meta.get("vol_valid_count", 0)
    n_tf      = meta.get("n_tf", 0)
    n_weak    = sum(1 for r in tf_results if r and r.get("vol_ratio") is not None
                    and 0.4 <= r["vol_ratio"] < 0.7)
    n_invalid = sum(1 for r in tf_results if r and (
                    r.get("vol_ratio") is None or
                    (r.get("vol_ratio") is not None and r["vol_ratio"] < 0.4)))

    if n_valid == n_tf:
        counter_html = f'<span style="color:#4ade80;font-weight:600">{n_valid} de {n_tf} válidos</span>'
    elif n_valid > 0:
        counter_html = (f'<span style="color:#4ade80;font-weight:600">{n_valid} válido(s)</span>' +
                        (f' · <span style="color:#fbbf24">{n_weak} débil(es)</span>' if n_weak else "") +
                        (f' · <span style="color:#f87171">{n_invalid} sin datos/inválido(s)</span>' if n_invalid else ""))
    else:
        parts = []
        if n_weak:    parts.append(f'<span style="color:#fbbf24">{n_weak} débil(es)</span>')
        if n_invalid: parts.append(f'<span style="color:#f87171">{n_invalid} sin datos/inválido(s)</span>')
        counter_html = " · ".join(parts) if parts else f'<span style="color:#6b7280">{n_tf} timeframes</span>'

    banners = ""
    if meta.get("div_alert"):
        banners += (
            '<div style="color:#f59e0b;font-size:0.82rem;margin-top:14px;padding:10px 14px;'
            'background:rgba(120,53,15,0.15);border-radius:8px;border-left:2px solid #92400e">'
            '⚠️ Divergencia bajista RSI en 15min cerca de resistencia — señal alcista degradada</div>'
        )
    if meta.get("inactive"):
        banners += (
            '<div style="color:#374151;font-size:0.82rem;margin-top:14px;padding:10px 14px;'
            'background:rgba(10,14,28,0.9);border-radius:8px;border-left:2px solid #1a2240">'
            '⏸ Mercado inactivo — ningún timeframe supera el umbral mínimo de volumen</div>'
        )
    elif meta.get("all_low_vol"):
        banners += (
            '<div style="color:#f59e0b;font-size:0.82rem;margin-top:14px;padding:10px 14px;'
            'background:rgba(90,45,5,0.2);border-radius:8px;border-left:2px solid #78350f">'
            '⚠️ Volumen &lt; 50% de la media en todos los timeframes — esperar confirmación</div>'
        )

    th = ("padding:8px 12px;border-bottom:1px solid #0f1428;color:#1e2c50;font-size:0.6rem;"
          "font-weight:900;text-transform:uppercase;letter-spacing:.12em;text-align:left")
    st.markdown(
        f'<div style="background:rgba(255,255,255,0.018);border:1px solid #0f1428;'
        f'border-radius:16px;padding:22px 26px;margin-top:14px">'
        f'<div style="color:#1e2c50;font-size:0.6rem;font-weight:900;letter-spacing:.18em;'
        f'text-transform:uppercase;margin-bottom:16px">'
        f'VALIDACIÓN DE SEÑALES &nbsp;<span style="color:#0f1428">·</span>&nbsp;'
        f'<span style="font-weight:500;text-transform:none;letter-spacing:0;color:#2d3a5a">{counter_html}</span>'
        f'</div>'
        f'<table style="width:100%;border-collapse:collapse"><thead><tr>'
        f'<th style="{th}">Temporalidad</th><th style="{th}">Veredicto</th>'
        f'<th style="{th}">Score</th><th style="{th}">Vol/20d</th>'
        f'<th style="{th}">Validez</th><th style="{th}">Div. RSI</th>'
        f'<th style="{th}">Acción sugerida</th>'
        f'</tr></thead><tbody>{"".join(rows)}</tbody></table>'
        f'{banners}</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# CATALIZADOR (EARNINGS)
# ─────────────────────────────────────────────
def render_catalyst(cat):
    _neutral = (
        '<div style="background:rgba(255,255,255,0.018);border:1px solid #0f1428;'
        'border-radius:14px;padding:16px 22px;color:#2d3a5a;font-size:0.88rem">'
        '📅 Sin resultados trimestrales en los últimos 45 días — análisis puramente técnico.</div>'
    )
    if not cat:
        st.markdown(_neutral, unsafe_allow_html=True)
        return
    if not cat.get("has_catalyst"):
        last_info = ""
        if cat.get("last_quarter"):
            last_info = (f' Último resultado conocido: {cat["last_quarter"]} '
                         f'({cat.get("last_date","")}) — fuera de la ventana de 45 días.')
        st.markdown(
            f'<div style="background:rgba(255,255,255,0.018);border:1px solid #0f1428;'
            f'border-radius:14px;padding:16px 22px;color:#2d3a5a;font-size:0.88rem">'
            f'📅 Sin resultados trimestrales en los últimos 45 días — análisis puramente técnico.{last_info}'
            f'</div>',
            unsafe_allow_html=True,
        )
        return

    pct    = cat["pct_rx"]
    vr     = cat.get("vol_ratio")
    clr    = "#4ade80" if pct > 1.5 else "#f87171" if pct < -1.5 else "#f59e0b"
    vr_str = f"{vr:.2f}×" if vr is not None else "N/D"
    vr_clr = "#4ade80" if vr and vr >= 1.0 else "#f59e0b" if vr and vr >= 0.7 else "#f87171"
    st.markdown(
        f'<div style="background:rgba(255,255,255,0.018);border:1px solid #0f1428;'
        f'border-radius:16px;padding:20px 24px">'
        f'<div style="display:flex;flex-wrap:wrap;gap:14px;align-items:center">'
        f'<div class="chip"><span class="chip-label">Resultado {cat.get("quarter","")}</span>'
        f'<span class="chip-value">{cat["date"]}</span></div>'
        f'<div class="chip"><span class="chip-label">Reacción (3 sesiones)</span>'
        f'<span class="chip-value" style="color:{clr}">{pct:+.1f}%</span></div>'
        f'<div class="chip"><span class="chip-label">Vol reacción vs 20d</span>'
        f'<span class="chip-value" style="color:{vr_clr}">{vr_str}</span></div>'
        f'<div style="flex:1;min-width:220px;padding-left:8px;border-left:1px solid #0f1428">'
        f'<div style="color:#1e2c50;font-size:0.6rem;font-weight:900;letter-spacing:.14em;'
        f'text-transform:uppercase;margin-bottom:5px">Conclusión</div>'
        f'<div style="color:#9ca3af;font-size:0.9rem;line-height:1.5">Mercado {cat["conclusion"]}</div>'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# ESCENARIOS DE RESOLUCIÓN
# ─────────────────────────────────────────────
def render_scenarios(day_tf, intraday_tfs, price):
    if not day_tf or not day_tf.get("atr"):
        return
    atr        = day_tf["atr"]
    max_trigger = price * 1.20
    intra_ress = [r["resistance"] for r in (intraday_tfs or [])
                  if r and r.get("resistance") and price < r["resistance"] <= max_trigger]
    op_res     = min(intra_ress) if intra_ress else min(day_tf["resistance"], max_trigger)
    intra_sups = [r["support"] for r in (intraday_tfs or [])
                  if r and r.get("support") and r["support"] < price]
    op_sup     = max(intra_sups) if intra_sups else day_tf["support"]
    tgt_bull   = op_res + 2.0 * atr
    stop_bear  = op_sup - 1.0 * atr
    res_src    = "op. intraday" if intra_ress else "estructural diario"

    _sth = ("padding:9px 14px;border-bottom:1px solid #090e1e;color:#1e2c50;font-size:0.6rem;"
            "font-weight:900;text-transform:uppercase;letter-spacing:.12em;text-align:left")
    st.markdown(
        f'<div style="background:rgba(255,255,255,0.018);border:1px solid #0f1428;'
        f'border-radius:16px;padding:22px 26px;margin-top:14px">'
        f'<div style="color:#1e2c50;font-size:0.6rem;font-weight:900;letter-spacing:.18em;'
        f'text-transform:uppercase;margin-bottom:16px">ESCENARIOS DE RESOLUCIÓN</div>'
        f'<table style="width:100%;border-collapse:collapse"><thead><tr>'
        f'<th style="{_sth}">Escenario</th><th style="{_sth}">Trigger</th>'
        f'<th style="{_sth}">Precio objetivo</th><th style="{_sth}">Acción</th>'
        f'</tr></thead><tbody>'
        f'<tr style="border-bottom:1px solid #090e1e">'
        f'<td style="padding:12px 14px;color:#4ade80;font-weight:800;font-size:0.85rem">▲ Alcista</td>'
        f'<td style="padding:12px 14px;color:#4b5563;font-size:0.85rem">'
        f'Cierre &gt; <strong style="color:#dde5ff">{op_res:.2f}€</strong>'
        f'<span style="color:#1e2c50;font-size:0.78rem"> ({res_src})</span> · Vol ≥ 1×</td>'
        f'<td style="padding:12px 14px;color:#4ade80;font-weight:700">{tgt_bull:.2f}€'
        f'<span style="color:#1e2c50;font-size:0.75rem;font-weight:400"> +2×ATR</span></td>'
        f'<td style="padding:12px 14px;color:#4ade80;font-weight:700">Mantener / ampliar</td>'
        f'</tr><tr>'
        f'<td style="padding:12px 14px;color:#f87171;font-weight:800;font-size:0.85rem">▼ Bajista</td>'
        f'<td style="padding:12px 14px;color:#4b5563;font-size:0.85rem">'
        f'Cierre &lt; <strong style="color:#dde5ff">{op_sup:.2f}€</strong>'
        f'<span style="color:#1e2c50;font-size:0.78rem"> (soporte op.)</span> · Vol ≥ 0.7×</td>'
        f'<td style="padding:12px 14px;color:#f87171;font-weight:700">{stop_bear:.2f}€'
        f'<span style="color:#1e2c50;font-size:0.75rem;font-weight:400"> −1×ATR</span></td>'
        f'<td style="padding:12px 14px;color:#f87171;font-weight:700">Reducir / salir</td>'
        f'</tr></tbody></table></div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# BLOQUE DE TIMEFRAME
# ─────────────────────────────────────────────
def render_tf_block(r):
    if r is None:
        st.warning("Sin datos para este timeframe.")
        return

    v    = r["verdict"]
    tc   = {"COMPRAR": "tf-buy",  "VENDER": "tf-sell"}.get(v, "tf-hold")
    pc   = {"COMPRAR": "pill-buy","VENDER": "pill-sell"}.get(v, "pill-hold")
    clr  = {"COMPRAR": "#4ade80", "VENDER": "#f87171"}.get(v, "#fbbf24")
    rsi  = f"{r['rsi']:.0f}" if r["rsi"] else "—"
    atr  = f"{r['atr']:.2f}€" if r.get("atr") else "—"

    vr = r.get("vol_ratio")
    if vr is not None:
        vol_clr = "#4ade80" if vr >= 1.3 else "#fbbf24" if vr >= 0.9 else "#f87171"
        vol_txt = f"{vr:.1f}×" + (" ✎" if r.get("vol_manual") else "")
    else:
        vol_clr, vol_txt = "#6b7280", "N/D"

    vwap_chip = ""
    if r.get("vwap") and r["interval"] == "15m":
        vwap_chip = (
            f'<div class="chip"><span class="chip-label">VWAP</span>'
            f'<span class="chip-value">{r["vwap"]:.2f}€</span></div>'
        )

    div     = r.get("rsi_div")
    div_clr = "#4ade80" if div == "bullish" else "#f87171" if div == "bearish" else "#6b7280"
    div_txt = "DIV ↑" if div == "bullish" else "DIV ↓" if div == "bearish" else "Sin div."

    chips = (
        f'<div class="chip"><span class="chip-label">Score</span>'
        f'<span class="chip-value" style="color:{clr}">{r["score"]:+.1f}</span></div>'
        f'<div class="chip"><span class="chip-label">RSI</span>'
        f'<span class="chip-value">{rsi}</span></div>'
        f'<div class="chip"><span class="chip-label">ATR(14)</span>'
        f'<span class="chip-value">{atr}</span></div>'
        f'<div class="chip"><span class="chip-label">Vol/20d</span>'
        f'<span class="chip-value" style="color:{vol_clr}">{vol_txt}</span></div>'
        f'<div class="chip"><span class="chip-label">RSI Div.</span>'
        f'<span class="chip-value" style="color:{div_clr};font-size:0.9rem">{div_txt}</span></div>'
        f'<div class="chip"><span class="chip-label">Soporte</span>'
        f'<span class="chip-value" style="color:#7dd3fc">{r["support"]:.2f}€</span></div>'
        f'<div class="chip"><span class="chip-label">Resistencia</span>'
        f'<span class="chip-value" style="color:#fda4af">{r["resistance"]:.2f}€</span></div>'
        + vwap_chip
    )
    sigs_html = "".join(
        f'<div class="sig-{"bull" if t=="bull" else "bear" if t=="bear" else "neut"}">'
        f'{"▲" if t=="bull" else "▼" if t=="bear" else "·"}&nbsp; {txt}</div>'
        for t, txt in r["signals"]
    )
    vol_nd_note = ""
    if r.get("vol_ratio") is None and r["interval"] in ("1h", "15m"):
        vol_nd_note = (
            '<div style="color:#4b5563;font-size:0.78rem;margin-top:10px;padding:7px 10px;'
            'background:rgba(17,24,39,0.7);border-radius:6px;border-left:2px solid #374151">'
            '⚠️ Vol: no disponible — Yahoo Finance no reporta volumen intraday fiable para '
            'valores españoles. Dato condicionado.</div>'
        )
    st.markdown(f"""
    <div class="tf-card {tc}">
      <div style="display:flex;align-items:center;justify-content:space-between;
                  flex-wrap:wrap;gap:10px;margin-bottom:14px">
        <span style="color:#d1d5db;font-size:1rem;font-weight:600">{r['label']}</span>
        <span class="pill {pc}">{v}</span>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:10px;margin-bottom:14px">{chips}</div>
      <div>{sigs_html}</div>
      {vol_nd_note}
    </div>
    <div style="height:10px"></div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# POSICIÓN ABIERTA
# ─────────────────────────────────────────────
def render_position(entries, price):
    if not entries:
        return {"shares": 0, "avg_price": 0, "total_cost": 0, "pnl_eur": 0, "pnl_pct": 0}

    total_shares = sum(e["shares"] for e in entries)
    total_cost   = sum(e["shares"] * e["price"] for e in entries)
    avg_price    = total_cost / total_shares
    current_val  = total_shares * price
    pnl_eur      = current_val - total_cost
    pnl_pct      = (current_val / total_cost - 1) * 100
    sign         = "+" if pnl_eur >= 0 else ""

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Precio actual",  f"{price:.3f} €")
    c2.metric("Precio medio",   f"{avg_price:.2f} €")
    c3.metric("P&L total",      f"{sign}{pnl_eur:,.2f} €",
              f"{sign}{pnl_pct:.2f}%",
              delta_color="normal" if pnl_eur >= 0 else "inverse")
    c4.metric("Valor posición", f"{current_val:,.2f} €",
              f"{total_shares:.2f} acc · coste {total_cost:,.2f}€")

    st.markdown("")
    for i, e in enumerate(entries, 1):
        ev   = e["shares"] * price
        ec   = e["shares"] * e["price"]
        ep   = ev - ec
        epct = (ev / ec - 1) * 100
        s    = "+" if ep >= 0 else ""
        c    = "#4ade80" if ep >= 0 else "#f87171"
        st.markdown(f"""
        <div class="pos-row">
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
            <div>
              <span style="color:#4b5563;font-size:0.72rem;font-weight:700;
                           letter-spacing:.08em;text-transform:uppercase">Entrada #{i}</span>
              <span style="color:#e2e8f0;font-size:1rem;font-weight:600;margin-left:12px">
                {e['shares']:.2f} acc &nbsp;@&nbsp; {e['price']:.2f}€
              </span>
            </div>
            <div style="text-align:right">
              <span style="color:{c};font-size:1.1rem;font-weight:700">{s}{ep:,.2f}€</span>
              <span style="color:{c};font-size:0.85rem;margin-left:8px">({s}{epct:.1f}%)</span>
            </div>
          </div>
          <div style="margin-top:8px;display:flex;gap:16px">
            <span style="color:#374151;font-size:0.8rem">Coste <strong style="color:#9ca3af">{ec:,.2f}€</strong></span>
            <span style="color:#374151;font-size:0.8rem">Valor <strong style="color:#9ca3af">{ev:,.2f}€</strong></span>
          </div>
        </div>""", unsafe_allow_html=True)

    return {"shares": total_shares, "avg_price": avg_price,
            "total_cost": total_cost, "pnl_eur": pnl_eur, "pnl_pct": pnl_pct}


# ─────────────────────────────────────────────
# NOTICIAS
# ─────────────────────────────────────────────
def render_news(news):
    if not news:
        st.markdown(
            '<div style="color:#4b5563;font-size:0.9rem;padding:12px">No se encontraron noticias recientes.</div>',
            unsafe_allow_html=True,
        )
        return
    for n in news:
        st.markdown(f"""
        <div class="news-item">
          <a href="{n['link']}" target="_blank"
             style="color:#93c5fd;text-decoration:none;font-size:0.95rem;font-weight:600;
                    line-height:1.4;display:block;margin-bottom:6px">{n['title']}</a>
          <div style="display:flex;gap:12px;align-items:center">
            <span style="color:#374151;font-size:0.75rem;font-weight:600;
                         text-transform:uppercase;letter-spacing:.05em">{n['publisher']}</span>
            <span style="color:#1f2937;font-size:0.75rem">·</span>
            <span style="color:#374151;font-size:0.75rem">{n['time']}</span>
          </div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# BACKTESTING UI
# ─────────────────────────────────────────────
def render_backtest_results(result):
    if result is None:
        st.error("No hay suficientes datos históricos para este ticker.")
        return
    if result.get("n_signals", 0) == 0:
        st.warning("El sistema no generó ninguna señal en el período seleccionado. "
                   "Prueba con un período más largo o ajusta los umbrales.")
        return

    fwd   = result["forward_days"]
    buy   = result["buy"]
    watch = result.get("watch", {"n": 0, "win_rate": 0.0, "avg_ret": 0.0, "best": 0.0, "worst": 0.0})
    sell  = result["sell"]
    total = result["n_signals"]

    # Métricas resumen
    st.markdown(
        f'<div style="background:rgba(255,255,255,0.018);border:1px solid #0f1428;'
        f'border-radius:16px;padding:22px 26px;margin-bottom:16px">'
        f'<div style="color:#1e2c50;font-size:0.6rem;font-weight:900;letter-spacing:.18em;'
        f'text-transform:uppercase;margin-bottom:18px">'
        f'RESULTADOS — {result["ticker"]} · Retorno a {fwd} días · {total} señales totales</div>'
        f'<div style="display:flex;flex-wrap:wrap;gap:24px">'
        + _backtest_stat_block("COMPRAR", buy,   "#4ade80", "#14532d")
        + _backtest_stat_block("VIGILAR", watch, "#fbbf24", "#78350f")
        + _backtest_stat_block("VENDER",  sell,  "#f87171", "#7f1d1d")
        + '</div>'
        + _backtest_disclaimer()
        + '</div>',
        unsafe_allow_html=True,
    )

    # ── Tabla señales COMPRAR (siempre visible)
    detail = result["detail"]

    def _signal_table(signals_df, label, accent_clr, border_clr, score_clr):
        if signals_df.empty:
            return
        ret_col = f"Retorno {fwd}d (%)"
        rows = ""
        for _, row in signals_df.iterrows():
            ret     = row[ret_col]
            ret_clr = "#4ade80" if ret > 0 else "#f87171"
            rows += (
                f"<tr style='border-bottom:1px solid #090e1e'>"
                f"<td style='padding:10px 14px;color:#dde5ff;font-weight:700;font-size:0.9rem'>{row['Fecha']}</td>"
                f"<td style='padding:10px 14px;color:{score_clr};font-weight:700'>{row['Score']:+.2f}</td>"
                f"<td style='padding:10px 14px;color:#9ca3af'>{row['Entrada (€)']:.3f} €</td>"
                f"<td style='padding:10px 14px;color:#9ca3af'>{row[f'Salida +{fwd}d (€)']:.3f} €</td>"
                f"<td style='padding:10px 14px;color:{ret_clr};font-weight:800;font-size:1rem'>{ret:+.2f}%</td>"
                f"</tr>"
            )
        th = ("padding:8px 14px;border-bottom:1px solid #0f1428;color:#1e2c50;font-size:0.6rem;"
              "font-weight:900;text-transform:uppercase;letter-spacing:.12em;text-align:left")
        st.markdown(
            f'<div style="border:1px solid {border_clr};border-radius:16px;padding:22px 26px;margin-top:16px">'
            f'<div style="color:{accent_clr};font-size:0.6rem;font-weight:900;letter-spacing:.18em;'
            f'text-transform:uppercase;margin-bottom:16px">'
            f'{label} · HISTÓRICO COMPLETO ({len(signals_df)} entradas)</div>'
            f'<table style="width:100%;border-collapse:collapse"><thead><tr>'
            f'<th style="{th}">Fecha</th>'
            f'<th style="{th}">Score</th>'
            f'<th style="{th}">Entrada</th>'
            f'<th style="{th}">Salida (+{fwd}d)</th>'
            f'<th style="{th}">Retorno</th>'
            f'</tr></thead><tbody>{rows}</tbody></table>'
            f'</div>',
            unsafe_allow_html=True,
        )

    _signal_table(
        detail[detail["Señal"] == "COMPRAR"].copy(),
        "🎯 SEÑALES DE COMPRA", "#4ade80", "#14532d", "#86efac",
    )
    _signal_table(
        detail[detail["Señal"] == "VIGILAR"].copy(),
        "👁 SEÑALES VIGILAR (score 1.5 – umbral COMPRAR)", "#fbbf24", "#78350f", "#fde68a",
    )

    # Tabla completa en expander
    with st.expander("Ver todas las señales (COMPRAR + VIGILAR + VENDER)"):
        st.dataframe(
            detail.style.map(
                lambda v: "color: #4ade80" if v is True else "color: #f87171" if v is False else "",
                subset=["Correcto"],
            ),
            use_container_width=True,
            hide_index=True,
        )


def _backtest_stat_block(label, stats, clr, border):
    if stats["n"] == 0:
        return (
            f'<div style="border:1px solid {border};border-radius:12px;padding:16px 20px;min-width:220px">'
            f'<div style="color:{clr};font-size:0.65rem;font-weight:900;letter-spacing:.14em;'
            f'text-transform:uppercase;margin-bottom:8px">{label}</div>'
            f'<div style="color:#374151;font-size:0.9rem">Sin señales en este período</div>'
            f'</div>'
        )
    wr_clr = "#4ade80" if stats["win_rate"] >= 55 else "#f59e0b" if stats["win_rate"] >= 45 else "#f87171"
    return (
        f'<div style="border:1px solid {border};border-radius:12px;padding:16px 20px;min-width:220px">'
        f'<div style="color:{clr};font-size:0.65rem;font-weight:900;letter-spacing:.14em;'
        f'text-transform:uppercase;margin-bottom:12px">{label} · {stats["n"]} señales</div>'
        f'<div style="display:flex;gap:16px;flex-wrap:wrap">'
        f'<div><div style="color:#1e2c50;font-size:0.6rem;font-weight:700;text-transform:uppercase;margin-bottom:4px">Win rate</div>'
        f'<div style="color:{wr_clr};font-size:1.6rem;font-weight:900">{stats["win_rate"]}%</div></div>'
        f'<div><div style="color:#1e2c50;font-size:0.6rem;font-weight:700;text-transform:uppercase;margin-bottom:4px">Ret. medio</div>'
        f'<div style="color:{"#4ade80" if stats["avg_ret"] >= 0 else "#f87171"};font-size:1.6rem;font-weight:900">'
        f'{stats["avg_ret"]:+.1f}%</div></div>'
        f'<div><div style="color:#1e2c50;font-size:0.6rem;font-weight:700;text-transform:uppercase;margin-bottom:4px">Mejor</div>'
        f'<div style="color:#4ade80;font-size:1rem;font-weight:700">{stats["best"]:+.1f}%</div></div>'
        f'<div><div style="color:#1e2c50;font-size:0.6rem;font-weight:700;text-transform:uppercase;margin-bottom:4px">Peor</div>'
        f'<div style="color:#f87171;font-size:1rem;font-weight:700">{stats["worst"]:+.1f}%</div></div>'
        f'</div></div>'
    )


def _backtest_disclaimer():
    return (
        '<div style="margin-top:16px;padding:10px 14px;background:rgba(10,14,28,0.8);'
        'border-radius:8px;border-left:2px solid #1a2240;color:#374151;font-size:0.78rem;line-height:1.5">'
        '⚠️ Backtesting solo con datos diarios (sin 1H ni 15min). Resultados pasados no garantizan '
        'resultados futuros. Win rate &gt; 55% sugiere edge; &lt; 45% indica revisar umbrales. '
        '<strong style="color:#4b5563">VIGILAR</strong>: señales con score entre 1.5 y el umbral COMPRAR '
        '— oportunidades moderadas que no alcanzan la confluencia fuerte, útiles para vigilar el valor.'
        '</div>'
    )
