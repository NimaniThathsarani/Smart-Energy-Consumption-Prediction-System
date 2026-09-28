const KEYS = {
  forecast: ["forecast", "forecasts", "predictions", "results", "data"],
  peak: ["peak", "peaks", "predictions", "results", "data"],
  anomalies: ["anomalies", "alerts", "results", "data"],
  clusters: ["clusters", "results", "data"],
  recommendations: ["recommendations", "results", "data"],
  performance: ["models", "metrics", "model_performance", "results", "data"]
};

export function unwrap(payload, type) {
  if (Array.isArray(payload)) return payload;
  if (payload == null || typeof payload !== "object") return [];
  for (const key of KEYS[type] || []) {
    if (Array.isArray(payload[key])) return payload[key];
    if (payload[key] && typeof payload[key] === "object") return [payload[key]];
  }
  return [payload];
}

export function firstValue(object, keys, fallback = null) {
  for (const key of keys) {
    const value = object?.[key];
    if (value !== undefined && value !== null && value !== "") return value;
  }
  return fallback;
}

export function numberValue(object, keys, fallback = null) {
  const value = Number(firstValue(object, keys));
  return Number.isFinite(value) ? value : fallback;
}

export function booleanValue(value) {
  if (typeof value === "boolean") return value;
  return ["true", "1", "yes"].includes(String(value).toLowerCase());
}

export function normalizeForecast(payload) {
  return unwrap(payload, "forecast").map((item, index) => ({
    timestamp: firstValue(item, ["timestamp", "datetime", "Datetime", "date", "Date"], String(index)),
    actual: numberValue(item, ["actual", "Actual", "consumption", "value", "actual_kw"]),
    predicted: numberValue(item, ["predicted", "Predicted", "forecast", "prediction", "predicted_kw"])
  })).filter(item => item.actual !== null || item.predicted !== null);
}

export function normalizePeaks(payload) {
  return unwrap(payload, "peak").map(item => ({
    date: firstValue(item, ["date", "Date", "prediction_date"]),
    value: numberValue(item, ["predicted_peak", "pred_peak_kw", "peak_value", "value", "peak_kw"]),
    time: firstValue(item, ["predicted_peak_time", "pred_peak_time", "peak_time", "time"]),
    period: firstValue(item, ["predicted_peak_period", "pred_peak_period", "period"], "Peak demand")
  })).filter(item => item.value !== null);
}

export function normalizeAnomalies(payload) {
  return unwrap(payload, "anomalies").filter(item => item.is_anomaly === undefined || booleanValue(item.is_anomaly)).map(item => ({
    timestamp: firstValue(item, ["timestamp", "datetime", "Datetime", "date", "Date"]),
    actual: numberValue(item, ["actual", "Actual", "value", "consumption"]),
    predicted: numberValue(item, ["predicted", "Predicted", "expected"]),
    severity: String(firstValue(item, ["severity", "level"], "medium")).toLowerCase(),
    direction: firstValue(item, ["direction"], "unusual"),
    source: firstValue(item, ["flagged_by", "method", "detector"], "anomaly detector")
  }));
}

export function normalizeClusters(payload) {
  return unwrap(payload, "clusters").map((item, index) => ({
    id: firstValue(item, ["cluster", "id"], index),
    name: firstValue(item, ["cluster_name", "name", "label"], `Cluster ${index + 1}`),
    count: numberValue(item, ["num_days", "count", "size"], 1),
    average: numberValue(item, ["avg_consumption", "average", "mean"]),
    peak: numberValue(item, ["peak_consumption", "peak", "max"])
  }));
}

export function normalizeRecommendations(payload) {
  return unwrap(payload, "recommendations").map(item => ({
    id: firstValue(item, ["recommendation_id", "id"]),
    type: firstValue(item, ["recommendation_type", "type", "title"], "Energy recommendation"),
    priority: String(firstValue(item, ["priority"], "medium")).toLowerCase(),
    message: firstValue(item, ["recommendation", "message", "description"], "Review current consumption."),
    reason: firstValue(item, ["reason", "supporting_signals"], "Based on recent energy signals.")
  }));
}

export function normalizePerformance(payload) {
  return unwrap(payload, "performance").map(item => ({
    model: firstValue(item, ["model", "Model", "name"], "Model"),
    mae: numberValue(item, ["mae", "MAE"]),
    rmse: numberValue(item, ["rmse", "RMSE"]),
    mape: numberValue(item, ["mape", "MAPE"]),
    r2: numberValue(item, ["r2", "R2", "r_squared"])
  }));
}

export function accuracyFromMetrics(metrics) {
  if (!metrics.length) return null;
  const best = [...metrics].filter(metric => metric.r2 !== null).sort((a, b) => b.r2 - a.r2)[0];
  if (best) return { value: Math.max(0, Math.min(100, best.r2 * 100)), model: best.model };
  const mapeBest = [...metrics].filter(metric => metric.mape !== null).sort((a, b) => a.mape - b.mape)[0];
  return mapeBest ? { value: Math.max(0, 100 - mapeBest.mape), model: mapeBest.model } : null;
}

export function summary(values) {
  const clean = values.filter(Number.isFinite);
  if (!clean.length) return { average: null, min: null, max: null };
  return { average: clean.reduce((total, value) => total + value, 0) / clean.length, min: Math.min(...clean), max: Math.max(...clean) };
}

export function selectHighestPriority(items, limit = 4) {
  const rank = { critical: 0, high: 1, medium: 2, low: 3 };
  return [...items].sort((a, b) => (rank[a.priority] ?? 4) - (rank[b.priority] ?? 4)).slice(0, limit);
}

export function formatNumber(value, digits = 2) {
  return Number.isFinite(value) ? value.toFixed(digits) : "—";
}
