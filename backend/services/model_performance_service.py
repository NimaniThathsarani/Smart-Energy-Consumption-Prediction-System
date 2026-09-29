from pathlib import Path
import pandas as pd


REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"

MODEL_PERFORMANCE_FILE = REPORTS_DIR / "member3_model_comparison.csv"


def get_model_performance():
    """
    Load model performance comparison results.
    """

    if not MODEL_PERFORMANCE_FILE.exists():
        raise FileNotFoundError(
            f"Model performance file not found: {MODEL_PERFORMANCE_FILE}"
        )

    df = pd.read_csv(MODEL_PERFORMANCE_FILE)

    if df.empty:
        return []

    # Convert missing values to JSON-safe values
    df = df.where(pd.notnull(df), None)

    return df.to_dict(orient="records")