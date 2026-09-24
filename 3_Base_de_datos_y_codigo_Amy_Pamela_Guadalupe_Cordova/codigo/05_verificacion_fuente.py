# Autora: Amy Pamela Guadalupe Cordova
# Código de matrícula: 2024200501G
# Tema N.º 18 (S03 · Valor del dinero en el tiempo I): Valor presente del crédito hipotecario y su sensibilidad a la tasa de interés
# Fecha de extracción: 2026-09-24 (fecha de los datos que verifica este script)

"""
05_verificacion_fuente.py
-------------------------
Comprueba que los datos del proyecto provienen de la fuente oficial. Vuelve a
consultar EN VIVO la API del BCRP (una serie a la vez) y compara, SIN MODIFICAR
ningún archivo de datos:

  Prueba 1. Integridad: el SHA-256 de datos_procesados coincide con hash_sha256.txt
  Prueba 2. Crudo vs. fuente: cada valor de datos_crudos es idéntico al que
            publica el BCRP, incluidos los 'n.d.'
  Prueba 3. Procesado vs. fuente: cada variable extraída en datos_procesados es
            igual a la fuente. En los días 'n.d.' se comprueba que el valor sea
            el último observado (LOCF) y que el día esté marcado con imputado = 1
  Prueba 4. Variables calculadas: se recalcula vp_credito con la fórmula de la
            anualidad y el cambio diario de la tasa de referencia
  Prueba 5. Muestra al azar de 10 filas, como la que tomará el docente
            (numeral 2.4.6), con el enlace de la API para cotejarlas a mano

Resultados:
  - salidas/verificacion_fuente.md          -> informe con el veredicto
  - salidas/muestra_cotejo_2024200501G.csv  -> las 10 filas cotejadas
  - log_ejecucion.txt                       -> fecha, hora y código HTTP
"""

# ---------------------------------------------------------------------------
# BLOQUE 1. Librerías
# ---------------------------------------------------------------------------
import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# ---------------------------------------------------------------------------
# BLOQUE 2. Parámetros (los mismos del script 01: se verifica la misma consulta)
# ---------------------------------------------------------------------------
FECHA_INICIO = "2018-01-02"
FECHA_CORTE = "2026-08-31"
CODIGO_MATRICULA = "2024200501G"

# Semilla de la muestra al azar: últimos cuatro dígitos de la matrícula
# (2024200501G -> 0501), como exige el numeral 2.4.4 de la consigna.
SEMILLA = 501
TAMANO_MUESTRA = 10

TOLERANCIA = 1e-9     # los valores extraídos deben ser idénticos
TOLERANCIA_VP = 0.05  # soles: la TEA diaria se guardó con 6 decimales (redondeo)
UMBRAL_EQUIVALENCIA = 95.0   # % de celdas que deben coincidir (numeral 2.4.5)

URL_BASE = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
PAUSA_SEGUNDOS = 1.5
REINTENTOS = 3
TIEMPO_ESPERA = 60

# Nombre que tiene cada serie del crudo dentro de datos_procesados
# (la TEA mensual cambia de nombre; las demás conservan el suyo)
COLUMNA_EN_PROCESADO = {"tea_hipotecaria_pen": "tea_hipotecaria_mensual"}

MESES = {"Ene": 1, "Feb": 2, "Mar": 3, "Abr": 4, "May": 5, "Jun": 6,
         "Jul": 7, "Ago": 8, "Sep": 9, "Set": 9, "Oct": 10, "Nov": 11, "Dic": 12}

