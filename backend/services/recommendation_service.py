from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
RECOMMENDATIONS_FILE = BASE_DIR / "reports" / "recommendations.csv"


def get_recommendations(limit: int = 10):
    if not RECOMMENDATIONS_FILE.exists():
        raise FileNotFoundError(
            f"Recommendations file not found: {RECOMMENDATIONS_FILE}"
        )

    df = pd.read_csv(RECOMMENDATIONS_FILE)

    if df.empty:
        return []

    # Return the latest recommendation records
    data = df.tail(limit).copy()

    # Replace NaN values so the result can be safely returned as JSON
    data = data.where(pd.notnull(data), None)

    return data.to_dict(orient="records")