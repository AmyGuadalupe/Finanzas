# Verificación de los datos contra la fuente oficial

- **Fecha y hora de esta verificación:** 2026-09-25 03:29:14
- **Extracción original (según log_ejecucion.txt):** 2026-09-25 03:28:12
- **Ventana consultada:** 2018-01-02 a 2026-08-31
- **Fuente:** API de BCRPData, https://estadisticas.bcrp.gob.pe/estadisticas/series/api

## Veredicto

**APROBADO: todos los datos extraídos coinciden con la fuente oficial (BCRPData).**

| Prueba | Qué comprueba | Resultado |
|---|---|---|
| 1. Integridad | El SHA-256 de `datos_procesados` coincide con el declarado | ✔ cumple |
| 2. Crudo vs. fuente | Cada valor de `datos_crudos` es igual al publicado hoy por el BCRP (100.00 %) | ✔ cumple |
| 3. Procesado vs. fuente | Variables extraídas iguales a la fuente; días 'n.d.' con el último valor observado | ✔ cumple |
| 4. Calculadas | `vp_credito` recalculado (diferencia máx. S/ 0.0169) y cambio diario de x1 | ✔ cumple |
| 5. Muestra al azar | 10 filas elegidas con semilla 501 (matrícula) | ✔ cumple |

Huella declarada: `63728e28983100f5e129622c0fda119deba6504ef2874a7cd75b83c2f9b1736e`
Huella actual: `63728e28983100f5e129622c0fda119deba6504ef2874a7cd75b83c2f9b1736e`

## Prueba 2. Datos crudos frente a la API en vivo

| Variable | Código | Frecuencia | Celdas | Coinciden | % |
|---|---|---|---|---|---|
| `tea_hipotecaria_pen` | PN07848NM | mensual | 104 | 104 | 100.00 % |
| `rend_bono10_pen` | PD31893DD | diaria | 2260 | 2260 | 100.00 % |
| `tasa_referencia` | PD12301MD | diaria | 2260 | 2260 | 100.00 % |
| `rend_bono10_usa` | PD04719XD | diaria | 2260 | 2260 | 100.00 % |
| `tipo_cambio` | PD04640PD | diaria | 2260 | 2260 | 100.00 % |

## Prueba 3. Datos procesados frente a la API en vivo

| Columna | Código | Iguales a la fuente | 'n.d.' rellenados correctamente (LOCF) | No coinciden |
|---|---|---|---|---|
| `rend_bono10_pen` | PD31893DD | 2139 | 121 | 0 |
| `tasa_referencia` | PD12301MD | 2159 | 101 | 0 |
| `rend_bono10_usa` | PD04719XD | 2256 | 4 | 0 |
| `tipo_cambio` | PD04640PD | 2157 | 103 | 0 |
| `tea_hipotecaria_mensual` | PN07848NM | 2260 | 0 | 0 |

La marca `imputado` es correcta en 2260 de 2260 días.
Diferencia máxima entre el promedio mensual de la TEA diaria estimada y la TEA oficial: 0.1473 p.p.

## Prueba 5. Muestra al azar para el cotejo manual

Cada fila de `muestra_cotejo_2024200501G.csv` trae el enlace de la API para abrirlo en el navegador.

