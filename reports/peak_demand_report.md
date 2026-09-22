# Peak Demand Prediction Report

Notebook: `notebooks/peak_demand_prediction.ipynb`
Outputs: `reports/peak_predictions.csv`, `reports/peak_predictions_hourly.csv`, `reports/peak_approach_comparison.csv`, `reports/peak_hour_metrics.csv`, `reports/peak_dayahead_comparison.csv`, `reports/figures/peak_hours_and_week_zoom.png`, `reports/figures/peak_daily_evaluation.png`

## 1. Objective and input data

Identify historical peak demand patterns, define what counts as a peak, and predict peak value and peak time from the forecasts of Groups 3 and 4. Consumption is in kW (`Global_active_power`, see `data_dictionary.md`).

| File | Source | Used for |
|---|---|---|
| `final_dl_predictions.csv` | Group 4, Tuned LSTM (the selected model in `final_dl_selection.csv`) | Main forecast |
| `xgboost_test_predictions.csv` | Group 3, XGBoost | Comparison |
| `classical_timeseries_predictions.csv` | Group 3, ARIMA (hourly) | Classical baseline |

`lstm_predictions.csv` and `gru_predictions.csv` were not used: they have no `Datetime` column and their values are scaled.

- All forecasts cover only the test period, 2010-04-18 to 2010-11-26. Minute-level forecasts were averaged to hourly means. The three files share 5,120 common hours, and their Actual values differ by at most 0.05 kW.
- Group 2's feature-engineered dataset was not in the repository (`data/processed/` contains only `.gitkeep`), so all analysis uses the Actual and Predicted columns of the forecast files.

## 2. Historical peak analysis (Actual, 5,120 hours)

- Highest hourly value: 5.627 kW on 2010-11-20 18:00. Next highest: 4.463 kW (2010-11-04 20:00), 4.419 kW (2010-11-04 08:00), 4.157 kW (2010-11-14 15:00), 4.118 kW (2010-10-14 19:00).
- Percentiles of hourly kW: 80th 1.547, 90th 1.931, 95th 2.330, 99th 3.128.
- 213 days had at least 20 hours of data. The mean daily peak is 2.362 kW.
- **Peak hour of the day:** 20:00 on 34 days, 07:00 on 27, 21:00 on 25, 08:00 on 15, 23:00 on 13, 19:00 on 11.
- **Peak period:** evening (18:00-22:00) 40.8% of days, other hours 35.2%, morning (06:00-09:00) 23.9%.
- **Weekdays vs weekends (read from the notebook charts, approximate):** on weekdays the daily peak falls in the evening on about 43% of days and in the morning on about 28%; on weekends the morning peak is less common (about 12%) and about half of the peaks occur outside the morning and evening windows. The mean daily peak is higher on weekends (about 2.6 kW) than on weekdays (about 2.3 kW).
- **By month (approximate):** the mean daily peak is lowest in August (about 1.5 kW) and highest in October and November (about 2.9-3.0 kW). The maximum daily peak of 5.6 kW is in November.

## 3. Peak definition

| Level | Rule | Threshold | Hours |
|---|---|---|---|
| High demand | hourly mean >= 75th percentile | 1.432 kW | - |
| Peak | hourly mean >= 95th percentile | 2.330 kW | 256 of 5,120 |
| Extreme peak | hourly mean >= 99th percentile | 3.128 kW | 52 |

Group 2's `Peak` feature marks values above the 75th percentile of minute-level `Global_active_power`. The "high demand" level here corresponds to that idea; "peak" is deliberately stricter (about 5% of hours). A daily peak is the highest hourly mean of each day, together with its hour. Thresholds were computed from the same period that is evaluated (the only period available), which is a limitation.

## 4. Approaches compared

1. **Forecast-based:** each model's hourly forecast is treated as the prediction. A predicted peak hour is one with forecast >= 2.330 kW; the predicted daily peak is the highest forecast hour of the day (value, time, and period).
2. **Day-ahead (history-based):** uses only earlier days: yesterday's peak, same day last week, mean of the previous 14 days (most common peak hour), and a Random Forest trained on the first 70% of days (146 days) and tested on the last 63 days (2010-09-21 to 2010-11-26). Features: weekday, previous day's peak, 7-day mean peak, peak 7 days earlier, previous day's mean kW, previous day's evening flag.