# ---------------------------------------------------------------------------
# BLOQUE 3. Rutas relativas a la carpeta del proyecto
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[1]
ARCHIVO_CRUDO = RAIZ / "datos_crudos" / f"datos_crudos_{CODIGO_MATRICULA}.csv"
ARCHIVO_PROCESADO = RAIZ / "datos_procesados" / f"datos_procesados_{CODIGO_MATRICULA}.csv"
ARCHIVO_HASH = RAIZ / "hash_sha256.txt"
ARCHIVO_LOG = RAIZ / "log_ejecucion.txt"
CARPETA_SALIDAS = RAIZ / "salidas"
ARCHIVO_INFORME = CARPETA_SALIDAS / "verificacion_fuente.md"
ARCHIVO_MUESTRA = CARPETA_SALIDAS / f"muestra_cotejo_{CODIGO_MATRICULA}.csv"
CARPETA_SALIDAS.mkdir(exist_ok=True)

CONTACTO = os.getenv("CONTACTO_EMAIL", "sin-contacto")
CABECERAS = {"User-Agent": f"UNCP-Finanzas-I/1.0 (investigacion academica; contacto: {CONTACTO})"}


# ---------------------------------------------------------------------------
# BLOQUE 4. Funciones
# ---------------------------------------------------------------------------
def registrar_log(mensaje: str) -> None:
    """Escribe una línea con fecha y hora en el log y en pantalla."""
    linea = f"{datetime.now():%Y-%m-%d %H:%M:%S} | 05_verificacion | {mensaje}"
    print(linea)
    with open(ARCHIVO_LOG, "a", encoding="utf-8") as archivo:
        archivo.write(linea + "\n")


def formatear_periodo(fecha: datetime, frecuencia: str) -> str:
    """Formato de fecha de la API: diaria AAAA-M-D, mensual AAAA-M."""
    if frecuencia == "diaria":
        return f"{fecha.year}-{fecha.month}-{fecha.day}"
    return f"{fecha.year}-{fecha.month}"


def construir_url(codigo: str, frecuencia: str, inicio: datetime, fin: datetime) -> str:
    return (f"{URL_BASE}/{codigo}/json/{formatear_periodo(inicio, frecuencia)}/"
            f"{formatear_periodo(fin, frecuencia)}/esp")


def consultar_fuente(codigo: str, frecuencia: str):
    """Descarga UNA serie completa de la API y devuelve {periodo: valor en texto}.
    Si la API no responde tras los reintentos, devuelve None (la prueba queda
    como 'no verificada', no como fallida)."""
    url = construir_url(codigo, frecuencia, datetime.strptime(FECHA_INICIO, "%Y-%m-%d"),
                        datetime.strptime(FECHA_CORTE, "%Y-%m-%d"))
    for intento in range(1, REINTENTOS + 1):
        try:
            respuesta = requests.get(url, headers=CABECERAS, timeout=TIEMPO_ESPERA)
            respuesta.raise_for_status()
            texto = respuesta.text
            datos = json.loads(texto[texto.find("{"):])
            periodos = datos.get("periods", [])
            registrar_log(f"GET {codigo} | HTTP {respuesta.status_code} | filas={len(periodos)}")
            return {p.get("name"): str((p.get("values") or [""])[0]) for p in periodos}
        except (requests.RequestException, ValueError) as error:
            registrar_log(f"ERROR {codigo} intento {intento}/{REINTENTOS} | {error}")
            time.sleep(PAUSA_SEGUNDOS * intento)
    return None


def a_numero(texto) -> float:
    """'3.552' -> 3.552 ; 'n.d.' o vacío -> NaN (dato no disponible)."""
    try:
        return float(texto)
    except (TypeError, ValueError):
        return np.nan


def son_iguales(a: float, b: float, tolerancia: float = TOLERANCIA) -> bool:
    """Dos valores coinciden si ambos son 'n.d.' o si son numéricamente iguales."""
    if np.isnan(a) and np.isnan(b):
        return True
    if np.isnan(a) or np.isnan(b):
        return False
    return abs(a - b) <= tolerancia


def periodo_a_fecha(periodo: str) -> pd.Timestamp:
    """'04.Ene.21' -> 2021-01-04"""
    dia, mes, anio = periodo.split(".")
    return pd.Timestamp(year=2000 + int(anio), month=MESES[mes], day=int(dia))


