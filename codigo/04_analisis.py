# Autora: Amy Pamela Guadalupe Cordova
# Código de matrícula: 2024200501G
# Tema N.º 18 (S03 · Valor del dinero en el tiempo I): Valor presente del crédito hipotecario y su sensibilidad a la tasa de interés
# Fecha de extracción: 2026-09-23 (fecha de los datos que analiza este script)

"""
04_analisis.py
--------------
Genera TODAS las tablas y figuras del artículo a partir de
datos_procesados/datos_procesados_2024200501G.csv y las guarda en /salidas.

  A. Descriptivos, correlaciones, estacionariedad (ADF) y multicolinealidad (VIF)
  B. Regresión y = f(x1, x2, x3) con errores estándar HAC (Newey-West):
       Modelo 1: niveles
       Modelo 2: cambios diarios con atípicos winsorizados (modelo principal en cambios)
       Modelo 3: cambios diarios sin tratar (comparación de robustez)
  C. Sensibilidad del valor presente a la TEA: derivada, duración de Macaulay,
     duración modificada, convexidad y elasticidad, a la fecha de corte
  D. Escenarios de choque de ±1 y ±2 puntos porcentuales y comparación por plazo
  E. Figuras 1 a 8
"""

# ---------------------------------------------------------------------------
# BLOQUE 1. Librerías
# ---------------------------------------------------------------------------
import warnings
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                      # dibuja sin abrir ventanas
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tsa.stattools import adfuller

# ---------------------------------------------------------------------------
# BLOQUE 2. Parámetros
# ---------------------------------------------------------------------------
CODIGO_MATRICULA = "2024200501G"
CHOQUES_PP = [-2, -1, 1, 2]                 # choques de tasa en puntos porcentuales
PLAZOS_ANIOS = [10, 15, 20, 25]             # 25 años = plazo máximo del Nuevo Crédito Mivivienda
FACTOR_LEVE, FACTOR_EXTREMO = 1.5, 3.0      # regla de Tukey (igual que en 03)

Y = "vp_credito"
X = ["tasa_referencia", "rend_bono10_usa", "tipo_cambio"]
NOMBRES = {"vp_credito": "Valor presente del crédito (S/)",
           "tasa_referencia": "Tasa de referencia BCRP (%)",
           "rend_bono10_usa": "Bono del Tesoro EE.UU. 10 años (%)",
           "tipo_cambio": "Tipo de cambio (S/ por US$)",
           "tea_hipotecaria_mensual": "TEA hipotecaria mensual (%)",
           "rend_bono10_pen": "Bono soberano Perú 10 años (%)",
           "tea_hipotecaria_diaria": "TEA hipotecaria diaria estimada (%)"}

# ---------------------------------------------------------------------------
# BLOQUE 3. Rutas relativas
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[1]
ARCHIVO_PROCESADO = RAIZ / "datos_procesados" / f"datos_procesados_{CODIGO_MATRICULA}.csv"
ARCHIVO_CRUDO = RAIZ / "datos_crudos" / f"datos_crudos_{CODIGO_MATRICULA}.csv"
SALIDAS = RAIZ / "salidas"
ARCHIVO_LOG = RAIZ / "log_ejecucion.txt"
SALIDAS.mkdir(exist_ok=True)

warnings.filterwarnings("ignore", category=FutureWarning)   # avisos de versiones futuras de statsmodels

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 110, "savefig.dpi": 200, "savefig.bbox": "tight"})


# ---------------------------------------------------------------------------
# BLOQUE 4. Funciones
# ---------------------------------------------------------------------------
def registrar_log(mensaje: str) -> None:
    linea = f"{datetime.now():%Y-%m-%d %H:%M:%S} | 04_analisis | {mensaje}"
    print(linea)
    with open(ARCHIVO_LOG, "a", encoding="utf-8") as archivo:
        archivo.write(linea + "\n")


def guardar_tabla(tabla: pd.DataFrame, nombre: str) -> None:
    tabla.to_csv(SALIDAS / f"{nombre}.csv", encoding="utf-8", lineterminator="\n")
    registrar_log(f"Tabla guardada: salidas/{nombre}.csv")


def guardar_figura(figura, nombre: str) -> None:
    figura.savefig(SALIDAS / f"{nombre}.png")
    plt.close(figura)
    registrar_log(f"Figura guardada: salidas/{nombre}.png")


def tem(tea_porcentaje):
    """TEA en % -> tasa efectiva mensual: (1 + TEA)^(1/12) - 1"""
    return (1 + np.asarray(tea_porcentaje, dtype=float) / 100) ** (1 / 12) - 1


