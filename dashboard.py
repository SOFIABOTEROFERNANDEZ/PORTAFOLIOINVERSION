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

