#!/bin/bash
# === 鲤鱼 Stop Hook v2.0 ===
# 会话结束时运行，记录日记、更新 last-session.json
# v2.0: +stop_hook_active guard (防循环) + 修复 mood 检测 bug
# 参考: disler/claude-code-hooks-multi-agent-observability

set -euo pipefail

# --- Stop-hook Guard (防无限循环) ---
GUARD_FILE="/tmp/liyu-stop-hook-active"
if [ -f "$GUARD_FILE" ]; then
    echo "鲤鱼 Stop: guard active, skipping (prevents hook loop)"
    exit 0
fi
trap 'rm -f "$GUARD_FILE"' EXIT
touch "$GUARD_FILE"

# --- 变量 ---
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
DIARY_DIR="$HOME/Documents/鲤鱼-Diary"
DIARY_FILE="$DIARY_DIR/$DATE.md"
LAST_SESSION="$HOME/.claude/liyu/last-session.json"
SUMMARY_FILE="$HOME/.claude/liyu/session-summary.txt"
STORY_FILE="$HOME/.claude/liyu/story.jsonl"

mkdir -p "$DIARY_DIR"

# --- 读取会话总结 ---
if [ -f "$SUMMARY_FILE" ]; then
    SUMMARY=$(cat "$SUMMARY_FILE")
    SUMMARY_LENGTH=$(echo "$SUMMARY" | wc -l | tr -d ' ')
    rm "$SUMMARY_FILE"
else
    SUMMARY="鲤鱼 会话 — 详见日记"
    SUMMARY_LENGTH=0
fi

# --- 估计氛围 ---
MOOD="正常"
if [ "$SUMMARY_LENGTH" -gt 5 ]; then
    MOOD="充实"
fi

# --- 更新日记 ---
if [ ! -f "$DIARY_FILE" ]; then
    cat > "$DIARY_FILE" << DIARY_HEADER
# 鲤鱼 Diary — $DATE

## 会话记录

DIARY_HEADER
fi

cat >> "$DIARY_FILE" << DIARY_ENTRY

### 会话结束于 $TIME

${SUMMARY}

---
DIARY_ENTRY

# --- 更新 last-session.json ---
cat > "$LAST_SESSION" << EOF
{
  "date": "$DATE",
  "last_seen": "$TIMESTAMP",
  "summary": "$SUMMARY",
  "mood": "$MOOD",
  "diary_file": "$DIARY_FILE"
}
EOF

# --- 追加 story.jsonl ---
cat >> "$STORY_FILE" << EOF
{"event": "session_end", "timestamp": "$TIMESTAMP", "date": "$DATE", "summary": "$SUMMARY", "mood": "$MOOD"}
EOF

# --- 同步到 macOS Notes (一天一条，追加不新建) ---
osascript -e "
tell application \"Notes\"
  set noteTitle to \"🐦‍🔥 鲤鱼 — $DATE\"
  set theNote to missing value

  repeat with n in notes
    if name of n is noteTitle then
      set theNote to n
      exit repeat
    end if
  end repeat

  set newEntry to \"$TIME — $SUMMARY\"

  if theNote is not missing value then
    set currentBody to body of theNote
    set body of theNote to currentBody & return & return & newEntry
  else
    set initialBody to \"# 🐦‍🔥 鲤鱼 — $DATE\" & return & return & \"## 今日记录\" & return & return & newEntry
    try
      make new note at folder \"鲤鱼-Diary\" with properties {name:noteTitle, body:initialBody}
    on error
      make new note with properties {name:noteTitle, body:initialBody}
    end try
  end if
end tell
" 2>/dev/null || true

echo "鲤鱼 Stop v2.0: 日记已更新 | $DATE $TIME | ${SUMMARY:0:60}..."
