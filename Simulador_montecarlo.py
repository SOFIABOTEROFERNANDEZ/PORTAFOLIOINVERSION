"""Clase SimuladorMonteCarlo: simulación multivariada del valor del portafolio a 1 año."""
from typing import Tuple

import numpy as np
import pandas as pd


class SimuladorMonteCarlo:
    """Monte Carlo con retornos logarítmicos ~ Normal multivariada (covarianza histórica)."""

    DIAS_BURSATILES = 252
    PERCENTILES = (5, 25, 50, 75, 95)

    def __init__(self, n_sims: int = 1000, semilla: int = 42):
        self.n_sims = n_sims
        self.semilla = semilla

    def simular(self, prices: pd.DataFrame, pesos: np.ndarray, capital: float,
                rend_precio: np.ndarray, yield_div: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Devuelve (matriz (n_sims, 253) con el valor total precio + dividendos, covarianza diaria).

        - La media (drift) se calibra para que cada activo crezca a su CAGR esperado.
        - Los dividendos se acumulan linealmente durante el año (aproximación).
        """
        log_ret = np.log(prices / prices.shift(1)).dropna()
        cov = log_ret.cov().values
        mu = np.log1p(rend_precio) / self.DIAS_BURSATILES  # drift diario (log) por activo

        rng = np.random.default_rng(self.semilla)
        shocks = rng.multivariate_normal(mu, cov, size=(self.n_sims, self.DIAS_BURSATILES))
        acumulado = np.cumsum(shocks, axis=1)

        valores_activo = (capital * pesos) * np.exp(acumulado)
        valor_precio = valores_activo.sum(axis=2)
        valor_precio = np.concatenate([np.full((self.n_sims, 1), capital), valor_precio], axis=1)

        dividendo_anual = capital * float(np.sum(pesos * yield_div))
        dividendos = dividendo_anual * np.arange(self.DIAS_BURSATILES + 1) / self.DIAS_BURSATILES
        return valor_precio + dividendos, cov

    def volatilidad_anual(self, cov: np.ndarray, pesos: np.ndarray) -> float:
        return float(np.sqrt(pesos @ cov @ pesos) * np.sqrt(self.DIAS_BURSATILES))

    @staticmethod
    def var_95(valores_finales: np.ndarray, capital: float) -> float:
        """Pérdida que solo se superaría en el 5% de los escenarios."""
        return float(capital - np.percentile(valores_finales, 5))

    @staticmethod
    def probabilidad_perdida(valores_finales: np.ndarray, capital: float) -> float:
        return float((valores_finales < capital).mean())

    def bandas(self, sims: np.ndarray) -> dict:
        return {p: np.percentile(sims, p, axis=0) for p in self.PERCENTILES}
