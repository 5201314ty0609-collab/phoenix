#!/usr/bin/env python3
"""
鲤鱼 Unified Event Bus — Shared nervous system for 鲤鱼 + Hermes + MUNDO

Design: Append-only JSONL + pluggable bridges. Zero dependencies.
Pattern: MUNDO v2.0.9 Event Bus (25 event types, pub-sub)

Usage:
  bus.py emit <type> <source> [--payload '{}'] [--severity info]
  bus.py subscribe <pattern>        Subscribe to matching events
  bus.py tail [--source X] [--type X] [--since ISO] [--follow]
  bus.py stats                      Event statistics
  bus.py bridge --hermes|--mundo    Run bridge adapter
"""

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import re
import sys
import threading
import time

# ── Paths ────────────────────────────────────────────────────────────────
BUS_DIR = Path.home() / ".claude/liyu/event-bus"
EVENTS_FILE = BUS_DIR / "events.jsonl"
SUBSCRIBERS_FILE = BUS_DIR / "subscribers.json"
BRIDGES_DIR = BUS_DIR / "bridges"
STATE_FILE = BUS_DIR / "bus-state.json"

# ── Precompiled Regex Cache ──────────────────────────────────────────────
# Cache compiled regex patterns to avoid recompilation on every match call.
# Key: glob pattern string (e.g. "heal.*"), Value: compiled re.Pattern
_regex_cache: dict[str, re.Pattern] = {}
_regex_cache_lock = threading.Lock()


def _get_compiled_regex(glob_pattern: str) -> re.Pattern:
    """Return a precompiled regex for a glob-style pattern. Thread-safe cache."""
    if glob_pattern not in _regex_cache:
        with _regex_cache_lock:
            # Double-check after acquiring lock
            if glob_pattern not in _regex_cache:
                regex_str = glob_pattern.replace("*", ".*")
                _regex_cache[glob_pattern] = re.compile(regex_str)
    return _regex_cache[glob_pattern]


# ── Buffered Writer ──────────────────────────────────────────────────────
# Batches JSONL writes to reduce open/write/close syscall overhead.
# Flushes automatically when buffer reaches capacity or after a time interval.


class BufferedWriter:
    """Thread-safe buffered writer for append-only JSONL files.

    Reduces I/O overhead by batching multiple writes into a single
    file open/write/close cycle. Flushes when buffer is full (capacity)
    or after a time interval (flush_interval_s). Also supports manual
    flush and graceful shutdown via atexit.
    """

    def __init__(self, filepath: Path, capacity: int = 64,
                 flush_interval_s: float = 2.0):
        self._filepath = filepath
        self._capacity = capacity
        self._flush_interval_s = flush_interval_s
        self._buffer: list[str] = []
        self._lock = threading.Lock()
        self._last_flush = time.monotonic()

        # Register atexit to flush remaining buffer on process exit
        import atexit
        atexit.register(self.flush)

    def write(self, line: str) -> None:
        """Append a line to the buffer. Auto-flushes when full."""
        with self._lock:
            self._buffer.append(line)
            if len(self._buffer) >= self._capacity:
                self._flush_locked()
            elif time.monotonic() - self._last_flush >= self._flush_interval_s:
                self._flush_locked()

    def flush(self) -> None:
        """Flush all buffered lines to disk. Safe to call from any thread."""
        with self._lock:
            self._flush_locked()

    def _flush_locked(self) -> None:
        """Internal flush. Caller must hold self._lock."""
        if not self._buffer:
            return
        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self._filepath, "a") as f:
            f.write("".join(self._buffer))
        self._buffer.clear()
        self._last_flush = time.monotonic()


# Module-level buffered writer instance (shared across EventBus instances)
_event_writer = BufferedWriter(EVENTS_FILE, capacity=64, flush_interval_s=2.0)

