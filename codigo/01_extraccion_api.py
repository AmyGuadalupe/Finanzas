# Autora: Amy Pamela Guadalupe Cordova
# Código de matrícula: 2024200501G
# Tema N.º 18 (S03 · Valor del dinero en el tiempo I): Valor presente del crédito hipotecario y su sensibilidad a la tasa de interés
# Fecha de extracción: 2026-09-22 (actualizar si el script se ejecuta otro día)

"""
01_extraccion_api.py
--------------------
Descarga desde la API REST del BCRP (BCRPData) las 5 series del estudio y
las guarda TAL COMO LLEGAN, sin modificar ningún valor:

  - datos_crudos/json/<codigo>.json          -> respuesta original de la API
  - datos_crudos/datos_crudos_2024200501G.csv -> las 5 series juntas (formato largo)
  - log_ejecucion.txt                        -> fecha, hora, código HTTP y filas de cada consulta

Endpoint (método GET, documentado en la guía oficial de BCRPData):
  https://estadisticas.bcrp.gob.pe/estadisticas/series/api/[código]/json/[inicio]/[fin]/esp
"""

# ---------------------------------------------------------------------------
# BLOQUE 1. Librerías
# ---------------------------------------------------------------------------
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# BLOQUE 2. Parámetros congelados de la consulta (NO usar fechas tipo "hoy")
# La consigna exige que FECHA_INICIO y FECHA_CORTE sean constantes para que
# el docente obtenga la misma base al volver a ejecutar el script.
# ---------------------------------------------------------------------------
FECHA_INICIO = "2021-01-04"   # primer día hábil de 2021
FECHA_CORTE = "2026-08-31"    # último mes con dato de la tasa hipotecaria
CODIGO_MATRICULA = "2024200501G"

# Series a descargar: nombre de la columna -> (código BCRP, frecuencia)
SERIES = {
    "tea_hipotecaria_pen": ("PN07848NM", "mensual"),  # ingrediente de y
    "rend_bono10_pen":     ("PD31893DD", "diaria"),   # ingrediente de y
    "tasa_referencia":     ("PD12301MD", "diaria"),   # x1
    "rend_bono10_usa":     ("PD04719XD", "diaria"),   # x2
    "tipo_cambio":         ("PD04640PD", "diaria"),   # x3
}

URL_BASE = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
PAUSA_SEGUNDOS = 1.5      # pausa entre consultas para no saturar el portal
REINTENTOS = 3            # intentos por serie si la conexión falla
TIEMPO_ESPERA = 60        # segundos máximos por consulta

# ---------------------------------------------------------------------------
# BLOQUE 3. Rutas relativas a la carpeta del proyecto
# Path(__file__) es la ubicación de este script; .parents[1] es la carpeta
# que contiene a /codigo. Así el script funciona en cualquier computadora,
# sin rutas absolutas del tipo C:\Users\...
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[1]
CARPETA_CRUDOS = RAIZ / "datos_crudos"
CARPETA_JSON = CARPETA_CRUDOS / "json"
ARCHIVO_LOG = RAIZ / "log_ejecucion.txt"
ARCHIVO_CRUDO = CARPETA_CRUDOS / f"datos_crudos_{CODIGO_MATRICULA}.csv"

CARPETA_JSON.mkdir(parents=True, exist_ok=True)

# User-Agent identificable (buena práctica exigida en el numeral 2.4.8).
# El correo de contacto se lee de una variable de entorno (ver .env.example).
CONTACTO = os.getenv("CONTACTO_EMAIL", "sin-contacto")
CABECERAS = {
    "User-Agent": f"UNCP-Finanzas-I/1.0 (investigacion academica; contacto: {CONTACTO})"
}


# ---------------------------------------------------------------------------
# BLOQUE 4. Funciones auxiliares
# ---------------------------------------------------------------------------
def registrar_log(mensaje: str) -> None:
    """Escribe una línea con fecha y hora en log_ejecucion.txt y en pantalla."""
    marca = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"{marca} | {mensaje}"
    print(linea)
    with open(ARCHIVO_LOG, "a", encoding="utf-8") as archivo:
        archivo.write(linea + "\n")


