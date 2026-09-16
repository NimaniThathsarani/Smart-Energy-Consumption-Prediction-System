# Classical Time-Series Forecasting Report (ARIMA / SARIMA)

## Smart Energy Consumption Prediction System — Member 2

**Group task:** Time-Series Forecasting & Regression
**Member responsibility:** Classical Time-Series Models (ARIMA, SARIMA, parameter tuning, forecast generation, model evaluation)

---

## 1. Objective

Implement and evaluate classical (non deep-learning) time-series forecasting
models — ARIMA and, where seasonality is present, SARIMA — for household
energy consumption, and hand off results to Member 3 for the group-wide
model comparison and best-model selection.

---

## 2. Input Data

| Item | Value |
|---|---|
| Source file | `data/feature_engineered_dataset.csv` (output of Member 1's feature engineering stage) |
| Target variable | `Global_active_power` (kW) |
| Datetime column | `Datetime` |
| Native frequency | 1-minute |
| Raw row count | ~2,075,259 (Dec 2006 – Nov 2010) |

### Resampling decision

ARIMA/SARIMA parameter search over ~2 million 1-minute observations is not
computationally realistic within the project deadline, and several of
Member 1's engineered lag features (`Lag_24`, `Lag_168`) already imply an
hourly-scale mental model. The series was therefore **resampled to hourly
means** before fitting classical models:

```python
series = df.set_index("Datetime")["Global_active_power"].resample("h").mean().dropna()
```

Hours with no underlying readings (from Member 1's retained long-gap NaNs)
become NaN after resampling and are dropped, so no invented values enter
training or evaluation. This is a deliberate scope decision for the
*classical* models only — it does not affect Member 1's regression models
or Member 3's use of the raw-frequency dataset.

### Train / Validation / Test split

_Fill in the exact cutoff timestamps used once agreed with Member 1 and
Member 3 — this must be identical across the group's comparison table._

| Split | Start | End | Observations |
|---|---|---|---|
| Train | | | |
| Validation | | | |
| Test | | | |

Split method: chronological, no shuffling (70% / 15% / 15% by default in
`chronological_split()` — adjust and record the actual fractions/cutoffs
used here).

---

## 3. Stationarity Analysis

Augmented Dickey-Fuller (ADF) test applied to the training series.

| Series | ADF Statistic | p-value | Stationary? |
|---|---|---|---|
| Original | | | |
| Differenced (d = _) | | | |

**Selected differencing order:** d = _

---

## 4. Seasonality Analysis

Seasonal decomposition (`seasonal_decompose`, period = 24, additive) was
used to check for a daily consumption cycle.

- Seasonality strength score (F_s): **_**
- Decision threshold: 0.30
- Conclusion: **[ARIMA / SARIMA]** selected based on this threshold

_Insert the decomposition plot (trend / seasonal / residual) here or
reference `reports/figures/`._

---

## 5. Model Fitting

### 5.1 ARIMA (non-seasonal)

- Search method: stepwise `auto_arima` minimizing AIC, `max_p=5`, `max_q=5`
- Selected order (p, d, q): **_**
- AIC: **_**

### 5.2 SARIMA (seasonal) — if applicable

- Search method: stepwise `auto_arima` minimizing AIC, `max_p=3`, `max_q=3`,
  `max_P=1`, `max_Q=1`, `m=24`
- Selected order (p, d, q)(P, D, Q, m): **_**
- AIC: **_**

> `max_P`/`max_Q` were capped at 1 by default to keep the search tractable
> within the project deadline; widen to 2 if compute time allows and record
> whether it changes the selected order.

### Residual Diagnostics

_Summarize what the residual diagnostics plot showed: are residuals
approximately white noise, roughly normal, with no remaining significant
autocorrelation? Note anything of concern._

---

## 6. Model Evaluation

Metrics computed on the held-out test set (same metric set as Member 1's
regression models, for direct comparability):

| Metric | Value |
|---|---|
| MAE | |
| RMSE | |
| MAPE | |
| R² | |

### Actual vs Predicted

_Insert scatter plot / description of fit quality._

### Residual / Error Analysis

- Mean residual: **_** kW (should be close to 0 if unbiased)
- Residual std: **_** kW
- Any visible pattern over time (e.g., systematic under/over-prediction at
  particular hours or seasons)?

### High-Demand Period Error Analysis

Evaluated separately on the top 10% highest-demand hours in the test set,
since average accuracy can mask poor performance exactly when it matters
most operationally.

| Metric | High-demand subset |
|---|---|
| Threshold (kW) | |
| N points | |
| MAE | |
| RMSE | |
| MAPE | |

---

## 7. Comparison vs Baseline / Regression Models

_To be completed jointly with Member 1 and Member 3 once all model results
are collected. Summarize how the selected classical model (ARIMA or SARIMA)
compares against the Naive / Previous-Day / Moving-Average baselines and
against Linear Regression / Random Forest / Gradient Boosting / XGBoost._

| Model | MAE | RMSE | MAPE | R² |
|---|---|---|---|---|
| Naive (baseline) | | | | |
| Previous-Day (baseline) | | | | |
| Moving Average (baseline) | | | | |
| Linear Regression | | | | |
| Random Forest | | | | |
| Gradient Boosting / XGBoost | | | | |
| **ARIMA** | | | | |
| **SARIMA** | | | | |

---

## 8. Conclusion

_Summarize: which classical model was best (ARIMA vs SARIMA), why, and how
it stacks up against the group's non-DL models overall. Note any
limitations (e.g., resampling to hourly, seasonal-order search capped for
runtime) that should carry forward into the final system design._

---

## 9. Artifacts Handed Off to Member 3

| Artifact | Path |
|---|---|
| Saved model | `models/<arima or sarima>_model.pkl` |
| Test predictions (actual vs predicted) | `reports/classical_timeseries_predictions.csv` |
| Metrics + run metadata (JSON) | `reports/classical_timeseries_metrics.json` |

---

## 10. Technologies Used

- Python
- pandas, NumPy
- statsmodels (`adfuller`, `seasonal_decompose`, SARIMAX diagnostics)
- pmdarima (`auto_arima`)
- scikit-learn (evaluation metrics)
- matplotlib, seaborn (visualization)
- joblib (model persistence)

## 11. Project Structure

```text
data/
└── feature_engineered_dataset.csv

notebooks/
└── classical_timeseries.ipynb

src/
└── classical_timeseries.py

models/
└── <arima or sarima>_model.pkl

reports/
├── member2_classical_timeseries_report.md   (this file)
├── classical_timeseries_predictions.csv
└── classical_timeseries_metrics.json
```
