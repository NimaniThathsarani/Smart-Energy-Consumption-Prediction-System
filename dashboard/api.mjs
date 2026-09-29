export class ApiError extends Error {
  constructor(endpoint, status, message) {
    super(message || `Request to ${endpoint} failed`);
    this.name = "ApiError";
    this.endpoint = endpoint;
    this.status = status;
  }
}

export function createApiClient({ baseUrl = "", fetchImpl = globalThis.fetch, timeout = 10000 } = {}) {
  if (typeof fetchImpl !== "function") throw new TypeError("A fetch implementation is required");
  const base = String(baseUrl || "").replace(/\/$/, "");

  async function get(endpoint, params = {}, attempt = 0) {
    const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value !== undefined && value !== null));
    const url = `${base}${endpoint}${query.size ? `?${query}` : ""}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);
    try {
      const response = await fetchImpl(url, { headers: { Accept: "application/json" }, signal: controller.signal });
      let body;
      try { body = await response.json(); } catch { body = null; }
      if (!response.ok) {
        const detail = body?.detail || body?.error || body?.message || `HTTP ${response.status}`;
        throw new ApiError(endpoint, response.status, detail);
      }
      return body;
    } catch (error) {
      const apiError = error instanceof ApiError
        ? error
        : new ApiError(endpoint, error.name === "AbortError" ? 408 : 0, error.name === "AbortError" ? "Request timed out" : (error.message || "Network request failed"));
      if (attempt === 0 && (apiError.status === 0 || apiError.status === 408 || apiError.status >= 500)) {
        await new Promise(resolve => setTimeout(resolve, 200));
        return get(endpoint, params, attempt + 1);
      }
      throw apiError;
    } finally {
      clearTimeout(timer);
    }
  }

  return {
    forecast: limit => get("/forecast", { limit }),
    peak: () => get("/peak"),
    anomalies: () => get("/anomalies"),
    clusters: () => get("/clusters"),
    recommendations: () => get("/recommendations"),
    performance: () => get("/model-performance")
  };
}
