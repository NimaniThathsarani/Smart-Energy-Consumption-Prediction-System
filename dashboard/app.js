import { createApiClient } from "./api.mjs";
import {
  accuracyFromMetrics, formatNumber, normalizeAnomalies, normalizeClusters,
  normalizeForecast, normalizePeaks, normalizePerformance, normalizeRecommendations,
  selectHighestPriority, summary
} from "./core.mjs";

const $ = selector => document.querySelector(selector);
const configuredBase = new URLSearchParams(location.search).get("api") || document.documentElement.dataset.apiBase || "";
const api = createApiClient({ baseUrl: configuredBase });
const colors = ["#149985", "#4b7bec", "#e9a23b", "#ed6a5a", "#8d6ccf", "#59a9b5"];
let allAlerts = [];
let showingAllAlerts = false;

function safeDate(value) {
  if (!value) return null;
  const normalized = String(value).includes("T") ? String(value) : String(value).replace(" ", "T");
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}

function dateTime(value, options = {}) {
  const date = safeDate(value);
  if (!date) return value || "—";
  return new Intl.DateTimeFormat(undefined, options).format(date);
}

function setText(selector, value) {
  const target = $(selector);
  if (target) target.textContent = value;
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function toast(message) {
  const node = $("#toast");
  node.textContent = message;
  node.classList.add("show");
  window.setTimeout(() => node.classList.remove("show"), 2400);
}

function renderForecast(payload, requestedLimit) {
  const forecast = normalizeForecast(payload).slice(-requestedLimit);
  if (!forecast.length) throw new Error("Forecast response contains no usable readings");
  const latestActualIndex = forecast.map(point => point.actual).findLastIndex(Number.isFinite);
  const latest = forecast[Math.max(0, latestActualIndex)];
  const previous = forecast.slice(0, Math.max(0, latestActualIndex)).map(point => point.actual).filter(Number.isFinite).at(-1);
  const future = forecast.slice(latestActualIndex + 1).find(point => Number.isFinite(point.predicted)) || forecast.at(-1);
  const delta = Number.isFinite(previous) && previous !== 0 ? ((latest.actual - previous) / previous) * 100 : null;
  const state = latest.actual >= 2.5 ? "High demand" : latest.actual >= 1.3 ? "Moderate demand" : "Efficient usage";
  setText("#current-value", formatNumber(latest.actual));
  setText("#current-state", state);
  setText("#current-timestamp", dateTime(latest.timestamp, { dateStyle: "medium", timeStyle: "short" }));
  setText("#forecast-value", formatNumber(future.predicted));
  setText("#forecast-time", `Expected ${dateTime(future.timestamp, { dateStyle: "medium", timeStyle: "short" })}`);
  const trend = $("#consumption-trend");
  trend.textContent = delta === null ? "—" : `${delta >= 0 ? "↑" : "↓"} ${Math.abs(delta).toFixed(1)}%`;
  trend.classList.toggle("up", delta > 0);
  const stats = summary(forecast.map(point => point.actual));
  setText("#average-value", `${formatNumber(stats.average)} kW`);
  setText("#range-value", `${formatNumber(stats.min)}–${formatNumber(stats.max)} kW`);
  drawLineChart(forecast);
}

function drawLineChart(points) {
  const container = $("#consumption-chart");
  container.classList.remove("skeleton");
  const width = 760, height = 234, left = 38, right = 10, top = 12, bottom = 28;
  const allValues = points.flatMap(point => [point.actual, point.predicted]).filter(Number.isFinite);
  if (!allValues.length) { container.textContent = "No chart data available"; return; }
  const min = Math.min(...allValues, 0), max = Math.max(...allValues, 1), span = max - min || 1;
  const x = index => left + (index / Math.max(1, points.length - 1)) * (width - left - right);
  const y = value => top + ((max - value) / span) * (height - top - bottom);
  const line = key => points.map((point, index) => Number.isFinite(point[key]) ? `${index === 0 ? "M" : "L"}${x(index).toFixed(1)},${y(point[key]).toFixed(1)}` : "").join(" ");
  const actualPath = line("actual"), predictedPath = line("predicted");
  const areaPath = `${actualPath} L${x(points.length - 1)},${height - bottom} L${left},${height - bottom} Z`;
  const grid = Array.from({ length: 5 }, (_, index) => {
    const gridY = top + index * ((height - top - bottom) / 4);
    return `<line class="grid-line" x1="${left}" y1="${gridY}" x2="${width - right}" y2="${gridY}"/><text class="axis-label" x="0" y="${gridY + 3}">${(max - index * (span / 4)).toFixed(1)}</text>`;
  }).join("");
  const ticks = [0, .25, .5, .75, 1].map(fraction => {
    const index = Math.min(points.length - 1, Math.round((points.length - 1) * fraction));
    return `<text class="axis-label" text-anchor="middle" x="${x(index)}" y="${height - 7}">${dateTime(points[index].timestamp, { month: "short", day: "numeric", hour: "numeric" })}</text>`;
  }).join("");
  container.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Actual versus predicted consumption"><defs><linearGradient id="actualGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#149985" stop-opacity=".18"/><stop offset="1" stop-color="#149985" stop-opacity="0"/></linearGradient></defs>${grid}<path class="actual-area" d="${areaPath}"/><path class="predicted-line" d="${predictedPath}"/><path class="actual-line" d="${actualPath}"/>${ticks}</svg>`;
}

function renderPeak(payload) {
  const peaks = normalizePeaks(payload);
  if (!peaks.length) throw new Error("Peak response contains no usable prediction");
  const peak = peaks.at(-1), when = peak.time || peak.date;
  setText("#peak-value", formatNumber(peak.value));
  setText("#peak-time", dateTime(when, { dateStyle: "medium", timeStyle: peak.time ? "short" : undefined }));
  setText("#peak-ring-value", formatNumber(peak.value, 1));
  setText("#peak-date", dateTime(peak.date || when, { month: "short", day: "numeric", year: "numeric" }));
  setText("#peak-clock", dateTime(when, { hour: "numeric", minute: "2-digit" }));
  setText("#peak-period", peak.period);
  setText("#peak-note", `Consider shifting flexible loads away from ${dateTime(when, { hour: "numeric", minute: "2-digit" })} to reduce peak demand.`);
}

function alertNode(alert) {
  const item = element("div", `alert-item ${alert.severity}`);
  const icon = element("div", "alert-severity", ["high", "critical"].includes(alert.severity) ? "!!" : "!");
  const copy = element("div", "alert-copy");
  copy.append(element("strong", "", `${alert.severity[0]?.toUpperCase()}${alert.severity.slice(1)} ${alert.direction} usage`));
  copy.append(element("small", "", `${dateTime(alert.timestamp, { dateStyle: "medium", timeStyle: "short" })} · ${alert.source}`));
  const reading = element("div", "alert-reading");
  reading.append(element("strong", "", `${formatNumber(alert.actual)} kW`));
  reading.append(element("small", "", Number.isFinite(alert.predicted) ? `Expected ${formatNumber(alert.predicted)}` : "Unexpected signal"));
  item.append(icon, copy, reading);
  return item;
}

function renderAlertList() {
  const list = $("#alert-list");
  if (!allAlerts.length) { list.replaceChildren(element("div", "empty-state", "No anomalies detected in this period.")); return; }
  list.replaceChildren(...(showingAllAlerts ? allAlerts : allAlerts.slice(0, 3)).map(alertNode));
  $("#show-all-alerts").textContent = showingAllAlerts ? "Show recent" : `Show all (${allAlerts.length})`;
}

function renderAnomalies(payload) {
  allAlerts = normalizeAnomalies(payload).sort((a, b) => (safeDate(b.timestamp)?.getTime() || 0) - (safeDate(a.timestamp)?.getTime() || 0));
  setText("#anomaly-count", String(allAlerts.length));
  const high = allAlerts.filter(alert => ["high", "critical"].includes(alert.severity)).length;
  setText("#anomaly-summary", high ? `${high} high-priority alert${high === 1 ? "" : "s"} require review` : "No high-priority alerts detected");
  renderAlertList();
}

function renderClusters(payload) {
  const clusters = normalizeClusters(payload).filter(cluster => cluster.count > 0);
  if (!clusters.length) throw new Error("Cluster response contains no usable groups");
  const total = clusters.reduce((sumValue, cluster) => sumValue + cluster.count, 0);
  setText("#cluster-total", String(total));
  let cursor = 0;
  const stops = clusters.map((cluster, index) => { const start = cursor; cursor += (cluster.count / total) * 100; return `${colors[index % colors.length]} ${start.toFixed(1)}% ${cursor.toFixed(1)}%`; });
  $("#cluster-donut").style.background = `conic-gradient(${stops.join(",")})`;
  $("#cluster-legend").replaceChildren(...clusters.map((cluster, index) => {
    const row = element("div", "cluster-row"), swatch = element("i");
    swatch.style.background = colors[index % colors.length];
    row.append(swatch, element("span", "", cluster.name), element("strong", "", `${((cluster.count / total) * 100).toFixed(0)}%`));
    return row;
  }));
}

function renderRecommendations(payload) {
  const recommendations = selectHighestPriority(normalizeRecommendations(payload), 4), list = $("#recommendation-list");
  if (!recommendations.length) { list.replaceChildren(element("div", "empty-state", "No recommendations are available.")); return; }
  list.replaceChildren(...recommendations.map(recommendation => {
    const item = element("div", `recommendation-item ${recommendation.priority}`), copy = element("div", "recommendation-copy");
    copy.append(element("strong", "", recommendation.type), element("p", "", recommendation.message));
    item.append(copy, element("span", "priority", recommendation.priority.toUpperCase()));
    item.title = recommendation.reason;
    return item;
  }));
}

function tableMessage(message) {
  const row = document.createElement("tr"), cell = element("td", "empty-state", message);
  cell.colSpan = 5; row.append(cell); return row;
}

function renderPerformance(payload) {
  const metrics = normalizePerformance(payload).filter(metric => [metric.mae, metric.rmse, metric.r2].some(Number.isFinite));
  const tbody = $("#performance-body");
  if (!metrics.length) { tbody.replaceChildren(tableMessage("No model metrics are available.")); return; }
  const sorted = [...metrics].sort((a, b) => (b.r2 ?? -Infinity) - (a.r2 ?? -Infinity));
  tbody.replaceChildren(...sorted.slice(0, 6).map((metric, index) => {
    const row = document.createElement("tr");
    [metric.model, formatNumber(metric.mae, 4), formatNumber(metric.rmse, 4), formatNumber(metric.r2, 4)].forEach(value => row.append(element("td", "", value)));
    row.append(element("td", "model-status", index === 0 ? "Best" : "Validated"));
    return row;
  }));
  const accuracy = accuracyFromMetrics(metrics);
  if (accuracy) { setText("#accuracy-value", formatNumber(accuracy.value, 1)); setText("#accuracy-model", `${accuracy.model} · R² based`); }
  const mae = sorted.find(model => Number.isFinite(model.mae))?.mae;
  setText("#mae-value", Number.isFinite(mae) ? `${mae.toFixed(4)} kW` : "—");
}

async function loadDashboard({ announce = false } = {}) {
  const refresh = $("#refresh-button");
  refresh.classList.add("spinning"); refresh.disabled = true; $("#error-banner").hidden = true;
  const limit = Number($("#range-select").value) || 168;
  const requests = [
    ["Forecast", api.forecast(limit), data => renderForecast(data, limit)], ["Peak", api.peak(), renderPeak],
    ["Anomalies", api.anomalies(), renderAnomalies], ["Clusters", api.clusters(), renderClusters],
    ["Recommendations", api.recommendations(), renderRecommendations], ["Model performance", api.performance(), renderPerformance]
  ];
  const results = await Promise.allSettled(requests.map(([, request]) => request)), failures = [];
  results.forEach((result, index) => {
    if (result.status === "fulfilled") { try { requests[index][2](result.value); } catch (error) { failures.push(`${requests[index][0]}: ${error.message}`); } }
    else failures.push(`${requests[index][0]}: ${result.reason.message}`);
  });
  const syncLabel = new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit", second: "2-digit" }).format(new Date());
  setText("#sidebar-updated", `Last sync ${syncLabel}`); setText("#footer-sync", `Last synchronized at ${syncLabel}`);
  document.body.dataset.dashboardReady = "true";
  if (failures.length) { $("#error-banner").hidden = false; setText("#error-message", failures.join(" · ")); }
  else if (announce) toast("Dashboard data refreshed");
  refresh.classList.remove("spinning"); refresh.disabled = false;
}

function setupInteractions() {
  const hour = new Date().getHours();
  setText("#greeting-time", hour < 12 ? "morning" : hour < 18 ? "afternoon" : "evening");
  $("#refresh-button").addEventListener("click", () => loadDashboard({ announce: true }));
  $("#retry-button").addEventListener("click", () => loadDashboard({ announce: true }));
  $("#range-select").addEventListener("change", () => loadDashboard());
  $("#show-all-alerts").addEventListener("click", () => { showingAllAlerts = !showingAllAlerts; renderAlertList(); });
  $("#mobile-menu").addEventListener("click", event => { const open = $(".sidebar").classList.toggle("open"); event.currentTarget.setAttribute("aria-expanded", String(open)); });
  document.querySelectorAll(".nav-item").forEach(link => link.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach(item => item.classList.toggle("active", item === link));
    $(".sidebar").classList.remove("open");
  }));
}

setupInteractions();
loadDashboard();