def formatear_periodo(fecha_iso: str, frecuencia: str) -> str:
    """Convierte '2021-01-04' al formato que pide la API.
    Diaria: AAAA-M-D (ej. 2021-1-4). Mensual: AAAA-M (ej. 2021-1)."""
    fecha = datetime.strptime(fecha_iso, "%Y-%m-%d")
    if frecuencia == "diaria":
        return f"{fecha.year}-{fecha.month}-{fecha.day}"
    return f"{fecha.year}-{fecha.month}"


def construir_url(codigo: str, frecuencia: str) -> str:
    """Arma la URL de la API para UNA sola serie."""
    inicio = formatear_periodo(FECHA_INICIO, frecuencia)
    fin = formatear_periodo(FECHA_CORTE, frecuencia)
    return f"{URL_BASE}/{codigo}/json/{inicio}/{fin}/esp"


def descargar_serie(nombre: str, codigo: str, frecuencia: str) -> pd.DataFrame:
    """Descarga una serie, guarda el JSON original y devuelve una tabla con
    los valores tal como vienen (texto, incluido 'n.d.')."""
    url = construir_url(codigo, frecuencia)

    for intento in range(1, REINTENTOS + 1):
        try:
            respuesta = requests.get(url, headers=CABECERAS, timeout=TIEMPO_ESPERA)
            estado = respuesta.status_code
            respuesta.raise_for_status()          # error si el código HTTP no es 2xx

            # A veces la respuesta trae caracteres antes del JSON: se recorta
            # desde la primera llave "{" para leerlo sin errores.
            texto = respuesta.text
            datos = json.loads(texto[texto.find("{"):])

            periodos = datos.get("periods", [])
            if not periodos:
                raise ValueError("la API respondió sin periodos (serie vacía)")

            # Guardar la respuesta original completa como evidencia primaria
            with open(CARPETA_JSON / f"{codigo}.json", "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=1)

            nombre_oficial = datos.get("config", {}).get("series", [{}])[0].get("name", "")
            tabla = pd.DataFrame({
                "variable": nombre,
                "codigo_bcrp": codigo,
                "frecuencia": frecuencia,
                "nombre_oficial": nombre_oficial,
                "periodo": [p.get("name") for p in periodos],
                "valor": [(p.get("values") or [None])[0] for p in periodos],
            })
            registrar_log(f"GET {codigo} ({nombre}) | HTTP {estado} | filas={len(tabla)} | {url}")
            return tabla

        except (requests.RequestException, ValueError) as error:
            registrar_log(f"ERROR {codigo} intento {intento}/{REINTENTOS} | {error}")
            time.sleep(PAUSA_SEGUNDOS * intento)  # espera un poco más en cada intento

    # Si llega aquí, fallaron todos los intentos: se detiene para no dejar
    # una base incompleta.
    registrar_log(f"FALLA DEFINITIVA en {codigo}. Se detiene la extracción.")
    sys.exit(1)


# ---------------------------------------------------------------------------
# BLOQUE 5. Programa principal
# ---------------------------------------------------------------------------
def main() -> None:
    registrar_log(f"=== Inicio de extracción | ventana {FECHA_INICIO} a {FECHA_CORTE} ===")

    tablas = []
    for nombre, (codigo, frecuencia) in SERIES.items():
        tablas.append(descargar_serie(nombre, codigo, frecuencia))
        time.sleep(PAUSA_SEGUNDOS)  # pausa entre consultas

    # Se apilan las 5 series una debajo de otra (formato largo). No se cambia
    # ningún valor: las fechas y los 'n.d.' quedan exactamente como los envía
    # el BCRP. La limpieza se hace recién en 03_limpieza_datos.py
    crudo = pd.concat(tablas, ignore_index=True)
    crudo.to_csv(ARCHIVO_CRUDO, index=False, encoding="utf-8")

    registrar_log(f"Archivo crudo guardado: {ARCHIVO_CRUDO.relative_to(RAIZ)} | filas totales={len(crudo)}")
    resumen = crudo.groupby("variable")["periodo"].count()
    for variable, filas in resumen.items():
        registrar_log(f"   {variable}: {filas} filas")
    registrar_log("=== Fin de extracción ===")


if __name__ == "__main__":
    main()
