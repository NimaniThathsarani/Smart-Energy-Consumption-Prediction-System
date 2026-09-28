"""Development-only API fixture and static server for dashboard integration tests."""

from __future__ import annotations

import csv
import json
import mimetypes
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
DASHBOARD = ROOT / "dashboard"


def read_csv(name: str) -> list[dict[str, object]]:
    with (REPORTS / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def top_recommendations() -> list[dict[str, object]]:
    priority = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    rows = read_csv("recommendations.csv")
    rows.sort(key=lambda row: priority.get(str(row.get("priority", "LOW")), 4))
    return rows[:12]


def model_metrics() -> list[dict[str, object]]:
    return read_csv("member3_model_comparison.csv") + read_csv("final_dl_metrics.csv")


class DashboardHandler(SimpleHTTPRequestHandler):
    api_routes = {
        "/peak": lambda _query: {"data": read_csv("peak_predictions.csv")[-7:]},
        "/anomalies": lambda _query: {"anomalies": read_csv("anomalies.csv")[-30:]},
        "/clusters": lambda _query: {"clusters": read_csv("cluster_info.csv")},
        "/recommendations": lambda _query: {"recommendations": top_recommendations()},
        "/model-performance": lambda _query: {"models": model_metrics()},
    }

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        if parsed.path == "/forecast":
            query = parse_qs(parsed.query)
            try:
                limit = min(max(int(query.get("limit", ["168"])[0]), 1), 1000)
            except ValueError:
                return self.send_json({"error": "limit must be an integer"}, status=400)
            return self.send_json({"forecast": read_csv("final_dl_predictions.csv")[-limit:]})
        if parsed.path in self.api_routes:
            return self.send_json(self.api_routes[parsed.path](parse_qs(parsed.query)))
        return self.serve_dashboard_file("/index.html" if parsed.path == "/" else parsed.path)

    def serve_dashboard_file(self, url_path: str) -> None:
        target = (DASHBOARD / url_path.lstrip("/")).resolve()
        try:
            target.relative_to(DASHBOARD.resolve())
        except ValueError:
            return self.send_error(403)
        if not target.is_file():
            return self.send_error(404)
        content = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, body: object, status: int = 200) -> None:
        content = json.dumps(body, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: object) -> None:
        return


def create_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), DashboardHandler)


if __name__ == "__main__":
    server = create_server()
    print("Dashboard integration fixture: http://127.0.0.1:8765", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
