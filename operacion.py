"""Clase Operacion: registro de una transacción o flujo de caja del portafolio."""
from dataclasses import dataclass
from datetime import date
from typing import ClassVar, Dict, Optional, Tuple

import pandas as pd

from .activo import Activo


@dataclass
class Operacion:
    """Compra, venta, dividendo, interés o pago de capital.

    - cantidad x precio = valor bruto de la operación.
    - Para Dividendo/Interés manuales: cantidad = 1 y precio = monto recibido.
    - tasa_ea, vencimiento y capitaliza_intereses solo aplican a renta fija contractual.
    """

    fecha: date
    tipo: str
    activo: Activo
    cantidad: float
    precio: float
    comision: float = 0.0
    tasa_ea: Optional[float] = None          # tasa efectiva anual en decimales (0.11 = 11% E.A.)
    vencimiento: Optional[date] = None
    capitaliza_intereses: bool = True        # True: el valor crece a la tasa E.A. (CDT, TES)

    COMPRA: ClassVar[str] = "Compra"
    VENTA: ClassVar[str] = "Venta"
    TIPOS: ClassVar[Tuple[str, ...]] = ("Compra", "Venta", "Dividendo", "Interés", "Pago de capital")
    TIPOS_SALIDA_POSICION: ClassVar[Tuple[str, ...]] = ("Venta", "Pago de capital")
    TIPOS_INGRESO: ClassVar[Tuple[str, ...]] = ("Dividendo", "Interés")
    COLUMNAS: ClassVar[Tuple[str, ...]] = (
        "fecha", "tipo", "ticker", "nombre", "tipo_activo", "cantidad", "precio",
        "comision", "tasa_ea", "vencimiento", "capitaliza",
    )