## 5. Results

### 5.1 Hourly accuracy (5,120 common hours)

| Model | MAE (kW) | RMSE (kW) | Bias (kW) | Highest forecast (kW) |
|---|---|---|---|---|
| Tuned LSTM (Group 4) | 0.0238 | 0.0314 | +0.0125 | 5.467 |
| XGBoost (Group 3) | 0.0088 | 0.0141 | -0.0004 | 5.651 |
| ARIMA (Group 3) | 0.5949 | 0.7165 | +0.0407 | 1.090 |

The highest actual value is 5.627 kW. ARIMA never forecasts above 1.09 kW, so it cannot find peaks.

### 5.2 Peak hour detection (peak threshold 2.330 kW, 256 actual peak hours)

| Model | Flagged | Precision | Recall | F1 | MAE on peak hours (kW) | RMSE on peak hours (kW) | Bias on peak hours (kW) |
|---|---|---|---|---|---|---|---|
| Tuned LSTM | 252 | 0.988 | 0.973 | 0.980 | 0.057 | 0.080 | -0.051 |
| XGBoost | 253 | 0.988 | 0.977 | 0.982 | 0.022 | 0.028 | -0.003 |
| ARIMA | 0 | 0.000 | 0.000 | 0.000 | 1.852 | 1.911 | -1.852 |

Using each model's own 95th percentile as threshold (ARIMA: 1.081 kW) gives F1 0.980 (LSTM), 0.984 (XGBoost) and 0.027 (ARIMA).

### 5.3 Daily peak value and time (213 days)

| Approach | Peak MAE (kW) | Peak RMSE (kW) | Bias (kW) | Time exact | Within 1 h | Within 2 h |
|---|---|---|---|---|---|---|
| Tuned LSTM (forecast-based) | 0.041 | 0.064 | -0.030 | 0.944 | 0.953 | 0.958 |
| XGBoost (forecast-based) | 0.019 | 0.027 | -0.003 | 0.981 | 0.986 | 0.995 |
| ARIMA (forecast-based) | 1.366 | 1.557 | -1.363 | 0.033 | 0.113 | 0.169 |
| Yesterday's peak | 0.572 | 0.778 | -0.001 | 0.137 | 0.307 | 0.406 |
| Same day last week | 0.563 | 0.758 | 0.024 | 0.117 | 0.223 | 0.294 |
| Mean of last 14 days | 0.485 | 0.623 | -0.020 | 0.146 | 0.291 | 0.359 |

Hour distances are circular (23:00 and 00:00 are 1 hour apart). Always predicting 20:00 (the most common peak hour) gives exact 0.160, within 1 h 0.329, within 2 h 0.408.

### 5.4 Peak period (morning / evening / other)

| Approach | Accuracy |
|---|---|
| Tuned LSTM (forecast-based) | 0.962 |
| XGBoost (forecast-based) | 0.986 |
| ARIMA (forecast-based) | 0.352 |
| Yesterday's period | 0.472 |
| Most common period, last 14 days | 0.403 |
| Always "evening" | 0.408 |

### 5.5 Day-ahead models on the last 63 days

| Approach | Peak MAE (kW) | Peak RMSE (kW) | Period accuracy |
|---|---|---|---|
| Random Forest (day-ahead) | 0.597 | 0.792 | 0.365 |
| Last 14 days (day-ahead) | 0.528 | 0.722 | 0.349 |
| Yesterday (day-ahead) | 0.702 | 0.988 | 0.349 |
| Constant: training mean, "evening" | 0.755 | 1.000 | 0.413 |
| Tuned LSTM (forecast-based, same days) | 0.063 | 0.092 | 0.921 |
| XGBoost (forecast-based, same days) | 0.024 | 0.031 | 1.000 |

The Random Forest did not beat the simple "last 14 days" baseline on peak value, and no history-based approach beat the constant "evening" guess on period accuracy by a meaningful margin.

### 5.6 Visual checks (figures)

