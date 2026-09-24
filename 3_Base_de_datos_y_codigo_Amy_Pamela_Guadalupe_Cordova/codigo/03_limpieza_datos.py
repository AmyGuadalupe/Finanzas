# Autora: Amy Pamela Guadalupe Cordova
# Código de matrícula: 2024200501G
# Tema N.º 18 (S03 · Valor del dinero en el tiempo I): Valor presente del crédito hipotecario y su sensibilidad a la tasa de interés
# Fecha de extracción: 2026-09-24 (fecha de los datos crudos que limpia este script)

"""
03_limpieza_datos.py
--------------------
Toma el archivo crudo del script 01 y produce la base limpia del estudio:
id | dia | mes | anio | y | x1 | x2 | x3 | insumos de y | marcas | cambios diarios

Pasos:
  1. Convierte las fechas del BCRP ('04.Ene.21', 'Ene.2021', con 'Set' o 'Sep')
     y las separa en día, mes y año.
  2. 'n.d.' (dato no disponible, feriados y días sin negociación): el día se
     CONSERVA y se completa con el último valor observado (LOCF, "last
     observation carried forward"; Moritz y Bartz-Beielstein, 2017): con el
     mercado cerrado, la tasa se queda donde cerró. Esos días se marcan en la
     columna 'imputado'. No se usa el promedio del periodo porque distorsiona
     la serie (Little y Rubin, 2019) y crearía saltos artificiales (p. ej., la
     tasa de referencia era 0.25 % en 2021 y su promedio 2021-2026 es 4.73 %).
  3. Une la TEA hipotecaria mensual a cada día (llave: año-mes).
  4. Calcula la TEA hipotecaria diaria estimada con una serie relacionada
     diaria (Chow y Lin, 1971) y un margen suavizado sin discontinuidades
     artificiales (Denton, 1971), y la variable y (valor presente del
     crédito; Fabozzi y Fabozzi, 2021) con el monto y el plazo del crudo.
  5. Atípicos (regla del diagrama de caja de Tukey, 1977, sobre los cambios
     diarios de y, x2 y x3):
       - leves:    fuera de 1.5 × IQR -> se conservan (movimientos normales)
       - extremos: fuera de 3.0 × IQR -> se marcan y se WINSORIZAN
     Winsorizar = reemplazar el cambio extremo por el límite del bigote
     extremo (Dixon, 1960; Tukey, 1962). Los NIVELES publicados por el BCRP
     no se modifican.
  6. Guarda la base procesada, la tabla de atípicos, un resumen y el hash.
"""

# ---------------------------------------------------------------------------
# BLOQUE 1. Librerías
# ---------------------------------------------------------------------------
import hashlib
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# BLOQUE 2. Parámetros del estudio (constantes, declarados en el artículo)
# ---------------------------------------------------------------------------
CODIGO_MATRICULA = "2024200501G"
# El crédito se pacta en el primer mes del periodo (FECHA_INICIO del script 01):
# su TEA pactada es la TEA hipotecaria de ese mes. Así, si se amplía el
# periodo, el origen del crédito se ajusta solo.

# Regla de Tukey (1977), diagrama de caja: 1.5 × IQR = atípico leve; 3 × IQR = extremo
FACTOR_LEVE = 1.5
FACTOR_EXTREMO = 3.0
# Variables del modelo a las que se aplica la regla (sobre su cambio diario).
# La tasa de referencia (x1) se excluye: solo cambia en las reuniones del
# BCRP, su IQR de cambios diarios es 0 y cualquier decisión saldría "atípica".
VARIABLES_ATIPICOS = ["vp_credito", "rend_bono10_usa", "tipo_cambio"]

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
ARCHIVO_ATIPICOS = CARPETA_SALIDAS / f"tabla_atipicos_{CODIGO_MATRICULA}.csv"
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


def llave_mes(texto: pd.Series) -> pd.Series:
    """'Ene.2021' -> '2021-01'"""
    partes = texto.str.split(".", expand=True)
    return partes[1].astype(int).astype(str) + "-" + partes[0].map(MESES).map("{:02d}".format)


def tem(tea_porcentaje):
    """TEA en % -> tasa efectiva mensual en tanto por uno: (1 + TEA)^(1/12) - 1.
    No se divide entre 12 (eso sería una tasa nominal)."""
    return (1 + np.asarray(tea_porcentaje, dtype=float) / 100) ** (1 / 12) - 1


def cuota_francesa(monto, tea_porcentaje, meses):
    """Cuota fija del sistema francés: C = P·i / [1 - (1+i)^-n]"""
    i = tem(tea_porcentaje)
    return monto * i / (1 - (1 + i) ** -meses)


def valor_presente(cuota, tea_porcentaje, meses):
    """Valor presente de n cuotas iguales: VP = C·[1 - (1+i)^-n] / i"""
    i = tem(tea_porcentaje)
    return cuota * (1 - (1 + i) ** -meses) / i


def limites_tukey(serie: pd.Series, factor: float):
    """Límites del diagrama de caja: Q1 - k·IQR y Q3 + k·IQR."""
    q1, q3 = serie.quantile([0.25, 0.75])
    return q1 - factor * (q3 - q1), q3 + factor * (q3 - q1)


