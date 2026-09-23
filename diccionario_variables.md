# Diccionario de variables

Archivo: `datos_procesados/datos_procesados_2024200501G.csv` · Periodo: 2021-01-04 a 2026-08-31 · Fecha de corte: 2026-08-31

| Variable | Definición | Unidad | Frecuencia | Fuente | URL o endpoint |
|---|---|---|---|---|---|
| `id` | Número correlativo de la observación | entero | — | Calculada (orden cronológico) | — |
| `dia, mes, anio` | Fecha de la observación separada en día, mes y año | entero | Diaria | Calculada a partir del periodo del BCRP | — |
| `vp_credito` | **y.** Valor presente de 240 cuotas fijas del crédito representativo, descontadas a la TEA hipotecaria diaria: VP = C·[1−(1+i)^−n]/i, con i = (1+TEA)^(1/12)−1 | soles | Diaria | **Calculada** | — |
| `tasa_referencia` | **x1.** Tasa de referencia de la política monetaria | % | Diaria | BCRP (PD12301MD) | https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD12301MD/json/2021-1-4/2026-8-31/esp |
| `rend_bono10_usa` | **x2.** Rendimiento de los bonos del Tesoro de EE.UU. a 10 años | % | Diaria | BCRP (PD04719XD) | https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04719XD/json/2021-1-4/2026-8-31/esp |
| `tipo_cambio` | **x3.** Tipo de cambio del sistema bancario SBS, venta | S/ por US$ | Diaria | BCRP (PD04640PD) | https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04640PD/json/2021-1-4/2026-8-31/esp |
| `tea_hipotecaria_mensual` | Tasa activa promedio de las empresas bancarias, hipotecario en MN; se asigna a cada día de su mes | % (TEA) | Mensual | BCRP (PN07848NM), fuente original SBS | https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN07848NM/json/2021-1/2026-8/esp |
| `rend_bono10_pen` | Rendimiento del bono del gobierno peruano a 10 años en soles | % | Diaria | BCRP (PD31893DD) | https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD31893DD/json/2021-1-4/2026-8-31/esp |
| `tea_hipotecaria_diaria` | TEA hipotecaria diaria estimada = bono peruano del día + margen hipotecario (TEA mensual − promedio mensual del bono, anclado al día 15 e interpolado linealmente) | % (TEA) | Diaria | **Calculada** | — |
| `atipico` | 1 si el día tiene un cambio extremo (> 3 IQR) en y, x2 o x3; 0 en otro caso | 0/1 | Diaria | **Calculada** | — |
| `d_vp_credito` | Cambio diario de y, winsorizado en los límites de 3 IQR | soles | Diaria | **Calculada** | — |
| `d_tasa_referencia` | Cambio diario de x1 (sin winsorizar) | p.p. | Diaria | **Calculada** | — |
| `d_rend_bono10_usa` | Cambio diario de x2, winsorizado en los límites de 3 IQR | p.p. | Diaria | **Calculada** | — |
| `d_tipo_cambio` | Cambio diario de x3, winsorizado en los límites de 3 IQR | S/ por US$ | Diaria | **Calculada** | — |
| `monto_credito *(solo en el crudo)*` | Monto del crédito representativo | soles | Constante | Supuesto; límites del Nuevo Crédito Mivivienda | https://www.gob.pe/33425-programa-nuevo-credito-mivivienda |
| `plazo_meses *(solo en el crudo)*` | Plazo del crédito representativo | meses | Constante | Supuesto; límites del Nuevo Crédito Mivivienda | https://www.gob.pe/33425-programa-nuevo-credito-mivivienda |

Las variables marcadas como **Calculada** no existen en la fuente: se obtienen con las fórmulas indicadas a
partir de las variables extraídas del BCRP, que sí pueden cotejarse directamente con BCRPData.
