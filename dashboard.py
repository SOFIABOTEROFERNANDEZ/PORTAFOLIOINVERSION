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

