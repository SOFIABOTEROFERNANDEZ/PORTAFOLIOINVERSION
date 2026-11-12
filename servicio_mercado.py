"""Clase ServicioMercado: acceso a Yahoo Finance (yfinance) para precios y dividendos."""
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf


class ServicioMercado:
    """Descarga datos de mercado. No depende de Streamlit (el caché lo aplica el Dashboard)."""

    def __init__(self, nombres_conocidos: Optional[Dict[str, str]] = None):
        self.nombres_conocidos = nombres_conocidos or {}

    def descargar_historico(self, tickers, years: Optional[int] = None, inicio: Optional[date] = None,
                            ventana_comun: bool = True
                            ) -> Tuple[pd.DataFrame, Dict[str, pd.Series], Dict[str, str], List[str]]:
        """Descarga precios de cierre (SIN ajustar) y dividendos de cada ticker.

        - years: ventana en años hacia atrás (simulación).  inicio: fecha de inicio (seguimiento).
        - ventana_comun=True conserva solo las fechas en las que todos los activos tienen precio.
        Devuelve: (DataFrame de precios, dict de dividendos, dict de nombres, lista de fallidos).
        """
        closes, dividendos, nombres, fallidos = {}, {}, {}, []
        parametros = {"period": f"{years}y"} if inicio is None else {"start": inicio.isoformat()}

        for t in tickers:
            try:
                tk = yf.Ticker(t)
                # auto_adjust=False -> 'Close' es el precio real de mercado (sin sumar dividendos),
                # así evitamos contar los dividendos dos veces.
                hist = tk.history(auto_adjust=False, actions=True, **parametros)
                if hist.empty or "Close" not in hist:
                    fallidos.append(t)
                    continue

                hist.index = hist.index.tz_localize(None)  # quitar zona horaria
                closes[t] = hist["Close"]
                dividendos[t] = hist["Dividends"][hist["Dividends"] > 0]

                try:
                    nombres[t] = tk.info.get("shortName") or self.nombres_conocidos.get(t, t)
                except Exception:
                    nombres[t] = self.nombres_conocidos.get(t, t)
            except Exception:
                fallidos.append(t)

        precios = pd.DataFrame(closes)
        if ventana_comun:
            precios = precios.dropna()  # ventana común de fechas
        return precios, dividendos, nombres, fallidos

    def precio_en_fecha(self, ticker: str, fecha: date) -> Optional[float]:
        """Último precio de cierre disponible en o antes de la fecha indicada."""
        try:
            hist = yf.Ticker(ticker).history(
                start=(fecha - timedelta(days=7)).isoformat(),
                end=(fecha + timedelta(days=1)).isoformat(),
                auto_adjust=False,
            )
            if hist.empty:
                return None
            return float(hist["Close"].iloc[-1])
        except Exception:
            return None