- In `peak_hours_and_week_zoom.png`, LSTM-predicted peak hours overlap almost all actual peak hours, and in the one-week zoom the forecast follows the actual curve closely.
- In `peak_daily_evaluation.png`, predicted vs actual daily peaks lie close to the diagonal (the largest peaks are slightly underestimated), and the timing error is zero on most days, with a small number of days with large errors (clipped at +-6 hours in the chart).

## 6. Selected methods and justification

- **Main method: Tuned LSTM, forecast-based.** It is the model selected by Group 4. It finds 97% of peak hours with 99% precision, predicts the daily peak value within about 0.04 kW on average, and gets the peak time exactly right on 94% of days.
- **Comparison: XGBoost, forecast-based.** It is more accurate on every measure (daily peak MAE 0.019 kW, timing exact 98%). Its input features could not be checked because `regression_models.ipynb` and `src/regression_models.py` are empty in the repository, and its minute-level R2 of 0.9989 (`final_dl_vs_xgboost.csv`) is much higher than the LSTM's 0.942. If it uses same-minute measurements (for example `Global_intensity`) as inputs, its accuracy would not be a genuine forecast. Until this is confirmed with Group 3, XGBoost results are reported as unverified.
- **Baseline: ARIMA.** It cannot forecast peaks and is only used to show that the neural and boosted models add value.
- **Day-ahead prediction:** the mean of the last 14 days is the best simple baseline for peak value (MAE about 0.49-0.53 kW). Timing and period are hard to predict from history alone.

## 7. Limitations

- **The forecasts are one-step-ahead.** Group 4's forecast follows the previous minute's actual value closely (correlation 0.996 with the previous minute), so it finds peak hours almost perfectly once they are happening. The 94-99% results in sections 5.2-5.4 are not the accuracy of warning about a peak in advance. The day-ahead results in sections 5.3 and 5.5 (value error about 0.5-0.6 kW, timing exact on 12-15% of days) are a more realistic picture of predicting peaks ahead of time.
- **No forecasts beyond 2010-11-26.** The provided files only cover the test period, so no true future dates were predicted. The Groups 3 and 4 models would have to be run forward for that.
- **Short history.** Only about seven months are available, so yearly patterns cannot be assessed, and the day-ahead test uses 63 days, so those results are noisy. The test days (late September to November) have higher consumption than most training days, which also affects the day-ahead comparison.
- **Threshold from the evaluation period.** Peak thresholds use the same period that is evaluated.
- **Peak underestimation.** The LSTM underestimates peak hours by about 0.05 kW on average and the largest daily peaks slightly more.
- **Timing errors.** A few percent of days have a large timing error; this probably happens when a morning and an evening peak have similar values, but this was not investigated further.
- Group 3's feature set could not be checked (section 6).

## 8. Output files

`reports/peak_predictions.csv` (213 days, main file for Groups 6 and 7):

| Column | Meaning |
|---|---|
| Date | Day |
| actual_peak_kw, actual_peak_time, actual_peak_period | Actual highest hourly mean, its hour, and its period (morning / evening / other) |
| pred_peak_kw, pred_peak_time, pred_peak_period | Tuned LSTM forecast-based prediction of the same |
| peak_error_kw, timing_error_hours | Predicted minus actual value; predicted minus actual time in hours |
| actual_extreme_day, pred_extreme_day | Daily peak >= 3.128 kW (actual / predicted) |
| xgb_peak_kw, xgb_peak_time | XGBoost comparison (unverified features) |
| dayahead_peak_kw, dayahead_peak_hour | Day-ahead baseline: mean of the previous 14 daily peaks, and their most common peak hour (empty for the first days) |

`reports/peak_predictions_hourly.csv` (5,120 hours): `Datetime`, `Actual`, `Predicted_LSTM`, `Predicted_XGBoost`, `actual_high_demand`, `actual_peak`, `actual_extreme_peak`, `pred_peak_lstm`, `pred_peak_xgboost`.

`reports/peak_approach_comparison.csv` (section 5.3), `reports/peak_hour_metrics.csv` (section 5.2) and `reports/peak_dayahead_comparison.csv` (section 5.5) hold the comparison tables.
