# Smart Energy Consumption Prediction System

This project develops a smart household-energy system with time-series
forecasting, regression, LSTM/GRU models, anomaly detection, peak-demand
prediction, clustering, optimization recommendations, and a final dashboard.

## Project Starting Point

The project uses the **Individual Household Electric Power Consumption**
dataset. The raw file contains one household's electricity measurements at
minute-level timestamps.

The main prediction target is `Global_active_power`. `Date` and `Time` are
combined into the validated `Timestamp` field used by every time-series team.

The data-engineering subgroup has two stages:

1. **Member 1 - Data Cleaning:** understands the raw data, handles short
	 missing gaps, checks duplicates and invalid values, creates `Timestamp`,
	 and investigates outliers.
2. **Member 2 - Data Pipeline & Validation:** sorts chronologically, validates
	 timestamp frequency, standardizes data types, runs reusable quality checks,
	 documents the schema, and creates the final processed dataset.

The raw file and large generated CSV files are intentionally ignored by Git.
They must be available locally or regenerated before running the pipeline.

## Repository Structure

```text
data/
	raw/household_power_consumption.txt       Raw input, local only
	interim/energy_cleaned_intermediate.csv   Member 1 output, local only
	processed/energy_clean.csv                Member 2 final output, local only
notebooks/
	01_data_understanding.ipynb               Member 1 exploration
	02_data_cleaning.ipynb                    Member 1 cleaning analysis
	03_data_validation.ipynb                  Member 2 validation analysis
src/
	cleaning.py                               Member 1 reusable cleaning
	preprocessing.py                          Member 2 end-to-end pipeline
	validation.py                             Member 2 reusable checks
tests/test_preprocessing.py                 Member 2 focused tests
reports/
	cleaning_report.md                        Member 1 decisions
	data_quality_report.md                    Final validation explanation
	data_quality_summary.json                 Machine-readable results
	data_dictionary.md                        Final column definitions
```

## Setup

Run these commands from the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, run the Python commands using the virtual
environment interpreter directly: `.venv\Scripts\python.exe`.

## Run Member 2 Pipeline

The normal command starts from Member 1's intermediate output:

```powershell
python src/preprocessing.py --input data/interim/energy_cleaned_intermediate.csv --output data/processed/energy_clean.csv --report reports/data_quality_summary.json
```

The pipeline performs these steps:

1. Loads the intermediate CSV without changing the raw file.
2. Parses `Timestamp` explicitly.
3. Converts all seven measurement columns to `float64`.
4. Sorts records by `Timestamp` in ascending order.
5. Checks schema, chronological order, duplicate rows, duplicate timestamps,
	 invalid timestamps, one-minute frequency, missing timestamps, non-numeric
	 values, infinite values, and negative measurements.
6. Writes the final CSV only when structural quality checks pass.
7. Writes a JSON validation summary for review and automated use.

To reproduce Member 1 cleaning and Member 2 processing directly from the raw
file, use:

```powershell
python src/preprocessing.py --input data/raw/household_power_consumption.txt --input-kind raw --output data/processed/energy_clean.csv --report reports/data_quality_summary.json
```

## Final Dataset Contract

The final output is `data/processed/energy_clean.csv`.

- Expected shape: 2,075,259 rows and 10 columns.
- Expected cadence: one record per minute.
- Expected timestamp range: `2006-12-16 17:24:00` to
	`2010-11-26 21:02:00`.
- Target: `Global_active_power`.
- Timestamp column: `Timestamp`.
- Measurement columns: `Global_active_power`, `Global_reactive_power`,
	`Voltage`, `Global_intensity`, `Sub_metering_1`, `Sub_metering_2`, and
	`Sub_metering_3`.
- `Timestamp` is a datetime in memory. CSV consumers must parse it explicitly.
- Numeric measurement columns are standardized as `float64`.
- `Date` and `Time` remain as strings for traceability.

Member 1 interpolated complete missing runs of five minutes or less. The
remaining 25,903 long-gap rows remain missing in the final shared dataset.
They are not silently interpolated or dropped. Forecasting, LSTM/GRU,
anomaly-detection, and clustering teams must document their own handling,
such as complete-window filtering or model-specific imputation.

Zero measurements and genuine high-consumption peaks are retained. IQR
outlier results are screening information and were not used to delete valid
electricity peaks.

## Verify the Work

Run the focused tests:

```powershell
python -c "import tests.test_preprocessing as t; t.test_standardize_sorts_and_converts_types(); t.test_validation_detects_missing_timestamp_interval(); t.test_validation_accepts_remaining_measurement_missing_values(); t.test_validation_rejects_negative_measurements(); print('All tests passed')"
```

Also verify the Python files and notebook/report JSON:

```powershell
python -m compileall -q src tests
python -m json.tool notebooks/03_data_validation.ipynb > $null
python -m json.tool reports/data_quality_summary.json > $null
```

The expected final quality results are zero invalid timestamps, zero
duplicate timestamps, zero missing timestamps, zero irregular intervals,
zero negative measurements, and one-minute observed frequency.

## Documentation

- [Member 1 cleaning decisions](reports/cleaning_report.md)
- [Member 2 quality report](reports/data_quality_report.md)
- [Final data dictionary](reports/data_dictionary.md)
- [Validation notebook](notebooks/03_data_validation.ipynb)