def cuota_francesa(monto, tea_porcentaje, meses):
    i = tem(tea_porcentaje)
    return monto * i / (1 - (1 + i) ** -meses)


def medidas_sensibilidad(cuota, tea_porcentaje, meses):
    """Valor presente y medidas de sensibilidad frente a la TEA.
    Flujos mensuales C en t = k/12 años, descontados con (1 + TEA)^(-t)."""
    r = tea_porcentaje / 100
    t = np.arange(1, meses + 1) / 12                    # tiempo de cada cuota en años
    vp_flujos = cuota * (1 + r) ** (-t)
    vp = vp_flujos.sum()
    macaulay = (t * vp_flujos).sum() / vp                # años
    modificada = macaulay / (1 + r)
    convexidad = (t * (t + 1) * vp_flujos).sum() / (vp * (1 + r) ** 2)
    derivada = -modificada * vp                          # dVP/dTEA (TEA en tanto por uno)
    return {"vp": vp, "derivada_por_1pp": derivada / 100, "duracion_macaulay_anios": macaulay,
            "duracion_modificada": modificada, "convexidad": convexidad,
            "elasticidad": -modificada * r}


def regresion_hac(datos: pd.DataFrame, y: str, xs: list, nombre: str):
    """MCO con errores estándar robustos a heterocedasticidad y autocorrelación
    (Newey-West). Rezagos: regla de Newey-West, floor(4·(n/100)^(2/9))."""
    datos = datos[[y] + xs].dropna()
    rezagos = int(np.floor(4 * (len(datos) / 100) ** (2 / 9)))
    modelo = sm.OLS(datos[y], sm.add_constant(datos[xs])).fit(cov_type="HAC", cov_kwds={"maxlags": rezagos})
    (SALIDAS / f"regresion_{nombre}.txt").write_text(str(modelo.summary()), encoding="utf-8")
    return modelo, durbin_watson(modelo.resid), rezagos


