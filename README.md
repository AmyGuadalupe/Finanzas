# Valor presente del crédito hipotecario y su sensibilidad a la tasa de interés

- **Autora:** Amy Pamela Guadalupe Cordova
- **Código de matrícula:** 2024200501G
- **Curso:** Finanzas I (055D), Escuela Profesional de Economía, UNCP, 2026-II, Unidad I
- **Tema del temario:** N.º 18 (S03 · Valor del dinero en el tiempo I)
- **Repositorio:** https://github.com/AmyGuadalupe/Finanzas

## Objetivo

Calcular el valor presente de un crédito hipotecario representativo en soles y medir su
sensibilidad (elasticidad, duración y convexidad) ante variaciones de la TEA, y estimar
cómo dependen de la tasa de referencia del BCRP, de la tasa del Tesoro de EE.UU. a 10 años y
del tipo de cambio: **y = f(x1, x2, x3)**.

## Fuentes de datos y endpoints

Vía de extracción: **API REST de BCRPData** (Banco Central de Reserva del Perú). No requiere clave.

| Variable | Código | Frecuencia | Serie | Endpoint |
|---|---|---|---|---|
| `tea_hipotecaria_pen` | PN07848NM | Mensual | Tasa activa promedio bancaria, hipotecario MN (TEA %) | `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN07848NM/json/2021-1/2026-8/esp` |
| `rend_bono10_pen` | PD31893DD | Diaria | Rendimiento del bono del gobierno peruano a 10 años en S/ (%) | `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD31893DD/json/2021-1-4/2026-8-31/esp` |
| `tasa_referencia` | PD12301MD | Diaria | Tasa de referencia de la política monetaria (%) | `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD12301MD/json/2021-1-4/2026-8-31/esp` |
| `rend_bono10_usa` | PD04719XD | Diaria | Bonos del Tesoro EE.UU. a 10 años (%) | `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04719XD/json/2021-1-4/2026-8-31/esp` |
| `tipo_cambio` | PD04640PD | Diaria | Tipo de cambio sistema bancario SBS, venta (S/ por US$) | `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04640PD/json/2021-1-4/2026-8-31/esp` |

- **Periodo congelado:** `FECHA_INICIO = 2021-01-04` y `FECHA_CORTE = 2026-08-31` (constantes en `01_extraccion_api.py`).
- **Crédito representativo (supuesto):** S/ 300,000 a 240 meses, dentro de los límites oficiales del Nuevo
  Crédito Mivivienda (viviendas de S/ 64,200 a S/ 464,200, financiamiento hasta 90 %, plazo de 5 a 25 años;
  https://www.gob.pe/33425-programa-nuevo-credito-mivivienda). Se registra como columnas constantes en el crudo.
- **Segunda vía (SBS):** intento documentado en `incidencias_fuente.md`; no aporta datos (opcional en la Unidad I).

## Estructura

```
codigo/            01_extraccion_api.py · 02_scraping_web.py · 03_limpieza_datos.py · 04_analisis.py
datos_crudos/      datos_crudos_2024200501G.csv · json/ (respuestas originales de la API) · sbs/
datos_procesados/  datos_procesados_2024200501G.csv (1388 filas × 16 columnas)
salidas/           tablas (CSV), regresiones (TXT) y figuras (PNG) del artículo
diccionario_variables.md · README.md · requirements.txt · .env.example · log_ejecucion.txt · hash_sha256.txt · incidencias_fuente.md
```

## Orden de ejecución

Desde la carpeta raíz del proyecto:

```
pip install -r requirements.txt
python codigo/01_extraccion_api.py
python codigo/02_scraping_web.py
python codigo/03_limpieza_datos.py
python codigo/04_analisis.py
```

Los scripts usan rutas relativas a la carpeta del proyecto. El cuaderno `00_pipeline_colab.ipynb` ejecuta
la misma secuencia en Google Colab (allí la carpeta del proyecto es `/content/Finanzas`).

## Versiones

| Componente | Versión |
|---|---|
| Python | 3.13.15 |
| requests | 2.32.4 |
| pandas | 2.2.3 |
| numpy | 2.1.3 |
| statsmodels | 0.15.0 |
| matplotlib | 3.10.0 |

## Verificación de integridad

SHA-256 de `datos_procesados/datos_procesados_2024200501G.csv`:

```
d6df8261ae279d529f9c2aad04b89072bbc773ff99460ac565986005fca54133
```

## Resumen de la limpieza

```
RESUMEN DE LIMPIEZA
Días en el crudo (series diarias): 1476
Días eliminados por 'n.d.' (feriados): 88
Filas finales de la base procesada: 1388
Periodo: 2021-01-04 a 2026-08-31
Crédito representativo: S/ 300,000 a 240 meses | TEA pactada (2021-01): 7.3839% | cuota: S/ 2,352.12
Máxima diferencia entre el promedio mensual de la TEA diaria y la TEA oficial: 0.1478 p.p.
Días con atípico extremo (marcados y winsorizados, no eliminados): 27
```

## Notas metodológicas

- Los días con `n.d.` (feriados) se eliminan; no se rellena ningún valor extraído.
- Atípicos: regla del diagrama de caja de Tukey sobre los cambios diarios de y, x2 y x3. Los leves
  (1.5 IQR) se conservan; los extremos (3 IQR) se marcan en la columna `atipico` y su cambio diario se
  winsoriza. Los niveles publicados por el BCRP no se modifican.
- `vp_credito` y `tea_hipotecaria_diaria` son variables **calculadas** (ver fórmulas en el diccionario).
- Regresiones por MCO con errores estándar HAC (Newey-West). El estudio no usa procesos aleatorios, por lo
  que no requiere semilla.
- Uso de IA: se utilizó un asistente de IA (Claude, Anthropic) como apoyo para escribir y depurar el código;
  la autora revisó, ejecutó y es responsable de todo el contenido.
