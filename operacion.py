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

    @property
    def valor_bruto(self) -> float:
        return self.cantidad * self.precio

    def flujo_caja(self) -> float:
        """Flujo de caja desde la perspectiva del inversionista (negativo = sale dinero)."""
        if self.tipo == self.COMPRA:
            return -(self.valor_bruto + self.comision)
        return self.valor_bruto - self.comision

    def a_dict(self) -> Dict:
        return {
            "fecha": self.fecha.isoformat(),
            "tipo": self.tipo,
            "ticker": self.activo.ticker,
            "nombre": self.activo.nombre,
            "tipo_activo": self.activo.tipo,
            "cantidad": self.cantidad,
            "precio": self.precio,
            "comision": self.comision,
            "tasa_ea": self.tasa_ea,
            "vencimiento": self.vencimiento.isoformat() if self.vencimiento else None,
            "capitaliza": self.capitaliza_intereses,
        }

    @classmethod
    def desde_dict(cls, d: Dict) -> "Operacion":
        """Reconstruye una operación desde una fila de CSV/DataFrame."""
        def fecha_o_none(v):
            return None if pd.isna(v) else date.fromisoformat(str(v)[:10])

        tasa = None if pd.isna(d.get("tasa_ea")) else float(d["tasa_ea"])
        capitaliza = str(d.get("capitaliza", True)).strip().lower() in ("true", "1", "1.0")
        return cls(
            fecha=date.fromisoformat(str(d["fecha"])[:10]),
            tipo=str(d["tipo"]),
            activo=Activo(str(d["ticker"]), str(d["nombre"]), str(d["tipo_activo"])),
            cantidad=float(d["cantidad"]),
            precio=float(d["precio"]),
            comision=float(d.get("comision", 0) or 0),
            tasa_ea=tasa,
            vencimiento=fecha_o_none(d.get("vencimiento")),
            capitaliza_intereses=capitaliza,
        )
