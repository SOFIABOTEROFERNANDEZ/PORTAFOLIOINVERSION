"""Pruebas unitarias de las clases de cálculo.
Ejecutar desde la raíz del proyecto:  python -m unittest discover -s tests -v
"""
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from portafolio_app.activo import Activo
from portafolio_app.calculadora_rentabilidad import CalculadoraRentabilidad
from portafolio_app.operacion import Operacion
from portafolio_app.portafolio import Portafolio
from portafolio_app.proyeccion_anual import ProyeccionAnual
from portafolio_app.simulador_montecarlo import SimuladorMonteCarlo
from portafolio_app.valorador_renta_fija import ValoradorRentaFija

KO = Activo("KO", "Coca-Cola", "Acción")
CDT = Activo("CDT 1", "CDT", "CDT")
HOY = date(2026, 11, 6)


class TestActivoYOperacion(unittest.TestCase):
    def test_clases(self):
        self.assertEqual(KO.clase, "Renta variable")
        self.assertEqual(CDT.clase, "Renta fija")
        self.assertTrue(KO.cotiza_en_bolsa)
        self.assertFalse(CDT.cotiza_en_bolsa)

    def test_flujos_con_comision(self):
        compra = Operacion(HOY, "Compra", KO, 10, 50, 2)
        venta = Operacion(HOY, "Venta", KO, 10, 60, 2)
        self.assertAlmostEqual(compra.flujo_caja(), -502)
        self.assertAlmostEqual(venta.flujo_caja(), 598)

    def test_ida_y_vuelta_dict(self):
        op = Operacion(HOY, "Compra", CDT, 1, 1000, 0, 0.1, HOY + timedelta(days=360), True)
        df = pd.DataFrame([op.a_dict()])
        self.assertEqual(Operacion.desde_dict(df.iloc[0].to_dict()), op)


class TestRentaFija(unittest.TestCase):
    def test_devengo_un_anio(self):
        v = ValoradorRentaFija.valor_unitario(1000, HOY - timedelta(days=365), 0.10, HOY + timedelta(days=100), HOY)
        self.assertAlmostEqual(v, 1100)

    def test_no_crece_despues_del_vencimiento(self):
        compra = HOY - timedelta(days=400)
        venc = compra + timedelta(days=365)
        self.assertAlmostEqual(ValoradorRentaFija.valor_unitario(1000, compra, 0.10, venc, HOY), 1100)

    def test_sin_capitalizacion(self):
        self.assertEqual(ValoradorRentaFija.valor_unitario(1000, HOY - timedelta(days=200), 0.1, None, HOY, False), 1000)


class TestRentabilidad(unittest.TestCase):
    def test_ea_simple(self):
        flujos = [(HOY - timedelta(days=365), -1000.0), (HOY, 1100.0)]
        self.assertAlmostEqual(CalculadoraRentabilidad.tasa_efectiva_anual(flujos), 0.10, places=6)

    def test_ea_sin_solucion(self):
        self.assertIsNone(CalculadoraRentabilidad.tasa_efectiva_anual([(HOY, -100.0)]))

    def test_acumulada(self):
        self.assertAlmostEqual(CalculadoraRentabilidad.rentabilidad_acumulada(1000, 1100, 50), 0.15)


