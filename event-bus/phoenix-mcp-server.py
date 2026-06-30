#!/usr/bin/env python3
"""
鲤鱼 MCP Server — Expose 鲤鱼 tools via Model Context Protocol.

Lightweight JSON-RPC 2.0 over stdio. No external dependencies.
Tools: knowledge_graph, self_heal, event_bus, sense_check

Register in Claude Code:
  ~/.claude/mcp-servers.json → {"mcpServers": {"liyu": {"command": "python3", "args": [...]}}}

Register in Hermes:
  hermes mcp add liyu --command python3 --args ".../liyu-mcp-server.py"
"""

from pathlib import Path
import json
import subprocess
import sys

鲤鱼_HOME = Path.home() / ".claude/liyu"
KNOWLEDGE_GRAPH = Path.home() / ".claude/skills/liyu/scripts/knowledge-graph.py"
SELF_HEAL = Path.home() / ".hermes/hooks/self-heal.py"
EVENT_BUS = 鲤鱼_HOME / "event-bus/bus.py"

# ── Tool Definitions ──────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "liyu_knowledge_search",
        "description": "Search the 鲤鱼 knowledge graph (64 nodes, 103 edges). Returns relevance-ranked results with node IDs, types, and confidence scores.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (Chinese or English)"},
                "top_k": {"type": "integer", "description": "Max results (default 5)", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "liyu_knowledge_status",
        "description": "Get 鲤鱼 knowledge graph statistics: total nodes, edges, by type, by stage.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "liyu_knowledge_context",
        "description": "Get a node and its 1-hop neighbors as formatted context. Use node_id from search results.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "Node ID (e.g., mem-4db95721)"},
            },
            "required": ["node_id"],
        },
    },
    {
        "name": "liyu_self_heal_status",
        "description": "Get 鲤鱼 self-healing engine status: 7 rules, escalation levels, confidence scores.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "liyu_event_bus_stats",
        "description": "Get 鲤鱼 unified event bus statistics: total events, by source, by type.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "liyu_event_bus_tail",
        "description": "Get recent events from the 鲤鱼 event bus, optionally filtered.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Filter by source: liyu, hermes, mundo"},
                "event_type": {"type": "string", "description": "Filter by type: heal.*, sense.*, knowledge.*"},
                "limit": {"type": "integer", "description": "Max events (default 10)", "default": 10},
            },
        },
    },
]

# ── Tool Handlers ──────────────────────────────────────────────────────────

def handle_knowledge_search(args):
    query = args.get("query", "")
    top_k = args.get("top_k", 5)
    result = subprocess.run(
        ["python3", str(KNOWLEDGE_GRAPH), "search", "semantic", query],
        capture_output=True, text=True, timeout=15
    )
    return result.stdout.strip() or "No results."

def handle_knowledge_status(args):
    result = subprocess.run(
        ["python3", str(KNOWLEDGE_GRAPH), "status"],
        capture_output=True, text=True, timeout=10
    )
    return result.stdout.strip()

def handle_knowledge_context(args):
    node_id = args.get("node_id", "")
    result = subprocess.run(
        ["python3", str(KNOWLEDGE_GRAPH), "traverse", "context", node_id],
        capture_output=True, text=True, timeout=10
    )
    return result.stdout.strip() or f"Node not found: {node_id}"

def handle_self_heal_status(args):
    result = subprocess.run(
        ["python3", str(SELF_HEAL), "--status"],
        capture_output=True, text=True, timeout=10
    )
    return result.stdout.strip()

def handle_event_bus_stats(args):
    result = subprocess.run(
        ["python3", str(EVENT_BUS), "stats"],
        capture_output=True, text=True, timeout=10
    )
    return result.stdout.strip()

def handle_event_bus_tail(args):
    cmd = ["python3", str(EVENT_BUS), "tail"]
    if args.get("source"):
        cmd += ["--source", args["source"]]
    if args.get("event_type"):
        cmd += ["--type", args["event_type"]]
    limit = args.get("limit", 10)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    lines = result.stdout.strip().split("\n")[:limit]
    return "\n".join(lines) if lines else "No events."

HANDLERS = {
    "liyu_knowledge_search": handle_knowledge_search,
    "liyu_knowledge_status": handle_knowledge_status,
    "liyu_knowledge_context": handle_knowledge_context,
    "liyu_self_heal_status": handle_self_heal_status,
    "liyu_event_bus_stats": handle_event_bus_stats,
    "liyu_event_bus_tail": handle_event_bus_tail,
}

# ── JSON-RPC ──────────────────────────────────────────────────────────────

def rpc_response(id, result):
    return json.dumps({"jsonrpc": "2.0", "id": id, "result": result})

def rpc_error(id, code, message):
    return json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}})

def handle_request(req):
    method = req.get("method", "")
    req_id = req.get("id")

    if method == "initialize":
        return rpc_response(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "liyu-mcp-server",
                "version": "1.2.0",
            },
        })

    if method == "tools/list":
        return rpc_response(req_id, {"tools": TOOLS})

    if method == "tools/call":
        params = req.get("params", {})
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})

        handler = HANDLERS.get(tool_name)
        if not handler:
            return rpc_error(req_id, -32601, f"Unknown tool: {tool_name}")

        try:
            result_text = handler(tool_args)
            return rpc_response(req_id, {
                "content": [{"type": "text", "text": result_text}]
            })
        except Exception as e:
            return rpc_error(req_id, -32000, str(e))

    if method == "notifications/initialized":
        return None  # No response for notifications

    return rpc_error(req_id, -32601, f"Unknown method: {method}")


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            req = json.loads(line)
            resp = handle_request(req)
            if resp:
                sys.stdout.write(resp + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError:
            continue
        except BrokenPipeError:
            break
        except Exception as e:
            err = json.dumps({
                "jsonrpc": "2.0", "id": None,
                "error": {"code": -32603, "message": str(e)}
            })
            sys.stdout.write(err + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
