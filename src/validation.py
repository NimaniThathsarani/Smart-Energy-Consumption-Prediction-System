"""Reusable data-quality checks for the processed energy dataset."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


EXPECTED_COLUMNS = [
    "Date",
    "Time",
    "Global_active_power",
    "Global_reactive_power",
    "Voltage",
    "Global_intensity",
    "Sub_metering_1",
    "Sub_metering_2",
    "Sub_metering_3",
    "Timestamp",
]

MEASUREMENT_COLUMNS = [
    "Global_active_power",
    "Global_reactive_power",
    "Voltage",
    "Global_intensity",
    "Sub_metering_1",
    "Sub_metering_2",
    "Sub_metering_3",
]

TARGET_COLUMN = "Global_active_power"
EXPECTED_FREQUENCY = pd.Timedelta(minutes=1)


def validate_schema(df: pd.DataFrame) -> dict[str, Any]:
    """Return missing, unexpected, and ordered-column schema findings."""

    actual_columns = list(df.columns)
    missing_columns = [
        column for column in EXPECTED_COLUMNS if column not in actual_columns
    ]
    unexpected_columns = [
        column for column in actual_columns if column not in EXPECTED_COLUMNS
    ]

    return {
        "expected_columns": EXPECTED_COLUMNS.copy(),
        "actual_columns": actual_columns,
        "missing_columns": missing_columns,
        "unexpected_columns": unexpected_columns,
        "columns_in_expected_order": actual_columns == EXPECTED_COLUMNS,
    }


def validate_timestamps(
    df: pd.DataFrame,
    frequency: pd.Timedelta = EXPECTED_FREQUENCY,
) -> dict[str, Any]:
    """Check timestamp validity, order, duplicates, cadence, and gaps."""

    timestamps = pd.to_datetime(df["Timestamp"], errors="coerce")
    sorted_timestamps = timestamps.sort_values()
    differences = sorted_timestamps.diff().dropna()
    irregular_differences = differences[differences != frequency]

    if timestamps.notna().any():
        expected = pd.date_range(
            start=timestamps.min(),
            end=timestamps.max(),
            freq=frequency,
        )
        observed = pd.DatetimeIndex(timestamps.dropna().unique()).sort_values()
        missing_timestamps = expected.difference(observed)
    else:
        missing_timestamps = pd.DatetimeIndex([])

    return {
        "invalid_timestamps": int(timestamps.isna().sum()),
        "chronologically_sorted": bool(timestamps.is_monotonic_increasing),
        "duplicate_timestamps": int(timestamps.duplicated().sum()),
        "expected_frequency": str(frequency),
        "observed_frequency_values": {
            str(value): int(count)
            for value, count in differences.value_counts().items()
        },
        "irregular_intervals": int(len(irregular_differences)),
        "missing_timestamps": int(len(missing_timestamps)),
        "first_missing_timestamp": (
            missing_timestamps[0].isoformat()
            if len(missing_timestamps) else None
        ),
        "last_missing_timestamp": (
            missing_timestamps[-1].isoformat()
            if len(missing_timestamps) else None
        ),
        "start_timestamp": (
            timestamps.min().isoformat()
            if timestamps.notna().any() else None
        ),
        "end_timestamp": (
            timestamps.max().isoformat()
            if timestamps.notna().any() else None
        ),
    }


def validate_measurements(df: pd.DataFrame) -> dict[str, Any]:
    """Check measurement missingness, finiteness, and negative values."""

    result: dict[str, Any] = {}
    for column in MEASUREMENT_COLUMNS:
        values = pd.to_numeric(df[column], errors="coerce")
        result[column] = {
            "missing_values": int(values.isna().sum()),
            "non_numeric_values": int(
                df[column].notna().sum() - values.notna().sum()
            ),
            "infinite_values": int(
                np.isinf(values.dropna().to_numpy()).sum()
            ),
            "negative_values": int((values < 0).sum()),
            "minimum": (
                float(values.min()) if values.notna().any() else None
            ),
            "maximum": (
                float(values.max()) if values.notna().any() else None
            ),
        }
    return result


def validate_dataframe(
    df: pd.DataFrame,
    frequency: pd.Timedelta = EXPECTED_FREQUENCY,
) -> dict[str, Any]:
    """Run all final quality checks and return a JSON-friendly summary."""

    schema = validate_schema(df)
    timestamp = validate_timestamps(df, frequency=frequency)
    measurements = validate_measurements(df)

    return {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "schema": schema,
        "timestamp": timestamp,
        "exact_duplicate_rows": int(df.duplicated().sum()),
        "measurements": measurements,
        "dtypes": {column: str(dtype) for column, dtype in df.dtypes.items()},
    }


def quality_check_passed(summary: dict[str, Any]) -> bool:
    """Return whether structural and invalid-value checks passed."""

    schema = summary["schema"]
    timestamp = summary["timestamp"]
    measurements = summary["measurements"]

    return all(
        [
            not schema["missing_columns"],
            not schema["unexpected_columns"],
            schema["columns_in_expected_order"],
            timestamp["invalid_timestamps"] == 0,
            timestamp["chronologically_sorted"],
            timestamp["duplicate_timestamps"] == 0,
            timestamp["irregular_intervals"] == 0,
            timestamp["missing_timestamps"] == 0,
            summary["exact_duplicate_rows"] == 0,
            all(item["non_numeric_values"] == 0 for item in measurements.values()),
            all(item["infinite_values"] == 0 for item in measurements.values()),
            all(item["negative_values"] == 0 for item in measurements.values()),
        ]
    )