# ── Event Types ──────────────────────────────────────────────────────────
# Modeled after MUNDO v2.0.9 Event Bus (25 types) + 鲤鱼-specific
EVENT_TYPES = {
    # Session lifecycle
    "session.start":        {"severity": "info",    "desc": "Session begins"},
    "session.end":          {"severity": "info",    "desc": "Session ends"},
    "session.heartbeat":    {"severity": "info",    "desc": "Periodic heartbeat"},

    # Sense alerts (鲤鱼 metacognition)
    "sense.alert":          {"severity": "warn",    "desc": "Sense threshold breached"},
    "sense.o2":             {"severity": "warn",    "desc": "Context pressure alert"},
    "sense.nociception":    {"severity": "critical","desc": "Error cascade detected"},
    "sense.drift":          {"severity": "warn",    "desc": "Topic drift detected"},
    "sense.aesthetic":      {"severity": "info",    "desc": "Design quality alert"},

    # Knowledge graph
    "knowledge.add":        {"severity": "info",    "desc": "Node added to graph"},
    "knowledge.edge":       {"severity": "info",    "desc": "Edge created"},
    "knowledge.extract":    {"severity": "info",    "desc": "Insight extracted from session"},

    # Self-healing
    "heal.observe":         {"severity": "info",    "desc": "Issue observed (Lv1)"},
    "heal.warn":            {"severity": "warn",    "desc": "Pattern warning (Lv2)"},
    "heal.act":             {"severity": "warn",    "desc": "Auto-fix applied (Lv3)"},
    "heal.escalate":        {"severity": "warn",    "desc": "Rule escalated"},
    "heal.resolve":         {"severity": "info",    "desc": "Issue resolved"},

    # Tool calls (Hermes / Claude Code)
    "tool.call":            {"severity": "info",    "desc": "Tool invoked"},
    "tool.error":           {"severity": "warn",    "desc": "Tool call failed"},
    "tool.timeout":         {"severity": "warn",    "desc": "Tool call timed out"},

    # Agent orchestration
    "agent.delegate":       {"severity": "info",    "desc": "Task delegated to sub-agent"},
    "agent.complete":       {"severity": "info",    "desc": "Sub-agent task complete"},
    "agent.error":          {"severity": "warn",    "desc": "Sub-agent error"},

    # Evolution
    "evolution.cycle":      {"severity": "info",    "desc": "Evolution cycle run"},
    "evolution.promote":    {"severity": "info",    "desc": "Framework promoted"},
    "evolution.demote":     {"severity": "warn",    "desc": "Framework demoted"},

    # CTM (Continuous Thought Machine)
    "ctm.thinking.start":    {"severity": "info",    "desc": "Thinking stream started"},
    "ctm.thinking.advance":  {"severity": "info",    "desc": "Thinking stream advanced"},
    "ctm.thinking.complete": {"severity": "info",    "desc": "Thinking stream completed"},
    "ctm.thinking.interrupt":{"severity": "warn",    "desc": "Thinking stream interrupted"},

    # System
    "system.startup":       {"severity": "info",    "desc": "鲤鱼 startup"},
    "system.shutdown":      {"severity": "info",    "desc": "鲤鱼 shutdown"},
    "system.error":         {"severity": "critical","desc": "System-level error"},
    "system.config":        {"severity": "info",    "desc": "Configuration changed"},
}

# ── Core Bus ─────────────────────────────────────────────────────────────

