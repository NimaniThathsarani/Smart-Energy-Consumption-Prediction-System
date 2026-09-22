# Anomaly Detection Report

Notebook: `notebooks/anomaly_detection.ipynb`
Outputs: `reports/anomalies.csv`, `reports/anomaly_scores_hourly.csv`, `reports/figures/anomaly_timeline_severity.png`

## 1. Objective and input data

Identify unusual household energy consumption and separate it from normal high consumption (for example, daily evening peaks).

Input: Group 4 forecast file `reports/final_dl_predictions.csv` with columns `Datetime`, `Actual`, `Predicted`, `Residual` (Residual = Actual - Predicted).

| Item | Value |
|---|---|
| Rows | 307,058 (minute-level) |
| Period | 2010-04-18 18:06 to 2010-11-26 21:02 (test period of the forecasting models only) |
| Missing values | None |
| Time gaps | ~5 days ending 2010-08-23 00:16 and ~3.75 days ending 2010-09-28 22:01. These are missing data, not anomalies, and were not flagged. |
| Hourly data used for final detection | 5,120 hours (hourly mean of Actual and Predicted) |

Group 2's full feature-engineered dataset was not available in the repository (`data/processed/` only contains `.gitkeep`), so this version uses the Actual/Predicted columns of the forecast file only. Values are in kW.

## 2. Definition of normal and anomalous consumption

- **Normal:** consumption that is in the usual range for its hour of day and recent weeks, including regular daily peaks.
- **Anomalous:** consumption that is unusual for its context: much higher than usual for that hour of day compared with recent weeks, unusual in the combined pattern seen by Isolation Forest, or clearly different from what the forecasting model expected.
- A high value alone is not an anomaly. Evening peaks of 3-4 kW appear on many days and were not flagged unless they were also unusual for their context.

### Normal consumption patterns (hourly means, notebook section 3)

- **Daily shape:** consumption is lowest between about 03:00 and 05:00 (roughly 0.4-0.5 kW) and highest in the evening, around 20:00-21:00.
- **Weekdays:** a sharp rise at 07:00 to about 1.45 kW, a slow decline through the day to about 0.75 kW at 16:00, then the evening peak of about 1.45 kW at 20:00.
- **Weekends:** a later and gentler morning rise, higher midday use (about 1.2 kW) than on weekdays, and a higher evening peak of about 1.7 kW at 21:00.
- **Spread:** night hours are very stable (narrow boxes in the boxplot), while daytime and evening hours vary widely, with ordinary hourly values reaching 3-4 kW. This is why a small deviation at night is more unusual than a large value in the evening.
- **Monthly mean (kW):** April 0.95, May 1.10, June 0.97, July 0.72, August 0.59, September 0.95, October 1.16, November 1.20. The August low and the October-November high are level shifts that a single global baseline would misread as anomalies.

## 3. Methods and how they were tried

### 3.1 Minute-level residual (Expected vs Actual): first attempt

| Rule | Threshold (kW) | Flagged | % |
|---|---|---|---|
| 2 sigma | 0.414 | 14,767 | 4.81 |
| 3 sigma | 0.620 | 7,415 | 2.41 |
| 4 sigma | 0.827 | 4,473 | 1.46 |
| 5 sigma | 1.034 | 2,762 | 0.90 |
| 6 sigma | 1.241 | 1,746 | 0.57 |
| 99th percentile | 0.991 | 3,071 | 1.00 |
| 99.5th percentile | 1.302 | 1,536 | 0.50 |
| 99.9th percentile | 1.961 | 308 | 0.10 |

Findings:
- The 3-sigma rule flagged about 35 minutes per day, mostly normal spikes from appliances switching on and off.
- Residual spread grows with consumption level (std 0.075 in the lowest fifth of predicted values, 0.370 in the highest), so one global threshold is unfair to high-load periods. A level-scaled z-score (|z| > 4) gave 3,592 flagged minutes in 3,029 events; the median event lasted 1 minute.
- Plots of the longest events (10-03 11:16, 11-14 12:04, 06-06 12:51) show rapid on/off cycling of an appliance, with the forecast lagging one minute behind. These are forecast lag, not abnormal consumption. Of 93 events lasting 3+ minutes, 53 were classified as cycling (residual sign flipping in at least 60% of steps).
- The forecast behaves largely like a one-minute lag: corr(Predicted, Actual) = 0.971 but corr(Predicted, Actual one minute earlier) = 0.996.

