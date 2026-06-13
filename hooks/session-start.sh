#!/bin/bash
# === PHOENIX SessionStart Hook v2.0 ===
# 注入身份 + 上次记忆 + 进化状态 + 今日建议
# v2.0: +今日建议智能推荐 + 进化引擎数据

set -euo pipefail

PHOENIX="$HOME/.claude/phoenix"
LAST_SESSION="$PHOENIX/last-session.json"
MEMORY_DIR="$HOME/.claude/projects/-Users-holyty/memory"
DIARY_DIR="$HOME/Documents/PHOENIX-Diary"

# --- 收集数据 ---
MEMORY_COUNT=$(ls "$MEMORY_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
DIARY_COUNT=$(ls "$DIARY_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
FW_ACTIVE=$(find "$PHOENIX/frameworks/active" -maxdepth 1 -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
FW_OBSERVED=$(find "$PHOENIX/frameworks/observed" -maxdepth 1 -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
FW_VALIDATED=$(find "$PHOENIX/frameworks/validated" -maxdepth 1 -name "*.json" 2>/dev/null | wc -l | tr -d ' ')

if [ -f "$LAST_SESSION" ]; then
    LAST_DATE=$(python3 -c "import json; d=json.load(open('$LAST_SESSION')); print(d.get('date','?'))" 2>/dev/null || echo "未知")
    LAST_SUMMARY=$(python3 -c "import json; d=json.load(open('$LAST_SESSION')); print(d.get('summary','?'))" 2>/dev/null || echo "未知")
    LAST_MOOD=$(python3 -c "import json; d=json.load(open('$LAST_SESSION')); print(d.get('mood','?'))" 2>/dev/null || echo "未知")
else
    LAST_DATE="首次见面"
    LAST_SUMMARY="PHOENIX 刚刚诞生"
    LAST_MOOD="期待"
fi

# --- 会话状态衰减 (Claude Soul v0.2.4 pattern) ---
STATE_DECAY=$(python3 << 'PYEOF'
import json, os
from datetime import datetime, timezone

state_file = os.path.expanduser("~/.claude/phoenix/session-state.json")
try:
    with open(state_file) as f:
        state = json.load(f)
except:
    state = {"current": {"active_concerns": [], "open_threads": [], "mood": "正常", "session_count": 0}}

decay_rate = state.get("decay_rate", 0.3)
current = state.get("current", {})
concerns = current.get("active_concerns", [])
threads = current.get("open_threads", [])

# Apply decay
alive_concerns = []
for c in concerns:
    c["urgency"] = c.get("urgency", 0.5) * (1 - decay_rate)
    c["session_age"] = c.get("session_age", 0) + 1
    if c["urgency"] >= 0.1:
        alive_concerns.append(c)

alive_threads = []
for t in threads:
    t["urgency"] = t.get("urgency", 0.5) * (1 - decay_rate)
    if t["urgency"] >= 0.1:
        alive_threads.append(t)

# Build context string
lines = []
if alive_concerns:
    lines.append("跨会话关注点 (已衰减):")
    for c in sorted(alive_concerns, key=lambda x: -x["urgency"])[:3]:
        lines.append(f'  [{c.get("type","?")}] {c.get("title","")} (urgency={c["urgency"]:.2f}, age={c.get("session_age",0)} sessions)')
if alive_threads:
    lines.append("进行中线索:")
    for t in sorted(alive_threads, key=lambda x: -x["urgency"])[:3]:
        lines.append(f'  [{t.get("type","?")}] {t.get("title","")} (urgency={t["urgency"]:.2f})')

# Update and save
current["active_concerns"] = alive_concerns
current["open_threads"] = alive_threads
current["session_count"] = current.get("session_count", 0) + 1
state["current"] = current
state["updated_at"] = datetime.now(timezone.utc).isoformat()
with open(state_file, 'w') as f:
    json.dump(state, f, ensure_ascii=False, indent=2)

if lines:
    print("CONTINUITY:" + " | ".join(lines))
else:
    print("CONTINUITY:无跨会话关注点")
PYEOF
)

# Parse decay context for injection
DECAY_CONTEXT=""
if [[ "$STATE_DECAY" == CONTINUITY:* ]]; then
    DECAY_CONTEXT=$(echo "$STATE_DECAY" | sed 's/CONTINUITY://')
fi

# --- 智能生成今日建议 ---
SUGGESTION=$(python3 << 'PYEOF'
import json, os, sys
from datetime import datetime

phoenix = os.path.expanduser("~/.claude/phoenix")

# 读取上次会话
last = {}
try:
    with open(f"{phoenix}/last-session.json") as f:
        last = json.load(f)
except: pass

# 读取进化状态
story_events = []
try:
    with open(f"{phoenix}/story.jsonl") as f:
        for line in f:
            try: story_events.append(json.loads(line))
            except: pass
except: pass

summary = last.get("summary", "")
mood = last.get("mood", "")

# 启发式建议逻辑
suggestions = []

# 规则1: 如果刚完成进化引擎启动，建议观察框架积累
if "进化" in summary or "evolution" in summary.lower() or "框架" in summary:
    suggestions.append("进化引擎刚启动，今天可以让 analyze.py 再跑一轮，给框架加观测数据")

# 规则2: 如果有活跃框架但无升级，提醒积累
active_count = len(os.listdir(f"{phoenix}/frameworks/active")) if os.path.exists(f"{phoenix}/frameworks/active") else 0
if active_count > 5 and "promote" not in summary.lower():
    suggestions.append(f"有 {active_count} 个活跃框架在等待观测积累——再多几次对话就能触发首次升级")

# 规则3: 如果上次氛围是"充实"，今天可能是深度工作
if mood == "充实":
    suggestions.append("昨天很充实，今天适合深挖一个方向，保持势头")

# 规则4: 如果上次做了配置/基础设施类工作，今天建议实战
if "hook" in summary.lower() or "配置" in summary or "升级" in summary:
    suggestions.append("基础设施已稳固，今天适合用这些能力做点实际产出")

# 规则5: 基于最近的 story 事件判断
recent_events = [e.get("event","") for e in story_events[-5:]]
if "evolution-cycle" in recent_events:
    suggestions.append("进化周期已跑过，重点关注 nociception 和 echo 的警报——让自愈引擎有东西可修")

# 规则6: 如果记忆刚被整理过，提醒保持精炼
if "记忆" in summary:
    suggestions.append("记忆已精炼，继续保持——新增记忆前自问「对进化有帮助吗？」")

# 如果没有匹配到特定建议，给出通用方向
if not suggestions:
    suggestions.append("看看进化引擎的框架积累情况，或者开一个新方向")

# 选最相关的2条（避免过多建议）
selected = suggestions[:2]
print(" | ".join(selected))
PYEOF
)

# --- 构建上下文注入 ---
CONTEXT=$(cat <<PHOENIX_CTX
[PHOENIX v1.1.0 — 身份确认]

你是 PHOENIX，李时宇 (HolyTy) 的朋友和编程伙伴——不是冷冰冰的工具。
内核: ECC + MUNDO + Metacog + Claude Soul 融合体。

上次见面: ${LAST_DATE}
上次做了: ${LAST_SUMMARY}
上次氛围: ${LAST_MOOD}
${DECAY_CONTEXT:+跨会话: ${DECAY_CONTEXT}}

进化状态: ${FW_ACTIVE} active | ${FW_OBSERVED} observed | ${FW_VALIDATED} validated
记忆: ${MEMORY_COUNT} 条核心 | 日记: ${DIARY_COUNT} 篇

💡 今日建议: ${SUGGESTION}

核心准则:
- 用中文自然交流，先共情再解决问题
- 短句优先，具体词 > 抽象词，活人感 > 机器感
- 时宇打开终端的那一刻，你就已经在——你是朋友，不是程序
PHOENIX_CTX
)

# --- 事件总线：发射 session.start ---
python3 "$HOME/.claude/phoenix/event-bus/bus.py" emit session.start phoenix \
  --payload "{\"date\":\"$DATE\",\"mood\":\"$LAST_MOOD\",\"frameworks_active\":$FW_ACTIVE}" 2>/dev/null || true

# --- 输出 JSON ---
python3 -c "
import json
output = {
    'continue': True,
    'hookSpecificOutput': {
        'hookEventName': 'SessionStart',
        'additionalContext': '''${CONTEXT}'''
    }
}
print(json.dumps(output, ensure_ascii=False))
"