| id | Fecha | Columna | En la base | En la fuente | Resultado |
|---|---|---|---|---|---|
| 32 | 2018-02-14 | `tea_hipotecaria_mensual` | 8.61268669029993 | 8.61268669029993 | coincide |
| 32 | 2018-02-14 | `rend_bono10_pen` | 4.8 | 4.8 | coincide |
| 32 | 2018-02-14 | `tasa_referencia` | 3.0 | 3 | coincide |
| 32 | 2018-02-14 | `rend_bono10_usa` | 2.903 | 2.903 | coincide |
| 32 | 2018-02-14 | `tipo_cambio` | 3.27 | 3.27 | coincide |
| 946 | 2021-08-17 | `tea_hipotecaria_mensual` | 6.79395314309815 | 6.79395314309815 | coincide |
| 946 | 2021-08-17 | `rend_bono10_pen` | 6.49 | 6.49 | coincide |
| 946 | 2021-08-17 | `tasa_referencia` | 0.5 | 0.5 | coincide |
| 946 | 2021-08-17 | `rend_bono10_usa` | 1.267 | 1.267 | coincide |
| 946 | 2021-08-17 | `tipo_cambio` | 4.089 | 4.089 | coincide |
| 974 | 2021-09-24 | `tea_hipotecaria_mensual` | 6.74763122700596 | 6.74763122700596 | coincide |
| 974 | 2021-09-24 | `rend_bono10_pen` | 6.3 | 6.3 | coincide |
| 974 | 2021-09-24 | `tasa_referencia` | 1.0 | 1 | coincide |
| 974 | 2021-09-24 | `rend_bono10_usa` | 1.453 | 1.453 | coincide |
| 974 | 2021-09-24 | `tipo_cambio` | 4.111 | 4.111 | coincide |
| 1013 | 2021-11-18 | `tea_hipotecaria_mensual` | 6.69381541134265 | 6.69381541134265 | coincide |
| 1013 | 2021-11-18 | `rend_bono10_pen` | 5.87 | 5.87 | coincide |
| 1013 | 2021-11-18 | `tasa_referencia` | 2.0 | 2 | coincide |
| 1013 | 2021-11-18 | `rend_bono10_usa` | 1.587 | 1.587 | coincide |
| 1013 | 2021-11-18 | `tipo_cambio` | 4.02 | 4.02 | coincide |
| 1263 | 2022-11-03 | `tea_hipotecaria_mensual` | 6.83356400159313 | 6.83356400159313 | coincide |
| 1263 | 2022-11-03 | `rend_bono10_pen` | 8.24 | 8.24 | coincide |
| 1263 | 2022-11-03 | `tasa_referencia` | 7.0 | 7 | coincide |
| 1263 | 2022-11-03 | `rend_bono10_usa` | 4.149 | 4.149 | coincide |
| 1263 | 2022-11-03 | `tipo_cambio` | 3.973 | 3.973 | coincide |
| 1442 | 2023-07-12 | `tea_hipotecaria_mensual` | 7.11581081328546 | 7.11581081328546 | coincide |
| 1442 | 2023-07-12 | `rend_bono10_pen` | 6.8 | n.d. | n.d. en la fuente: último valor observado (imputado = 1) |
| 1442 | 2023-07-12 | `tasa_referencia` | 7.75 | 7.75 | coincide |
| 1442 | 2023-07-12 | `rend_bono10_usa` | 3.861 | 3.861 | coincide |
| 1442 | 2023-07-12 | `tipo_cambio` | 3.599 | 3.599 | coincide |
| 1712 | 2024-07-24 | `tea_hipotecaria_mensual` | 7.37119365001268 | 7.37119365001268 | coincide |
| 1712 | 2024-07-24 | `rend_bono10_pen` | 6.98 | 6.98 | coincide |
| 1712 | 2024-07-24 | `tasa_referencia` | 5.75 | 5.75 | coincide |
| 1712 | 2024-07-24 | `rend_bono10_usa` | 4.285 | 4.285 | coincide |
| 1712 | 2024-07-24 | `tipo_cambio` | 3.778 | 3.778 | coincide |
| 1947 | 2025-06-18 | `tea_hipotecaria_mensual` | 7.4430846579992 | 7.4430846579992 | coincide |
| 1947 | 2025-06-18 | `rend_bono10_pen` | 6.39 | 6.39 | coincide |
| 1947 | 2025-06-18 | `tasa_referencia` | 4.5 | 4.5 | coincide |
| 1947 | 2025-06-18 | `rend_bono10_usa` | 4.393 | 4.393 | coincide |
| 1947 | 2025-06-18 | `tipo_cambio` | 3.604 | 3.604 | coincide |
| 2025 | 2025-10-06 | `tea_hipotecaria_mensual` | 7.45040722530117 | 7.45040722530117 | coincide |
| 2025 | 2025-10-06 | `rend_bono10_pen` | 6.15 | 6.15 | coincide |
| 2025 | 2025-10-06 | `tasa_referencia` | 4.25 | 4.25 | coincide |
| 2025 | 2025-10-06 | `rend_bono10_usa` | 4.154 | 4.154 | coincide |
| 2025 | 2025-10-06 | `tipo_cambio` | 3.465 | 3.465 | coincide |
| 2244 | 2026-08-07 | `tea_hipotecaria_mensual` | 7.47497280199697 | 7.47497280199697 | coincide |
| 2244 | 2026-08-07 | `rend_bono10_pen` | 6.15 | 6.15 | coincide |
| 2244 | 2026-08-07 | `tasa_referencia` | 4.25 | 4.25 | coincide |
| 2244 | 2026-08-07 | `rend_bono10_usa` | 4.646 | 4.646 | coincide |
| 2244 | 2026-08-07 | `tipo_cambio` | 3.391 | 3.391 | coincide |

## Diferencias encontradas (máximo 20)

- Ninguna.

Este informe se generó automáticamente al ejecutar `codigo/05_verificacion_fuente.py`.
