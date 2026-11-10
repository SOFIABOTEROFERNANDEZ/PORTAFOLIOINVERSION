"""Clase ProyeccionAnual: rendimiento esperado a 1 año (precio + dividendos) por activo."""
from typing import Dict

import pandas as pd


class ProyeccionAnual:
    """Proyección determinista a 1 año basada en el CAGR histórico y los dividendos de 12 meses."""

    DIAS_ANIO = 365

    def tabla_por_activo(self, prices: pd.DataFrame, dividends: Dict[str, pd.Series],
                         names: Dict[str, str], weights: Dict[str, float], capital: float) -> pd.DataFrame:
        """Calcula, por activo, rendimiento esperado por precio y por dividendos a 1 año."""
        last_date = prices.index[-1]
        years_span = max((last_date - prices.index[0]).days / 365.25, 1e-9)
        rows = []

        for t in prices.columns:
            w = weights[t]
            invested = capital * w
            last_price = float(prices[t].iloc[-1])
            first_price = float(prices[t].iloc[0])
            shares = invested / last_price if last_price > 0 else 0.0

            # Rendimiento esperado por precio: CAGR histórico (extrapolado a 1 año)
            cagr = (last_price / first_price) ** (1 / years_span) - 1

            # Dividendos por acción de los últimos 12 meses (proxy del próximo año)
            div_series = dividends.get(t, pd.Series(dtype=float))
            if div_series.empty:
                div_ttm = 0.0
            else:
                div_ttm = float(div_series[div_series.index > last_date - pd.Timedelta(days=self.DIAS_ANIO)].sum())
            div_yield = div_ttm / last_price if last_price > 0 else 0.0

            price_gain = invested * cagr
            div_gain = shares * div_ttm

            rows.append({
                "Ticker": t,
                "Nombre": names.get(t, t),
                "Peso": w,
                "Inversión": invested,
                "Precio actual": last_price,
                "Acciones": shares,
                "Rend. precio esperado": cagr,
                "Dividendo/acción 12m": div_ttm,
                "Yield dividendos": div_yield,
                "Ganancia por precio": price_gain,
                "Ganancia por dividendos": div_gain,
                "Ganancia total": price_gain + div_gain,
                "Rend. total": (price_gain + div_gain) / invested if invested > 0 else 0.0,
            })
        return pd.DataFrame(rows)

    @staticmethod
    def totales(tabla: pd.DataFrame, capital: float) -> dict:
        """Totales del portafolio: rentabilidad total ajustada = precio + dividendos."""
        ganancia_precio = float(tabla["Ganancia por precio"].sum())
        ganancia_div = float(tabla["Ganancia por dividendos"].sum())
        ganancia = ganancia_precio + ganancia_div
        return {
            "ganancia_precio": ganancia_precio,
            "ganancia_dividendos": ganancia_div,
            "ganancia_total": ganancia,
            "rendimiento_total": ganancia / capital,
            "valor_final": capital + ganancia,
        }
