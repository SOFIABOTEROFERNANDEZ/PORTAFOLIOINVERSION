"""Clase Dashboard: interfaz gráfica en Streamlit que orquesta todas las demás clases."""
from datetime import date, timedelta
from typing import Dict, Optional

import numpy as np
import pandas as pd
import streamlit as st

from .activo import Activo
from .graficos import Graficos
from .operacion import Operacion
from .portafolio import Portafolio
from .proyeccion_anual import ProyeccionAnual
from .servicio_mercado import ServicioMercado
from .simulador_montecarlo import SimuladorMonteCarlo


class Dashboard:
    """Dos vistas: (1) Simulación a 1 año [KO y NKE obligatorios] y (2) Seguimiento de portafolio."""

    # Activos obligatorios (requisito del proyecto)
    MANDATORY = {"KO": "Coca-Cola", "NKE": "Nike"}

    # Sugerencias para agregar rápidamente (acciones, ETFs y bonos)
    SUGGESTED = {
        "AAPL": "Apple", "MSFT": "Microsoft", "JNJ": "Johnson & Johnson", "PG": "Procter & Gamble",
        "MCD": "McDonald's", "PEP": "PepsiCo", "SPY": "ETF S&P 500", "QQQ": "ETF Nasdaq 100",
        "VNQ": "ETF Inmobiliario", "AGG": "ETF Bonos EE.UU. (agregado)", "BND": "ETF Bonos Total Mercado",
        "TLT": "ETF Bonos Tesoro 20+ años", "GLD": "ETF Oro",
    }

    TOLERANCIA_PESOS = 0.05

    def __init__(self):
        self.servicio = ServicioMercado({**self.MANDATORY, **self.SUGGESTED})
        self.proyeccion = ProyeccionAnual()

    # ================================================================== punto de entrada
    def ejecutar(self) -> None:
        self._configurar_pagina()
        params = self._barra_lateral()

        st.title("📈 Seguimiento y Simulación de Portafolio de Inversión")
        st.caption("Datos: Yahoo Finance (yfinance) · Renta variable y renta fija")

        tab_sim, tab_seg = st.tabs(["🔮 Simulación a 1 año", "💼 Seguimiento de portafolio"])
        with tab_sim:
            self._vista_simulacion(params)
        with tab_seg:
            self._vista_seguimiento()

    # ================================================================== utilidades de UI
    @staticmethod
    def _configurar_pagina() -> None:
        st.set_page_config(page_title="Portafolio de Inversión", page_icon="📈", layout="wide")
        st.markdown(
            """
            <style>
            [data-testid="stMetricValue"] {font-size: 1.7rem; font-weight: 700;}
            [data-testid="stMetricLabel"] {opacity: 0.75;}
            .block-container {padding-top: 2rem;}
            </style>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def _mostrar_fig(fig) -> None:
        """Muestra una figura de Plotly ocupando todo el ancho (compatible con varias versiones)."""
        try:
            st.plotly_chart(fig, width="stretch")
        except TypeError:
            st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def _mostrar_df(df: pd.DataFrame) -> None:
        try:
            st.dataframe(df, width="stretch", hide_index=True)
        except TypeError:
            st.dataframe(df, use_container_width=True, hide_index=True)

    @staticmethod
    def _dinero(x: float) -> str:
        return f"${x:,.2f}"

    @staticmethod
    def _tarjeta(columna, etiqueta: str, valor: str, delta: Optional[str] = None, ayuda: Optional[str] = None) -> None:
        with columna:
            with st.container(border=True):
                st.metric(etiqueta, valor, delta, help=ayuda)

    # ================================================================== datos con caché
    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def _cargar_historico(tickers: tuple, years: int):
        """Descarga cacheada 1 hora para no llamar a Yahoo en cada interacción."""
        servicio = ServicioMercado({**Dashboard.MANDATORY, **Dashboard.SUGGESTED})
        return servicio.descargar_historico(tickers, years=years)

    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def _cargar_mercado_seguimiento(tickers: tuple, inicio_iso: str):
        """Precios y dividendos desde la primera operación del portafolio (sin ventana común)."""
        servicio = ServicioMercado({**Dashboard.MANDATORY, **Dashboard.SUGGESTED})
        inicio = date.fromisoformat(inicio_iso) - timedelta(days=10)
        return servicio.descargar_historico(tickers, inicio=inicio, ventana_comun=False)

    # ================================================================== barra lateral (simulación)
    def _barra_lateral(self) -> dict:
        st.sidebar.title("⚙️ Parámetros de la simulación")

        capital = st.sidebar.number_input("💵 Capital inicial (USD)", min_value=100.0, value=10_000.0, step=500.0)
        years = st.sidebar.selectbox("📅 Historial a usar (años)", [1, 2, 3, 5, 10], index=3)

        st.sidebar.markdown("**Activos obligatorios:** KO (Coca-Cola) y NKE (Nike)")
        extra_sel = st.sidebar.multiselect(
            "➕ Agregar activos sugeridos",
            options=list(self.SUGGESTED.keys()),
            format_func=lambda x: f"{x} – {self.SUGGESTED[x]}",
            default=["SPY", "AGG"],
        )
        extra_custom = st.sidebar.text_input("✍️ Otros tickers (separados por coma)", placeholder="Ej: TSLA, V, IEF")

        custom_list = [x.strip().upper() for x in extra_custom.split(",") if x.strip()]
        tickers = list(dict.fromkeys(list(self.MANDATORY.keys()) + extra_sel + custom_list))
        n_assets = len(tickers)

        st.sidebar.subheader("⚖️ Ponderación (%)")
        for t in tickers:  # reparto equitativo inicial para tickers nuevos
            if f"w_{t}" not in st.session_state:
                st.session_state[f"w_{t}"] = round(100 / n_assets, 2)

        def repartir_igual(lista):
            for tk in lista:
                st.session_state[f"w_{tk}"] = round(100 / len(lista), 2)

        st.sidebar.button("Repartir en partes iguales", on_click=repartir_igual, args=(tickers,))

        pesos_brutos = {}
        for t in tickers:
            pesos_brutos[t] = st.sidebar.number_input(f"{t}", min_value=0.0, max_value=100.0, step=1.0, key=f"w_{t}")

        total_w = sum(pesos_brutos.values())
        if abs(total_w - 100) > self.TOLERANCIA_PESOS:
            st.sidebar.error(f"La suma de pesos es {total_w:.2f}%. Debe ser 100%.")
        else:
            st.sidebar.success("Suma de pesos: 100% ✅")

        n_sims = st.sidebar.slider("🎲 Simulaciones Monte Carlo", 200, 3000, 1000, step=200)
        return {"capital": capital, "years": years, "tickers": tickers,
                "pesos_brutos": pesos_brutos, "total_w": total_w, "n_sims": n_sims}

    # ================================================================== vista 1: simulación a 1 año
    def _vista_simulacion(self, p: dict) -> None:
        if abs(p["total_w"] - 100) > self.TOLERANCIA_PESOS:
            st.warning("Ajusta las ponderaciones en la barra lateral hasta que sumen 100%.")
            return

        with st.spinner("Descargando datos de Yahoo Finance..."):
            prices, dividends, names, failed = self._cargar_historico(tuple(p["tickers"]), p["years"])

        if failed:
            st.warning(f"No se pudieron obtener datos de: {', '.join(failed)}. Se excluyen del análisis.")
        if any(m not in prices.columns for m in self.MANDATORY):
            st.error("No se pudieron descargar KO y/o NKE (obligatorios). Revisa tu conexión e inténtalo de nuevo.")
            return
        if len(prices) < 60:
            st.error("Muy pocos datos en común entre los activos. Reduce el historial o cambia de activos.")
            return

        capital = p["capital"]
        valid = list(prices.columns)
        w_sum = sum(p["pesos_brutos"][t] for t in valid)
        weights = {t: p["pesos_brutos"][t] / w_sum for t in valid}  # fracciones 0-1
        w_arr = np.array([weights[t] for t in valid])

        tabla = self.proyeccion.tabla_por_activo(prices, dividends, names, weights, capital)
        tot = self.proyeccion.totales(tabla, capital)

        simulador = SimuladorMonteCarlo(n_sims=p["n_sims"])
        sims, cov = simulador.simular(prices[valid], w_arr, capital,
                                      tabla["Rend. precio esperado"].values, tabla["Yield dividendos"].values)
        finales = sims[:, -1]
        var95 = simulador.var_95(finales, capital)
        vol = simulador.volatilidad_anual(cov, w_arr)
        prob_perdida = simulador.probabilidad_perdida(finales, capital)

        if p["years"] <= 2:
            st.info("Con un historial corto, el CAGR puede ser poco representativo. Considera usar 5 años o más.")

        # --- tarjetas de métricas
        c1, c2, c3, c4 = st.columns(4)
        self._tarjeta(c1, "💰 Capital inicial", self._dinero(capital))
        self._tarjeta(c2, "📊 Rendimiento total estimado", self._dinero(tot["ganancia_total"]),
                      f"{tot['rendimiento_total']:+.2%}")
        self._tarjeta(c3, "🪙 Ganancia por dividendos", self._dinero(tot["ganancia_dividendos"]),
                      f"{tot['ganancia_dividendos'] / capital:+.2%} del capital")
        self._tarjeta(c4, "🏁 Valor final estimado", self._dinero(tot["valor_final"]))

        c5, c6, c7, c8 = st.columns(4)
        self._tarjeta(c5, "📈 Ganancia por precio", self._dinero(tot["ganancia_precio"]),
                      f"{tot['ganancia_precio'] / capital:+.2%}")
        self._tarjeta(c6, "🌊 Volatilidad anual", f"{vol:.2%}")
        self._tarjeta(c7, "⚠️ VaR 95% (1 año)", self._dinero(max(var95, 0)),
                      ayuda="Pérdida que solo se superaría en el 5% de los escenarios simulados.")
        self._tarjeta(c8, "🎯 Prob. de pérdida", f"{prob_perdida:.1%}")

        st.divider()
        t1, t2, t3, t4 = st.tabs(["🍩 Distribución", "🔮 Proyección a 1 año",
                                  "📉 Histórico y comparativa", "📋 Detalle por activo"])

        with t1:
            col_a, col_b = st.columns(2)
            with col_a:
                self._mostrar_fig(Graficos.dona_distribucion(tabla))
            with col_b:
                self._mostrar_fig(Graficos.ganancia_por_activo(tabla))

        with t2:
            fechas = pd.bdate_range(start=prices.index[-1], periods=SimuladorMonteCarlo.DIAS_BURSATILES + 1)
            self._mostrar_fig(Graficos.proyeccion_bandas(fechas, simulador.bandas(sims), capital))
            col_a, col_b = st.columns(2)
            with col_a:
                self._mostrar_fig(Graficos.histograma_final(finales, capital, tot["valor_final"]))
            with col_b:
                nombres_esc = ["Pesimista (P5)", "Conservador (P25)", "Mediana (P50)",
                               "Optimista (P75)", "Muy optimista (P95)"]
                resumen = pd.DataFrame({
                    "Escenario": nombres_esc,
                    "Valor final": [self._dinero(np.percentile(finales, q)) for q in SimuladorMonteCarlo.PERCENTILES],
                    "Rentabilidad": [f"{np.percentile(finales, q) / capital - 1:+.2%}"
                                     for q in SimuladorMonteCarlo.PERCENTILES],
                })
                st.markdown("**Escenarios simulados**")
                self._mostrar_df(resumen)

        with t3:
            self._mostrar_fig(Graficos.historico_normalizado(prices, w_arr, valid, p["years"]))
            fig_div = Graficos.dividendos_por_anio(dividends, valid)
            if fig_div is not None:
                self._mostrar_fig(fig_div)
            else:
                st.info("Los activos seleccionados no pagaron dividendos en el periodo.")
            if len(valid) > 1:
                self._mostrar_fig(Graficos.correlacion(prices, valid))

        with t4:
            mostrar = tabla.copy()
            mostrar["Peso"] = mostrar["Peso"].map("{:.1%}".format)
            for col in ["Inversión", "Precio actual", "Dividendo/acción 12m", "Ganancia por precio",
                        "Ganancia por dividendos", "Ganancia total"]:
                mostrar[col] = mostrar[col].map(self._dinero)
            mostrar["Acciones"] = mostrar["Acciones"].map("{:,.4f}".format)
            for col in ["Rend. precio esperado", "Yield dividendos", "Rend. total"]:
                mostrar[col] = mostrar[col].map("{:+.2%}".format)
            self._mostrar_df(mostrar)
            st.markdown(
                """
**Cómo se calcula**
- **Rend. precio esperado:** CAGR histórico del precio de cierre (sin ajustar) en la ventana elegida.
- **Dividendos:** suma de los dividendos por acción pagados en los últimos 12 meses × acciones compradas.
- **Rentabilidad total ajustada** = ganancia por precio + ganancia por dividendos.
- **Simulación:** Monte Carlo con la covarianza histórica.
                """
            )

        st.caption("⚠️ Herramienta educativa. El rendimiento pasado no garantiza resultados futuros. "
                   "No constituye asesoría financiera.")

    # ================================================================== vista 2: seguimiento
    def _vista_seguimiento(self) -> None:
        if "portafolio" not in st.session_state:
            st.session_state["portafolio"] = Portafolio()
        portafolio: Portafolio = st.session_state["portafolio"]

        st.subheader("Registrar operación")
        self._formulario_operacion(portafolio)
        self._acciones_portafolio(portafolio)

        if not portafolio.operaciones:
            st.info("Aún no hay operaciones. Registra una arriba, importa un CSV o carga el ejemplo.")
            return

        st.divider()
        self._tabla_operaciones(portafolio)
        st.divider()
        self._resumen_portafolio(portafolio)

    def _formulario_operacion(self, portafolio: Portafolio) -> None:
        c1, c2, c3, c4 = st.columns(4)
        tipo_activo = c1.selectbox("Instrumento", Activo.TIPOS)
        tipo_op = c2.selectbox("Operación", Operacion.TIPOS)
        fecha = c3.date_input("Fecha", value=date.today(), max_value=date.today())
        ident = c4.text_input("Ticker / Nombre", placeholder="KO · NKE · CDT Banco X")

        es_flujo = tipo_op in Operacion.TIPOS_INGRESO
        contractual = tipo_activo in Activo.TIPOS_CONTRACTUALES

        c5, c6, c7 = st.columns(3)
        if es_flujo:
            cantidad = 1.0
            c5.caption("Para dividendos/intereses registra el monto total recibido.")
        else:
            cantidad = c5.number_input("Cantidad (unidades)", min_value=0.0, value=1.0, step=1.0)
        etiqueta_precio = "Monto recibido" if es_flujo else "Precio / valor unitario"
        precio = c6.number_input(etiqueta_precio, min_value=0.0, value=0.0, step=1.0,
                                 help="En acciones/ETF, deja 0 para traer el precio de cierre de esa fecha desde yfinance.")
        comision = c7.number_input("Comisión del broker", min_value=0.0, value=0.0, step=0.5)

        tasa_ea, vencimiento, capitaliza = None, None, True
        if contractual and tipo_op == Operacion.COMPRA:
            c8, c9, c10 = st.columns(3)
            tasa_ea = c8.number_input("Tasa efectiva anual (% E.A.)", min_value=0.0, value=10.0, step=0.1) / 100
            vencimiento = c9.date_input("Vencimiento", value=date.today() + timedelta(days=365),
                                        min_value=date(2000, 1, 1), max_value=date(2100, 1, 1))
            capitaliza = c10.checkbox("Capitaliza intereses (CDT/TES)", value=True,
                                      help="Si el título paga cupones aparte, desmárcalo y registra los intereses como 'Interés'.")

        if st.button("➕ Registrar operación", type="primary"):
            self._registrar(portafolio, tipo_activo, tipo_op, fecha, ident, cantidad, precio,
                            comision, tasa_ea, vencimiento, capitaliza)

    def _registrar(self, portafolio, tipo_activo, tipo_op, fecha, ident, cantidad, precio,
                   comision, tasa_ea, vencimiento, capitaliza) -> None:
        ident = ident.strip()
        if not ident:
            st.error("Escribe el ticker o el nombre del instrumento.")
            return
        contractual = tipo_activo in Activo.TIPOS_CONTRACTUALES
        ticker = ident if contractual else ident.upper()
        nombre = self.MANDATORY.get(ticker) or self.SUGGESTED.get(ticker) or ident
        activo = Activo(ticker, nombre, tipo_activo)

        if cantidad <= 0:
            st.error("La cantidad debe ser mayor que 0.")
            return
        if precio <= 0 and tipo_op in (Operacion.COMPRA, Operacion.VENTA) and activo.cotiza_en_bolsa:
            with st.spinner("Consultando precio de cierre en yfinance..."):
                precio = self.servicio.precio_en_fecha(ticker, fecha)
            if not precio:
                st.error(f"No se encontró precio para {ticker} el {fecha}. Escríbelo manualmente.")
                return
            st.info(f"Precio de cierre usado para {ticker}: {precio:,.2f}")
        if precio <= 0:
            st.error("Ingresa un precio/monto mayor que 0.")
            return
        if tipo_op == Operacion.COMPRA and contractual and (vencimiento is None or vencimiento <= fecha):
            st.error("El vencimiento debe ser posterior a la fecha de compra.")
            return

        try:
            portafolio.agregar(Operacion(fecha, tipo_op, activo, cantidad, precio, comision,
                                         tasa_ea, vencimiento, capitaliza))
            st.success(f"{tipo_op} de {ticker} registrada.")
        except ValueError as e:
            st.error(str(e))

    def _acciones_portafolio(self, portafolio: Portafolio) -> None:
        col_a, col_b, col_c = st.columns(3)
        if col_a.button("📦 Cargar portafolio de ejemplo"):
            self._cargar_ejemplo(portafolio)
        if col_b.button("🗑️ Vaciar portafolio"):
            portafolio.limpiar()
        col_c.download_button("⬇️ Exportar operaciones (CSV)",
                              data=portafolio.a_dataframe().to_csv(index=False).encode("utf-8"),
                              file_name="operaciones.csv", mime="text/csv")

        with st.expander("⬆️ Importar operaciones desde CSV"):
            archivo = st.file_uploader("Archivo CSV exportado por esta aplicación", type="csv")
            if archivo is not None and st.button("Importar CSV"):
                try:
                    portafolio.reemplazar(Portafolio.desde_dataframe(pd.read_csv(archivo)))
                    st.success("Operaciones importadas.")
                except Exception as e:  # CSV mal formado u operaciones inconsistentes
                    st.error(f"No se pudo importar el archivo: {e}")

    def _cargar_ejemplo(self, portafolio: Portafolio) -> None:
        """Portafolio de ejemplo: KO, NKE (con una venta parcial), un CDT y un TES."""
        hoy = date.today()
        portafolio.limpiar()
        compras_bolsa = [("KO", "Coca-Cola", 300, 20, "Compra"), ("NKE", "Nike", 200, 10, "Compra"),
                         ("KO", "Coca-Cola", 60, 5, "Venta")]
        with st.spinner("Consultando precios históricos..."):
            for ticker, nombre, dias, cantidad, tipo in compras_bolsa:
                fecha = hoy - timedelta(days=dias)
                precio = self.servicio.precio_en_fecha(ticker, fecha)
                if precio is None:
                    st.warning(f"Sin precio para {ticker} el {fecha}; se omitió esa operación.")
                    continue
                portafolio.agregar(Operacion(fecha, tipo, Activo(ticker, nombre, "Acción"), cantidad, precio, 1.5))
        portafolio.agregar(Operacion(hoy - timedelta(days=150), "Compra", Activo("CDT Ejemplo", "CDT a 360 días", "CDT"),
                                     1, 5000, 0.0, 0.115, hoy + timedelta(days=210), True))
        portafolio.agregar(Operacion(hoy - timedelta(days=100), "Compra", Activo("TES Ejemplo", "TES 2030", "TES"),
                                     1, 3000, 0.0, 0.098, hoy + timedelta(days=1500), True))

    def _tabla_operaciones(self, portafolio: Portafolio) -> None:
        st.subheader("Operaciones registradas")
        df = portafolio.a_dataframe()
        df.insert(0, "#", range(len(df)))
        self._mostrar_df(df)
        col_a, col_b = st.columns([1, 3])
        indice = col_a.selectbox("Eliminar operación #", list(range(len(df))))
        if col_b.button("Eliminar operación seleccionada"):
            try:
                portafolio.eliminar(indice)
                st.rerun()
            except ValueError as e:
                st.error(f"No se puede eliminar: {e}")

    def _resumen_portafolio(self, portafolio: Portafolio) -> None:
        tickers = portafolio.tickers_en_bolsa()
        precios_actuales: Dict[str, float] = {}
        dividendos: Dict[str, pd.Series] = {}
        if tickers:
            with st.spinner("Actualizando valoración con datos de mercado..."):
                prices, dividendos, _, fallidos = self._cargar_mercado_seguimiento(
                    tuple(tickers), portafolio.fecha_inicio().isoformat())
            if fallidos:
                st.warning(f"Sin datos de mercado para {', '.join(fallidos)}: se valoran a su precio de compra.")
            for t in prices.columns:
                serie = prices[t].dropna()
                if not serie.empty:
                    precios_actuales[t] = float(serie.iloc[-1])

        r = portafolio.resumen(precios_actuales, dividendos)

        st.subheader("Resumen consolidado")
        c1, c2, c3, c4 = st.columns(4)
        self._tarjeta(c1, "💰 Total invertido", self._dinero(r["total_invertido"]),
                      ayuda="Compras + comisiones de compra.")
        self._tarjeta(c2, "🏦 Valor actual del portafolio", self._dinero(r["valor_actual"]))
        self._tarjeta(c3, "📊 Ganancia total", self._dinero(r["ganancia_total"]), f"{r['rent_acumulada']:+.2%}")
        ea = "N/D" if r["rent_ea"] is None else f"{r['rent_ea']:+.2%}"
        self._tarjeta(c4, "📆 Rentabilidad efectiva anual (E.A.)", ea,
                      ayuda="TIR con fechas (XIRR) de todos los flujos. En periodos cortos puede ser muy alta o baja.")

        c5, c6, c7, c8 = st.columns(4)
        self._tarjeta(c5, "🪙 Dividendos e intereses", self._dinero(r["ingresos"]))
        self._tarjeta(c6, "💸 Comisiones pagadas", self._dinero(r["comisiones"]))
        self._tarjeta(c7, "🛒 Ventas netas recibidas", self._dinero(r["ventas_netas"]))
        self._tarjeta(c8, "🧮 Rentabilidad acumulada", f"{r['rent_acumulada']:+.2%}")

        col_a, col_b = st.columns(2)
        with col_a:
            if r["valor_actual"] > 0:
                self._mostrar_fig(Graficos.dona_clase(r["renta_fija"], r["renta_variable"]))
        with col_b:
            if not r["posiciones"].empty:
                self._mostrar_fig(Graficos.costo_vs_valor(r["posiciones"]))

        st.markdown("**Posiciones abiertas**")
        pos = r["posiciones"].copy()
        for col in ["Costo", "Valor actual", "Ganancia no realizada"]:
            pos[col] = pos[col].map(self._dinero)
        pos["Cantidad"] = pos["Cantidad"].map("{:,.4f}".format)
        pos["Rend. no realizado"] = pos["Rend. no realizado"].map(lambda x: "N/D" if pd.isna(x) else f"{x:+.2%}")
        self._mostrar_df(pos)

        st.markdown("**Dividendos e intereses recibidos** (los de acciones/ETF se calculan automáticamente con yfinance)")
        ing = r["ingresos_df"].copy()
        ing["Monto"] = ing["Monto"].map(self._dinero)
        self._mostrar_df(ing)

        st.caption("Registra todos los valores en una misma moneda. CDT/TES se valoran por devengo a su tasa E.A.; "
                   "acciones y ETF, a precio de mercado. No incluye impuestos.")
