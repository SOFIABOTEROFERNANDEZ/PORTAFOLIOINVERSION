"""Clase CalculadoraRentabilidad: rentabilidad acumulada y rentabilidad efectiva anual (E.A.)."""
from datetime import date
from typing import List, Optional, Tuple


class CalculadoraRentabilidad:
    """Cálculos de rentabilidad del portafolio."""

    DIAS_ANIO = 365

    @staticmethod
    def rentabilidad_acumulada(total_invertido: float, valor_actual: float, ingresos: float) -> float:
        """(valor actual + ingresos recibidos - total invertido) / total invertido.

        'ingresos' incluye ventas netas, dividendos, intereses y pagos de capital.
        'total_invertido' incluye las comisiones de compra.
        """
        if total_invertido <= 0:
            return 0.0
        return (valor_actual + ingresos - total_invertido) / total_invertido

    @classmethod
    def valor_presente_neto(cls, tasa: float, flujos: List[Tuple[date, float]]) -> float:
        t0 = flujos[0][0]
        return sum(cf / (1 + tasa) ** ((d - t0).days / cls.DIAS_ANIO) for d, cf in flujos)

    @classmethod
    def tasa_efectiva_anual(cls, flujos: List[Tuple[date, float]]) -> Optional[float]:
        """Tasa interna de retorno con fechas (XIRR) = rentabilidad efectiva anual.

        Recibe flujos (fecha, monto): compras y comisiones negativas; ventas, dividendos,
        intereses y el valor actual del portafolio (a la fecha de hoy) positivos.
        Resuelve por bisección. Devuelve None si no existe solución.
        """
        flujos = sorted(flujos, key=lambda x: x[0])
        if len(flujos) < 2 or not any(cf < 0 for _, cf in flujos) or not any(cf > 0 for _, cf in flujos):
            return None
        if (flujos[-1][0] - flujos[0][0]).days <= 0:
            return None

        bajo, alto = -0.9999, 1000.0
        f_bajo = cls.valor_presente_neto(bajo, flujos)
        f_alto = cls.valor_presente_neto(alto, flujos)
        if f_bajo * f_alto > 0:
            return None
        for _ in range(200):
            medio = (bajo + alto) / 2
            f_medio = cls.valor_presente_neto(medio, flujos)
            if abs(f_medio) < 1e-9:
                return medio
            if f_bajo * f_medio < 0:
                alto = medio
            else:
                bajo, f_bajo = medio, f_medio
        return (bajo + alto) / 2
