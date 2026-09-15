"""
Member 2 - Classical Time-Series Forecasting (ARIMA / SARIMA)
Smart Energy Consumption Prediction System

This module implements the classical (non deep-learning, non-regression)
time-series forecasting pipeline for the project:

    - Load the Member-1 feature-engineered dataset
    - Resample the 1-minute series to an hourly series suitable for
      ARIMA / SARIMA (fitting classical models on 2M+ one-minute rows is
      not computationally realistic within the project timeline)
    - Chronological train / validation / test split
    - Stationarity testing (ADF) and differencing order selection
    - Seasonality check (seasonal_decompose)
    - ARIMA fitting via auto_arima
    - SARIMA fitting via auto_arima (seasonal=True) when seasonality is present
    - Residual diagnostics
    - Forecast generation and evaluation (MAE, RMSE, MAPE, R2)
    - High-demand / peak-period error analysis
    - Saving the final model and predictions for Member 3

Can be used either as an importable module from the notebook, or run
end-to-end from the command line:

    python src/classical_timeseries.py \
        --data ../data/feature_engineered_dataset.csv \
        --output-dir ../reports \
        --models-dir ../models
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DATETIME_COL = "Datetime"
TARGET_COL = "Global_active_power"


# --------------------------------------------------------------------------- #
# 1. Data loading, resampling, splitting
# --------------------------------------------------------------------------- #

def load_feature_engineered_data(
    path: str | Path,
    datetime_col: str = DATETIME_COL,
) -> pd.DataFrame:
    """Load the Member-1 feature-engineered dataset, sorted chronologically.

    Mirrors the loading convention used in notebooks/baseline_forecasting.ipynb
    so results stay consistent across the group.
    """

    df = pd.read_csv(path)
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df = df.sort_values(datetime_col).reset_index(drop=True)
    return df


def resample_series(
    df: pd.DataFrame,
    target_col: str = TARGET_COL,
    datetime_col: str = DATETIME_COL,
    freq: str = "h",
    agg: str = "mean",
) -> pd.Series:
    """Resample the raw 1-minute series to a coarser frequency.

    Classical models (ARIMA/SARIMA) are fit on the resampled series rather
    than the raw 1-minute data. This is a deliberate, documented choice:
    1-minute ARIMA/SARIMA fitting over ~2M points is not tractable in the
    project timeline, and the existing Lag_24 / Lag_168 / RollingMean_24
    features already imply an hourly-scale mental model.

    Long gaps (retained as NaN by Member 1's cleaning policy) will produce
    NaN hourly bins where an entire hour has no readings; these are dropped
    after resampling so the model never trains or evaluates on invented
    values.
    """

    indexed = df.set_index(datetime_col)[target_col]
    resampled = getattr(indexed.resample(freq), agg)()
    resampled = resampled.dropna()
    resampled.name = target_col
    return resampled


def chronological_split(
    series: pd.Series,
    train_frac: float = 0.70,
    val_frac: float = 0.15,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Split a time-indexed series chronologically into train/val/test.

    No shuffling, no leakage: train precedes val precedes test in time.
    IMPORTANT: agree these fractions (or exact cutoff timestamps) with
    Member 1 and Member 3 so every model in the comparison table is
    evaluated on the identical test window.
    """

    n = len(series)
    train_end = int(n * train_frac)
    val_end = int(n * (train_frac + val_frac))

    train = series.iloc[:train_end]
    val = series.iloc[train_end:val_end]
    test = series.iloc[val_end:]

    return train, val, test


def split_summary(train: pd.Series, val: pd.Series, test: pd.Series) -> dict[str, Any]:
    """Human-readable summary of the split boundaries, for the report/handoff."""

    def _bounds(s: pd.Series) -> dict[str, Any]:
        return {
            "n_obs": int(len(s)),
            "start": str(s.index.min()),
            "end": str(s.index.max()),
        }

    return {"train": _bounds(train), "val": _bounds(val), "test": _bounds(test)}


# --------------------------------------------------------------------------- #
# 2. Stationarity and seasonality diagnostics
# --------------------------------------------------------------------------- #

def adf_test(series: pd.Series, name: str = "") -> dict[str, Any]:
    """Augmented Dickey-Fuller stationarity test."""

    from statsmodels.tsa.stattools import adfuller

    result = adfuller(series.dropna())
    summary = {
        "name": name,
        "adf_statistic": float(result[0]),
        "p_value": float(result[1]),
        "n_lags": int(result[2]),
        "n_obs": int(result[3]),
        "critical_values": {k: float(v) for k, v in result[4].items()},
        "is_stationary": bool(result[1] < 0.05),
    }
    return summary


def find_differencing_order(series: pd.Series, max_d: int = 2) -> int:
    """Find the minimal differencing order d that makes the series stationary."""

    current = series.dropna()
    for d in range(max_d + 1):
        result = adf_test(current, name=f"d={d}")
        if result["is_stationary"]:
            return d
        current = current.diff().dropna()
    return max_d


def seasonal_decomposition(
    series: pd.Series,
    period: int = 24,
    model: str = "additive",
):
    """Return a statsmodels DecomposeResult for visual/quantitative seasonality check."""

    from statsmodels.tsa.seasonal import seasonal_decompose

    return seasonal_decompose(series, model=model, period=period)


def seasonality_strength(decomposition) -> float:
    """Rough seasonality-strength score (0-1) used to decide ARIMA vs SARIMA.

    Based on Hyndman & Athanasopoulos's F_s measure:
        F_s = max(0, 1 - Var(residual) / Var(seasonal + residual))
    Values well above ~0.3-0.4 indicate seasonality worth modelling with SARIMA.
    """

    resid = decomposition.resid.dropna()
    seasonal_plus_resid = (decomposition.seasonal + decomposition.resid).dropna()
    var_resid = np.var(resid)
    var_total = np.var(seasonal_plus_resid)
    if var_total == 0:
        return 0.0
    return float(max(0.0, 1 - var_resid / var_total))


# --------------------------------------------------------------------------- #
# 3. Model fitting
# --------------------------------------------------------------------------- #

def fit_arima(
    train: pd.Series,
    max_p: int = 5,
    max_q: int = 5,
    trace: bool = True,
):
    """Fit a non-seasonal ARIMA model via stepwise auto_arima search.

    The series is fit on a plain sequential (RangeIndex) copy rather than its
    original DatetimeIndex. After resampling + dropping long-gap NaNs, the
    real timestamp index is often no longer perfectly regular, which makes
    statsmodels unable to extend it for out-of-sample forecasting and raises
    "ValueError: No supported index is available." at predict() time. Real
    timestamps are reattached separately in forecast_series(), so nothing is
    lost by fitting on a clean integer index here.
    """

    from pmdarima import auto_arima

    model = auto_arima(
        train.reset_index(drop=True),
        start_p=0,
        start_q=0,
        max_p=max_p,
        max_q=max_q,
        d=None,
        seasonal=False,
        stepwise=True,
        error_action="ignore",
        suppress_warnings=True,
        trace=trace,
    )
    return model


def fit_sarima(
    train: pd.Series,
    m: int = 24,
    max_p: int = 3,
    max_q: int = 3,
    max_P: int = 1,
    max_Q: int = 1,
    trace: bool = True,
):
    """Fit a seasonal SARIMA model via stepwise auto_arima search.

    m is the seasonal period in number of observations (24 for hourly data
    with a daily cycle, 7 for daily data with a weekly cycle, etc.). Confirm
    this matches the period used in seasonal_decomposition().

    max_P/max_Q default to 1 to keep the stepwise search tractable on a
    laptop within the project deadline (seasonal AR/MA terms are the most
    expensive part of the search). Widen them to 2 if you have spare compute
    time and want to double-check nothing better is being missed.

    Fit on a plain sequential (RangeIndex) copy for the same reason as
    fit_arima() above — see that docstring for details.
    """

    from pmdarima import auto_arima

    model = auto_arima(
        train.reset_index(drop=True),
        start_p=0,
        start_q=0,
        max_p=max_p,
        max_q=max_q,
        start_P=0,
        start_Q=0,
        max_P=max_P,
        max_Q=max_Q,
        d=None,
        D=None,
        seasonal=True,
        m=m,
        stepwise=True,
        error_action="ignore",
        suppress_warnings=True,
        trace=trace,
    )
    return model


# --------------------------------------------------------------------------- #
# 4. Forecasting and evaluation
# --------------------------------------------------------------------------- #

def forecast_series(model, n_periods: int, index: pd.Index) -> tuple[pd.Series, np.ndarray]:
    """Generate an n_periods-ahead forecast with 95% confidence intervals."""

    forecast, conf_int = model.predict(n_periods=n_periods, return_conf_int=True)
    forecast_series = pd.Series(np.asarray(forecast), index=index, name="forecast")
    return forecast_series, conf_int


def mean_absolute_percentage_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """MAPE, guarding against divide-by-zero on near-zero consumption readings."""

    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def evaluate_forecast(y_true: pd.Series, y_pred: pd.Series) -> dict[str, float]:
    """Compute MAE, RMSE, MAPE, R2 - matching the metric set used by Member 1 & 3."""

    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)

    return {
        "MAE": float(mean_absolute_error(y_true_arr, y_pred_arr)),
        "RMSE": float(np.sqrt(mean_squared_error(y_true_arr, y_pred_arr))),
        "MAPE": mean_absolute_percentage_error(y_true_arr, y_pred_arr),
        "R2": float(r2_score(y_true_arr, y_pred_arr)),
    }