class EventBus:
    def __init__(self):
        BUS_DIR.mkdir(parents=True, exist_ok=True)
        self.subscribers = self._load_subscribers()

    def _load_subscribers(self):
        if SUBSCRIBERS_FILE.exists():
            return json.loads(SUBSCRIBERS_FILE.read_text())
        return []

    def _save_subscribers(self):
        SUBSCRIBERS_FILE.write_text(json.dumps(self.subscribers, ensure_ascii=False, indent=2))

    def emit(self, event_type: str, source: str, payload: dict = None,
             severity: str = None, correlation_id: str = None) -> str:
        """Emit an event to the bus. Returns event ID."""
        if event_type not in EVENT_TYPES:
            print(f"Warning: unknown event type '{event_type}'")

        event = {
            "id": "evt-" + hashlib.md5(
                f"{event_type}{source}{time.time()}".encode()
            ).hexdigest()[:10],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "type": event_type,
            "severity": severity or EVENT_TYPES.get(event_type, {}).get("severity", "info"),
            "payload": payload or {},
            "correlation_id": correlation_id or "",
        }

        _event_writer.write(json.dumps(event, ensure_ascii=False) + "\n")

        # Notify matching subscribers
        self._notify(event)

        return event["id"]

    def _notify(self, event):
        for sub in self.subscribers:
            if not sub.get("enabled", True):
                continue
            pattern = sub.get("pattern", "")
            if self._match(event, pattern):
                self._deliver(sub, event)

    def _match(self, event, pattern):
        """Pattern matching: source:liyu type:heal.* severity:warn

        Uses precompiled regex from module-level cache for glob patterns.
        """
        if not pattern:
            return True
        conditions = pattern.split()
        for cond in conditions:
            if ":" not in cond:
                continue
            field, value = cond.split(":", 1)
            evt_value = event.get(field, "")
            if field == "type":
                # Use precompiled regex from cache (avoids recompilation)
                compiled = _get_compiled_regex(value)
                if not compiled.match(evt_value):
                    return False
            elif evt_value != value:
                return False
        return True

    def _deliver(self, subscriber, event):
        # Write to subscriber's target file
        target = subscriber.get("target", "")
        if target:
            target_path = Path(os.path.expanduser(target))
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "a") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def subscribe(self, pattern: str, target: str, command: str = "",
                  description: str = ""):
        """Add a subscriber."""
        sub = {
            "id": "sub-" + hashlib.md5(f"{pattern}{target}".encode()).hexdigest()[:8],
            "pattern": pattern,
            "target": target,
            "command": command,
            "description": description,
            "enabled": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.subscribers.append(sub)
        self._save_subscribers()
        return sub["id"]

    def unsubscribe(self, sub_id: str):
        for s in self.subscribers:
            if s["id"] == sub_id:
                s["enabled"] = False
        self._save_subscribers()

    def tail(self, source: str = None, event_type: str = None,
             since: str = None, limit: int = 50, follow: bool = False):
        """Read events from the bus. Flushes buffered writes first."""
        # Ensure all buffered events are on disk before reading
        _event_writer.flush()

        if not EVENTS_FILE.exists():
            return []

        # Precompile the type filter regex once if provided
        type_regex = _get_compiled_regex(event_type) if event_type else None

        events = []
        with open(EVENTS_FILE) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    evt = json.loads(line)
                    if source and evt["source"] != source:
                        continue
                    if type_regex and not type_regex.match(evt["type"]):
                        continue
                    if since and evt["timestamp"] < since:
                        continue
                    events.append(evt)
                except Exception:
                    pass

        return events[-limit:]

    def stats(self):
        """Compute event statistics. Flushes buffered writes first."""
        _event_writer.flush()
        if not EVENTS_FILE.exists():
            return {"total": 0, "by_source": {}, "by_type": {}, "by_severity": {}}

        stats = {"total": 0, "by_source": {}, "by_type": {}, "by_severity": {}}
        with open(EVENTS_FILE) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    evt = json.loads(line)
                    stats["total"] += 1
                    src = evt["source"]
                    typ = evt["type"]
                    sev = evt["severity"]
                    stats["by_source"][src] = stats["by_source"].get(src, 0) + 1
                    stats["by_type"][typ] = stats["by_type"].get(typ, 0) + 1
                    stats["by_severity"][sev] = stats["by_severity"].get(sev, 0) + 1
                except Exception:
                    pass
        return stats


# ── Bridge: Hermes → Event Bus ────────────────────────────────────────────

def bridge_hermes():
    """Bridge Hermes session events to 鲤鱼 Event Bus."""
    bus = EventBus()
    hermes_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
    state_db = hermes_home / "state.db"

    if not state_db.exists():
        print("[Hermes Bridge] No state.db found, skipping")
        return

    import sqlite3
    db = sqlite3.connect(str(state_db))
    db.row_factory = sqlite3.Row

    sessions = db.execute(
        "SELECT id, model, started_at, ended_at, message_count, tool_call_count "
        "FROM sessions ORDER BY started_at DESC LIMIT 5"
    ).fetchall()

    for s in sessions:
        bus.emit("session.start", "hermes", {
            "session_id": s["id"],
            "model": s["model"],
            "started_at": s["started_at"],
        })

    db.close()
    print(f"[Hermes Bridge] Bridged {len(sessions)} sessions")


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: bus.py {emit,tail,subscribe,stats,bridge}")
        return

    cmd = sys.argv[1]
    bus = EventBus()

    if cmd == "emit":
        etype = sys.argv[2] if len(sys.argv) > 2 else "system.startup"
        src = sys.argv[3] if len(sys.argv) > 3 else "liyu"
        payload = {}
        severity = None
        for i, arg in enumerate(sys.argv):
            if arg == "--payload" and i + 1 < len(sys.argv):
                try:
                    payload = json.loads(sys.argv[i + 1])
                except Exception:
                    payload = {"raw": sys.argv[i + 1]}
            if arg == "--severity" and i + 1 < len(sys.argv):
                severity = sys.argv[i + 1]
        eid = bus.emit(etype, src, payload, severity)
        print(f"Emitted: {eid} ({etype})")

    elif cmd == "subscribe":
        pattern = sys.argv[2] if len(sys.argv) > 2 else ""
        target = sys.argv[3] if len(sys.argv) > 3 else ""
        sid = bus.subscribe(pattern, target, description=f"CLI:{pattern}")
        print(f"Subscribed: {sid} → {target}")

    elif cmd == "tail":
        source = None
        etype = None
        for i, arg in enumerate(sys.argv):
            if arg == "--source" and i + 1 < len(sys.argv):
                source = sys.argv[i + 1]
            if arg == "--type" and i + 1 < len(sys.argv):
                etype = sys.argv[i + 1]
        events = bus.tail(source=source, event_type=etype, limit=20)
        for e in events:
            print(f"  {e['timestamp'][:19]} [{e['source']:10s}] {e['type']:25s} {json.dumps(e['payload'], ensure_ascii=False)[:80]}")

    elif cmd == "stats":
        s = bus.stats()
        print(f"Events: {s['total']}")
        print(f"By source: {s['by_source']}")
        print(f"By type: {dict(list(s['by_type'].items())[:10])}")
        print(f"By severity: {s['by_severity']}")

    elif cmd == "bridge":
        bridge_type = sys.argv[2] if len(sys.argv) > 2 else ""
        if bridge_type == "--hermes":
            bridge_hermes()
        else:
            print("Usage: bus.py bridge --hermes")

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
