# Import required libraries
from pathlib import Path

import numpy as np
import pandas as pd


# Define electrical measurement columns
MEASUREMENT_COLS = [
    "Global_active_power",
    "Global_reactive_power",
    "Voltage",
    "Global_intensity",
    "Sub_metering_1",
    "Sub_metering_2",
    "Sub_metering_3",
]


def load_raw_data(file_path):
    """Load the raw household electricity dataset."""

    # Read semicolon-separated data and treat '?' as missing
    df = pd.read_csv(
        file_path,
        sep=";",
        na_values="?",
        low_memory=False,
    )

    return df


def add_timestamp(df):
    """Combine Date and Time into a validated Timestamp column."""

    # Work on a copy to preserve the original dataframe
    clean_df = df.copy()

    # Combine the raw date and time strings
    datetime_text = (
        clean_df["Date"].astype(str)
        + " "
        + clean_df["Time"].astype(str)
    )

    # Convert the combined values to datetime
    clean_df["Timestamp"] = pd.to_datetime(
        datetime_text,
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce",
    )

    return clean_df


def handle_short_missing_gaps(df, max_gap=5):
    """Interpolate complete missing measurement gaps up to max_gap rows."""

    # Work on a copy before filling values
    clean_df = df.copy()

    # Identify rows where all measurements are missing
    all_missing_mask = (
        clean_df[MEASUREMENT_COLS]
        .isna()
        .all(axis=1)
    )

    # Create IDs for consecutive missing/non-missing runs
    group_id = all_missing_mask.ne(
        all_missing_mask.shift()
    ).cumsum()

    # Calculate the length of each missing run
    missing_runs = (
        all_missing_mask[all_missing_mask]
        .groupby(group_id[all_missing_mask])
        .size()
    )

    # Identify runs eligible for interpolation
    short_run_ids = missing_runs[
        missing_runs <= max_gap
    ].index

    # Mark rows belonging to short missing runs
    short_gap_mask = (
        all_missing_mask
        & group_id.isin(short_run_ids)
    )

    # Generate possible interpolated measurements
    interpolated_values = (
        clean_df[MEASUREMENT_COLS]
        .interpolate(
            method="linear",
            limit_area="inside",
        )
    )

    # Fill only rows belonging to short gaps
    clean_df.loc[
        short_gap_mask,
        MEASUREMENT_COLS,
    ] = interpolated_values.loc[
        short_gap_mask,
        MEASUREMENT_COLS,
    ]

    # Count successfully interpolated rows
    interpolated_rows = (
        clean_df.loc[
            short_gap_mask,
            MEASUREMENT_COLS,
        ]
        .notna()
        .all(axis=1)
        .sum()
    )

    return clean_df, int(interpolated_rows)


def remove_exact_duplicates(df):
    """Remove fully identical duplicate records."""

    # Record row count before duplicate removal
    rows_before = len(df)

    # Remove only exact duplicate rows
    clean_df = df.drop_duplicates().copy()

    # Calculate how many rows were removed
    removed_count = rows_before - len(clean_df)

    return clean_df, removed_count


def validate_measurements(df):
    """Check electrical measurements for clear invalid values."""

    validation = {}

    for column in MEASUREMENT_COLS:

        # Check negative values
        negative_count = (
            df[column] < 0
        ).sum()

        # Check infinite values
        infinite_count = np.isinf(
            df[column].dropna()
        ).sum()

        validation[column] = {
            "negative_values": int(negative_count),
            "infinite_values": int(infinite_count),
            "missing_values": int(
                df[column].isna().sum()
            ),
            "minimum": df[column].min(),
            "maximum": df[column].max(),
        }

    return validation


def clean_member1_data(df, max_gap=5):
    """Apply the reusable Member 1 data-cleaning operations."""

    # Add validated Timestamp column
    clean_df = add_timestamp(df)

    # Handle only short missing measurement gaps
    clean_df, interpolated_rows = (
        handle_short_missing_gaps(
            clean_df,
            max_gap=max_gap,
        )
    )

    # Remove exact duplicate records
    clean_df, duplicates_removed = (
        remove_exact_duplicates(clean_df)
    )

    # Validate remaining measurement values
    measurement_validation = (
        validate_measurements(clean_df)
    )

    # Create a small cleaning summary
    summary = {
        "rows": len(clean_df),
        "columns": clean_df.shape[1],
        "interpolated_rows": interpolated_rows,
        "duplicates_removed": duplicates_removed,
        "invalid_timestamps": int(
            clean_df["Timestamp"].isna().sum()
        ),
        "measurement_validation": measurement_validation,
    }

    return clean_df, summary


def save_intermediate_data(df, output_path):
    """Save the Member 1 cleaned intermediate dataset."""

    # Convert the output location into a Path object
    output_path = Path(output_path)

    # Create the parent directory if required
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Save the cleaned dataset without dataframe index
    df.to_csv(
        output_path,
        index=False,
    )