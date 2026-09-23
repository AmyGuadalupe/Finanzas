# Incidencias de fuente

## SBS: tasas de interés hipotecarias por empresa bancaria

| Campo | Detalle |
|---|---|
| URL consultada | https://www.sbs.gob.pe/app/pp/EstadisticasSAEEPortal/Paginas/TIActivaTipoCreditoEmpresa.aspx?tip=B |
| Fecha y hora de la consulta | 2026-09-23 08:22:55 (hora del servidor de ejecución) |
| Código de respuesta HTTP | 200 |
| Tipo de contenido recibido | text/html; charset=utf-8 |
| robots.txt | https://www.sbs.gob.pe/robots.txt (código 200); copia en `datos_crudos/sbs/robots_sbs.txt` |
| Respuesta guardada | `datos_crudos/sbs/respuesta_sbs.html` |
| Diagnóstico | El portal responde, pero es una aplicación ASP.NET con formulario dinámico: solo muestra el reporte de la fecha consultada y no ofrece una serie histórica descargable, por lo que no es viable construir con él una serie comparable. |
| Captura de pantalla | *(agregar aquí la captura tomada por la autora al intentar la consulta)* |

## Decisión

La información de la SBS **no se incorpora a la base de datos**. En la Unidad I
la consigna exige al menos una vía automatizada y considera opcional la segunda
(numeral 2.4.1). La base del estudio se construye íntegramente con la API del
BCRP (script `01_extraccion_api.py`), cuyas series de tasas hipotecarias
provienen de la propia SBS según los metadatos de BCRPData.

Este registro se generó automáticamente al ejecutar `codigo/02_scraping_web.py`.
