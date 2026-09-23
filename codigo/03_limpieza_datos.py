# Autora: Amy Pamela Guadalupe Cordova
# Código de matrícula: 2024200501G
# Tema N.º 18 (S03 · Valor del dinero en el tiempo I): Valor presente del crédito hipotecario y su sensibilidad a la tasa de interés
# Fecha de extracción: 2026-09-23 (fecha de los datos crudos que limpia este script)

"""
03_limpieza_datos.py
--------------------
Toma el archivo crudo del script 01 y produce la base limpia del estudio.

Pasos:
  1. Convierte las fechas del BCRP ('04.Ene.21', 'Ene.2021', con 'Set' o 'Sep')
     a fechas reales.
  2. Convierte los 'n.d.' (dato no disponible) en vacíos y elimina los días
     incompletos. NO se rellena ningún valor: todo dato que queda existe
     tal cual en el BCRP.
  3. Detecta y elimina atípicos con el método IQR (3 × IQR, valores
     extremos) sobre los cambios diarios.
  4. Une la TEA hipotecaria mensual a cada día de su mes (armonización
     de frecuencias por la llave común 'fecha').
  5. Guarda la base procesada, la lista de atípicos, un resumen y el
     hash SHA-256.

La base procesada contiene SOLO series del BCRP, sin variables calculadas,
para que cualquier fila pueda cotejarse con la fuente oficial. Las
variables calculadas (TEA diaria estimada y valor presente) se generan en
04_analisis.py.
"""

# ---------------------------------------------------------------------------
# BLOQUE 1. Librerías
# ---------------------------------------------------------------------------
import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# BLOQUE 2. Parámetros del estudio (constantes, declarados en el artículo)
# ---------------------------------------------------------------------------
CODIGO_MATRICULA = "2024200501G"

# Atípicos: factor del rango intercuartílico. 3.0 = "valores extremos"
# (criterio de Tukey). Con 1.5 se eliminarían ~170 días de movimientos
# normales del mercado.
FACTOR_IQR = 3.0
# La tasa de referencia se excluye: solo cambia en las reuniones del BCRP,
# su IQR de cambios diarios es 0 y cualquier decisión saldría "atípica".
VARIABLES_IQR = ["rend_bono10_pen", "rend_bono10_usa", "tipo_cambio"]

# Meses en español tal como los escribe el BCRP (septiembre llega como
# 'Set' en series diarias y como 'Sep' en series mensuales).
MESES = {"Ene": 1, "Feb": 2, "Mar": 3, "Abr": 4, "May": 5, "Jun": 6,
         "Jul": 7, "Ago": 8, "Sep": 9, "Set": 9, "Oct": 10, "Nov": 11, "Dic": 12}

# ---------------------------------------------------------------------------
# BLOQUE 3. Rutas relativas a la carpeta del proyecto
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[1]
ARCHIVO_CRUDO = RAIZ / "datos_crudos" / f"datos_crudos_{CODIGO_MATRICULA}.csv"
CARPETA_PROCESADOS = RAIZ / "datos_procesados"
CARPETA_SALIDAS = RAIZ / "salidas"
ARCHIVO_PROCESADO = CARPETA_PROCESADOS / f"datos_procesados_{CODIGO_MATRICULA}.csv"
ARCHIVO_ATIPICOS = CARPETA_SALIDAS / f"atipicos_eliminados_{CODIGO_MATRICULA}.csv"
ARCHIVO_RESUMEN = CARPETA_SALIDAS / "resumen_limpieza.txt"
ARCHIVO_HASH = RAIZ / "hash_sha256.txt"
ARCHIVO_LOG = RAIZ / "log_ejecucion.txt"

CARPETA_PROCESADOS.mkdir(exist_ok=True)
CARPETA_SALIDAS.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# BLOQUE 4. Funciones
# ---------------------------------------------------------------------------
def registrar_log(mensaje: str) -> None:
    """Escribe una línea con fecha y hora en el log y en pantalla."""
    linea = f"{datetime.now():%Y-%m-%d %H:%M:%S} | 03_limpieza | {mensaje}"
    print(linea)
    with open(ARCHIVO_LOG, "a", encoding="utf-8") as archivo:
        archivo.write(linea + "\n")


def fecha_diaria(texto: pd.Series) -> pd.Series:
    """'04.Ene.21' -> 2021-01-04"""
    partes = texto.str.split(".", expand=True)
    return pd.to_datetime(dict(year=2000 + partes[2].astype(int),
                               month=partes[1].map(MESES),
                               day=partes[0].astype(int)))


def mes_de_periodo(texto: pd.Series) -> pd.Series:
    """'Ene.2021' -> '2021-01'"""
    partes = texto.str.split(".", expand=True)
    return partes[1].astype(int).astype(str) + "-" + partes[0].map(MESES).map("{:02d}".format)