Decision: minute-level residuals are not used as a stand-alone anomaly detector. Detection moved to hourly means.

### 3.2 Hourly methods (final)

| Method | Setup | Flagged hours |
|---|---|---|
| Global Z-score (baseline) | Z per (weekday/weekend, hour of day), abs(z) > 3 | 66 |
| IQR (baseline) | 1.5 x IQR per (weekday/weekend, hour of day) | 212 (64 also flagged by Z) |
| Rolling Z (main) | Z vs the same hour over the previous 28 days (min 14 days, current day excluded), abs(z) > 3 | 114 (32 shared with global Z) |
| Isolation Forest (main) | 300 trees, contamination 1%, features: kW, hour sin/cos, weekend flag, 1-hour difference, 24-hour rolling mean and deviation from it | 52 |
| Residual (main) | Robust z of hourly residual (median -0.0172, MAD 0.0172 kW), robust z > 6, about 0.10 kW | 66 |

Why the global baselines were replaced:
- Global Z / IQR use one profile for all seven months. Flags then follow seasonal level (October and November have the highest mean consumption, 1.16 and 1.20 kW) and are concentrated in night hours 02:00-05:00 (38% of flags) because night consumption is low and stable.
- Rolling Z adapts to recent levels and removed the night bias. Its side effect is that after the low-usage period in August (daily mean about 0.4 kW), normal usage returning to higher levels was flagged (27 rolling-Z flags in August, mostly 08-15 and 08-27). Requiring agreement from a second method removed most of these.

Threshold justification:
- Isolation Forest contamination: 0.5% / 1% / 2% flagged 26 / 52 / 103 hours (this count is set by the parameter, not a finding). 1% was chosen as a compromise between too few and too many alerts.
- Residual robust z: >3, >4, >5, >6 flagged 308, 168, 97, 66 hours. The value 6 (about 0.10 kW) avoids alerts for hourly deviations of only a few tens of watts (at K = 4 the cut-off is only 0.069 kW).

### 3.3 Final rule: ensemble of the three main methods

| Severity | Rule | Hours |
|---|---|---|
| high | all 3 methods agree | 16 |
| medium | 2 methods agree | 26 |
| low (watch-list) | 1 method | 132 |
| none | no method | 4,946 |

Anomaly alerts = high + medium = 42 hours (0.82% of hours, about one every 5 days). Low-severity hours are kept in `anomalies.csv` as a watch-list, not as confirmed anomalies.

