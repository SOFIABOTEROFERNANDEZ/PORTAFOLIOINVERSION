"""Clase Portafolio: registro de operaciones, posiciones, flujos y resumen consolidado."""
from datetime import date
from typing import Dict, List, Optional, Tuple

import pandas as pd

from .calculadora_rentabilidad import CalculadoraRentabilidad
from .operacion import Operacion
from .valorador_renta_fija import ValoradorRentaFija


class Portafolio:
    """Libro de operaciones de un portafolio de renta fija y renta variable.

    Las posiciones se calculan con método FIFO (las primeras unidades compradas son las primeras
    en venderse). Los dividendos de renta variable se calculan automáticamente con los dividendos
    históricos de yfinance y la cantidad de acciones que se tenía antes de la fecha ex-dividendo.
    """

    TOLERANCIA = 1e-9

    def __init__(self, operaciones: Optional[List[Operacion]] = None):
        self.operaciones: List[Operacion] = []
        for op in sorted(operaciones or [], key=lambda o: o.fecha):
            self.agregar(op)

    # ------------------------------------------------------------------ registro
    def agregar(self, operacion: Operacion) -> None:
        """Agrega una operación validando que no se venda más de lo que se posee."""
        self._calcular_lotes(self.operaciones + [operacion])  # lanza ValueError si es inválida
        self.operaciones.append(operacion)

    def eliminar(self, indice: int) -> None:
        restantes = [o for i, o in enumerate(self.operaciones) if i != indice]
        self._calcular_lotes(restantes)  # evita dejar ventas sin su compra
        self.operaciones = restantes

    def limpiar(self) -> None:
        self.operaciones = []

    def reemplazar(self, otro: "Portafolio") -> None:
        self.operaciones = list(otro.operaciones)

    def fecha_inicio(self) -> Optional[date]:
        return min((o.fecha for o in self.operaciones), default=None)

    def tickers_en_bolsa(self) -> List[str]:
        return sorted({o.activo.ticker for o in self.operaciones if o.activo.cotiza_en_bolsa})

    def a_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([o.a_dict() for o in self.operaciones], columns=list(Operacion.COLUMNAS))

    @classmethod
    def desde_dataframe(cls, df: pd.DataFrame) -> "Portafolio":
        return cls([Operacion.desde_dict(fila) for fila in df.to_dict("records")])

    # ------------------------------------------------------------------ posiciones
    def _calcular_lotes(self, operaciones: List[Operacion]) -> List[dict]:
        """Procesa compras y ventas en orden cronológico (FIFO) y devuelve los lotes abiertos."""
        lotes: List[dict] = []
        orden = sorted(operaciones, key=lambda o: (o.fecha, 0 if o.tipo == Operacion.COMPRA else 1))
        for op in orden:
            if op.cantidad <= 0 or op.precio < 0:
                raise ValueError("La cantidad debe ser positiva y el precio no puede ser negativo.")
            if op.tipo == Operacion.COMPRA:
                lotes.append({
                    "activo": op.activo,
                    "fecha": op.fecha,
                    "cantidad": op.cantidad,
                    "precio": op.precio,
                    "costo_unit": (op.valor_bruto + op.comision) / op.cantidad,  # incluye comisión
                    "tasa_ea": op.tasa_ea,
                    "vencimiento": op.vencimiento,
                    "capitaliza": op.capitaliza_intereses,
                })
            elif op.tipo in Operacion.TIPOS_SALIDA_POSICION:
                pendiente = op.cantidad
                for lote in lotes:
                    if lote["activo"].ticker != op.activo.ticker or lote["cantidad"] <= self.TOLERANCIA:
                        continue
                    usar = min(lote["cantidad"], pendiente)
                    lote["cantidad"] -= usar
                    pendiente -= usar
                    if pendiente <= self.TOLERANCIA:
                        break
                if pendiente > self.TOLERANCIA:
                    raise ValueError(
                        f"No puedes registrar {op.tipo.lower()} de {op.cantidad:g} {op.activo.ticker} "
                        f"el {op.fecha}: solo tenías disponible {op.cantidad - pendiente:g}."
                    )
        return [l for l in lotes if l["cantidad"] > self.TOLERANCIA]

    def posiciones(self, precios_actuales: Dict[str, float], hoy: Optional[date] = None) -> pd.DataFrame:
        """Valoración actual de las posiciones abiertas.

        Renta variable / ETF: cantidad x precio de mercado (yfinance).
        CDT / TES / bonos: valoración contractual por devengo (ValoradorRentaFija).
        """
        hoy = hoy or date.today()
        acumulado: Dict[str, dict] = {}
        for lote in self._calcular_lotes(self.operaciones):
            activo = lote["activo"]
            if activo.cotiza_en_bolsa:
                valor_unit = precios_actuales.get(activo.ticker) or lote["precio"]
            else:
                valor_unit = ValoradorRentaFija.valor_unitario(
                    lote["precio"], lote["fecha"], lote["tasa_ea"], lote["vencimiento"], hoy, lote["capitaliza"]
                )
            fila = acumulado.setdefault(activo.ticker, {
                "Ticker": activo.ticker, "Nombre": activo.nombre, "Tipo": activo.tipo,
                "Clase": activo.clase, "Cantidad": 0.0, "Costo": 0.0, "Valor actual": 0.0,
            })
            fila["Cantidad"] += lote["cantidad"]
            fila["Costo"] += lote["cantidad"] * lote["costo_unit"]
            fila["Valor actual"] += lote["cantidad"] * valor_unit

        columnas = ["Ticker", "Nombre", "Tipo", "Clase", "Cantidad", "Costo", "Valor actual"]
        df = pd.DataFrame(list(acumulado.values()), columns=columnas)
        df["Ganancia no realizada"] = df["Valor actual"] - df["Costo"]
        df["Rend. no realizado"] = df["Ganancia no realizada"] / df["Costo"].where(df["Costo"] > 0)
        return df

    # ------------------------------------------------------------------ dividendos
    def _cantidad_antes_de(self, ticker: str, fecha: date) -> float:
        """Unidades en poder del inversionista antes de la fecha ex-dividendo."""
        comprado = sum(o.cantidad for o in self.operaciones
                       if o.activo.ticker == ticker and o.tipo == Operacion.COMPRA and o.fecha < fecha)
        salido = sum(o.cantidad for o in self.operaciones
                     if o.activo.ticker == ticker and o.tipo in Operacion.TIPOS_SALIDA_POSICION and o.fecha < fecha)
        return comprado - salido

    def dividendos_automaticos(self, dividendos: Dict[str, pd.Series], hoy: Optional[date] = None) -> List[Operacion]:
        """Genera operaciones de tipo Dividendo a partir de los dividendos históricos de yfinance."""
        hoy = hoy or date.today()
        generados: List[Operacion] = []
        for ticker, serie in dividendos.items():
            propias = [o for o in self.operaciones if o.activo.ticker == ticker and o.activo.cotiza_en_bolsa]
            if not propias:
                continue
            activo = propias[0].activo
            primera = min(o.fecha for o in propias)
            for marca, dps in serie.items():
                ex_dividendo = marca.date()
                if ex_dividendo < primera or ex_dividendo > hoy:
                    continue
                cantidad = self._cantidad_antes_de(ticker, ex_dividendo)
                if cantidad > self.TOLERANCIA:
                    generados.append(Operacion(ex_dividendo, "Dividendo", activo, cantidad, float(dps)))
        return generados

    # ------------------------------------------------------------------ resumen
    def resumen(self, precios_actuales: Dict[str, float], dividendos: Dict[str, pd.Series],
                hoy: Optional[date] = None) -> dict:
        """Información consolidada: invertido, valor actual, rentabilidad acumulada y E.A."""
        hoy = hoy or date.today()
        posiciones = self.posiciones(precios_actuales, hoy)
        auto = self.dividendos_automaticos(dividendos, hoy)
        todas = self.operaciones + auto

        total_invertido = sum(-o.flujo_caja() for o in todas if o.tipo == Operacion.COMPRA)
        ventas_netas = sum(o.flujo_caja() for o in todas if o.tipo in Operacion.TIPOS_SALIDA_POSICION)
        ingresos = sum(o.flujo_caja() for o in todas if o.tipo in Operacion.TIPOS_INGRESO)
        comisiones = sum(o.comision for o in todas)
        valor_actual = float(posiciones["Valor actual"].sum())
        ganancia = valor_actual + ventas_netas + ingresos - total_invertido

        flujos: List[Tuple[date, float]] = [(o.fecha, o.flujo_caja()) for o in todas]
        if valor_actual > 0:
            flujos.append((hoy, valor_actual))  # valor terminal del portafolio

        por_clase = posiciones.groupby("Clase")["Valor actual"].sum()
        return {
            "total_invertido": total_invertido,
            "valor_actual": valor_actual,
            "ventas_netas": ventas_netas,
            "ingresos": ingresos,
            "comisiones": comisiones,
            "ganancia_total": ganancia,
            "rent_acumulada": CalculadoraRentabilidad.rentabilidad_acumulada(
                total_invertido, valor_actual, ventas_netas + ingresos),
            "rent_ea": CalculadoraRentabilidad.tasa_efectiva_anual(flujos),
            "renta_fija": float(por_clase.get("Renta fija", 0.0)),
            "renta_variable": float(por_clase.get("Renta variable", 0.0)),
            "posiciones": posiciones,
            "ingresos_df": self._tabla_ingresos(todas),
        }

    @staticmethod
    def _tabla_ingresos(operaciones: List[Operacion]) -> pd.DataFrame:
        filas = [{"Fecha": o.fecha, "Tipo": o.tipo, "Ticker": o.activo.ticker,
                  "Unidades": o.cantidad, "Monto": o.flujo_caja()}
                 for o in operaciones if o.tipo in Operacion.TIPOS_INGRESO]
        df = pd.DataFrame(filas, columns=["Fecha", "Tipo", "Ticker", "Unidades", "Monto"])
        return df.sort_values("Fecha").reset_index(drop=True)
