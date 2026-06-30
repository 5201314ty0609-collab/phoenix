#!/usr/bin/env bash
# 鲤鱼 Memory v2.0 — Session Start Hook
# Primes context from unified memory system and writes to a temp file
# for the agent to read at session start.

set -euo pipefail

PRIME_FILE="/tmp/liyu-memory-prime.md"
鲤鱼_HOME="$HOME/.claude/liyu"

# Generate prime context
python3 "$鲤鱼_HOME/liyu-memory-v2.py" prime > "$PRIME_FILE" 2>/dev/null || true

# Run auto-memory capture from recent sessions
python3 "$鲤鱼_HOME/liyu-memory-v2.py" capture 2>/dev/null || true

# Build cross-store links (lightweight, runs in background)
python3 "$鲤鱼_HOME/liyu-memory-v2.py" link 2>/dev/null &

echo "Memory primed: $PRIME_FILE"