The three methods use overlapping information (all depend on the same hourly Actual series, and two use the model's short-term behaviour), so "3 methods agree" is best read as higher confidence, not as three independent confirmations.

## 4. Results

Monthly anomaly alerts (2+ methods): Apr 0, May 7, Jun 5, Jul 1, Aug 1, Sep 1, Oct 16, Nov 11. April has 0 because rolling Z needs 14 days of history (`z_roll` is empty at the start of the data).

Patterns around the alerts:
- **Hour of day:** 18:00-21:00 contains 19 of 42 alerts (45%); almost none between 01:00 and 04:00.
- **Day of week:** Saturday 10 and Sunday 11 (21 of 42, 50%; weekend days are 28.6% of days). Thursday 8, Monday 7, Tuesday 3, Friday 2, Wednesday 1.
- **Month:** October and November hold 27 of 42 alerts (64%).
- **Clustering:** 29 days contain an alert; 9 days contain 2+ (2010-11-04 has 5, 2010-10-18 has 3). Mean consumption on alert days was 1.32 kW versus 0.958 kW across all days. Alerts concentrate on high-usage days.
- **Direction:** the strongest alerts are upward spikes (for example 2010-11-20 18:00 at 5.63 kW, 2010-10-31 05:00 at 2.91 kW at night, 2010-07-01 00:00 at 3.33 kW).
- **High values not flagged:** several daily peaks of about 3.3 kW (for example around 2010-10-30) were not flagged, which is the intended behaviour.

## 5. Evaluation

No labelled anomalies exist, so detection was tested by injecting synthetic anomalies into hours that no method had flagged. Precision cannot be measured this way (all real flags would count as false positives by construction), so only recall is reported. Each cell used 30 injected hours, so values are approximate (roughly plus or minus 0.1).

Test A (20 injected hours per type; only Actual changed, the forecast was left unchanged). This is a best case for the residual method:

| Method | Recall |
|---|---|
| Rolling Z | 0.38 |
| Isolation Forest | 0.20 |
| Residual | 1.00 |
| Ensemble >= 2 | 0.45 |
| Ensemble >= 1 | 1.00 |

By type: night spike +2 kW recall 0.75 (rolling Z), daytime spike x2.5 recall 0.40, evening drop x0.2 recall 0.00 for rolling Z, Isolation Forest and Ensemble >= 2.

Test B (spike size sweep). "follow" is the share of the spike the forecast also reproduces. follow = 0 is the best case for the residual method; follow = 0.95 is closer to the real forecast, which mostly tracks recent values (0.95 is an assumption, not a measured value).

Recall for a 2 kW spike:

| Period | follow | Rolling Z | Iso. Forest | Residual | Ens >= 2 | Ens >= 1 |
|---|---|---|---|---|---|---|
| Night | 0 | 0.83 | 0.27 | 1.00 | 0.87 | 1.00 |
| Night | 0.95 | 0.83 | 0.27 | 0.23 | 0.33 | 0.90 |
| Day | 0 | 0.50 | 0.47 | 1.00 | 0.67 | 1.00 |
| Day | 0.95 | 0.50 | 0.47 | 0.50 | 0.43 | 0.77 |

Spikes of 0.5 kW or less were almost never detected (recall 0.00-0.03), except by the residual method (and Ensemble >= 1, which includes it) when follow = 0. For 1 kW spikes, only rolling Z detected a meaningful share, and only at night (recall 0.37; daytime 0.03; at follow = 0.95 Ensemble >= 2 detected none).

Conclusions:
- The detector reliably finds large deviations (about 2 kW or more); small deviations are treated as normal variation, in line with "not every high value is an anomaly".
- Ensemble >= 2 (alerts) trades recall for fewer false alarms; Ensemble >= 1 has higher recall but flags 174 hours (3.4%), so it is kept as a watch-list.
- Evening drops are not detected by the level-based methods, since low evening values fall within normal variation.
- These tests are only a sanity check. The injection sizes are our own choice and do not measure real-world accuracy.

## 6. Limitations

- The forecasts cover only the test period (about seven months of 2010), so there is no full-year seasonality, and rolling Z has no output for the first two weeks.
- Group 4's forecast is close to a one-minute lag, so residual-based detection only catches sudden changes and misses hour-long abnormal periods that the model follows.
- Rolling Z does not separate weekdays and weekends, so weekend hours may be flagged more often (50% of alerts fall on weekends; this was not tested further).
- Data gaps (August and September) affect the rolling windows around them. Flags on 2010-08-15 and 2010-08-27 are probably a level shift after a low-usage period, not real anomalies.
- Sub-metering and other Group 2 features were not used, so the causes of anomalies (kitchen, laundry, water heater and so on) are not identified.
- No ground-truth labels, so results cannot be validated beyond the synthetic tests above.

## 7. Output files for Groups 6 and 7

`reports/anomalies.csv` contains the 174 hours with severity low, medium or high. `reports/anomaly_scores_hourly.csv` contains all 5,120 hours.

| Column | Meaning |
|---|---|
| Datetime | Hour start time |
| Actual, Predicted, Residual | Hourly mean kW and residual |
| z_roll | Rolling Z-score (empty when there is less than 14 days of history) |
| iso_score | Isolation Forest score (lower = more unusual) |
| resid_rz | Robust z of the hourly residual |
| roll_anom, iso_anom, resid_anom | Flag per main method |
| z_anom, iqr_anom | Flags from the baseline methods (global Z-score, IQR), for comparison |
| methods_agree | Number of main methods that flagged the hour (0-3) |
| severity | none / low / medium / high |
| is_anomaly | True for medium and high |
| direction | higher or lower than expected |
| flagged_by | Names of the methods that flagged the hour |
| hour, weekday | Time features |
