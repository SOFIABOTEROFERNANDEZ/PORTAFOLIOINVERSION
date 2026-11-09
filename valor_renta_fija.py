"""Clase ValoradorRentaFija: valoración de CDT, TES y bonos según sus condiciones contractuales."""
from datetime import date
from typing import Optional


class ValoradorRentaFija:
    """Valora un título de renta fija por devengo (causación) a su tasa efectiva anual.

    valor = precio_compra x (1 + tasa_ea) ^ (días / 365), con días contados hasta
    min(fecha de valoración, vencimiento). Después del vencimiento el valor deja de crecer.
    Si el título NO capitaliza (paga cupones/intereses aparte), se mantiene a su valor de compra
    y los intereses se registran como operaciones de tipo "Interés".
    """

    DIAS_ANIO = 365

    @classmethod
    def valor_unitario(cls, precio_compra: float, fecha_compra: date, tasa_ea: Optional[float],
                       vencimiento: Optional[date], fecha_valoracion: date,
                       capitaliza: bool = True) -> float:
        if not capitaliza or tasa_ea is None:
            return precio_compra
        fecha_fin = min(fecha_valoracion, vencimiento) if vencimiento else fecha_valoracion
        dias = max((fecha_fin - fecha_compra).days, 0)
        return precio_compra * (1 + tasa_ea) ** (dias / cls.DIAS_ANIO)

    @staticmethod
    def dias_al_vencimiento(vencimiento: Optional[date], hoy: date) -> Optional[int]:
        return None if vencimiento is None else (vencimiento - hoy).days
