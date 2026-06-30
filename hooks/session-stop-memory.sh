#!/usr/bin/env bash
# 鲤鱼 Memory v2.0 — Session Stop Hook
# Captures session memories and consolidates stale entries.

set -euo pipefail

鲤鱼_HOME="$HOME/.claude/liyu"

# Capture memories from current session
python3 "$鲤鱼_HOME/liyu-memory-v2.py" capture 2>/dev/null || true

# Run consolidation (merge duplicates, archive stale)
python3 "$鲤鱼_HOME/liyu-memory-v2.py" consolidate 2>/dev/null || true

# Update last-session.json
SESSION_DATE=$(date -u +%Y-%m-%d)
SESSION_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat > "$鲤鱼_HOME/last-session.json" << EOF
{
  "date": "$SESSION_DATE",
  "last_seen": "$SESSION_TIME",
  "summary": "Session completed at $SESSION_TIME",
  "mood": "正常"
}
EOF

echo "Memory captured and consolidated for session ending at $SESSION_TIME"