def periodo_a_mes(periodo: str) -> str:
    """'Ene.2021' -> '2021-01'"""
    mes, anio = periodo.split(".")
    return f"{int(anio)}-{MESES[mes]:02d}"


def tem(tea_porcentaje):
    """TEA en % -> tasa efectiva mensual: (1 + TEA)^(1/12) - 1 (igual que en 03)."""
    return (1 + np.asarray(tea_porcentaje, dtype=float) / 100) ** (1 / 12) - 1


def cuota_francesa(monto, tea_porcentaje, meses):
    i = tem(tea_porcentaje)
    return monto * i / (1 - (1 + i) ** -meses)


def valor_presente(cuota, tea_porcentaje, meses):
    i = tem(tea_porcentaje)
    return cuota * (1 - (1 + i) ** -meses) / i


def hora_extraccion_original() -> str:
    """Busca en el log la hora de la última extracción del script 01 (prueba de
    la fecha original si el BCRP revisara sus datos; numeral 2.4.5)."""
    if not ARCHIVO_LOG.exists():
        return "no registrada"
    lineas = [l for l in ARCHIVO_LOG.read_text(encoding="utf-8").splitlines()
              if "Inicio de extracción" in l]
    return lineas[-1].split(" | ")[0] if lineas else "no registrada"


