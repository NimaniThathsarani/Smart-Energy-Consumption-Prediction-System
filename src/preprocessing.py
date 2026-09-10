"""Member 2 preprocessing pipeline for the household energy dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from .cleaning import clean_member1_data, load_raw_data
    from .validation import (
        EXPECTED_COLUMNS,
        MEASUREMENT_COLUMNS,
        quality_check_passed,
        validate_dataframe,
    )
except ImportError:  # Support direct execution as ``python src/preprocessing.py``.
    from cleaning import clean_member1_data, load_raw_data
    from validation import (
        EXPECTED_COLUMNS,
        MEASUREMENT_COLUMNS,
        quality_check_passed,
        validate_dataframe,
    )

DATE_FORMAT = "%d/%m/%Y %H:%M:%S"


def standardize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Parse fields, enforce numeric types, sort timestamps, and set schema."""

    standardized = df.copy()
    standardized.columns = [column.strip() for column in standardized.columns]

    if "Timestamp" not in standardized:
        datetime_text = (
            standardized["Date"].astype(str)
            + " "
            + standardized["Time"].astype(str)
        )
        standardized["Timestamp"] = pd.to_datetime(
            datetime_text,
            format=DATE_FORMAT,
            errors="coerce",
        )
    else:
        standardized["Timestamp"] = pd.to_datetime(
            standardized["Timestamp"], errors="coerce"
        )

    for column in MEASUREMENT_COLUMNS:
        standardized[column] = pd.to_numeric(
            standardized[column], errors="coerce"
        ).astype("float64")

    standardized["Date"] = standardized["Date"].astype("string")
    standardized["Time"] = standardized["Time"].astype("string")
    standardized = standardized.sort_values("Timestamp", kind="mergesort")
    standardized = standardized[EXPECTED_COLUMNS].reset_index(drop=True)

    return standardized


def load_intermediate_data(input_path: str | Path) -> pd.DataFrame:
    """Load the Member 1 CSV and parse its timestamp and measurements."""

    dataframe = pd.read_csv(input_path, low_memory=False)
    return standardize_dataframe(dataframe)


def preprocess_raw_data(
    raw_path: str | Path,
    intermediate_path: str | Path | None = None,
    max_gap: int = 5,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run Member 1 cleaning, then Member 2 standardization and sorting."""

    raw_dataframe = load_raw_data(raw_path)
    cleaned_dataframe, cleaning_summary = clean_member1_data(
        raw_dataframe,
        max_gap=max_gap,
    )
    standardized_dataframe = standardize_dataframe(cleaned_dataframe)

    if intermediate_path is not None:
        intermediate_path = Path(intermediate_path)
        intermediate_path.parent.mkdir(parents=True, exist_ok=True)
        standardized_dataframe.to_csv(intermediate_path, index=False)

    return standardized_dataframe, cleaning_summary


def run_pipeline(
    input_path: str | Path,
    output_path: str | Path,
    report_path: str | Path | None = None,
    input_kind: str = "intermediate",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Create the final CSV and JSON-friendly quality report."""

    if input_kind == "raw":
        dataframe, cleaning_summary = preprocess_raw_data(input_path)
    elif input_kind == "intermediate":
        dataframe = load_intermediate_data(input_path)
        cleaning_summary = None
    else:
        raise ValueError("input_kind must be 'raw' or 'intermediate'")

    summary = validate_dataframe(dataframe)
    summary["input_kind"] = input_kind
    summary["cleaning_summary"] = cleaning_summary
    summary["long_gap_policy"] = (
        "Retain timestamp rows and remaining measurement NaN values. "
        "Downstream model-specific steps must handle or exclude them explicitly."
    )
    summary["quality_check_passed"] = quality_check_passed(summary)

    if not summary["quality_check_passed"]:
        raise ValueError(
            "Final data-quality checks failed; inspect the validation summary "
            "before writing the processed dataset."
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False, date_format=DATE_FORMAT)

    if report_path is not None:
        report_path = Path(report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(summary, indent=2),
            encoding="utf-8",
        )

    return dataframe, summary


def main() -> None:
    """Run the pipeline from the command line."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input CSV or raw TXT")
    parser.add_argument("--output", required=True, help="Final processed CSV")
    parser.add_argument("--report", required=True, help="Validation JSON report")
    parser.add_argument(
        "--input-kind",
        choices=["intermediate", "raw"],
        default="intermediate",
    )
    args = parser.parse_args()

    _, summary = run_pipeline(
        args.input,
        args.output,
        args.report,
        input_kind=args.input_kind,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
