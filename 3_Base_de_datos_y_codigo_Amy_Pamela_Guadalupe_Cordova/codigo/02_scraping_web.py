# Autora: Amy Pamela Guadalupe Cordova
# Código de matrícula: 2024200501G
# Tema N.º 18 (S03 · Valor del dinero en el tiempo I): Valor presente del crédito hipotecario y su sensibilidad a la tasa de interés
# Fecha de extracción: 2026-09-24 (actualizar si el script se ejecuta otro día)

"""
02_scraping_web.py
------------------
Intento documentado de rastreo del portal de la SBS (tasas hipotecarias por
empresa bancaria), segunda vía sugerida por el temario.

En la Unidad I la segunda vía es OPCIONAL (numeral 2.4.1 de la consigna).
Este script NO aporta datos al análisis: consulta el portal una sola vez,
revisa su robots.txt y deja evidencia real de la respuesta en:

  - datos_crudos/sbs/robots_sbs.txt        -> robots.txt tal como lo sirve la SBS
  - datos_crudos/sbs/respuesta_sbs.html    -> página tal como la devolvió el portal
  - incidencias_fuente.md                  -> registro de la incidencia (numeral 2.4.3)
  - log_ejecucion.txt                      -> fecha, hora y código HTTP

Buenas prácticas del numeral 2.4.8: User-Agent identificable, pausa entre
solicitudes y respeto del robots.txt.
"""

# ---------------------------------------------------------------------------
# BLOQUE 1. Librerías
# ---------------------------------------------------------------------------
import os
import time
from datetime import datetime
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# BLOQUE 2. Parámetros
# ---------------------------------------------------------------------------
URL_SBS = ("https://www.sbs.gob.pe/app/pp/EstadisticasSAEEPortal/Paginas/"
           "TIActivaTipoCreditoEmpresa.aspx?tip=B")
URL_ROBOTS = "https://www.sbs.gob.pe/robots.txt"
RUTA_INTERES = "/app/pp/EstadisticasSAEEPortal/"
PAUSA_SEGUNDOS = 2
TIEMPO_ESPERA = 60

CONTACTO = os.getenv("CONTACTO_EMAIL", "sin-contacto")
CABECERAS = {"User-Agent": f"UNCP-Finanzas-I/1.0 (investigacion academica; contacto: {CONTACTO})"}

# ---------------------------------------------------------------------------
# BLOQUE 3. Rutas relativas
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[1]
CARPETA_SBS = RAIZ / "datos_crudos" / "sbs"
ARCHIVO_INCIDENCIAS = RAIZ / "incidencias_fuente.md"
# Captura de pantalla tomada por la autora en su navegador (numeral 2.4.3).
# Se sube a mano a la carpeta 3 con este nombre; si existe, se inserta sola.
NOMBRES_CAPTURA = ["captura_sbs.png", "captura_sbs.jpg", "captura_sbs.jpeg"]
ARCHIVO_LOG = RAIZ / "log_ejecucion.txt"
CARPETA_SBS.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# BLOQUE 4. Funciones
# ---------------------------------------------------------------------------
def registrar_log(mensaje: str) -> None:
    linea = f"{datetime.now():%Y-%m-%d %H:%M:%S} | 02_scraping | {mensaje}"
    print(linea)
    with open(ARCHIVO_LOG, "a", encoding="utf-8") as archivo:
        archivo.write(linea + "\n")


