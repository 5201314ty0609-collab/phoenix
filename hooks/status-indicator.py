#!/usr/bin/env python3
"""
PHOENIX Status Indicator — 状态指示器
提供上下文使用率、工具执行成功率、错误级联状态、Agent 协调状态等可视化指示

功能：
  1. 实时状态概览
  2. 健康分数计算
  3. 趋势分析
  4. 预警系统
  5. 状态导出

用法：
  status-indicator.py overview
    显示完整状态概览

  status-indicator.py health
    显示健康分数

  status-indicator.py trends [--hours <n>]
    显示趋势分析

  status-indicator.py warnings
    显示当前警告

  status-indicator.py export [--format <json|text>]
    导出状态数据
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import statistics

PHOENIX_HOME = Path.home() / ".claude" / "phoenix"
SENSES_DIR = PHOENIX_HOME / "senses"
TOOL_GUARD_STATE = PHOENIX_HOME / "tool-guard-state.json"
SESSION_STATE = PHOENIX_HOME / "session-state.json"
HEARTBEAT_DIR = PHOENIX_HOME / "heartbeats"
METRICS_HISTORY = PHOENIX_HOME / "monitor-metrics-history.jsonl"


def load_senses() -> dict:
    """加载所有 Sense 数据"""
    senses = {}
    if SENSES_DIR.exists():
        for sense_file in SENSES_DIR.glob("*.json"):
            try:
                with open(sense_file) as f:
                    senses[sense_file.stem] = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
    return senses


def load_tool_guard_state() -> dict:
    """加载 Tool Guard 状态"""
    if TOOL_GUARD_STATE.exists():
        try:
            with open(TOOL_GUARD_STATE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def load_session_state() -> dict:
    """加载 Session 状态"""
    if SESSION_STATE.exists():
        try:
            with open(SESSION_STATE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def load_heartbeats() -> List[dict]:
    """加载心跳数据"""
    heartbeats = []
    if HEARTBEAT_DIR.exists():
        for hb_file in HEARTBEAT_DIR.glob("*.heartbeat"):
            try:
                with open(hb_file) as f:
                    heartbeats.append(json.load(f))
            except (json.JSONDecodeError, OSError):
                pass
    return heartbeats


def load_metrics_history(hours: int = 24) -> List[dict]:
    """加载指标历史"""
    history = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    if METRICS_HISTORY.exists():
        try:
            with open(METRICS_HISTORY) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        timestamp = entry.get("timestamp", "")
                        if timestamp:
                            entry_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                            if entry_time > cutoff:
                                history.append(entry)
                    except:
                        pass
        except OSError:
            pass

    return history


def calculate_health_score(senses: dict, tool_guard: dict, heartbeats: List[dict]) -> dict:
    """计算健康分数"""
    score = 100
    issues = []

    # O2 (Vitality) - 上下文压力
    o2 = senses.get("o2", {})
    o2_status = o2.get("status", "normal")
    if o2_status == "critical":
        score -= 25
        issues.append("O2: 上下文压力严重")
    elif o2_status == "warning":
        score -= 10
        issues.append("O2: 上下文压力较高")

    # Nociception (Pain) - 错误级联
    nociception = senses.get("nociception", {})
    nociception_status = nociception.get("status", "normal")
    if nociception_status == "critical":
        score -= 30
        issues.append("Nociception: 错误级联严重")
    elif nociception_status == "warning":
        score -= 15
        issues.append("Nociception: 错误较多")

    # Chronos (Time) - 会话节奏
    chronos = senses.get("chronos", {})
    chronos_status = chronos.get("status", "normal")
    if chronos_status == "critical":
        score -= 15
        issues.append("Chronos: 会话时间过长")
    elif chronos_status == "warning":
        score -= 5
        issues.append("Chronos: 会话时间较长")

    # Spatial (Workspace) - 文件变动
    spatial = senses.get("spatial", {})
    spatial_status = spatial.get("status", "normal")
    if spatial_status == "critical":
        score -= 10
        issues.append("Spatial: 文件变动过大")
    elif spatial_status == "warning":
        score -= 5
        issues.append("Spatial: 文件变动较多")

    # Vestibular (Balance) - 工具多样性
    vestibular = senses.get("vestibular", {})
    vestibular_status = vestibular.get("status", "normal")
    if vestibular_status == "critical":
        score -= 10
        issues.append("Vestibular: 工具使用不平衡")
    elif vestibular_status == "warning":
        score -= 5
        issues.append("Vestibular: 工具使用较集中")

    # Echo (Repetition) - 模式重复
    echo = senses.get("echo", {})
    echo_status = echo.get("status", "normal")
    if echo_status == "critical":
        score -= 15
        issues.append("Echo: 模式重复严重")
    elif echo_status == "warning":
        score -= 5
        issues.append("Echo: 有一定重复")

    # Drift (Focus) - 主题漂移
    drift = senses.get("drift", {})
    drift_status = drift.get("status", "normal")
    if drift_status == "critical":
        score -= 10
        issues.append("Drift: 主题漂移严重")
    elif drift_status == "warning":
        score -= 5
        issues.append("Drift: 主题有些漂移")

    # Tool Guard 状态
    total_observed = tool_guard.get("total_observed", 0)
    total_blocked = tool_guard.get("total_blocked", 0)
    total_halted = tool_guard.get("total_halted", 0)

    if total_halted > 0:
        score -= 20
        issues.append(f"Tool Guard: {total_halted} 次强制中止")
    elif total_blocked > 0:
        score -= 10
        issues.append(f"Tool Guard: {total_blocked} 次阻断")

    # Agent 心跳状态
    stale_agents = [hb for hb in heartbeats
                    if hb.get("timestamp", "") and
                    (datetime.now(timezone.utc) - datetime.fromisoformat(
                        hb["timestamp"].replace("Z", "+00:00"))).total_seconds() > 120]

    if len(stale_agents) > 0:
        score -= 10
        issues.append(f"Agent: {len(stale_agents)} 个 Agent 心跳过期")

    # 确保分数在 0-100 之间
    score = max(0, min(100, score))

    # 确定健康等级
    if score >= 90:
        level = "excellent"
    elif score >= 75:
        level = "good"
    elif score >= 60:
        level = "fair"
    elif score >= 40:
        level = "poor"
    else:
        level = "critical"

    return {
        "score": score,
        "level": level,
        "issues": issues,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def analyze_trends(history: List[dict]) -> dict:
    """分析趋势"""
    if not history:
        return {"trend": "stable", "change_rate": 0, "data_points": 0}

    # 提取健康分数
    scores = []
    for entry in history:
        summary = entry.get("metrics_summary", {})
        # 简单估算健康分数
        error_count = summary.get("error_count", 0)
        score = max(0, 100 - error_count * 10)
        scores.append(score)

    if len(scores) < 2:
        return {"trend": "stable", "change_rate": 0, "data_points": len(scores)}

    # 计算趋势
    avg_first_half = statistics.mean(scores[:len(scores)//2])
    avg_second_half = statistics.mean(scores[len(scores)//2:])

    change_rate = avg_second_half - avg_first_half

    if change_rate > 5:
        trend = "improving"
    elif change_rate < -5:
        trend = "declining"
    else:
        trend = "stable"

    return {
        "trend": trend,
        "change_rate": round(change_rate, 2),
        "data_points": len(scores),
        "average_score": round(statistics.mean(scores), 2),
        "min_score": min(scores),
        "max_score": max(scores)
    }


def get_warnings(senses: dict, tool_guard: dict, heartbeats: List[dict]) -> List[dict]:
    """获取当前警告"""
    warnings = []

    # 检查各 Sense 状态
    for sense_name, sense_data in senses.items():
        status = sense_data.get("status", "normal")
        if status in ("warning", "critical"):
            warnings.append({
                "source": sense_name,
                "level": status,
                "message": f"{sense_name} 状态: {status}",
                "recommendation": sense_data.get("recommendation", ""),
                "metrics": sense_data.get("metrics", {})
            })

    # 检查 Tool Guard 警告
    exact_failures = tool_guard.get("exact_failures", {})
    for key, count in exact_failures.items():
        if count >= 3:
            warnings.append({
                "source": "tool_guard",
                "level": "warning",
                "message": f"工具 {key} 精确失败 {count} 次",
                "recommendation": "change_strategy"
            })

    # 检查 Agent 心跳警告
    now = datetime.now(timezone.utc)
    for hb in heartbeats:
        timestamp = hb.get("timestamp", "")
        if timestamp:
            try:
                hb_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                age_seconds = (now - hb_time).total_seconds()
                if age_seconds > 120:
                    warnings.append({
                        "source": "heartbeat",
                        "level": "warning",
                        "message": f"Agent {hb.get('agent_id', 'unknown')} 心跳过期 {int(age_seconds)} 秒",
                        "recommendation": "check_agent"
                    })
            except:
                pass

    # 按级别排序
    level_order = {"critical": 0, "warning": 1, "info": 2}
    warnings.sort(key=lambda x: level_order.get(x.get("level", "info"), 2))

    return warnings


def format_overview(senses: dict, tool_guard: dict, heartbeats: List[dict],
                    health: dict, warnings: List[dict]) -> str:
    """格式化状态概览"""
    lines = []
    lines.append("═══ PHOENIX Status Overview ═══")
    lines.append("")

    # 健康分数
    score = health["score"]
    level = health["level"]
    level_icons = {"excellent": "🟢", "good": "🟡", "fair": "🟠", "poor": "🔴", "critical": "⛔"}
    icon = level_icons.get(level, "⚪")

    lines.append(f"健康分数: {score}/100 {icon} ({level})")
    lines.append("")

    # 7-Sense 状态
    lines.append("7-Sense 状态:")
    sense_icons = {"normal": "🟢", "warning": "🟡", "critical": "🔴"}
    for sense_name, sense_data in senses.items():
        status = sense_data.get("status", "normal")
        icon = sense_icons.get(status, "⚪")
        lines.append(f"  {icon} {sense_name}: {status}")
    lines.append("")

    # Tool Guard 统计
    lines.append("Tool Guard 统计:")
    lines.append(f"  总观测: {tool_guard.get('total_observed', 0)}")
    lines.append(f"  警告: {tool_guard.get('total_warned', 0)}")
    lines.append(f"  阻断: {tool_guard.get('total_blocked', 0)}")
    lines.append(f"  中止: {tool_guard.get('total_halted', 0)}")
    lines.append("")

    # Agent 状态
    lines.append("Agent 状态:")
    lines.append(f"  活跃 Agent: {len(heartbeats)}")
    lines.append("")

    # 警告
    if warnings:
        lines.append(f"当前警告 ({len(warnings)}):")
        for warning in warnings[:5]:  # 只显示前 5 个
            icon = "🔴" if warning.get("level") == "critical" else "🟡"
            lines.append(f"  {icon} {warning.get('message', '')}")
        if len(warnings) > 5:
            lines.append(f"  ... 还有 {len(warnings) - 5} 个警告")
    else:
        lines.append("当前无警告 ✅")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    # 加载数据
    senses = load_senses()
    tool_guard = load_tool_guard_state()
    heartbeats = load_heartbeats()

    if cmd == "overview":
        health = calculate_health_score(senses, tool_guard, heartbeats)
        warnings = get_warnings(senses, tool_guard, heartbeats)
        overview = format_overview(senses, tool_guard, heartbeats, health, warnings)
        print(overview)

    elif cmd == "health":
        health = calculate_health_score(senses, tool_guard, heartbeats)
        print(json.dumps(health, ensure_ascii=False, indent=2))

    elif cmd == "trends":
        hours = 24
        if "--hours" in sys.argv:
            idx = sys.argv.index("--hours")
            if idx + 1 < len(sys.argv):
                hours = int(sys.argv[idx + 1])

        history = load_metrics_history(hours)
        trends = analyze_trends(history)
        print(json.dumps(trends, ensure_ascii=False, indent=2))

    elif cmd == "warnings":
        warnings = get_warnings(senses, tool_guard, heartbeats)
        print(json.dumps(warnings, ensure_ascii=False, indent=2))

    elif cmd == "export":
        output_format = "json"
        if "--format" in sys.argv:
            idx = sys.argv.index("--format")
            if idx + 1 < len(sys.argv):
                output_format = sys.argv[idx + 1]

        health = calculate_health_score(senses, tool_guard, heartbeats)
        warnings = get_warnings(senses, tool_guard, heartbeats)

        export_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health": health,
            "senses": senses,
            "tool_guard": tool_guard,
            "heartbeats": heartbeats,
            "warnings": warnings
        }

        if output_format == "json":
            print(json.dumps(export_data, ensure_ascii=False, indent=2))
        else:
            # 文本格式
            overview = format_overview(senses, tool_guard, heartbeats, health, warnings)
            print(overview)

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
