import assert from "node:assert/strict";
import test from "node:test";
import { createApiClient, ApiError } from "../dashboard/api.mjs";
import {
  accuracyFromMetrics, normalizeAnomalies, normalizeClusters, normalizeForecast,
  normalizePeaks, normalizePerformance, normalizeRecommendations, selectHighestPriority,
  summary, unwrap
} from "../dashboard/core.mjs";

test("unwrap accepts arrays and common API envelopes", () => {
  assert.deepEqual(unwrap([1, 2], "forecast"), [1, 2]);
  assert.deepEqual(unwrap({ forecast: [{ value: 1 }] }, "forecast"), [{ value: 1 }]);
  assert.deepEqual(unwrap({ data: [{ value: 2 }] }, "forecast"), [{ value: 2 }]);
});

test("normalizers support the project CSV field names", () => {
  assert.deepEqual(normalizeForecast({ forecast: [{ Datetime: "2026-01-01", Actual: "1.2", Predicted: "1.3" }] })[0], { timestamp: "2026-01-01", actual: 1.2, predicted: 1.3 });
  assert.equal(normalizePeaks([{ Date: "2026-01-01", pred_peak_kw: "3.4", pred_peak_time: "2026-01-01 18:00:00" }])[0].value, 3.4);
  assert.equal(normalizeAnomalies([{ is_anomaly: "False" }, { is_anomaly: "True", Actual: "2.1" }]).length, 1);
  assert.equal(normalizeClusters([{ cluster_name: "Low", num_days: "5" }])[0].count, 5);
  assert.equal(normalizeRecommendations([{ recommendation_type: "Shift", priority: "HIGH", recommendation: "Move load" }])[0].priority, "high");
  assert.equal(normalizePerformance([{ Model: "XGBoost", R2: "0.99" }])[0].r2, .99);
});

test("summary and performance accuracy are calculated correctly", () => {
  assert.deepEqual(summary([1, 2, null, 3]), { average: 2, min: 1, max: 3 });
  assert.deepEqual(accuracyFromMetrics([{ model: "A", r2: .91 }, { model: "B", r2: .97 }]), { value: 97, model: "B" });
});

test("recommendations are ordered by urgency", () => {
  const result = selectHighestPriority([{ priority: "low" }, { priority: "critical" }, { priority: "high" }], 2);
  assert.deepEqual(result.map(item => item.priority), ["critical", "high"]);
});

test("API client builds routes and query strings", async () => {
  const calls = [];
  const client = createApiClient({ baseUrl: "http://localhost:8000/", fetchImpl: async url => { calls.push(url); return { ok: true, json: async () => ({ data: [] }) }; } });
  await client.forecast(24);
  await client.performance();
  assert.equal(calls[0], "http://localhost:8000/forecast?limit=24");
  assert.equal(calls[1], "http://localhost:8000/model-performance");
});

test("API client reports useful backend errors", async () => {
  const client = createApiClient({ fetchImpl: async () => ({ ok: false, status: 422, json: async () => ({ detail: "invalid range" }) }) });
  await assert.rejects(() => client.forecast(0), error => error instanceof ApiError && error.status === 422 && error.message === "invalid range");
});

test("API client retries one transient network failure", async () => {
  let calls = 0;
  const client = createApiClient({ fetchImpl: async () => {
    calls += 1;
    if (calls === 1) throw new TypeError("Failed to fetch");
    return { ok: true, json: async () => ({ data: [1] }) };
  } });
  assert.deepEqual(await client.clusters(), { data: [1] });
  assert.equal(calls, 2);
});