# ---------------------------------------------------------------------------
# BLOQUE 5. Programa principal
# ---------------------------------------------------------------------------
def main() -> None:
    registrar_log("=== Inicio de limpieza ===")

    # 5.1 Leer el crudo como texto (tal cual salió del script 01)
    crudo = pd.read_csv(ARCHIVO_CRUDO, dtype=str)
    registrar_log(f"Crudo leído: {len(crudo)} filas")

    # 5.2 Series diarias: fechas reales, 'n.d.' -> vacío, formato ancho
    diarias = crudo[crudo["frecuencia"] == "diaria"].copy()
    diarias["fecha"] = fecha_diaria(diarias["periodo"])
    diarias["valor"] = pd.to_numeric(diarias["valor"], errors="coerce")  # 'n.d.' -> NaN
    base = diarias.pivot(index="fecha", columns="variable", values="valor").sort_index()
    filas_iniciales = len(base)

    # 5.3 Eliminar días con algún dato faltante (feriados y días sin negociación)
    dias_incompletos = int(base.isna().any(axis=1).sum())
    base = base.dropna()
    registrar_log(f"Días diarios: {filas_iniciales} | con 'n.d.': {dias_incompletos} | completos: {len(base)}")

    # 5.4 Atípicos: método IQR sobre el cambio diario de cada variable
    cambios = base[VARIABLES_IQR].diff()
    marcas = pd.DataFrame(False, index=base.index, columns=VARIABLES_IQR)
    limites = {}
    for variable in VARIABLES_IQR:
        q1, q3 = cambios[variable].quantile([0.25, 0.75])
        rango = q3 - q1
        inferior, superior = q1 - FACTOR_IQR * rango, q3 + FACTOR_IQR * rango
        limites[variable] = (inferior, superior)
        marcas[variable] = (cambios[variable] < inferior) | (cambios[variable] > superior)
        registrar_log(f"IQR {variable}: límites del cambio diario [{inferior:.4f}, {superior:.4f}] "
                      f"| atípicos: {int(marcas[variable].sum())}")

    es_atipico = marcas.any(axis=1)
    atipicos = base[es_atipico].copy()
    atipicos["cambio_bono10_pen"] = cambios.loc[es_atipico, "rend_bono10_pen"]
    atipicos["cambio_bono10_usa"] = cambios.loc[es_atipico, "rend_bono10_usa"]
    atipicos["cambio_tipo_cambio"] = cambios.loc[es_atipico, "tipo_cambio"]
    atipicos["variables_que_lo_marcan"] = marcas[es_atipico].apply(
        lambda fila: ", ".join(fila.index[fila]), axis=1)
    atipicos.reset_index().to_csv(ARCHIVO_ATIPICOS, index=False, encoding="utf-8", lineterminator="\n")
    base = base[~es_atipico]
    registrar_log(f"Días eliminados por atípicos: {int(es_atipico.sum())} | quedan: {len(base)}")

    # 5.5 Unir la TEA hipotecaria mensual a cada día de su mes
    mensual = crudo[crudo["variable"] == "tea_hipotecaria_pen"].copy()
    mensual["mes"] = mes_de_periodo(mensual["periodo"])
    mensual["tea_hipotecaria_mensual"] = pd.to_numeric(mensual["valor"], errors="coerce")
    base = base.reset_index()
    base["mes"] = base["fecha"].dt.strftime("%Y-%m")
    base = base.merge(mensual[["mes", "tea_hipotecaria_mensual"]], on="mes", how="left")
    sin_tea = int(base["tea_hipotecaria_mensual"].isna().sum())
    if sin_tea:
        registrar_log(f"Aviso: {sin_tea} días sin TEA mensual; se eliminan")
        base = base.dropna(subset=["tea_hipotecaria_mensual"])

    # 5.6 Orden final de columnas y guardado
    # Todas las columnas vienen del BCRP sin transformar sus valores.
    columnas = ["fecha", "tasa_referencia", "rend_bono10_usa", "tipo_cambio",
                "rend_bono10_pen", "tea_hipotecaria_mensual"]
    procesado = base[columnas].copy()
    procesado["fecha"] = procesado["fecha"].dt.strftime("%Y-%m-%d")
    procesado.to_csv(ARCHIVO_PROCESADO, index=False, encoding="utf-8", lineterminator="\n")

    # 5.7 Hash SHA-256 (huella digital del archivo procesado)
    huella = hashlib.sha256(ARCHIVO_PROCESADO.read_bytes()).hexdigest()
    ARCHIVO_HASH.write_text(f"SHA-256 de datos_procesados/{ARCHIVO_PROCESADO.name}:\n{huella}\n",
                            encoding="utf-8")

    # 5.8 Resumen para la sección de Materiales y métodos del artículo
    resumen = [
        "RESUMEN DE LIMPIEZA",
        f"Días en el crudo (series diarias): {filas_iniciales}",
        f"Días eliminados por 'n.d.': {dias_incompletos}",
        f"Días eliminados por atípicos (IQR x {FACTOR_IQR}): {int(es_atipico.sum())}",
        f"Filas finales de la base procesada: {len(procesado)}",
        f"Periodo: {procesado['fecha'].iloc[0]} a {procesado['fecha'].iloc[-1]}",
        "Límites IQR del cambio diario:",
    ] + [f"  {v}: [{a:.4f}, {b:.4f}]" for v, (a, b) in limites.items()]
    ARCHIVO_RESUMEN.write_text("\n".join(resumen) + "\n", encoding="utf-8")

    registrar_log(f"Base procesada: {ARCHIVO_PROCESADO.relative_to(RAIZ)} | "
                  f"{len(procesado)} filas x {procesado.shape[1]} columnas")
    registrar_log(f"SHA-256: {huella}")
    registrar_log("=== Fin de limpieza ===")


if __name__ == "__main__":
    main()
