#!/usr/bin/env python3
"""
PHOENIX Web Server — 独立 HTTP API + 仪表盘
Pure Python stdlib. Zero dependencies.

Endpoints:
  GET  /                  PHOENIX Dashboard
  GET  /api/status        System health + 7-Sense + drift
  GET  /api/modules       Module inventory
  GET  /api/timeline      Recent timeline (query: ?limit=20&type=X)
  GET  /api/persona       NexSandglass persona
  GET  /api/tool-guard    Tool guard alerts
  GET  /api/skills        Skill registry stats
  GET  /api/events        Event bus stats

Usage:
  python3 server.py [--port 8765] [--host 0.0.0.0]
"""

import json
import os
import sys
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """多线程 HTTP 服务器——支持 SSE 长连接不阻塞其他请求"""
    daemon_threads = True
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs

PHOENIX_HOME = Path.home() / ".claude" / "phoenix"
sys.path.insert(0, str(PHOENIX_HOME))
DASHBOARD_FILE = PHOENIX_HOME / "dashboard.html"
PORT = 8765
HOST = "127.0.0.1"


# ── API Handlers ───────────────────────────────────────────────────────────

def api_status() -> dict:
    """系统综合状态"""
    data = {
        "phoenix": {
            "version": "1.3.0",
            "uptime": "since session start",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }

    # 7-Sense states
    senses = {}
    senses_dir = PHOENIX_HOME / "senses"
    if senses_dir.exists():
        for f in sorted(senses_dir.glob("*.json")):
            try:
                sense = json.loads(f.read_text())
                senses[f.stem] = {
                    "state": sense.get("state", "unknown"),
                    "trend": sense.get("trend", ""),
                }
            except (json.JSONDecodeError, OSError):
                pass
    data["senses"] = senses

    # Drift velocity (NexSandglass)
    drift_file = PHOENIX_HOME / "nexsandglass" / "drift.json"
    if drift_file.exists():
        try:
            drift = json.loads(drift_file.read_text())
            data["drift"] = {
                "direction": drift.get("current_direction", "unknown"),
                "stability": drift.get("stability", "unknown"),
                "trend_slope": drift.get("trend_slope", 0),
            }
        except (json.JSONDecodeError, OSError):
            pass

    # Framework evolution
    frameworks_dir = PHOENIX_HOME / "frameworks" / "active"
    if frameworks_dir.exists():
        data["evolution"] = {
            "active_frameworks": len(list(frameworks_dir.glob("*.json"))),
        }

    return data


def api_modules() -> dict:
    """模块清单与统计"""
    modules = {}
    for py_file in sorted(PHOENIX_HOME.glob("*.py")):
        if py_file.name.startswith("test_"):
            continue
        try:
            content = py_file.read_text()
            lines = len(content.split("\n"))
            # Extract docstring summary
            summary = ""
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith('"""') and not line == '"""':
                    summary = line.replace('"""', "").strip()[:100]
                    break
            modules[py_file.stem] = {
                "lines": lines,
                "summary": summary,
                "size_kb": round(py_file.stat().st_size / 1024, 1),
            }
        except OSError:
            pass

    total_lines = sum(m["lines"] for m in modules.values())
    return {
        "modules": modules,
        "total_modules": len(modules),
        "total_lines": total_lines,
    }


def api_timeline(params: dict) -> dict:
    """时间线查询"""
    limit = min(int(params.get("limit", [20])[0]), 100)
    event_type = params.get("type", [None])[0]

    try:
        from timeline import query
        rows = query(limit=limit, event_type=event_type)
        return {"entries": rows, "total": len(rows)}
    except ImportError:
        # Fallback: read story.jsonl directly
        story_file = PHOENIX_HOME / "story.jsonl"
        entries = []
        if story_file.exists():
            with open(story_file) as f:
                for line in f:
                    if line.strip():
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        return {"entries": entries[-limit:], "total": len(entries), "source": "story.jsonl"}


def api_persona() -> dict:
    """NexSandglass 画像"""
    persona_file = PHOENIX_HOME / "nexsandglass" / "persona.md"
    drift_file = PHOENIX_HOME / "nexsandglass" / "drift.json"
    sand_db = PHOENIX_HOME / "nexsandglass" / "sand.db"

    result = {"available": False}

    if persona_file.exists():
        try:
            result["persona"] = persona_file.read_text()[:3000]
            result["available"] = True
        except OSError:
            pass

    if drift_file.exists():
        try:
            drift = json.loads(drift_file.read_text())
            result["drift"] = {
                "direction": drift.get("current_direction"),
                "stability": drift.get("stability"),
                "history": drift.get("history", [])[-7:],
            }
        except (json.JSONDecodeError, OSError):
            pass

    # Grain count
    if sand_db.exists():
        import sqlite3
        try:
            db = sqlite3.connect(str(sand_db))
            count = db.execute("SELECT COUNT(*) FROM sand").fetchone()[0]
            db.close()
            result["total_grains"] = count
        except Exception:
            pass

    return result


def api_tool_guard() -> dict:
    """工具防护状态"""
    state_file = PHOENIX_HOME / "tool-guard-state.json"
    config_file = PHOENIX_HOME / "tool-guard-config.json"

    result = {}
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
            result["alerts"] = {
                "exact_failures": {
                    k: v for k, v in state.get("exact_failures", {}).items() if v >= 2
                },
                "tool_failures": {
                    k: v for k, v in state.get("tool_failures", {}).items() if v >= 2
                },
                "no_progress": state.get("no_progress", {}),
            }
            result["summary"] = {
                "total_observed": state.get("total_observed", 0),
                "total_warned": state.get("total_warned", 0),
                "total_blocked": state.get("total_blocked", 0),
                "total_halted": state.get("total_halted", 0),
            }
        except (json.JSONDecodeError, OSError):
            pass

    if config_file.exists():
        try:
            config = json.loads(config_file.read_text())
            result["thresholds"] = config.get("thresholds", {})
        except (json.JSONDecodeError, OSError):
            pass

    return result


def api_skills() -> dict:
    """技能注册表统计"""
    skills_dir = Path.home() / ".claude" / "skills"
    if not skills_dir.exists():
        return {"total": 0}

    # Count skills with skill.json
    total = 0
    with_deps = 0
    with_conflicts = 0
    for d in skills_dir.iterdir():
        if d.is_dir() and (d / "SKILL.md").exists():
            total += 1
            if (d / "skill.json").exists():
                try:
                    meta = json.loads((d / "skill.json").read_text())
                    if meta.get("dependencies"):
                        with_deps += 1
                    if meta.get("conflicts"):
                        with_conflicts += 1
                except (json.JSONDecodeError, OSError):
                    pass

    return {
        "total": total,
        "with_dependencies": with_deps,
        "with_conflicts": with_conflicts,
        "orphans": total - with_deps - with_conflicts,
    }


def api_events() -> dict:
    """事件总线统计"""
    events_file = PHOENIX_HOME / "event-bus" / "events.jsonl"
    if not events_file.exists():
        return {"total": 0}

    total = 0
    by_type = {}
    by_source = {}
    with open(events_file) as f:
        for line in f:
            if line.strip():
                try:
                    evt = json.loads(line)
                    total += 1
                    t = evt.get("type", "unknown")
                    s = evt.get("source", "unknown")
                    by_type[t] = by_type.get(t, 0) + 1
                    by_source[s] = by_source.get(s, 0) + 1
                except json.JSONDecodeError:
                    pass

    return {
        "total": total,
        "by_type": dict(sorted(by_type.items(), key=lambda x: -x[1])[:10]),
        "by_source": by_source,
    }


# ── Action APIs (POST) ─────────────────────────────────────────────────────

def api_evolve(params: dict = None) -> dict:
    """触发进化分析"""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "policy_engine", PHOENIX_HOME / "policy-engine.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        engine = mod.PolicyEngine()
        stats = engine.stats()
        return {"status": "ok", "action": "evolve", "rules": stats["total_rules"]}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def api_tool_guard_reset(params: dict = None) -> dict:
    """重置工具防护状态"""
    tool = (params or {}).get("tool", ["all"])
    if isinstance(tool, list): tool = tool[0]
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "tool_guard", PHOENIX_HOME / "tool-guard.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        guard = mod.ToolGuard()
        result = guard.reset(tool)
        return {"status": "ok", "action": "reset", "detail": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def api_persona_rebuild(params: dict = None) -> dict:
    """强制重建画像（full scan）"""
    try:
        from nexsandglass import NexSandglass
        ns = NexSandglass()
        persona = ns.persona.build(full=True)
        guide = ns.interaction_guide()
        return {
            "status": "ok",
            "action": "persona_rebuild",
            "grains": persona.get("total_grains", 0),
            "guide_preview": guide[:200],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def api_drift_recalc(params: dict = None) -> dict:
    """重新计算偏移率"""
    try:
        from nexsandglass import NexSandglass
        ns = NexSandglass()
        drift = ns.drift.compute_range(30)
        return {"status": "ok", "action": "drift_recalc", "drift": drift}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def api_timeline_detail(params: dict) -> dict:
    """增强时间线查询——支持搜索、过滤、分页"""
    limit = min(int(params.get("limit", [50])[0]), 200)
    event_type = params.get("type", [None])[0]
    search = params.get("search", [None])[0]
    source = params.get("source", [None])[0]

    try:
        from timeline import query
        rows = query(limit=limit, event_type=event_type, source=source, search=search)
        return {"entries": rows, "total": len(rows), "filters": {
            "type": event_type, "search": search, "source": source,
        }}
    except ImportError:
        return api_timeline(params)


def api_users() -> dict:
    """用户层级列表"""
    try:
        from user_manager import UserManager
        mgr = UserManager()
        return {
            "users": mgr.list_all(),
            "stats": mgr.stats(),
        }
    except Exception as e:
        return {"error": str(e)}


def api_sense_detail(params: dict) -> dict:
    """单个 sense 详情"""
    sense_name = params.get("name", ["o2"])[0]
    sense_file = PHOENIX_HOME / "senses" / f"{sense_name}.json"
    if sense_file.exists():
        try:
            return json.loads(sense_file.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"error": "sense not found"}


# ── SSE (Server-Sent Events) ─────────────────────────────────────────────

# SSE 客户端列表：每个客户端是一个 queue
_sse_clients: list = []


def api_stream(params: dict = None):
    """SSE 事件流——Generator，不返回 dict"""
    import queue
    q = queue.Queue()
    _sse_clients.append(q)
    try:
        # 发送初始连接事件
        yield f"event: connected\ndata: {json.dumps({'status':'connected','clients':len(_sse_clients)})}\n\n"
        while True:
            try:
                event = q.get(timeout=30)
                yield f"event: {event.get('event','update')}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
            except queue.Empty:
                yield f"event: heartbeat\ndata: {json.dumps({'timestamp':datetime.now(timezone.utc).isoformat()})}\n\n"
    except GeneratorExit:
        pass
    finally:
        if q in _sse_clients:
            _sse_clients.remove(q)


def _broadcast_sse(event: dict):
    """向所有 SSE 客户端广播事件"""
    dead = []
    for q in _sse_clients:
        try:
            q.put_nowait(event)
        except Exception:
            dead.append(q)
    for q in dead:
        if q in _sse_clients:
            _sse_clients.remove(q)


def _poll_sse_events():
    """检查 sse-events.jsonl 是否有新事件，有则广播"""
    sse_file = PHOENIX_HOME / "nexsandglass" / "sse-events.jsonl"
    if not sse_file.exists():
        return
    # Track last read position
    state_file = PHOENIX_HOME / "nexsandglass" / ".sse-position"
    last_pos = 0
    if state_file.exists():
        try:
            last_pos = int(state_file.read_text().strip())
        except (ValueError, OSError):
            pass
    current_size = sse_file.stat().st_size
    if current_size > last_pos:
        with open(sse_file) as f:
            f.seek(last_pos)
            for line in f:
                if line.strip():
                    try:
                        event = json.loads(line)
                        _broadcast_sse(event)
                    except json.JSONDecodeError:
                        pass
        state_file.write_text(str(current_size))


# ── HTTP Server ────────────────────────────────────────────────────────────

GET_ROUTES = {
    "/api/status": api_status,
    "/api/modules": api_modules,
    "/api/timeline": api_timeline,
    "/api/persona": api_persona,
    "/api/tool-guard": api_tool_guard,
    "/api/skills": api_skills,
    "/api/events": api_events,
    "/api/timeline/detail": api_timeline_detail,
    "/api/sense/detail": api_sense_detail,
    "/api/stream": api_stream,
    "/api/users": api_users,
}

POST_ROUTES = {
    "/api/evolve": api_evolve,
    "/api/tool-guard/reset": api_tool_guard_reset,
    "/api/persona/rebuild": api_persona_rebuild,
    "/api/drift/recalc": api_drift_recalc,
}


class PhoenixHandler(BaseHTTPRequestHandler):
    """PHOENIX HTTP Request Handler"""

    def log_message(self, format, *args):
        """Silence default logging — use our own."""
        pass

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False, indent=2)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def _send_html(self, html: str, status: int = 200):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_sse(self, generator):
        """发送 SSE 事件流"""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            for chunk in generator:
                self.wfile.write(chunk.encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send_error(self, msg: str, status: int = 500):
        self._send_json({"error": msg}, status)

    def _route_get(self, path, params):
        """Handle GET routes. Returns (result, is_sse)"""
        if path in GET_ROUTES:
            handler = GET_ROUTES[path]
            is_sse = (path == "/api/stream")
            if path in ("/api/timeline", "/api/timeline/detail", "/api/sense/detail"):
                return handler(params), is_sse
            return handler(), is_sse
        return None, False

    def do_GET(self):
        # Poll SSE events on any request (keeps broadcasts flowing)
        _poll_sse_events()

        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        params = parse_qs(parsed.query)

        # Dashboard
        if path == "/" or path == "/dashboard":
            if DASHBOARD_FILE.exists():
                try:
                    html = DASHBOARD_FILE.read_text()
                    self._send_html(html)
                    return
                except OSError:
                    pass
            self._send_html("<h1>PHOENIX Dashboard</h1><p>Dashboard file not found.</p>")
            return

        # API routes
        try:
            result, is_sse = self._route_get(path, params)
            if result is not None:
                if is_sse:
                    self._send_sse(result)
                else:
                    self._send_json(result)
                return
        except Exception as e:
            self._send_error(str(e))
            return

        # Health check
        if path == "/health":
            self._send_json({"status": "ok", "service": "PHOENIX"})
            return

        # 404
        self._send_error("Not found", 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        params = parse_qs(parsed.query)

        # Read body for JSON params
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > 0:
                body = self.rfile.read(length)
                body_params = json.loads(body)
                if isinstance(body_params, dict):
                    # Merge body params into query params
                    for k, v in body_params.items():
                        params[k] = [v] if not isinstance(v, list) else v
        except (json.JSONDecodeError, ValueError):
            pass

        if path in POST_ROUTES:
            try:
                handler = POST_ROUTES[path]
                result = handler(params)
                self._send_json(result)
            except Exception as e:
                self._send_error(str(e))
            return

        self._send_error("Not found", 404)

    def do_OPTIONS(self):
        """CORS preflight"""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def main():
    global PORT, HOST

    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            PORT = int(sys.argv[i + 1])
        if arg == "--host" and i + 1 < len(sys.argv):
            HOST = sys.argv[i + 1]

    server = ThreadingHTTPServer((HOST, PORT), PhoenixHandler)
    print(f"🐦‍🔥 PHOENIX Server")
    print(f"   http://{HOST}:{PORT}")
    print(f"   API: http://{HOST}:{PORT}/api/status")
    print(f"   Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 PHOENIX Server stopped")
        server.server_close()


if __name__ == "__main__":
    main()
