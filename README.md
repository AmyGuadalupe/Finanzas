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
| `tea_hipotecaria_pen` | PN07848NM | Mensual | Tasa activa promedio bancaria, hipotecario MN (TEA %) | `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN07848NM/json/2018-1/2026-8/esp` |
| `rend_bono10_pen` | PD31893DD | Diaria | Rendimiento del bono del gobierno peruano a 10 años en S/ (%) | `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD31893DD/json/2018-1-2/2026-8-31/esp` |
| `tasa_referencia` | PD12301MD | Diaria | Tasa de referencia de la política monetaria (%) | `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD12301MD/json/2018-1-2/2026-8-31/esp` |
| `rend_bono10_usa` | PD04719XD | Diaria | Bonos del Tesoro EE.UU. a 10 años (%) | `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04719XD/json/2018-1-2/2026-8-31/esp` |
| `tipo_cambio` | PD04640PD | Diaria | Tipo de cambio sistema bancario SBS, venta (S/ por US$) | `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04640PD/json/2018-1-2/2026-8-31/esp` |

- **Periodo congelado:** `FECHA_INICIO = 2018-01-02` y `FECHA_CORTE = 2026-08-31` (constantes en `01_extraccion_api.py`).
- **Crédito representativo (supuesto):** S/ 300,000 a 240 meses, dentro de los límites oficiales del Nuevo
  Crédito Mivivienda (viviendas de S/ 64,200 a S/ 464,200, financiamiento hasta 90 %, plazo de 5 a 25 años;
  https://www.gob.pe/33425-programa-nuevo-credito-mivivienda). Se registra como columnas constantes en el crudo.
- **Segunda vía (SBS):** intento documentado en `incidencias_fuente.md`; no aporta datos (opcional en la Unidad I).

## Estructura

```
codigo/            01_extraccion_api.py · 02_scraping_web.py · 03_limpieza_datos.py · 04_analisis.py
datos_crudos/      datos_crudos_2024200501G.csv · json/ (respuestas originales de la API) · sbs/
datos_procesados/  datos_procesados_2024200501G.csv (2260 filas × 17 columnas)
salidas/           tablas (CSV), regresiones (TXT) y figuras (PNG) del artículo
diccionario_variables.md · fundamento_metodologico.md · README.md · requirements.txt · .env.example · log_ejecucion.txt · hash_sha256.txt · incidencias_fuente.md
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
63728e28983100f5e129622c0fda119deba6504ef2874a7cd75b83c2f9b1736e
```

## Resumen de la limpieza

```
RESUMEN DE LIMPIEZA
Días en el crudo (series diarias): 2260
Días con 'n.d.' completados con el último valor observado (LOCF): 123 (329 datos)
Filas finales de la base procesada: 2260
Periodo: 2018-01-02 a 2026-08-31
Crédito representativo: S/ 300,000 a 240 meses | TEA pactada (2018-01): 8.6595% | cuota: S/ 2,571.98
Máxima diferencia entre el promedio mensual de la TEA diaria y la TEA oficial: 0.1473 p.p.
Días con atípico extremo (marcados y winsorizados, no eliminados): 73
```

## Notas metodológicas

El respaldo bibliográfico de cada método (autor que lo propone y referencias en APA 7) está en
[`fundamento_metodologico.md`](fundamento_metodologico.md).

- Los días con `n.d.` (feriados y días sin negociación) se conservan y se completan con el último valor
  observado de cada serie (LOCF): con el mercado cerrado, la tasa se queda donde cerró. Se marcan en la
  columna `imputado`. No se usa el promedio del periodo porque crearía saltos artificiales.
- Atípicos: regla del diagrama de caja de Tukey sobre los cambios diarios de y, x2 y x3. Los leves
  (1.5 IQR) se conservan; los extremos (3 IQR) se marcan en la columna `atipico` y su cambio diario se
  winsoriza. Los niveles publicados por el BCRP no se modifican.
- `vp_credito` y `tea_hipotecaria_diaria` son variables **calculadas** (ver fórmulas en el diccionario).
- Regresiones por MCO con errores estándar HAC (Newey-West). El estudio no usa procesos aleatorios, por lo
  que no requiere semilla.
- Uso de IA: se utilizó un asistente de IA (Claude, Anthropic) como apoyo para escribir y depurar el código;
  la autora revisó, ejecutó y es responsable de todo el contenido.
