# Cálculos financieros

## Flujo de caja por operación
- Compra: `-(cantidad × precio + comisión)`
- Venta / Pago de capital: `+(cantidad × precio − comisión)`
- Dividendo / Interés: `+monto`

## Valoración
- **Acciones y ETF**: `cantidad × último cierre` (yfinance, `auto_adjust=False` para no contar dividendos dos veces).
- **CDT, TES, bonos**: `precio × (1 + tasa_EA)^(días/365)`, con días hasta `min(hoy, vencimiento)`.
  Si no capitaliza (paga cupones), se mantiene el valor de compra y los intereses se registran como "Interés".

## Dividendos automáticos
Para cada dividendo histórico: `unidades antes de la fecha ex-dividendo × dividendo por acción`.

## Rentabilidades
- Acumulada = `(valor actual + ventas netas + ingresos − total invertido) / total invertido`
- Efectiva anual (E.A.): tasa `r` que cumple `Σ flujo_i / (1+r)^(días_i/365) = 0` (XIRR), incluyendo el valor actual hoy.
- En periodos menores a unos meses la E.A. puede ser extrema; es una anualización matemática.

## Posiciones
FIFO: las ventas consumen primero los lotes más antiguos. El costo de cada lote incluye la comisión de compra.

## Proyección a 1 año (simulación)
CAGR histórico del precio + dividendos de los últimos 12 meses; Monte Carlo con la covarianza histórica.
