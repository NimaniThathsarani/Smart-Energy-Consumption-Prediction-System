# Data Quality Report

## Scope

This report covers Member 2 Data Pipeline & Validation work performed on `data/interim/energy_cleaned_intermediate.csv`.

## Processing Steps

1. Read the Member 1 intermediate dataset.
2. Parse `Timestamp` explicitly and coerce all seven measurement fields to `float64`.
3. Retain the original `Date` and `Time` fields for traceability.
4. Sort rows by `Timestamp` using a stable sort.
5. Validate schema, timestamp validity, chronological order, duplicate rows, duplicate timestamps, one-minute frequency, missing timestamps, and measurement constraints.
6. Write `data/processed/energy_clean.csv` only after all structural checks pass.

## Final Validation Results

| Check | Result |
|---|---:|
| Rows | 2,075,259 |
| Columns | 10 |
| Timestamp range | 2006-12-16 17:24:00 to 2010-11-26 21:02:00 |
| Chronologically sorted | Yes |
| Duplicate rows | 0 |
| Duplicate timestamps | 0 |
| Invalid timestamps | 0 |
| Irregular intervals | 0 |
| Missing timestamps | 0 |
| Observed cadence | 1 minute |
| Missing values per measurement column | 25,903 |
| Negative measurements | 0 |
| Infinite measurements | 0 |
| IQR outliers removed | 0 |

## Long-Gap Decision

The final processed dataset preserves all timestamp rows and the 25,903 remaining missing measurement rows. This maintains the observed time axis for forecasting, anomaly detection, and later window construction. Long gaps are not imputed at this shared data-engineering stage. Downstream teams must document any model-specific complete-case filtering or imputation.

## Reproducibility

Run the pipeline from the repository root:

```powershell
python src/preprocessing.py --input data/interim/energy_cleaned_intermediate.csv --output data/processed/energy_clean.csv --report reports/data_quality_summary.json
```

Use `--input-kind raw` with the raw text file to reproduce Member 1 cleaning followed by Member 2 processing in one command.