# ---------------------------------------------------------------------------
# BLOQUE 5. Programa principal
# ---------------------------------------------------------------------------
def main() -> None:
    registrar_log("=== Inicio de limpieza ===")

    # 5.1 Leer el crudo como texto (tal cual salió del script 01)
    crudo = pd.read_csv(ARCHIVO_CRUDO, dtype=str)
    monto = float(crudo["monto_credito"].iloc[0])
    plazo = int(crudo["plazo_meses"].iloc[0])
    registrar_log(f"Crudo leído: {len(crudo)} filas | crédito: S/ {monto:,.0f} a {plazo} meses")

    # 5.2 Series diarias: fechas reales, 'n.d.' -> vacío, una columna por serie
    diarias = crudo[crudo["frecuencia"] == "diaria"].copy()
    diarias["fecha"] = fecha_diaria(diarias["periodo"])
    diarias["valor"] = pd.to_numeric(diarias["valor"], errors="coerce")
    base = diarias.pivot(index="fecha", columns="variable", values="valor").sort_index()
    filas_iniciales = len(base)
    marca_imputado = base.isna().any(axis=1)
    dias_incompletos = int(marca_imputado.sum())
    datos_imputados = int(base.isna().sum().sum())
    # LOCF (Moritz y Bartz-Beielstein, 2017): cada vacío toma el último valor observado de su serie.
    # Si la serie empezara con vacío, se usa el primer valor disponible (bfill).
    base = base.ffill().bfill()
    base["imputado"] = marca_imputado.astype(int)
    base = base.reset_index()
    registrar_log(f"Días: {filas_iniciales} | con algún 'n.d.': {dias_incompletos} "
                  f"({datos_imputados} datos) -> completados con el último valor observado y marcados en 'imputado'")

    # 5.3 TEA hipotecaria mensual unida a cada día de su mes
    mensual = crudo[crudo["variable"] == "tea_hipotecaria_pen"].copy()
    mensual["llave_mes"] = llave_mes(mensual["periodo"])
    mensual["tea_hipotecaria_mensual"] = pd.to_numeric(mensual["valor"], errors="coerce")
    base["llave_mes"] = base["fecha"].dt.strftime("%Y-%m")
    base = base.merge(mensual[["llave_mes", "tea_hipotecaria_mensual"]], on="llave_mes", how="inner")

    # 5.4 TEA hipotecaria diaria estimada = bono peruano del día + margen hipotecario.
    #     Base metodológica: desagregación temporal con serie relacionada
    #     (Chow y Lin, 1971) y variante aditiva de Denton (1971), que mantiene
    #     suave la diferencia entre la serie estimada y la serie indicadora.
    #     Margen del mes = TEA hipotecaria oficial - promedio mensual del bono.
    #     El margen se ancla al día 15 de cada mes y avanza de forma gradual
    #     (interpolación lineal) para no crear saltos artificiales al cambiar
    #     de mes. El movimiento diario proviene solo del bono (dato real).
    margen_mes = (mensual.set_index("llave_mes")["tea_hipotecaria_mensual"]
                  - base[base["imputado"] == 0].groupby("llave_mes")["rend_bono10_pen"].mean()).dropna()
    anclas = pd.Series(margen_mes.values, index=pd.to_datetime([m + "-15" for m in margen_mes.index]))
    calendario = pd.date_range(min(anclas.index.min(), base["fecha"].min()),
                               max(anclas.index.max(), base["fecha"].max()), freq="D")
    margen_diario = anclas.reindex(calendario).interpolate("linear", limit_direction="both")
    base["tea_hipotecaria_diaria"] = base["rend_bono10_pen"] + margen_diario.reindex(base["fecha"]).values

    # 5.5 Variable y: valor presente del crédito representativo (anualidad;
    #     Fabozzi y Fabozzi, 2021).
    #     Cuota fija pactada con la TEA del mes de origen; se valoran siempre
    #     'plazo' cuotas por delante (plazo constante), de modo que lo único
    #     que cambia de un día a otro es la tasa de interés.
    MES_ORIGEN = base["llave_mes"].min()
    tea_pactada = float(mensual.loc[mensual["llave_mes"] == MES_ORIGEN, "tea_hipotecaria_mensual"].iloc[0])
    cuota = float(cuota_francesa(monto, tea_pactada, plazo))
    base["vp_credito"] = valor_presente(cuota, base["tea_hipotecaria_diaria"], plazo)
    registrar_log(f"TEA pactada ({MES_ORIGEN}) = {tea_pactada:.4f}% | cuota = S/ {cuota:,.2f}")

    # 5.6 Identificador y fecha separada
    base = base.sort_values("fecha").reset_index(drop=True)
    base["id"] = np.arange(1, len(base) + 1)
    base["dia"], base["mes"], base["anio"] = base["fecha"].dt.day, base["fecha"].dt.month, base["fecha"].dt.year

    # 5.7 Atípicos: regla del diagrama de caja sobre el cambio diario
    base["d_tasa_referencia"] = base["tasa_referencia"].diff()   # x1: sin tratamiento
    base["atipico"] = 0
    filas_tabla = []
    for variable in VARIABLES_ATIPICOS:
        cambio = base[variable].diff()
        inf_leve, sup_leve = limites_tukey(cambio, FACTOR_LEVE)
        inf_ext, sup_ext = limites_tukey(cambio, FACTOR_EXTREMO)
        es_leve = ((cambio < inf_leve) | (cambio > sup_leve)) & ~((cambio < inf_ext) | (cambio > sup_ext))
        es_extremo = (cambio < inf_ext) | (cambio > sup_ext)
        # Tratamiento: winsorización (Dixon, 1960; Tukey, 1962) en los límites extremos
        base[f"d_{variable}"] = cambio.clip(lower=inf_ext, upper=sup_ext)
        base.loc[es_extremo, "atipico"] = 1
        for i in base.index[es_extremo]:
            filas_tabla.append({"fecha": base.at[i, "fecha"].strftime("%Y-%m-%d"), "variable": variable,
                                "cambio_original": cambio.at[i], "limite_inferior": inf_ext,
                                "limite_superior": sup_ext, "cambio_tratado": base.at[i, f"d_{variable}"]})
        registrar_log(f"Atípicos en cambio de {variable}: leves={int(es_leve.sum())} (se conservan) | "
                      f"extremos={int(es_extremo.sum())} (winsorizados a [{inf_ext:.4f}, {sup_ext:.4f}])")

    tabla_atipicos = pd.DataFrame(filas_tabla).sort_values(["fecha", "variable"]).round(4)
    tabla_atipicos.to_csv(ARCHIVO_ATIPICOS, index=False, encoding="utf-8", lineterminator="\n")
    registrar_log(f"Días con al menos un atípico extremo: {int(base['atipico'].sum())} (se conservan, marcados)")

    # 5.8 Orden final de columnas y guardado
    columnas = ["id", "dia", "mes", "anio",
                "vp_credito",                                         # y
                "tasa_referencia", "rend_bono10_usa", "tipo_cambio",  # x1, x2, x3
                "tea_hipotecaria_mensual", "rend_bono10_pen",         # insumos extraídos
                "tea_hipotecaria_diaria",                             # insumo calculado
                "imputado",                                           # 1 = día con 'n.d.' completado (LOCF)
                "atipico",                                            # 1 = día con atípico extremo
                "d_vp_credito", "d_tasa_referencia",                  # cambios diarios
                "d_rend_bono10_usa", "d_tipo_cambio"]                 # (winsorizados en y, x2, x3)
    procesado = base[columnas].copy()
    redondeos = {"vp_credito": 2, "d_vp_credito": 2, "tea_hipotecaria_diaria": 6,
                 "d_tasa_referencia": 4, "d_rend_bono10_usa": 4, "d_tipo_cambio": 4}
    procesado = procesado.round(redondeos)
    procesado.to_csv(ARCHIVO_PROCESADO, index=False, encoding="utf-8", lineterminator="\n")

    # 5.9 Hash SHA-256 (huella digital del archivo procesado)
    huella = hashlib.sha256(ARCHIVO_PROCESADO.read_bytes()).hexdigest()
    ARCHIVO_HASH.write_text(f"SHA-256 de datos_procesados/{ARCHIVO_PROCESADO.name}:\n{huella}\n", encoding="utf-8")

    # 5.10 Resumen para la sección de Materiales y métodos
    promedio_vs_oficial = (base.groupby("llave_mes")["tea_hipotecaria_diaria"].mean()
                           - base.groupby("llave_mes")["tea_hipotecaria_mensual"].first()).abs().max()
    resumen = [
        "RESUMEN DE LIMPIEZA",
        f"Días en el crudo (series diarias): {filas_iniciales}",
        f"Días con 'n.d.' completados con el último valor observado (LOCF): {dias_incompletos} ({datos_imputados} datos)",
        f"Filas finales de la base procesada: {len(procesado)}",
        f"Periodo: {base['fecha'].iloc[0]:%Y-%m-%d} a {base['fecha'].iloc[-1]:%Y-%m-%d}",
        f"Crédito representativo: S/ {monto:,.0f} a {plazo} meses | TEA pactada ({MES_ORIGEN}): {tea_pactada:.4f}% | cuota: S/ {cuota:,.2f}",
        f"Máxima diferencia entre el promedio mensual de la TEA diaria y la TEA oficial: {promedio_vs_oficial:.4f} p.p.",
        f"Días con atípico extremo (marcados y winsorizados, no eliminados): {int(base['atipico'].sum())}",
    ]
    ARCHIVO_RESUMEN.write_text("\n".join(resumen) + "\n", encoding="utf-8")

    registrar_log(f"Base procesada: {ARCHIVO_PROCESADO.relative_to(RAIZ)} | {len(procesado)} filas x {procesado.shape[1]} columnas")
    registrar_log(f"SHA-256: {huella}")
    registrar_log("=== Fin de limpieza ===")


if __name__ == "__main__":
    main()
