# ★ Seguimiento y Simulación de Portafolio de Inversión

Aplicación en **Python + Streamlit + Plotly + yfinance** para registrar, monitorear y evaluar un portafolio de
**renta variable** (acciones, ETF) y **renta fija** (CDT, TES, bonos), con una simulación a 1 año del portafolio.


## ★ Funcionalidades

| Vista | Qué hace |
|---|---|
| **💼 Seguimiento de portafolio** | Registra compras, ventas, dividendos, intereses y pagos de capital (fecha, cantidad, precio/valor y **comisión del broker**). Valora acciones/ETF con precios de mercado (yfinance) y CDT/TES/bonos por sus condiciones contractuales (tasa E.A., plazo, vencimiento). Calcula **valor total invertido, valor actual, rentabilidad acumulada, rentabilidad efectiva anual (E.A.)** y la **distribución renta fija vs. renta variable**. Importa/exporta CSV. |
| **🔮 Simulación a 1 año** | Proyección del rendimiento esperado (precio + dividendos), tarjetas de métricas, dona de distribución, histórico comparativo y simulación Monte Carlo.

## ★ Estructura del proyecto (una clase por archivo)

```
main.py                              # Archivo principal: carga el Dashboard (streamlit run main.py)
portafolio_app/
├── activo.py                        # class Activo
├── operacion.py                     # class Operacion
├── valorador_renta_fija.py          # class ValoradorRentaFija
├── calculadora_rentabilidad.py      # class CalculadoraRentabilidad
├── portafolio.py                    # class Portafolio
├── servicio_mercado.py              # class ServicioMercado
├── proyeccion_anual.py              # class ProyeccionAnual
├── simulador_montecarlo.py          # class SimuladorMonteCarlo
├── graficos.py                      # class Graficos
└── dashboard.py                     # class Dashboard
tests/test_calculos.py               # pruebas unitarias de los cálculos
docs/                                # diagrama UML (png + mermaid), generador y wiki
scripts/crear_historial_git.sh       # crea ramas y commits del repositorio
```

## ★ Instalación y ejecución

```bash
git clone <URL-DEL-REPOSITORIO>
cd seguimiento_portafolio
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run main.py
```

Se abre en `http://localhost:8501`. Requiere conexión a internet (Yahoo Finance).
