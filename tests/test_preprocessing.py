"""Focused tests for Member 2 preprocessing and validation behavior."""

import pandas as pd

from src.preprocessing import standardize_dataframe
from src.validation import quality_check_passed, validate_dataframe


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


def sample_dataframe() -> pd.DataFrame:
    """Create a small valid minute-level dataset for unit tests."""

    rows = []
    for timestamp in pd.date_range("2006-12-16 17:24:00", periods=3, freq="min"):
        rows.append(
            {
                "Date": timestamp.strftime("%d/%m/%Y"),
                "Time": timestamp.strftime("%H:%M:%S"),
                "Global_active_power": "1.0",
                "Global_reactive_power": "0.1",
                "Voltage": "230.0",
                "Global_intensity": "4.5",
                "Sub_metering_1": "0.0",
                "Sub_metering_2": "0.0",
                "Sub_metering_3": "5.0",
                "Timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    return pd.DataFrame(rows)


def test_standardize_sorts_and_converts_types() -> None:
    """The pipeline should sort timestamps and produce stable dtypes."""

    dataframe = sample_dataframe().iloc[::-1].reset_index(drop=True)

    standardized = standardize_dataframe(dataframe)

    assert standardized["Timestamp"].is_monotonic_increasing
    assert str(standardized["Timestamp"].dtype).startswith("datetime64")
    assert standardized["Global_active_power"].dtype == "float64"
    assert list(standardized.columns) == EXPECTED_COLUMNS


def test_validation_detects_missing_timestamp_interval() -> None:
    """A missing minute must fail cadence validation."""

    dataframe = sample_dataframe().drop(index=1).reset_index(drop=True)
    dataframe = standardize_dataframe(dataframe)

    summary = validate_dataframe(dataframe)

    assert summary["timestamp"]["missing_timestamps"] == 1
    assert not quality_check_passed(summary)


def test_validation_accepts_remaining_measurement_missing_values() -> None:
    """Long-gap NaN values are reported but are not structural failures."""

    dataframe = standardize_dataframe(sample_dataframe())
    dataframe.loc[1, "Global_active_power"] = None

    summary = validate_dataframe(dataframe)

    assert summary["measurements"]["Global_active_power"]["missing_values"] == 1
    assert quality_check_passed(summary)


def test_validation_rejects_negative_measurements() -> None:
    """Negative measurements remain invalid after type conversion."""

    dataframe = standardize_dataframe(sample_dataframe())
    dataframe.loc[0, "Voltage"] = -1

    summary = validate_dataframe(dataframe)

    assert summary["measurements"]["Voltage"]["negative_values"] == 1
    assert not quality_check_passed(summary)
