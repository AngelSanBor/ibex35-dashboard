# IBEX 35 · Análisis IA Swing Trading

Dashboard de análisis técnico multi-timeframe para valores del IBEX 35. Orientado a swing trading (días/semanas), con señales de compra/venta basadas en indicadores técnicos, volumen y noticias.

## Características

- Análisis multi-timeframe: Diario (6 meses), 1H (1 mes), 15min (5 días)
- Señal combinada COMPRAR / VENDER / MANTENER con score ponderado
- Seguimiento de posición abierta con P&L en tiempo real
- Niveles clave: soporte operativo, soporte estructural, resistencia
- Escenarios de resolución alcista/bajista
- Noticias recientes del valor
- Análisis de gráficos por IA (Claude)
- Backtesting histórico por señal
- Optimizado para móvil (iPhone)

## Instalación local

```bash
pip install -r requirements.txt
streamlit run ibex35_dashboard.py
```

## Uso en iPhone

Accede a través de [Streamlit Cloud](https://streamlit.io/cloud) y guarda el enlace en la pantalla de inicio de Safari como webapp.

## Aviso

Análisis orientativo. No constituye asesoramiento financiero.