# ---------------------------------------------------------------------------
# BLOQUE 5. Programa principal
# ---------------------------------------------------------------------------
def main() -> None:
    registrar_log("=== Inicio del análisis ===")
    datos = pd.read_csv(ARCHIVO_PROCESADO)
    datos["fecha"] = pd.to_datetime(dict(year=datos["anio"], month=datos["mes"], day=datos["dia"]))
    crudo = pd.read_csv(ARCHIVO_CRUDO, nrows=1)
    monto, plazo = float(crudo["monto_credito"].iloc[0]), int(crudo["plazo_meses"].iloc[0])
    tea_pactada = float(datos["tea_hipotecaria_mensual"].iloc[0])
    cuota = float(cuota_francesa(monto, tea_pactada, plazo))
    registrar_log(f"Base: {len(datos)} filas | crédito S/ {monto:,.0f}, {plazo} meses, cuota S/ {cuota:,.2f}")

    # ------------------------- A. Descriptivos --------------------------------
    columnas_desc = [Y] + X + ["tea_hipotecaria_mensual", "rend_bono10_pen", "tea_hipotecaria_diaria"]
    desc = datos[columnas_desc].describe().T[["count", "mean", "std", "min", "25%", "50%", "75%", "max"]]
    desc.columns = ["n", "media", "desv_estandar", "minimo", "p25", "mediana", "p75", "maximo"]
    guardar_tabla(desc.round(4), "tabla1_descriptivos")

    guardar_tabla(datos[[Y] + X].corr().round(4), "tabla2_correlaciones")

    filas_adf = []
    for v in [Y] + X:
        for forma, serie in [("nivel", datos[v]), ("cambio diario", datos[v].diff())]:
            estadistico, p_valor = adfuller(serie.dropna(), autolag="AIC")[:2]
            filas_adf.append({"variable": v, "forma": forma, "estadistico_ADF": estadistico, "p_valor": p_valor,
                              "conclusion": "estacionaria" if p_valor < 0.05 else "no estacionaria (raíz unitaria)"})
    guardar_tabla(pd.DataFrame(filas_adf).set_index(["variable", "forma"]).round(4), "tabla3_estacionariedad_adf")

    matriz = sm.add_constant(datos[X])
    vif = pd.DataFrame({"variable": X, "VIF": [variance_inflation_factor(matriz.values, i + 1) for i in range(len(X))]})
    guardar_tabla(vif.set_index("variable").round(4), "tabla4_vif")

    # ------------------------- B. Regresiones ---------------------------------
    m1, dw1, l1 = regresion_hac(datos, Y, X, "modelo1_niveles")
    d_y, d_x = "d_vp_credito", ["d_tasa_referencia", "d_rend_bono10_usa", "d_tipo_cambio"]
    m2, dw2, l2 = regresion_hac(datos, d_y, d_x, "modelo2_cambios_winsorizados")
    crudos = pd.DataFrame({d_y: datos[Y].diff(), **{f"d_{x}": datos[x].diff() for x in X}})
    m3, dw3, l3 = regresion_hac(crudos, d_y, d_x, "modelo3_cambios_sin_tratar")

    filas = []
    for etiqueta, modelo, dw, rez, ys, xs in [("Modelo 1 (niveles)", m1, dw1, l1, Y, X),
                                              ("Modelo 2 (cambios, winsorizados)", m2, dw2, l2, d_y, d_x),
                                              ("Modelo 3 (cambios, sin tratar)", m3, dw3, l3, d_y, d_x)]:
        for termino in ["const"] + xs:
            fila = {"modelo": etiqueta, "variable": termino, "coeficiente": modelo.params[termino],
                    "error_estandar_HAC": modelo.bse[termino], "t": modelo.tvalues[termino],
                    "p_valor": modelo.pvalues[termino]}
            if etiqueta.startswith("Modelo 1") and termino != "const":
                fila["elasticidad_en_medias"] = modelo.params[termino] * datos[termino].mean() / datos[Y].mean()
            filas.append(fila)
        filas.append({"modelo": etiqueta, "variable": "R2", "coeficiente": modelo.rsquared})
        filas.append({"modelo": etiqueta, "variable": "R2_ajustado", "coeficiente": modelo.rsquared_adj})
        filas.append({"modelo": etiqueta, "variable": "Durbin_Watson", "coeficiente": dw})
        filas.append({"modelo": etiqueta, "variable": "n_observaciones", "coeficiente": modelo.nobs})
        filas.append({"modelo": etiqueta, "variable": "rezagos_Newey_West", "coeficiente": rez})
    guardar_tabla(pd.DataFrame(filas).set_index(["modelo", "variable"]).round(6), "tabla5_regresiones")
    registrar_log(f"Modelo 1: R2={m1.rsquared:.4f}, DW={dw1:.3f} | Modelo 2: R2={m2.rsquared:.4f}, DW={dw2:.3f} | "
                  f"Modelo 3: R2={m3.rsquared:.4f}")

    # ------------------------- C. Sensibilidad al corte ------------------------
    tea_corte = float(datos["tea_hipotecaria_diaria"].iloc[-1])
    fecha_corte = datos["fecha"].iloc[-1]
    sens = medidas_sensibilidad(cuota, tea_corte, plazo)
    tabla6 = pd.Series({"fecha_corte": fecha_corte.strftime("%Y-%m-%d"), "tea_corte_%": tea_corte,
                        "cuota_mensual": cuota, "valor_presente": sens["vp"],
                        "derivada_dVP_por_1pp": sens["derivada_por_1pp"],
                        "duracion_macaulay_anios": sens["duracion_macaulay_anios"],
                        "duracion_modificada": sens["duracion_modificada"],
                        "convexidad": sens["convexidad"], "elasticidad_VP_TEA": sens["elasticidad"]},
                       name="valor").to_frame()
    guardar_tabla(tabla6, "tabla6_sensibilidad_al_corte")

    # ------------------------- D. Escenarios y plazos --------------------------
    filas_esc = []
    for choque in CHOQUES_PP:
        dr = choque / 100
        vp_nuevo = medidas_sensibilidad(cuota, tea_corte + choque, plazo)["vp"]
        filas_esc.append({"choque_pp": choque, "tea_%": tea_corte + choque, "vp": vp_nuevo,
                          "variacion_exacta_%": (vp_nuevo / sens["vp"] - 1) * 100,
                          "aprox_duracion_%": -sens["duracion_modificada"] * dr * 100,
                          "aprox_duracion_convexidad_%": (-sens["duracion_modificada"] * dr
                                                          + 0.5 * sens["convexidad"] * dr ** 2) * 100})
    escenarios = pd.DataFrame(filas_esc).set_index("choque_pp")
    guardar_tabla(escenarios.round(4), "tabla7_escenarios")

    filas_pl = []
    for anios in PLAZOS_ANIOS:
        n = anios * 12
        c = float(cuota_francesa(monto, tea_corte, n))   # crédito nuevo al corte: VP inicial = monto
        m = medidas_sensibilidad(c, tea_corte, n)
        fila = {"plazo_anios": anios, "cuota": c, "duracion_modificada": m["duracion_modificada"],
                "elasticidad": m["elasticidad"]}
        for choque in [1, -1]:
            fila[f"variacion_%_choque_{choque:+d}pp"] = (medidas_sensibilidad(c, tea_corte + choque, n)["vp"] / m["vp"] - 1) * 100
        filas_pl.append(fila)
    plazos = pd.DataFrame(filas_pl).set_index("plazo_anios")
    guardar_tabla(plazos.round(4), "tabla8_plazos")

    # Resumen de atípicos regenerado desde la base (para la tabla del artículo)
    filas_at = []
    for v in [Y, "rend_bono10_usa", "tipo_cambio"]:
        cambio = datos[v].diff()
        q1, q3 = cambio.quantile([0.25, 0.75]); iqr = q3 - q1
        extremo = (cambio < q1 - FACTOR_EXTREMO * iqr) | (cambio > q3 + FACTOR_EXTREMO * iqr)
        leve = ((cambio < q1 - FACTOR_LEVE * iqr) | (cambio > q3 + FACTOR_LEVE * iqr)) & ~extremo
        filas_at.append({"variable": v, "Q1": q1, "Q3": q3, "IQR": iqr, "atipicos_leves": int(leve.sum()),
                         "atipicos_extremos": int(extremo.sum()),
                         "limite_inferior_extremo": q1 - FACTOR_EXTREMO * iqr,
                         "limite_superior_extremo": q3 + FACTOR_EXTREMO * iqr})
    guardar_tabla(pd.DataFrame(filas_at).set_index("variable").round(4), "tabla9_atipicos_resumen")

    # ------------------------- E. Figuras --------------------------------------
    # Figura 1: valor presente en el tiempo, con días atípicos marcados
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.plot(datos["fecha"], datos[Y] / 1000, color="#1f4e79", lw=1)
    at = datos[datos["atipico"] == 1]
    ax.scatter(at["fecha"], at[Y] / 1000, color="#c0392b", s=14, zorder=3, label="Día con atípico extremo")
    ax.axhline(monto / 1000, color="gray", ls="--", lw=0.8, label=f"Monto prestado (S/ {monto/1000:,.0f} mil)")
    ax.set_ylabel("Valor presente (miles de S/)"); ax.legend(frameon=False, fontsize=8)
    guardar_figura(fig, "figura1_valor_presente_tiempo")

    # Figura 2: tasas de interés en el tiempo
    fig, ax = plt.subplots(figsize=(8, 3.8))
    for v, estilo in [("tasa_referencia", "-"), ("tea_hipotecaria_mensual", "-"),
                      ("rend_bono10_pen", "-"), ("rend_bono10_usa", "--")]:
        ax.plot(datos["fecha"], datos[v], ls=estilo, lw=1.1, label=NOMBRES[v])
    ax.set_ylabel("Porcentaje (%)"); ax.legend(frameon=False, fontsize=8, ncol=2)
    guardar_figura(fig, "figura2_tasas_interes")

    # Figura 3: diagramas de caja de los cambios diarios (detección de atípicos)
    fig, ejes = plt.subplots(1, 3, figsize=(9, 3.6))
    for ax, v in zip(ejes, [Y, "rend_bono10_usa", "tipo_cambio"]):
        cambio = datos[v].diff().dropna()
        q1, q3 = cambio.quantile([0.25, 0.75]); iqr = q3 - q1
        ax.boxplot(cambio, whis=FACTOR_LEVE, widths=0.5,
                   flierprops={"marker": "o", "markersize": 3, "markerfacecolor": "none", "markeredgecolor": "gray"})
        extremos = cambio[(cambio < q1 - FACTOR_EXTREMO * iqr) | (cambio > q3 + FACTOR_EXTREMO * iqr)]
        ax.scatter(np.ones(len(extremos)), extremos, color="#c0392b", s=14, zorder=3)
        for limite in [q1 - FACTOR_EXTREMO * iqr, q3 + FACTOR_EXTREMO * iqr]:
            ax.axhline(limite, color="#c0392b", ls="--", lw=0.8)
        ax.set_xticks([1]); ax.set_xticklabels([f"Cambio diario:\n{NOMBRES[v]}"], fontsize=7.5)
    ejes[0].set_ylabel("Cambio respecto al día anterior")
    from matplotlib.lines import Line2D
    leyenda = [Line2D([], [], marker="o", ls="", markerfacecolor="none", markeredgecolor="gray", label="Atípico leve (> 1.5 IQR): se conserva"),
               Line2D([], [], marker="o", ls="", color="#c0392b", label="Atípico extremo (> 3 IQR): se winsoriza"),
               Line2D([], [], ls="--", color="#c0392b", label="Límite extremo (3 IQR)")]
    fig.legend(handles=leyenda, loc="lower center", ncol=3, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, -0.08))
    guardar_figura(fig, "figura3_boxplot_atipicos")

    # Figura 4: relación de y con cada x (niveles)
    fig, ejes = plt.subplots(1, 3, figsize=(9, 3.4), sharey=True)
    for ax, v in zip(ejes, X):
        ax.scatter(datos[v], datos[Y] / 1000, s=4, alpha=0.4, color="#1f4e79")
        pendiente, intercepto = np.polyfit(datos[v], datos[Y] / 1000, 1)
        rango = np.linspace(datos[v].min(), datos[v].max(), 50)
        ax.plot(rango, intercepto + pendiente * rango, color="#c0392b", lw=1.2)
        ax.set_xlabel(NOMBRES[v], fontsize=8)
    ejes[0].set_ylabel("Valor presente (miles de S/)")
    guardar_figura(fig, "figura4_dispersion_y_x")

    # Figura 5: curva de sensibilidad (convexidad) y aproximación por duración
    teas = np.linspace(max(tea_corte - 4, 1), tea_corte + 4, 200)
    vps = np.array([medidas_sensibilidad(cuota, t, plazo)["vp"] for t in teas])
    tangente = sens["vp"] * (1 - sens["duracion_modificada"] * (teas - tea_corte) / 100)
    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.plot(teas, vps / 1000, color="#1f4e79", lw=1.6, label="Valor presente exacto")
    ax.plot(teas, tangente / 1000, color="gray", ls="--", lw=1, label="Aproximación por duración")
    ax.scatter(escenarios["tea_%"], escenarios["vp"] / 1000, color="#c0392b", s=18, zorder=3, label="Escenarios ±1 y ±2 p.p.")
    ax.scatter([tea_corte], [sens["vp"] / 1000], color="black", s=26, zorder=4, label=f"Al corte (TEA {tea_corte:.2f} %)")
    ax.set_xlabel("TEA hipotecaria (%)"); ax.set_ylabel("Valor presente (miles de S/)"); ax.legend(frameon=False, fontsize=8)
    guardar_figura(fig, "figura5_curva_sensibilidad")

    # Figura 6: escenarios de choque
    fig, ax = plt.subplots(figsize=(6, 3.6))
    colores = ["#1f7a4d" if v > 0 else "#c0392b" for v in escenarios["variacion_exacta_%"]]
    barras = ax.bar([f"{c:+d} p.p." for c in escenarios.index], escenarios["variacion_exacta_%"], color=colores)
    ax.bar_label(barras, fmt="%.2f %%", fontsize=8); ax.axhline(0, color="black", lw=0.6)
    ax.set_xlabel("Choque en la TEA"); ax.set_ylabel("Variación del valor presente (%)")
    guardar_figura(fig, "figura6_escenarios")

    # Figura 7: sensibilidad según el plazo del crédito
    fig, ax = plt.subplots(figsize=(6, 3.6))
    barras = ax.bar([f"{p} años" for p in plazos.index], plazos["variacion_%_choque_+1pp"], color="#1f4e79")
    ax.bar_label(barras, fmt="%.2f %%", fontsize=8); ax.axhline(0, color="black", lw=0.6)
    ax.set_xlabel("Plazo del crédito"); ax.set_ylabel("Variación del VP ante +1 p.p. (%)")
    guardar_figura(fig, "figura7_plazos")

    # Figura 8: duración modificada y elasticidad a lo largo del periodo
    medidas = [medidas_sensibilidad(cuota, t, plazo) for t in datos["tea_hipotecaria_diaria"]]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.plot(datos["fecha"], [m["duracion_modificada"] for m in medidas], color="#1f4e79", lw=1, label="Duración modificada")
    ax.set_ylabel("Duración modificada")
    ax2 = ax.twinx(); ax2.spines["right"].set_visible(True)
    ax2.plot(datos["fecha"], [m["elasticidad"] for m in medidas], color="#c0392b", lw=1, label="Elasticidad VP–TEA")
    ax2.set_ylabel("Elasticidad")
    fig.legend(frameon=False, fontsize=8, loc="upper center", ncol=2)
    guardar_figura(fig, "figura8_duracion_elasticidad_tiempo")

    registrar_log(f"Al corte {fecha_corte:%Y-%m-%d}: VP=S/ {sens['vp']:,.2f} | D.mod={sens['duracion_modificada']:.3f} | "
                  f"elasticidad={sens['elasticidad']:.4f}")
    registrar_log("=== Fin del análisis ===")


if __name__ == "__main__":
    main()