# ---------------------------------------------------------------------------
# BLOQUE 5. Programa principal
# ---------------------------------------------------------------------------
def main() -> None:
    registrar_log("=== Inicio de la verificación contra la fuente ===")
    # keep_default_na=False: los 'n.d.' del crudo se leen como texto, tal cual
    crudo = pd.read_csv(ARCHIVO_CRUDO, dtype=str, keep_default_na=False)
    procesado = pd.read_csv(ARCHIVO_PROCESADO)
    procesado["fecha"] = pd.to_datetime(dict(year=procesado["anio"], month=procesado["mes"],
                                             day=procesado["dia"]))
    procesado["llave_mes"] = procesado["fecha"].dt.strftime("%Y-%m")
    series = crudo[["variable", "codigo_bcrp", "frecuencia"]].drop_duplicates().to_dict("records")
    informe = []

    # ------------------ Prueba 1. Integridad (hash SHA-256) --------------------
    huella_actual = hashlib.sha256(ARCHIVO_PROCESADO.read_bytes()).hexdigest()
    huella_declarada = ARCHIVO_HASH.read_text(encoding="utf-8").strip().splitlines()[-1].strip()
    prueba1 = huella_actual == huella_declarada
    registrar_log(f"Prueba 1 (hash): {'OK' if prueba1 else 'NO COINCIDE'}")

    # ------------------ Prueba 2. Crudo vs. fuente en vivo ---------------------
    fuentes, filas_p2, discrepancias_p2 = {}, [], []
    for s in series:
        fuente = consultar_fuente(s["codigo_bcrp"], s["frecuencia"])
        time.sleep(PAUSA_SEGUNDOS)
        fuentes[s["variable"]] = fuente
        del_crudo = crudo[crudo["variable"] == s["variable"]]
        crudo_dict = dict(zip(del_crudo["periodo"], del_crudo["valor"]))
        if fuente is None:
            filas_p2.append({**s, "celdas": len(crudo_dict), "coinciden": None, "pct": None})
            continue
        periodos = sorted(set(crudo_dict) | set(fuente))
        coinciden = 0
        for p in periodos:
            if p in crudo_dict and p in fuente and son_iguales(a_numero(crudo_dict[p]), a_numero(fuente[p])):
                coinciden += 1
            else:
                discrepancias_p2.append(f"{s['variable']} {p}: crudo={crudo_dict.get(p, '(no está)')} "
                                        f"| fuente={fuente.get(p, '(no está)')}")
        filas_p2.append({**s, "celdas": len(periodos), "coinciden": coinciden,
                         "pct": 100 * coinciden / len(periodos)})
        registrar_log(f"Prueba 2 ({s['codigo_bcrp']}): {coinciden}/{len(periodos)} celdas coinciden")
    verificadas = [f for f in filas_p2 if f["coinciden"] is not None]
    total_celdas = sum(f["celdas"] for f in verificadas)
    total_coinciden = sum(f["coinciden"] for f in verificadas)
    pct_p2 = 100 * total_coinciden / total_celdas if total_celdas else 0.0
    prueba2 = len(verificadas) == len(series) and pct_p2 >= UMBRAL_EQUIVALENCIA

    # ------------------ Prueba 3. Procesado vs. fuente -------------------------
    diarias = [s for s in series if s["frecuencia"] == "diaria" and fuentes[s["variable"]] is not None]
    tabla_fuente = pd.DataFrame({s["variable"]: pd.Series({periodo_a_fecha(p): a_numero(v)
                                                           for p, v in fuentes[s["variable"]].items()})
                                 for s in diarias}).sort_index()
    faltante_en_fuente = tabla_fuente.isna()                       # dónde el BCRP publica 'n.d.'
    esperado = tabla_fuente.ffill().bfill()                         # misma regla LOCF del script 03
    filas_p3, errores_p3 = [], []
    for s in diarias:
        v = s["variable"]
        col = COLUMNA_EN_PROCESADO.get(v, v)
        exp = esperado[v].reindex(procesado["fecha"]).to_numpy()
        # Clasificación de cada celda: igual a la fuente, rellenada (LOCF) o distinta
        nd = faltante_en_fuente[v].reindex(procesado["fecha"]).fillna(True).to_numpy()
        ok = np.array([son_iguales(a, b) for a, b in zip(procesado[col].to_numpy(), exp)])
        filas_p3.append({"columna": col, "codigo": s["codigo_bcrp"],
                         "originales_iguales": int((ok & ~nd).sum()),
                         "rellenados_LOCF_correctos": int((ok & nd).sum()),
                         "no_coinciden": int((~ok).sum())})
        for i in np.where(~ok)[0][:5]:
            errores_p3.append(f"{col} {procesado['fecha'].iloc[i]:%Y-%m-%d}: procesado={procesado[col].iloc[i]} "
                              f"| esperado={exp[i]}")
    # La TEA hipotecaria mensual se compara por mes (llave año-mes)
    mensual = next(s for s in series if s["frecuencia"] == "mensual")
    if fuentes[mensual["variable"]] is not None:
        fuente_mes = {periodo_a_mes(p): a_numero(v) for p, v in fuentes[mensual["variable"]].items()}
        col = COLUMNA_EN_PROCESADO.get(mensual["variable"], mensual["variable"])
        ok = np.array([son_iguales(a, fuente_mes.get(m, np.nan))
                       for a, m in zip(procesado[col], procesado["llave_mes"])])
        filas_p3.append({"columna": col, "codigo": mensual["codigo_bcrp"],
                         "originales_iguales": int(ok.sum()), "rellenados_LOCF_correctos": 0,
                         "no_coinciden": int((~ok).sum())})
    # La marca 'imputado' debe ser 1 exactamente en los días con algún 'n.d.'
    imputado_esperado = faltante_en_fuente.any(axis=1).reindex(procesado["fecha"]).fillna(True).astype(int)
    marca_ok = int((imputado_esperado.to_numpy() == procesado["imputado"].to_numpy()).sum())
    prueba3 = (len(diarias) == sum(s["frecuencia"] == "diaria" for s in series)
               and all(f["no_coinciden"] == 0 for f in filas_p3) and marca_ok == len(procesado))
    registrar_log(f"Prueba 3 (procesado): {'OK' if prueba3 else 'CON DIFERENCIAS'} | "
                  f"marca 'imputado' correcta en {marca_ok}/{len(procesado)} días")

    # ------------------ Prueba 4. Variables calculadas -------------------------
    monto = float(crudo["monto_credito"].iloc[0])
    plazo = int(crudo["plazo_meses"].iloc[0])
    tea_pactada = float(procesado["tea_hipotecaria_mensual"].iloc[0])
    cuota = float(cuota_francesa(monto, tea_pactada, plazo))
    vp_recalculado = valor_presente(cuota, procesado["tea_hipotecaria_diaria"], plazo)
    dif_vp = float(np.max(np.abs(vp_recalculado - procesado["vp_credito"])))
    d_x1 = procesado["tasa_referencia"].diff().round(4)
    d_ok = all(son_iguales(a, b) for a, b in zip(d_x1, procesado["d_tasa_referencia"]))
    promedio_vs_oficial = float((procesado.groupby("llave_mes")["tea_hipotecaria_diaria"].mean()
                                 - procesado.groupby("llave_mes")["tea_hipotecaria_mensual"].first()).abs().max())
    prueba4 = dif_vp <= TOLERANCIA_VP and d_ok
    registrar_log(f"Prueba 4 (calculadas): diferencia máxima en vp_credito = S/ {dif_vp:.4f}")

    # ------------------ Prueba 5. Muestra al azar (como el docente) -----------
    generador = np.random.default_rng(SEMILLA)
    filas_muestra = sorted(generador.choice(len(procesado), size=TAMANO_MUESTRA, replace=False))
    muestra = []
    for i in filas_muestra:
        fila = procesado.iloc[i]
        for s in series:
            v = s["variable"]
            col = COLUMNA_EN_PROCESADO.get(v, v)
            if fuentes[v] is None:
                continue
            # Valor que publica la fuente para esa fecha (o ese mes, si la serie es mensual)
            if s["frecuencia"] == "diaria":
                texto_fuente = next((val for p, val in fuentes[v].items() if periodo_a_fecha(p) == fila["fecha"]), "(no está)")
            else:
                texto_fuente = next((val for p, val in fuentes[v].items() if periodo_a_mes(p) == fila["llave_mes"]), "(no está)")
            dia = fila["fecha"].to_pydatetime()   # enlace de la API solo para ese día (o ese mes)
            if son_iguales(fila[col], a_numero(texto_fuente)):
                resultado = "coincide"
            elif np.isnan(a_numero(texto_fuente)) and son_iguales(fila[col], esperado[v].get(fila["fecha"], np.nan)):
                resultado = "n.d. en la fuente: último valor observado (imputado = 1)"
            else:
                resultado = "NO COINCIDE"
            muestra.append({"id": int(fila["id"]), "fecha": f"{fila['fecha']:%Y-%m-%d}", "columna": col,
                            "codigo_bcrp": s["codigo_bcrp"], "valor_procesado": fila[col],
                            "valor_en_fuente": texto_fuente, "resultado": resultado,
                            "url_cotejo": construir_url(s["codigo_bcrp"], s["frecuencia"], dia, dia)})
    tabla_muestra = pd.DataFrame(muestra)
    tabla_muestra.to_csv(ARCHIVO_MUESTRA, index=False, encoding="utf-8", lineterminator="\n")
    prueba5 = bool(len(tabla_muestra)) and not (tabla_muestra["resultado"] == "NO COINCIDE").any()
    registrar_log(f"Prueba 5 (muestra de {TAMANO_MUESTRA} filas, semilla {SEMILLA}): "
                  f"{'OK' if prueba5 else 'CON DIFERENCIAS'}")

    # ------------------ Veredicto e informe -----------------------------------
    aprobado = all([prueba1, prueba2, prueba3, prueba4, prueba5])
    if aprobado and pct_p2 == 100:
        veredicto = "APROBADO: todos los datos extraídos coinciden con la fuente oficial (BCRPData)."
    elif aprobado:
        veredicto = (f"APROBADO POR EQUIVALENCIA: coincide el {pct_p2:.2f} % de las celdas (mínimo "
                     f"{UMBRAL_EQUIVALENCIA:.0f} %, numeral 2.4.5). Las diferencias pueden ser revisiones oficiales "
                     f"del BCRP posteriores a la extracción original ({hora_extraccion_original()}).")
    else:
        veredicto = "REVISAR: alguna prueba no se cumplió. Ver el detalle abajo."

    def marca(ok):
        return "✔ cumple" if ok else "✘ revisar"

    for f in filas_p2:
        f["pct_texto"] = "no se pudo consultar" if f["pct"] is None else f"{f['pct']:.2f} %"
        f["coinciden_texto"] = "—" if f["coinciden"] is None else str(f["coinciden"])
    tabla2 = "\n".join(f"| `{f['variable']}` | {f['codigo_bcrp']} | {f['frecuencia']} | {f['celdas']} | "
                       f"{f['coinciden_texto']} | {f['pct_texto']} |" for f in filas_p2)
    tabla3 = "\n".join(f"| `{f['columna']}` | {f['codigo']} | {f['originales_iguales']} | "
                       f"{f['rellenados_LOCF_correctos']} | {f['no_coinciden']} |" for f in filas_p3)
    tabla5 = "\n".join(f"| {r['id']} | {r['fecha']} | `{r['columna']}` | {r['valor_procesado']} | "
                       f"{r['valor_en_fuente']} | {r['resultado']} |" for r in muestra)
    detalle = "\n".join(f"- {d}" for d in (discrepancias_p2[:10] + errores_p3[:10])) or "- Ninguna."

    ARCHIVO_INFORME.write_text(f"""# Verificación de los datos contra la fuente oficial

- **Fecha y hora de esta verificación:** {datetime.now():%Y-%m-%d %H:%M:%S}
- **Extracción original (según log_ejecucion.txt):** {hora_extraccion_original()}
- **Ventana consultada:** {FECHA_INICIO} a {FECHA_CORTE}
- **Fuente:** API de BCRPData, {URL_BASE}

## Veredicto

**{veredicto}**

| Prueba | Qué comprueba | Resultado |
|---|---|---|
| 1. Integridad | El SHA-256 de `datos_procesados` coincide con el declarado | {marca(prueba1)} |
| 2. Crudo vs. fuente | Cada valor de `datos_crudos` es igual al publicado hoy por el BCRP ({pct_p2:.2f} %) | {marca(prueba2)} |
| 3. Procesado vs. fuente | Variables extraídas iguales a la fuente; días 'n.d.' con el último valor observado | {marca(prueba3)} |
| 4. Calculadas | `vp_credito` recalculado (diferencia máx. S/ {dif_vp:.4f}) y cambio diario de x1 | {marca(prueba4)} |
| 5. Muestra al azar | {TAMANO_MUESTRA} filas elegidas con semilla {SEMILLA} (matrícula) | {marca(prueba5)} |

Huella declarada: `{huella_declarada}`
Huella actual: `{huella_actual}`

## Prueba 2. Datos crudos frente a la API en vivo

| Variable | Código | Frecuencia | Celdas | Coinciden | % |
|---|---|---|---|---|---|
{tabla2}

## Prueba 3. Datos procesados frente a la API en vivo

| Columna | Código | Iguales a la fuente | 'n.d.' rellenados correctamente (LOCF) | No coinciden |
|---|---|---|---|---|
{tabla3}

La marca `imputado` es correcta en {marca_ok} de {len(procesado)} días.
Diferencia máxima entre el promedio mensual de la TEA diaria estimada y la TEA oficial: {promedio_vs_oficial:.4f} p.p.

## Prueba 5. Muestra al azar para el cotejo manual

Cada fila de `muestra_cotejo_{CODIGO_MATRICULA}.csv` trae el enlace de la API para abrirlo en el navegador.

| id | Fecha | Columna | En la base | En la fuente | Resultado |
|---|---|---|---|---|---|
{tabla5}

## Diferencias encontradas (máximo 20)

{detalle}

Este informe se generó automáticamente al ejecutar `codigo/05_verificacion_fuente.py`.
""", encoding="utf-8")
    registrar_log(f"Veredicto: {veredicto}")
    registrar_log("=== Fin de la verificación ===")


if __name__ == "__main__":
    main()
