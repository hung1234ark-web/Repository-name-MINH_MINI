# ============================================================
# MINH MINI — TEAM CENTER WEB UI
# P10-TEAM-03 foundation
# Standard library only; no third-party dependency.
# ============================================================

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import json
import html
import team_center


HOST = "127.0.0.1"
PORT = 8765


def esc(value) -> str:
    return html.escape(str(value or ""))


def page() -> str:
    data = team_center.get_dashboard()
    tasks = data["tasks"]
    reports = data["reports"]
    agents = data["agents"]
    counts = data["task_counts"]

    agent_cards = "".join(
        f"""
        <div class="agent">
          <div class="agent-name">{esc(a["name"])}</div>
          <div class="role">{esc(a["role"])}</div>
          <div class="scope">{esc(a["scope"])}</div>
          <div class="active">Đang xử lý: <b>{a["active_tasks"]}</b></div>
        </div>
        """
        for a in agents
    )

    task_rows = "".join(
        f"""
        <div class="task">
          <div>
            <b>{esc(t["id"])} · {esc(t["title"])}</b>
            <div class="muted">{esc(t["agent_name"])} · {esc(t["priority"])}</div>
          </div>
          <span class="status">{esc(t["status"])}</span>
        </div>
        """
        for t in tasks
    ) or '<div class="empty">Chưa có task.</div>'

    report_rows = "".join(
        f"""
        <div class="report">
          <b>{esc(r["id"])} · {esc(r["agent_name"])}</b>
          <span class="result">{esc(r["result"])}</span>
          <div>{esc(r["summary"])}</div>
          <div class="muted">Task: {esc(r["task_id"])} · {esc(r["created_at"])}</div>
        </div>
        """
        for r in reports
    ) or '<div class="empty">Chưa có report.</div>'

    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MINH MINI — Team Center</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;background:#f7f7f8;color:#242424;font:14px Arial,sans-serif}}
.app{{display:flex;height:100vh;overflow:hidden}}
.side{{width:235px;background:#202123;color:#eee;padding:18px 12px}}
.brand{{font-size:20px;font-weight:700;padding:8px 10px 20px}}
.nav{{padding:10px;border-radius:8px;background:#343541;margin-bottom:7px}}
.nav.dim{{background:transparent;color:#aaa}}
.main{{flex:1;overflow:auto;padding:28px;max-width:1200px;margin:auto;width:100%}}
h1{{margin:0 0 6px;font-size:27px}} .sub{{color:#777;margin-bottom:24px}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
.agent{{background:white;border:1px solid #ddd;border-radius:12px;padding:17px;box-shadow:0 1px 2px #ddd}}
.agent-name{{font-size:18px;font-weight:700}} .role{{margin-top:4px;font-weight:600}}
.scope,.muted{{color:#777;margin-top:7px;line-height:1.4}} .active{{margin-top:12px}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:20px}}
.panel{{background:white;border:1px solid #ddd;border-radius:12px;padding:16px}}
.panel h2{{font-size:17px;margin:0 0 12px}}
.task,.report{{padding:12px 0;border-bottom:1px solid #eee;display:flex;justify-content:space-between;gap:12px}}
.task:last-child,.report:last-child{{border-bottom:0}}
.status,.result{{font-size:11px;padding:4px 7px;border:1px solid #ccc;border-radius:8px;height:max-content;white-space:nowrap}}
.statbar{{display:flex;gap:7px;flex-wrap:wrap;margin:15px 0}}
.stat{{background:#fff;border:1px solid #ddd;border-radius:9px;padding:8px 10px}}
.empty{{color:#888;padding:15px 0}}
@media(max-width:800px){{.side{{display:none}}.main{{padding:18px}}.grid,.cols{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="app">
<aside class="side">
  <div class="brand">MINH MINI</div>
  <div class="nav">💬 Chat</div>
  <div class="nav">👥 Team Center</div>
  <div class="nav dim">🧠 Memory</div>
  <div class="nav dim">📋 Tasks</div>
  <div class="nav dim">📨 Reports</div>
  <div class="nav dim">⚙ Settings</div>
</aside>
<main class="main">
  <h1>Team Center</h1>
  <div class="sub">Trung tâm giao việc và nhận báo cáo của Minh.</div>
  <div class="grid">{agent_cards}</div>
  <div class="statbar">
    <div class="stat">Assigned: <b>{counts["ASSIGNED"]}</b></div>
    <div class="stat">In progress: <b>{counts["IN_PROGRESS"]}</b></div>
    <div class="stat">Reports: <b>{counts["REPORT_SUBMITTED"]}</b></div>
    <div class="stat">Done: <b>{counts["DONE"]}</b></div>
  </div>
  <div class="cols">
    <section class="panel"><h2>📋 Tasks</h2>{task_rows}</section>
    <section class="panel"><h2>📨 Reports</h2>{report_rows}</section>
  </div>
</main>
</div>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: str, status: int = 200, content_type: str = "text/html; charset=utf-8"):
        raw = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self._send(page())
            return
        if path == "/api/dashboard":
            self._send(
                json.dumps(team_center.get_dashboard(), ensure_ascii=False),
                content_type="application/json; charset=utf-8",
            )
            return
        self._send("Not found", 404, "text/plain; charset=utf-8")

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            self._send('{"error":"invalid_json"}', 400, "application/json; charset=utf-8")
            return

        try:
            if path == "/api/tasks":
                task = team_center.create_task(
                    payload.get("agent_id", ""),
                    payload.get("title", ""),
                    payload.get("description", ""),
                    priority=payload.get("priority", "NORMAL"),
                )
                self._send(json.dumps(task, ensure_ascii=False), content_type="application/json; charset=utf-8")
                return

            if path == "/api/tasks/status":
                result = team_center.update_task_status(
                    payload.get("task_id", ""),
                    payload.get("status", ""),
                )
                self._send(json.dumps(result, ensure_ascii=False), content_type="application/json; charset=utf-8")
                return

            if path == "/api/reports":
                report = team_center.submit_report(
                    payload.get("task_id", ""),
                    payload.get("summary", ""),
                    payload.get("details", ""),
                    result=payload.get("result", "UNKNOWN"),
                    reporter=payload.get("reporter", ""),
                )
                self._send(json.dumps(report, ensure_ascii=False), content_type="application/json; charset=utf-8")
                return

            self._send('{"error":"not_found"}', 404, "application/json; charset=utf-8")
        except Exception as exc:
            self._send(
                json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False),
                400,
                "application/json; charset=utf-8",
            )

    def log_message(self, fmt, *args):
        return


def run(host: str = HOST, port: int = PORT):
    team_center.self_check()
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"MINH MINI Team Center: http://{host}:{port}")
    print("Nhan Ctrl+C de dung.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