class TestPortafolio(unittest.TestCase):
    def setUp(self):
        self.inicio = HOY - timedelta(days=365)
        self.p = Portafolio()
        self.p.agregar(Operacion(self.inicio, "Compra", KO, 10, 100, 5))
        self.p.agregar(Operacion(self.inicio + timedelta(days=10), "Compra", KO, 10, 110, 5))

    def test_no_permite_vender_de_mas(self):
        with self.assertRaises(ValueError):
            self.p.agregar(Operacion(HOY, "Venta", KO, 25, 120, 0))

    def test_fifo_y_posicion(self):
        self.p.agregar(Operacion(HOY - timedelta(days=30), "Venta", KO, 15, 120, 0))
        pos = self.p.posiciones({"KO": 130.0}, HOY)
        self.assertAlmostEqual(pos.loc[0, "Cantidad"], 5)
        # quedan 5 unidades del 2.º lote: costo unitario (10*110+5)/10 = 110.5
        self.assertAlmostEqual(pos.loc[0, "Costo"], 5 * 110.5)
        self.assertAlmostEqual(pos.loc[0, "Valor actual"], 650)

    def test_resumen_con_dividendos_y_ea(self):
        div = pd.Series([1.0, 1.0], index=pd.to_datetime([self.inicio + timedelta(days=100),
                                                          self.inicio + timedelta(days=200)]))
        r = self.p.resumen({"KO": 120.0}, {"KO": div}, HOY)
        self.assertAlmostEqual(r["total_invertido"], 1005 + 1105)
        self.assertAlmostEqual(r["valor_actual"], 20 * 120)
        # en ambas fechas ex-dividendo ya había 20 acciones (el 2.º lote se compró el día 10): 20 x 1.0 x 2
        self.assertAlmostEqual(r["ingresos"], 40)
        self.assertIsNotNone(r["rent_ea"])

    def test_dividendo_solo_con_acciones_previas_a_ex_dividendo(self):
        ex = self.inicio + timedelta(days=5)  # el 2.º lote se compra el día 10: no cuenta
        div = pd.Series([2.0], index=pd.to_datetime([ex]))
        auto = self.p.dividendos_automaticos({"KO": div}, HOY)
        self.assertEqual(len(auto), 1)
        self.assertAlmostEqual(auto[0].cantidad, 10)
        self.assertAlmostEqual(auto[0].valor_bruto, 20)

    def test_distribucion_renta_fija_variable(self):
        self.p.agregar(Operacion(self.inicio, "Compra", CDT, 1, 1000, 0, 0.10, HOY + timedelta(days=100), True))
        r = self.p.resumen({"KO": 100.0}, {}, HOY)
        self.assertAlmostEqual(r["renta_fija"], 1100)
        self.assertAlmostEqual(r["renta_variable"], 2000)


class TestProyeccionYSimulacion(unittest.TestCase):
    def setUp(self):
        idx = pd.bdate_range("2021-01-01", periods=1300)
        rng = np.random.default_rng(0)
        self.prices = pd.DataFrame({
            "KO": 50 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, len(idx)))),
            "NKE": 100 * np.exp(np.cumsum(rng.normal(0.0002, 0.015, len(idx)))),
        }, index=idx)
        ultimo = idx[-1]
        self.divs = {"KO": pd.Series([0.4] * 4, index=[ultimo - pd.Timedelta(days=d) for d in (300, 210, 120, 30)]),
                     "NKE": pd.Series(dtype=float)}

    def test_totales(self):
        pa = ProyeccionAnual()
        tabla = pa.tabla_por_activo(self.prices, self.divs, {}, {"KO": 0.6, "NKE": 0.4}, 10_000)
        tot = pa.totales(tabla, 10_000)
        self.assertAlmostEqual(tot["ganancia_total"], tot["ganancia_precio"] + tot["ganancia_dividendos"])
        ko = tabla[tabla.Ticker == "KO"].iloc[0]
        self.assertAlmostEqual(ko["Ganancia por dividendos"], ko["Acciones"] * 1.6)

    def test_simulacion(self):
        pa = ProyeccionAnual()
        tabla = pa.tabla_por_activo(self.prices, self.divs, {}, {"KO": 0.6, "NKE": 0.4}, 10_000)
        sim = SimuladorMonteCarlo(n_sims=200)
        sims, cov = sim.simular(self.prices, np.array([0.6, 0.4]), 10_000,
                                tabla["Rend. precio esperado"].values, tabla["Yield dividendos"].values)
        self.assertEqual(sims.shape, (200, 253))
        self.assertTrue(np.allclose(sims[:, 0], 10_000))


if __name__ == "__main__":
    unittest.main()