def consultar(url: str) -> dict:
    """Hace UNA solicitud GET y devuelve lo observado (sin reintentos, para
    no insistir sobre un portal que restringe el acceso)."""
    resultado = {"url": url, "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    try:
        respuesta = requests.get(url, headers=CABECERAS, timeout=TIEMPO_ESPERA)
        resultado.update(codigo=respuesta.status_code, texto=respuesta.text,
                         tipo=respuesta.headers.get("Content-Type", "desconocido"))
    except requests.RequestException as error:
        resultado.update(codigo="sin respuesta", texto="", tipo="-", error=str(error))
    registrar_log(f"GET {url} | HTTP {resultado['codigo']} | {len(resultado['texto'])} caracteres")
    return resultado


def diagnosticar(pagina: dict, robots: dict) -> str:
    """Clasifica lo ocurrido con base en la respuesta real."""
    texto = pagina["texto"].lower()
    lineas_robots = [l.strip().lower() for l in robots["texto"].splitlines()]
    prohibida = any(l.startswith("disallow:") and l.split(":", 1)[1].strip()
                    and RUTA_INTERES.lower().startswith(l.split(":", 1)[1].strip())
                    for l in lineas_robots)
    if "error" in pagina:
        return f"No se obtuvo respuesta del portal (error de conexión: {pagina['error'][:150]})."
    if prohibida:
        return "La ruta de interés está prohibida en el robots.txt del portal."
    if pagina["codigo"] != 200:
        return f"El portal rechazó la solicitud automatizada (código {pagina['codigo']})."
    if "incapsula" in texto or "request unsuccessful" in texto:
        return "El portal respondió con una página de bloqueo del cortafuegos (WAF) en lugar de los datos."
    if "__viewstate" in texto:
        return ("El portal responde, pero es una aplicación ASP.NET con formulario dinámico: "
                "solo muestra el reporte de la fecha consultada y no ofrece una serie histórica "
                "descargable, por lo que no es viable construir con él una serie comparable.")
    return "El portal respondió, pero la página no contiene una tabla histórica aprovechable."


# ---------------------------------------------------------------------------
# BLOQUE 5. Programa principal
# ---------------------------------------------------------------------------
def main() -> None:
    registrar_log("=== Inicio del intento de rastreo SBS ===")
    robots = consultar(URL_ROBOTS)
    (CARPETA_SBS / "robots_sbs.txt").write_text(robots["texto"], encoding="utf-8")
    time.sleep(PAUSA_SEGUNDOS)

    pagina = consultar(URL_SBS)
    (CARPETA_SBS / "respuesta_sbs.html").write_text(pagina["texto"], encoding="utf-8")

    diagnostico = diagnosticar(pagina, robots)
    registrar_log(f"Diagnóstico: {diagnostico}")

    # Si la autora ya subió su captura de pantalla, se muestra en el registro
    captura = next((RAIZ / nombre for nombre in NOMBRES_CAPTURA if (RAIZ / nombre).exists()), None)
    if captura:
        fila_captura = f"Ver la sección *Captura de pantalla* (`{captura.name}`)"
        bloque_captura = ("\n## Captura de pantalla\n\nTomada por la autora al abrir el portal de la SBS en su "
                          f"navegador; la fecha y la hora se ven en la barra de tareas.\n\n"
                          f"![Captura de pantalla del portal de la SBS]({captura.name})\n")
        registrar_log(f"Captura de pantalla incluida: {captura.name}")
    else:
        fila_captura = "*(pendiente: subir `captura_sbs.png` a la carpeta 3)*"
        bloque_captura = ""

    ARCHIVO_INCIDENCIAS.write_text(f"""# Incidencias de fuente

## SBS: tasas de interés hipotecarias por empresa bancaria

| Campo | Detalle |
|---|---|
| URL consultada | {URL_SBS} |
| Fecha y hora de la consulta | {pagina['hora']} (hora del servidor de ejecución) |
| Código de respuesta HTTP | {pagina['codigo']} |
| Tipo de contenido recibido | {pagina['tipo']} |
| robots.txt | {URL_ROBOTS} (código {robots['codigo']}); copia en `datos_crudos/sbs/robots_sbs.txt` |
| Respuesta guardada | `datos_crudos/sbs/respuesta_sbs.html` |
| Diagnóstico | {diagnostico} |
| Captura de pantalla | {fila_captura} |
{bloque_captura}
## Decisión

La información de la SBS **no se incorpora a la base de datos**. En la Unidad I
la consigna exige al menos una vía automatizada y considera opcional la segunda
(numeral 2.4.1). La base del estudio se construye íntegramente con la API del
BCRP (script `01_extraccion_api.py`), cuyas series de tasas hipotecarias
provienen de la propia SBS según los metadatos de BCRPData.

Este registro se generó automáticamente al ejecutar `codigo/02_scraping_web.py`.
""", encoding="utf-8")
    registrar_log("Incidencia registrada en incidencias_fuente.md")
    registrar_log("=== Fin del intento de rastreo SBS ===")


if __name__ == "__main__":
    main()