def high_demand_error_analysis(
    y_true: pd.Series,
    y_pred: pd.Series,
    top_quantile: float = 0.90,
) -> dict[str, Any]:
    """Evaluate forecast error restricted to the highest-demand periods.

    Defines "high demand" as actual consumption above the given quantile of
    the test set (default: top 10% of observations). Reported separately
    because peak-demand accuracy matters more operationally than average
    accuracy for an energy system, and average metrics can hide poor
    performance exactly when it matters most.
    """

    threshold = float(np.quantile(y_true, top_quantile))
    mask = y_true >= threshold

    if mask.sum() == 0:
        return {
            "threshold": threshold,
            "n_high_demand_points": 0,
            "metrics": None,
        }

    metrics = evaluate_forecast(y_true[mask], y_pred[mask])
    return {
        "threshold": threshold,
        "n_high_demand_points": int(mask.sum()),
        "metrics": metrics,
    }


def residuals(y_true: pd.Series, y_pred: pd.Series) -> pd.Series:
    """Forecast residuals (actual - predicted), for error-analysis plots."""

    return pd.Series(np.asarray(y_true) - np.asarray(y_pred), index=y_true.index, name="residual")


# --------------------------------------------------------------------------- #
# 5. Saving artifacts for Member 3
# --------------------------------------------------------------------------- #

