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
