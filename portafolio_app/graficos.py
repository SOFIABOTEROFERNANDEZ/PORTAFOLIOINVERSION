"""Clase Graficos: construcción de las figuras Plotly del dashboard."""
from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class Graficos:
    """Fábrica de gráficos. Cada método devuelve una figura de Plotly."""

    # ---------------------------------------------------------------- simulación a 1 año
    @staticmethod
    def dona_distribucion(tabla: pd.DataFrame) -> go.Figure:
        fig = px.pie(tabla, names="Ticker", values="Inversión", hole=0.55, title="Distribución del capital")
        fig.update_traces(textinfo="label+percent")
        return fig

    @staticmethod
    def ganancia_por_activo(tabla: pd.DataFrame) -> go.Figure:
        contrib = tabla.melt(id_vars="Ticker", value_vars=["Ganancia por precio", "Ganancia por dividendos"],
                             var_name="Fuente", value_name="USD")
        fig = px.bar(contrib, x="Ticker", y="USD", color="Fuente", barmode="stack",
                     title="Ganancia esperada por activo (precio + dividendos)")
        fig.add_hline(y=0, line_color="gray")
        return fig

    @staticmethod
    def proyeccion_bandas(fechas, bandas: Dict[int, np.ndarray], capital: float) -> go.Figure:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=fechas, y=bandas[95], line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=fechas, y=bandas[5], fill="tonexty", line=dict(width=0),
                                 fillcolor="rgba(99,110,250,0.15)", name="Rango 5%–95%"))
        fig.add_trace(go.Scatter(x=fechas, y=bandas[75], line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=fechas, y=bandas[25], fill="tonexty", line=dict(width=0),
                                 fillcolor="rgba(99,110,250,0.30)", name="Rango 25%–75%"))
        fig.add_trace(go.Scatter(x=fechas, y=bandas[50], line=dict(color="#636EFA", width=3), name="Mediana"))
        fig.add_hline(y=capital, line_dash="dot", line_color="gray", annotation_text="Capital inicial")
        fig.update_layout(title="Proyección del valor del portafolio (precio + dividendos)",
                          yaxis_title="Valor (USD)", hovermode="x unified")
        return fig

    @staticmethod
    def histograma_final(valores_finales: np.ndarray, capital: float, valor_final: float) -> go.Figure:
        fig = px.histogram(x=valores_finales, nbins=50, title="Distribución del valor final simulado",
                           labels={"x": "Valor final (USD)"})
        fig.add_vline(x=capital, line_dash="dot", line_color="gray", annotation_text="Capital")
        fig.add_vline(x=valor_final, line_color="green", annotation_text="Estimación determinista")
        return fig

    @staticmethod
    def historico_normalizado(prices: pd.DataFrame, pesos: np.ndarray, activos: List[str], years: int) -> go.Figure:
        norm = prices[activos] / prices[activos].iloc[0] * 100
        portafolio = (norm * pesos).sum(axis=1)  # portafolio buy & hold con los pesos actuales
        fig = go.Figure()
        for t in activos:
            fig.add_trace(go.Scatter(x=norm.index, y=norm[t], name=t, line=dict(width=1.5), opacity=0.8))
        fig.add_trace(go.Scatter(x=portafolio.index, y=portafolio, name="PORTAFOLIO",
                                 line=dict(color="black", width=4)))
        fig.update_layout(title=f"Rendimiento histórico de precios (base 100, últimos {years} años)",
                          yaxis_title="Índice (base 100)", hovermode="x unified")
        return fig

    @staticmethod
    def dividendos_por_anio(dividends: Dict[str, pd.Series], activos: List[str]):
        filas = []
        for t in activos:
            s = dividends.get(t, pd.Series(dtype=float))
            for anio, val in s.groupby(s.index.year).sum().items():
                filas.append({"Año": anio, "Ticker": t, "Dividendo por acción": val})
        if not filas:
            return None
        return px.bar(pd.DataFrame(filas), x="Año", y="Dividendo por acción", color="Ticker",
                      barmode="group", title="Dividendos pagados por acción, por año")

    @staticmethod
    def correlacion(prices: pd.DataFrame, activos: List[str]) -> go.Figure:
        corr = prices[activos].pct_change().dropna().corr()
        return px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                         title="Correlación de retornos diarios")

    # ---------------------------------------------------------------- seguimiento de portafolio
    @staticmethod
    def dona_clase(renta_fija: float, renta_variable: float) -> go.Figure:
        fig = px.pie(names=["Renta fija", "Renta variable"], values=[renta_fija, renta_variable], hole=0.55,
                     title="Renta fija vs. renta variable (valor actual)",
                     color_discrete_sequence=["#00CC96", "#636EFA"])
        fig.update_traces(textinfo="label+percent")
        return fig

    @staticmethod
    def costo_vs_valor(posiciones: pd.DataFrame) -> go.Figure:
        datos = posiciones.melt(id_vars="Ticker", value_vars=["Costo", "Valor actual"],
                                var_name="Concepto", value_name="Monto")
        return px.bar(datos, x="Ticker", y="Monto", color="Concepto", barmode="group",
                      title="Costo vs. valor actual por posición")
