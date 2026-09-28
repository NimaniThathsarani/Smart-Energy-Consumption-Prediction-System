# Member 2 — Dashboard and Integration

The responsive dashboard in `dashboard/` covers current and historical consumption, forecasts, peak demand, anomaly alerts, consumption clusters, prioritized recommendations, and model performance.

## Run locally with the integration fixture

```powershell
python tests/mock_dashboard_server.py
```

Open <http://127.0.0.1:8765>. The fixture reads the real Group 3–6 CSV outputs in `reports/`; it is only for frontend development and integration testing. The production backend remains Member 1's responsibility.

## Connect to the production backend

The dashboard uses same-origin APIs by default. If the backend runs elsewhere, supply its base URL:

```text
http://127.0.0.1:8765/?api=http://127.0.0.1:5000
```

The backend must permit the dashboard origin with CORS when the two run on different origins.

### API contract

| Route | Required data | Accepted envelope keys |
|---|---|---|
| `GET /forecast?limit=168` | timestamp, actual consumption, predicted consumption | `forecast`, `forecasts`, `predictions`, `results`, `data` |
| `GET /peak` | predicted peak value, date/time, period | `peak`, `peaks`, `predictions`, `results`, `data` |
| `GET /anomalies` | timestamp, actual/expected value, severity, detector | `anomalies`, `alerts`, `results`, `data` |
| `GET /clusters` | name, count/size, average and peak consumption | `clusters`, `results`, `data` |
| `GET /recommendations` | type, priority, recommendation, reason | `recommendations`, `results`, `data` |
| `GET /model-performance` | model, MAE, RMSE, R² and optionally MAPE | `models`, `metrics`, `model_performance`, `results`, `data` |

The adapter accepts both project CSV columns such as `Datetime`, `Actual`, `Predicted`, and `pred_peak_kw`, and conventional JSON names. Responses may be direct arrays or objects with the envelope keys above.

## Error and loading behavior

- The six requests run independently, so one failed route does not blank the rest of the dashboard.
- A visible error banner names failed sections and provides a retry button.
- Requests time out after ten seconds, retry transient network/server failures once, and surface HTTP error details.
- Empty or malformed responses produce a section-specific fallback.
- Data text is inserted with DOM text nodes to avoid rendering untrusted API content as HTML.

## Tests

```powershell
node --test --test-isolation=none tests/dashboard_core.test.mjs
python -m unittest tests/test_dashboard_integration.py
```

The JavaScript suite checks API contracts, normalization, calculations, prioritization, and errors. The Python suite starts an isolated server, confirms dashboard assets and all six API flows, and checks invalid query/path handling.

## Screenshots

- `reports/screenshots/dashboard-desktop.png` — integrated desktop view at 1440 px.
- `reports/screenshots/dashboard-mobile.png` — responsive mobile view at 390 px.

## Final integration checklist

1. Start the production backend and open the dashboard with its API base URL.
2. Confirm all six sections populate and the error banner is absent.
3. Change the time range and confirm `/forecast` receives the new `limit`.
4. Test refresh, alert expansion, navigation, and mobile layout.
5. Compare peak, anomaly count, cluster totals, recommendation priorities, and model metrics against backend responses.
6. Capture desktop and mobile screenshots after connecting the production API.