def save_model(model, path: str | Path) -> None:
    import joblib

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def save_predictions(
    test_index: pd.Index,
    y_true: pd.Series,
    predictions: dict[str, pd.Series],
    path: str | Path,
) -> None:
    """Save a tidy actual-vs-predicted CSV. predictions maps model name -> series."""

    out = pd.DataFrame({"Datetime": test_index, "actual": np.asarray(y_true)})
    for name, pred in predictions.items():
        out[name] = np.asarray(pred)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(path, index=False)


def save_metrics(metrics: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- #
# 6. End-to-end pipeline (importable + CLI)
# --------------------------------------------------------------------------- #

def run_pipeline(
    data_path: str | Path,
    output_dir: str | Path,
    models_dir: str | Path,
    freq: str = "h",
    seasonal_period: int = 24,
    train_frac: float = 0.70,
    val_frac: float = 0.15,
    seasonality_threshold: float = 0.30,
) -> dict[str, Any]:
    """Run the full classical time-series pipeline and persist all artifacts.

    Returns a results dict that also gets written to
    <output_dir>/classical_timeseries_metrics.json for Member 3 to consume.
    """

    output_dir = Path(output_dir)
    models_dir = Path(models_dir)

    # 1. Load + resample + split
    df = load_feature_engineered_data(data_path)
    series = resample_series(df, freq=freq)
    train, val, test = chronological_split(series, train_frac=train_frac, val_frac=val_frac)

    # 2. Stationarity
    d = find_differencing_order(train)

    # 3. Seasonality
    decomposition = seasonal_decomposition(train, period=seasonal_period)
    strength = seasonality_strength(decomposition)
    use_sarima = strength >= seasonality_threshold

    results: dict[str, Any] = {
        "split": split_summary(train, val, test),
        "differencing_order_d": d,
        "seasonality_strength": strength,
        "seasonal_period_used": seasonal_period,
        "sarima_selected": use_sarima,
        "models": {},
    }

    # 4. Fit ARIMA (always) and SARIMA (if seasonality is meaningful)
    arima_model = fit_arima(train)
    results["models"]["ARIMA"] = {"order": arima_model.order}

    active_model = arima_model
    active_name = "ARIMA"

    if use_sarima:
        sarima_model = fit_sarima(train, m=seasonal_period)
        results["models"]["SARIMA"] = {
            "order": sarima_model.order,
            "seasonal_order": sarima_model.seasonal_order,
        }
        active_model = sarima_model
        active_name = "SARIMA"

    # 5. Forecast on test set and evaluate
    forecast_vals, _ = forecast_series(active_model, n_periods=len(test), index=test.index)
    metrics = evaluate_forecast(test, forecast_vals)
    peak_metrics = high_demand_error_analysis(test, forecast_vals)

    results["selected_model"] = active_name
    results["test_metrics"] = metrics
    results["high_demand_metrics"] = peak_metrics

    # 6. Persist artifacts
    save_model(active_model, models_dir / f"{active_name.lower()}_model.pkl")
    save_predictions(
        test.index,
        test,
        {active_name.lower() + "_pred": forecast_vals},
        output_dir / "classical_timeseries_predictions.csv",
    )
    save_metrics(results, output_dir / "classical_timeseries_metrics.json")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="Path to feature_engineered_dataset.csv")
    parser.add_argument("--output-dir", required=True, help="Directory for predictions/metrics")
    parser.add_argument("--models-dir", required=True, help="Directory for saved model files")
    parser.add_argument("--freq", default="h", help="Resample frequency, e.g. h, D")
    parser.add_argument("--period", type=int, default=24, help="Seasonal period in observations")
    parser.add_argument("--train-frac", type=float, default=0.70)
    parser.add_argument("--val-frac", type=float, default=0.15)
    args = parser.parse_args()

    results = run_pipeline(
        data_path=args.data,
        output_dir=args.output_dir,
        models_dir=args.models_dir,
        freq=args.freq,
        seasonal_period=args.period,
        train_frac=args.train_frac,
        val_frac=args.val_frac,
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
