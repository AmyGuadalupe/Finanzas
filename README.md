# Valor presente del crédito hipotecario y su sensibilidad a la tasa de interés

**Autora:** Amy Pamela Guadalupe Cordova
**Código de matrícula:** 2024200501G
**Curso:** Finanzas I
**Trabajo:** Componente procedimental — Unidad I

## Descripción del proyecto

Este proyecto analiza cómo el Valor Presente (VP) de un crédito hipotecario
de referencia (S/ 300,000 a 20 años) cambia según la tasa de interés
hipotecaria vigente en el mercado peruano, usando datos históricos reales
del Banco Central de Reserva del Perú (BCRP) entre setiembre 2003 y
agosto 2026 (276 meses).

Se plantea el modelo **y = f(x₁, x₂, x₃, x₄)**, donde:

| Símbolo | Variable | Rol |
|---|---|---|
| y | Valor Presente del crédito hipotecario | Endógena (calculada) |
| x₁ | Tasa de interés hipotecaria (MN) | Exógena |
| x₂ | Tasa de referencia de política monetaria del BCRP | Exógena |
| x₃ | Tipo de cambio interbancario venta | Exógena |
| x₄ | Inflación (IPC, var% 12 meses) | Exógena |

## Estructura del repositorio

```
├── codigo/
│   ├── 01_extraccion_api.py    # Descarga las 4 series desde la API del BCRP
│   ├── 03_limpieza_datos.py    # Limpia, estructura y calcula la variable "y"
│   └── 04_analisis.py          # Regresión, sensibilidad, escenarios y gráficos
├── datos_crudos/
│   └── datos_crudos_2024200501G.csv       # Datos tal como los entrega el BCRP
├── datos_procesados/
│   ├── datos_procesados_2024200501G.csv   # Dataset final (8 columnas)
│   └── reporte_atipicos_2024200501G.csv   # Valores atípicos detectados (IQR)
├── salidas/
│   ├── grafico_vp_tiempo.png
│   ├── grafico_vp_vs_tasa.png
│   ├── grafico_escenarios.png
│   ├── resultados_sensibilidad_2024200501G.csv
│   ├── escenarios_shock_2024200501G.csv
│   └── regresion_resumen_2024200501G.txt
├── diccionario_variables.md
├── requirements.txt
├── .env.example
├── log_ejecucion.txt
└── README.md
```

## Fuente de datos

Banco Central de Reserva del Perú (BCRP) — API pública de series estadísticas
(no requiere clave de acceso): https://estadisticas.bcrp.gob.pe/estadisticas/series/

| Variable | Código BCRP |
|---|---|
| Tasa de interés hipotecaria (MN) | PN07848NM |
| Tasa de referencia de política monetaria | PD04722MM |
| Tipo de cambio interbancario venta | PN01215PM |
| Inflación (IPC, var% 12 meses) | PN01273PM |

Ventana de datos: **setiembre 2003 – agosto 2026** (276 observaciones × 4
variables = 1,104 datos, por encima del mínimo de 1,000 exigido).

## Cómo ejecutar el proyecto (en orden)

1. **Instalar dependencias:**
   ```
   pip install -r requirements.txt
   ```

2. **Extraer los datos** (genera `datos_crudos/datos_crudos_2024200501G.csv`):
   ```
   cd codigo
   python 01_extraccion_api.py
   ```

3. **Limpiar y estructurar los datos** (genera `datos_procesados/`):
   ```
   python 03_limpieza_datos.py
   ```

4. **Correr el análisis** (genera gráficos y tablas en `salidas/`):
   ```
   python 04_analisis.py
   ```

Cada script deja un registro de su ejecución en `log_ejecucion.txt`.

## Supuestos del crédito de referencia

- Monto del préstamo (S0): S/ 300,000
- Plazo: 20 años (240 cuotas mensuales)
- Sistema de amortización: francés (cuota fija)
- La cuota se calcula una sola vez con la tasa vigente en el mes de origen
  (setiembre 2003) y se mantiene fija; el VP se revaloriza cada mes con la
  tasa de mercado observada ese mes (misma lógica que el precio de un bono
  a tasa fija frente a su tasa de rendimiento).

## Principales resultados

- Duración de Macaulay del crédito: ~92.6 meses (7.7 años)
- Elasticidad-precio del VP frente a la tasa: -0.55
- Ante un shock de -2pp / +2pp sobre la tasa vigente al corte, el VP varía
  +16.2% / -12.8% respectivamente (relación inversa y asimétrica, típica de
  instrumentos de tasa fija)
- La regresión y = f(x₁,x₂,x₃,x₄) muestra R² = 0.992; se corrigió con
  errores estándar robustos HAC/Newey-West por autocorrelación detectada
  (Durbin-Watson = 0.083 en el modelo sin corregir)

## Limitaciones

- El Valor Presente es una variable calculada (no reportada por ninguna
  fuente), a partir de un crédito de referencia con supuestos fijos, no de
  un contrato real.
- Al tratarse de niveles de series de tiempo con tendencia, existe riesgo
  de regresión espuria; se mitigó con errores estándar HAC, pero no
  reemplaza un análisis de cointegración más profundo (fuera del alcance
  de este trabajo de Unidad I).
