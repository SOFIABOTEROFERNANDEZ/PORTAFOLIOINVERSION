# ★ Seguimiento y Simulación de Portafolio de Inversión

Aplicación en **Python + Streamlit + Plotly + yfinance** para registrar, monitorear y evaluar un portafolio de
**renta variable** (acciones, ETF) y **renta fija** (CDT, TES, bonos), con una simulación a 1 año del portafolio.


## ★ Funcionalidades

| Vista | Qué hace |
|---|---|
| **💼 Seguimiento de portafolio** | Registra compras, ventas, dividendos, intereses y pagos de capital (fecha, cantidad, precio/valor y **comisión del broker**). Valora acciones/ETF con precios de mercado (yfinance) y CDT/TES/bonos por sus condiciones contractuales (tasa E.A., plazo, vencimiento). Calcula **valor total invertido, valor actual, rentabilidad acumulada, rentabilidad efectiva anual (E.A.)** y la **distribución renta fija vs. renta variable**. Importa/exporta CSV. |
| **🔮 Simulación a 1 año** | Proyección del rendimiento esperado (precio + dividendos), tarjetas de métricas, dona de distribución, histórico comparativo y simulación Monte Carlo.
