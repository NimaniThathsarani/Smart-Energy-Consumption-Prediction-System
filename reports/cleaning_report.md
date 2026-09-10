# Data Cleaning Report

## Smart Energy Consumption Prediction System

### Data Engineering & Preprocessing

---

## 1. Purpose

This report summarizes the data-cleaning activities performed on the
Individual Household Electric Power Consumption dataset.

The purpose of this stage was to inspect and clean the raw energy data
before handing it over to the preprocessing and validation stage.

---

## 2. Raw Dataset

**Dataset:** Individual Household Electric Power Consumption

**Raw file:** `household_power_consumption.txt`

**Format:** Semicolon-separated text file

**Number of rows:** 2,075,259

**Number of original columns:** 9

### Original Columns

- Date
- Time
- Global_active_power
- Global_reactive_power
- Voltage
- Global_intensity
- Sub_metering_1
- Sub_metering_2
- Sub_metering_3

The raw dataset was preserved without modification.

---

## 3. Target and Timestamp Identification

The raw dataset contains separate `Date` and `Time` columns.

These columns were combined during cleaning to create:

`Timestamp`

The main prediction target selected for the project is:

`Global_active_power`

The remaining electrical measurements are retained as supporting variables.

---

## 4. Missing Value Analysis

Missing values were represented by `?` in the original text file and were
converted to `NaN` when loading the dataset with pandas.

### Initial Missing Values

| Column | Missing Values | Percentage |
|---|---:|---:|
| Date | 0 | 0.00% |
| Time | 0 | 0.00% |
| Global_active_power | 25,979 | 1.25% |
| Global_reactive_power | 25,979 | 1.25% |
| Voltage | 25,979 | 1.25% |
| Global_intensity | 25,979 | 1.25% |
| Sub_metering_1 | 25,979 | 1.25% |
| Sub_metering_2 | 25,979 | 1.25% |
| Sub_metering_3 | 25,979 | 1.25% |

The identical missing-value counts across all seven measurement columns
indicate that complete electrical measurement records are missing at
certain timestamps rather than isolated individual values.

Missing periods were also analyzed as consecutive runs.

---

## 5. Missing Value Treatment

A conservative time-series cleaning strategy was used.

- Missing periods of 5 minutes or less were treated using linear interpolation.
- Interpolation was restricted to values located between valid observations.
- Longer missing periods were retained as missing values.
- Timestamp rows were not deleted.
- Long gaps were not interpolated because doing so could create unrealistic
  synthetic electricity-consumption patterns.

### Treatment Result

**Short missing rows interpolated:** 76

**Long-gap rows retained:** 25903

**Remaining missing values per measurement column:** 25,903

---

## 6. Duplicate Analysis

Two types of duplicates were checked:

1. Fully identical records
2. Repeated `Date` and `Time` combinations

### Results

**Exact duplicate rows:** 0

**Duplicate timestamps:** 0

No duplicate records required removal.

---

## 7. Invalid and Inconsistent Value Checking

Electrical measurement columns were checked for:

- Unexpected non-numeric values
- Positive infinity
- Negative infinity
- Negative measurement values
- Zero values
- Suspicious minimum and maximum values

### Findings

- No unexpected non-numeric measurement values were identified.
- No infinite values were identified.
- No negative electrical measurement values were identified.
- Zero values were retained because zero consumption or zero sub-metering
  may represent valid measurements.
- Extreme values were not classified as invalid solely because of their magnitude.

---

## 8. Datetime Handling

The original dataset stored date and time separately.

The following fields:

`Date`

and

`Time`

were combined into a new:

`Timestamp`

column.

The explicit datetime format used was:

`%d/%m/%Y %H:%M:%S`

### Validation

**Invalid timestamps:** 0

All date-time values were converted successfully.

The original `Date` and `Time` columns were retained for traceability.

Chronological sorting and timestamp-frequency validation were not performed
during this stage because they belong to the preprocessing and validation stage.

---

## 9. Outlier Analysis

The Interquartile Range (IQR) method was used to identify statistical
outlier candidates.

For each electrical measurement:

- Q1 was calculated.
- Q3 was calculated.
- IQR was calculated as `Q3 - Q1`.
- Lower and upper statistical limits were calculated using `1.5 × IQR`.

Statistical outliers were treated as investigation candidates rather than
automatic errors.

High `Global_active_power` observations were inspected together with:

- Global_intensity
- Voltage
- Sub_metering_1
- Sub_metering_2
- Sub_metering_3

Extreme electricity-demand values were retained when there was no clear
evidence that they represented measurement errors.

This decision is important because genuine peaks may be useful for
peak-demand prediction and anomaly-detection tasks.

### Outlier Result

No observations were removed solely because they were identified by the
IQR method.

---

## 10. Intermediate Cleaned Dataset

The output of the Data Cleaning stage is:

`data/interim/energy_cleaned_intermediate.csv`

This dataset contains the results of Member 1 cleaning and is intended as
an intermediate handoff dataset.

It is not the final processed dataset.

The final dataset will be created after:

- Chronological sorting
- Frequency and timestamp validation
- Data type standardization
- Reusable preprocessing pipeline execution
- Final data-quality validation

---

## 11. Cleaning Decisions Summary

| Data Quality Issue | Action |
|---|---|
| Missing measurement values | Investigated |
| Short missing gaps | Linear interpolation |
| Long missing gaps | Retained as missing |
| Exact duplicates | Checked; none found |
| Duplicate timestamps | Checked; none found |
| Invalid numeric values | Checked |
| Negative measurements | Checked; none identified |
| Date and time | Combined into Timestamp |
| Invalid timestamps | Checked; none identified |
| Statistical outliers | Investigated and retained unless clearly invalid |
| Raw dataset | Preserved unchanged |

---

## 12. Handoff

The cleaned intermediate dataset is ready to be passed to the
Data Pipeline & Validation stage.

The next stage is responsible for:

- Chronological sorting
- Frequency/timestamp validation
- Data type standardization
- Reusable preprocessing pipeline
- Final quality checks
- Data dictionary and documentation
- Creation of the final processed dataset