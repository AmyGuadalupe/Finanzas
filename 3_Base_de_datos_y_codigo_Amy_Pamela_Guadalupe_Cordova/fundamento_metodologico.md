# Fundamento metodológico

Cada decisión de procesamiento y análisis del proyecto se apoya en un autor que la propuso.
La columna *Script* indica dónde se aplica en el código.

| Script | Decisión | Qué se hace | Autor(es) |
|---|---|---|---|
| 03 | Días con 'n.d.' (feriados) | Se completan con el último valor observado (LOCF) y se marcan en `imputado` | Moritz y Bartz-Beielstein (2017) |
| 03 | Por qué no usar el promedio | La imputación por la media distorsiona la distribución y la varianza de la serie | Little y Rubin (2019) |
| 03 | TEA hipotecaria diaria | Desagregación temporal con serie relacionada (bono diario) y margen suavizado sin discontinuidades artificiales | Chow y Lin (1971); Denton (1971) |
| 03 | Variable y | Valor presente de una anualidad (cuota fija) con tasa efectiva mensual equivalente a la TEA | Fabozzi y Fabozzi (2021) |
| 03 | Detección de atípicos | Diagrama de caja: 1.5 IQR (leve) y 3 IQR (extremo) | Tukey (1977) |
| 03 | Tratamiento de atípicos | Winsorización: el cambio extremo se reemplaza por el límite del bigote | Dixon (1960); Tukey (1962) |
| 04 | Robustez ante atípicos | Se reportan resultados con y sin tratamiento (modelos 2 y 3) | Adams et al. (2019) |
| 04 | Estacionariedad | Prueba de raíz unitaria de Dickey-Fuller aumentada | Dickey y Fuller (1979) |
| 04 | Regresión en niveles vs. en cambios | Riesgo de regresión espuria entre series con tendencia | Granger y Newbold (1974) |
| 04 | Autocorrelación de residuos | Estadístico de Durbin-Watson | Durbin y Watson (1950) |
| 04 | Errores estándar robustos | Matriz HAC y regla de selección de rezagos | Newey y West (1987, 1994) |
| 04 | Multicolinealidad | Factor de inflación de la varianza, interpretado sin reglas fijas | O'Brien (2007) |
| 04 | Duración | Duración de Macaulay | Macaulay (1938) |
| 04 | Duración modificada y elasticidad | Elasticidad del valor presente respecto de la tasa | Hicks (1939); Fabozzi y Fabozzi (2021) |
| 04 | Convexidad | Corrección de segundo orden de la aproximación por duración | Fabozzi y Fabozzi (2021) |
| 04 | Escenarios de choque | Choques paralelos de tasa sobre el valor económico | Basel Committee on Banking Supervision (2016) |
| 01 | Monto y plazo del crédito | Dentro de los límites del Nuevo Crédito Mivivienda | Fondo Mivivienda S.A. (s.f.) |

**Precisiones.** La TEA hipotecaria diaria es una adaptación simplificada de la desagregación
temporal con serie relacionada (Chow y Lin, 1971; Denton, 1971): el movimiento diario proviene del
bono soberano y el margen mensual se suaviza por interpolación lineal. Adams et al. (2019) advierten
que los atípicos pueden alterar las conclusiones en finanzas; por ello se comparan los modelos con y
sin winsorización. O'Brien (2007) desaconseja reglas fijas para el VIF; en este estudio los VIF se
reportan e interpretan junto con las correlaciones.

## Referencias

Adams, J., Hayunga, D., Mansi, S., Reeb, D. y Verardi, V. (2019). Identifying and treating outliers in finance. *Financial Management, 48*(2), 345–384. https://doi.org/10.1111/fima.12269

Basel Committee on Banking Supervision. (2016). *Interest rate risk in the banking book*. Bank for International Settlements. https://www.bis.org/bcbs/publ/d368.htm

Chow, G. C. y Lin, A. (1971). Best linear unbiased interpolation, distribution, and extrapolation of time series by related series. *The Review of Economics and Statistics, 53*(4), 372–375. https://doi.org/10.2307/1928739

Denton, F. T. (1971). Adjustment of monthly or quarterly series to annual totals: An approach based on quadratic minimization. *Journal of the American Statistical Association, 66*(333), 99–102. https://doi.org/10.1080/01621459.1971.10482227

Dickey, D. A. y Fuller, W. A. (1979). Distribution of the estimators for autoregressive time series with a unit root. *Journal of the American Statistical Association, 74*(366a), 427–431. https://doi.org/10.1080/01621459.1979.10482531

Dixon, W. J. (1960). Simplified estimation from censored normal samples. *The Annals of Mathematical Statistics, 31*(2), 385–391. https://doi.org/10.1214/aoms/1177705900

Durbin, J. y Watson, G. S. (1950). Testing for serial correlation in least squares regression. I. *Biometrika, 37*(3–4), 409–428. https://doi.org/10.1093/biomet/37.3-4.409

Fabozzi, F. J. y Fabozzi, F. A. (2021). *Bond markets, analysis, and strategies* (10.ª ed.). The MIT Press.

Fondo Mivivienda S.A. (s.f.). *Programa Nuevo Crédito Mivivienda*. Plataforma digital única del Estado peruano. https://www.gob.pe/33425-programa-nuevo-credito-mivivienda

Granger, C. W. J. y Newbold, P. (1974). Spurious regressions in econometrics. *Journal of Econometrics, 2*(2), 111–120. https://doi.org/10.1016/0304-4076(74)90034-7

Hicks, J. R. (1939). *Value and capital: An inquiry into some fundamental principles of economic theory*. Clarendon Press.

Little, R. J. A. y Rubin, D. B. (2019). *Statistical analysis with missing data* (3.ª ed.). Wiley. https://doi.org/10.1002/9781119482260

Macaulay, F. R. (1938). *Some theoretical problems suggested by the movements of interest rates, bond yields and stock prices in the United States since 1856*. National Bureau of Economic Research. https://www.nber.org/books-and-chapters/some-theoretical-problems-suggested-movements-interest-rates-bond-yields-and-stock-prices-united

Moritz, S. y Bartz-Beielstein, T. (2017). imputeTS: Time series missing value imputation in R. *The R Journal, 9*(1), 207–218. https://doi.org/10.32614/RJ-2017-009

Newey, W. K. y West, K. D. (1987). A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix. *Econometrica, 55*(3), 703–708. https://doi.org/10.2307/1913610

Newey, W. K. y West, K. D. (1994). Automatic lag selection in covariance matrix estimation. *The Review of Economic Studies, 61*(4), 631–653. https://doi.org/10.2307/2297912

O'Brien, R. M. (2007). A caution regarding rules of thumb for variance inflation factors. *Quality & Quantity, 41*(5), 673–690. https://doi.org/10.1007/s11135-006-9018-6

Tukey, J. W. (1962). The future of data analysis. *The Annals of Mathematical Statistics, 33*(1), 1–67. https://doi.org/10.1214/aoms/1177704711

Tukey, J. W. (1977). *Exploratory data analysis*. Addison-Wesley.
