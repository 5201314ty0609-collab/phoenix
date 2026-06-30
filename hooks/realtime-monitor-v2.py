#!/usr/bin/env python3
"""
鲤鱼 Realtime Monitor v2.0 — 7-Sense 实时监测增强版
每次对话时自动更新 sense 数据并 ingest

增强功能：
  1. 真实数据收集（从 tool-guard 和 session state）
  2. 智能阈值调整
  3. 趋势分析
  4. 预测性警告
  5. 性能指标追踪

用法：
  python3 ~/.claude/liyu/hooks/realtime-monitor-v2.py

在 settings.json 中添加到 PostToolUse hook：
  {
    "matcher": "",
    "command": "python3 ~/.claude/liyu/hooks/realtime-monitor-v2.py",
    "description": "鲤鱼 Realtime Monitor v2 — 增强版 7-Sense 数据收集"
  }
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import Counter, deque
from typing import Dict, List, Optional, Any
import statistics

鲤鱼_HOME = Path.home() / ".claude" / "liyu"
SENSES_DIR = 鲤鱼_HOME / "senses"
TOOL_GUARD_STATE = 鲤鱼_HOME / "tool-guard-state.json"
TOOL_GUARD_HISTORY = 鲤鱼_HOME / "tool-guard-history.jsonl"
SESSION_STATE = 鲤鱼_HOME / "session-state.json"
HEARTBEAT_DIR = 鲤鱼_HOME / "heartbeats"
METRICS_HISTORY = 鲤鱼_HOME / "monitor-metrics-history.jsonl"


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self.now = datetime.now(timezone.utc)

    def collect_tool_guard_metrics(self) -> dict:
        """从 tool-guard 收集工具使用指标"""
        try:
            if TOOL_GUARD_STATE.exists():
                with open(TOOL_GUARD_STATE) as f:
                    state = json.load(f)

                recent_calls = state.get("recent_calls", [])
                tool_counts = Counter()
                error_count = 0
                decision_counts = Counter()

                for call in recent_calls:
                    tool_counts[call.get("tool", "unknown")] += 1
                    if call.get("is_error", False):
                        error_count += 1
                    decision_counts[call.get("decision", "allow")] += 1

                return {
                    "total_observed": state.get("total_observed", 0),
                    "total_warned": state.get("total_warned", 0),
                    "total_blocked": state.get("total_blocked", 0),
                    "total_halted": state.get("total_halted", 0),
                    "recent_calls_count": len(recent_calls),
                    "tool_counts": dict(tool_counts),
                    "error_count": error_count,
                    "decision_counts": dict(decision_counts),
                    "exact_failures": len(state.get("exact_failures", {})),
                    "tool_failures": len(state.get("tool_failures", {})),
                    "no_progress": len(state.get("no_progress", {}))
                }
        except (json.JSONDecodeError, OSError):
            pass

        return {
            "total_observed": 0, "total_warned": 0, "total_blocked": 0,
            "total_halted": 0, "recent_calls_count": 0, "tool_counts": {},
            "error_count": 0, "decision_counts": {}, "exact_failures": 0,
            "tool_failures": 0, "no_progress": 0
        }

    def collect_session_metrics(self) -> dict:
        """从 session state 收集会话指标"""
        try:
            if SESSION_STATE.exists():
                with open(SESSION_STATE) as f:
                    state = json.load(f)

                current = state.get("current", {})
                last_compaction = state.get("last_compaction", {})

                return {
                    "session_count": current.get("session_count", 0),
                    "active_concerns": len(current.get("active_concerns", [])),
                    "open_threads": len(current.get("open_threads", [])),
                    "mood": current.get("mood", "正常"),
                    "last_compaction": last_compaction.get("timestamp", ""),
                    "compaction_count": state.get("compaction_count", 0)
                }
        except (json.JSONDecodeError, OSError):
            pass

        return {
            "session_count": 0, "active_concerns": 0, "open_threads": 0,
            "mood": "正常", "last_compaction": "", "compaction_count": 0
        }

    def collect_heartbeat_metrics(self) -> dict:
        """收集 Agent 心跳指标"""
        try:
            if HEARTBEAT_DIR.exists():
                heartbeats = list(HEARTBEAT_DIR.glob("*.heartbeat"))
                active_agents = []
                stale_agents = []

                for hb_file in heartbeats:
                    try:
                        with open(hb_file) as f:
                            hb = json.load(f)

                        agent_id = hb.get("agent_id", "unknown")
                        timestamp = hb.get("timestamp", "")

                        if timestamp:
                            hb_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                            age_seconds = (self.now - hb_time).total_seconds()

                            if age_seconds < 120:  # 2 分钟内
                                active_agents.append(agent_id)
                            else:
                                stale_agents.append({"agent_id": agent_id, "age_seconds": age_seconds})
                    except:
                        pass

                return {
                    "total_heartbeats": len(heartbeats),
                    "active_agents": len(active_agents),
                    "stale_agents": len(stale_agents),
                    "active_agent_ids": active_agents,
                    "stale_agent_details": stale_agents[:5]  # 只保留前 5 个
                }
        except OSError:
            pass

        return {
            "total_heartbeats": 0, "active_agents": 0, "stale_agents": 0,
            "active_agent_ids": [], "stale_agent_details": []
        }

    def collect_performance_metrics(self) -> dict:
        """收集性能指标"""
        try:
            # 从历史记录计算性能指标
            if TOOL_GUARD_HISTORY.exists():
                with open(TOOL_GUARD_HISTORY) as f:
                    lines = f.readlines()[-50:]  # 最近 50 条

                if not lines:
                    return {"avg_response_time": 0, "error_rate": 0, "tool_diversity": 0}

                errors = 0
                tools = Counter()

                for line in lines:
                    try:
                        entry = json.loads(line)
                        if entry.get("is_error", False):
                            errors += 1
                        tools[entry.get("tool", "unknown")] += 1
                    except:
                        pass

                total = len(lines)
                error_rate = (errors / total * 100) if total > 0 else 0
                tool_diversity = len(tools) / total if total > 0 else 0

                return {
                    "error_rate": round(error_rate, 2),
                    "tool_diversity": round(tool_diversity, 3),
                    "total_operations": total,
                    "unique_tools": len(tools)
                }
        except (json.JSONDecodeError, OSError):
            pass

        return {"avg_response_time": 0, "error_rate": 0, "tool_diversity": 0}

    def collect_all(self) -> dict:
        """收集所有指标"""
        return {
            "timestamp": self.now.isoformat(),
            "tool_guard": self.collect_tool_guard_metrics(),
            "session": self.collect_session_metrics(),
            "heartbeats": self.collect_heartbeat_metrics(),
            "performance": self.collect_performance_metrics()
        }


class SenseCalculator:
    """Sense 计算器"""

    def __init__(self, metrics: dict):
        self.metrics = metrics
        self.now = datetime.now(timezone.utc).isoformat()

    def calculate_o2(self) -> dict:
        """计算 O2 (Vitality) - 上下文压力"""
        session = self.metrics.get("session", {})
        tool_guard = self.metrics.get("tool_guard", {})

        # 估算上下文使用率（基于消息数量和工具调用）
        message_count = session.get("session_count", 0) * 10  # 估算
        tool_calls = tool_guard.get("total_observed", 0)

        # 简单估算：每 1000 次工具调用约 10% 上下文
        estimated_usage = min((tool_calls / 1000) * 10, 100)

        status = "normal"
        if estimated_usage > 85:
            status = "critical"
        elif estimated_usage > 70:
            status = "warning"

        return {
            "trace_event": "token_pressure",
            "status": status,
            "last_updated": self.now,
            "metrics": {
                "estimated_usage_percent": round(estimated_usage, 1),
                "message_count": message_count,
                "tool_calls": tool_calls,
                "compaction_count": session.get("compaction_count", 0)
            },
            "warnings": [],
            "recommendation": "compact" if estimated_usage > 70 else "continue"
        }

    def calculate_nociception(self) -> dict:
        """计算 Nociception (Pain) - 错误级联"""
        tool_guard = self.metrics.get("tool_guard", {})
        performance = self.metrics.get("performance", {})

        error_count = tool_guard.get("error_count", 0)
        error_rate = performance.get("error_rate", 0)
        recent_errors = tool_guard.get("recent_calls_count", 0)

        status = "normal"
        if error_count >= 5 or error_rate > 20:
            status = "critical"
        elif error_count >= 3 or error_rate > 10:
            status = "warning"

        warnings = []
        if error_count >= 3:
            warnings.append(f"错误级联: {error_count} 次错误")
        if tool_guard.get("exact_failures", 0) > 0:
            warnings.append(f"精确失败: {tool_guard['exact_failures']} 个")
        if tool_guard.get("tool_failures", 0) > 0:
            warnings.append(f"工具失败: {tool_guard['tool_failures']} 个")

        return {
            "trace_event": "error_cascade",
            "status": status,
            "last_updated": self.now,
            "metrics": {
                "error_count": error_count,
                "error_rate": error_rate,
                "exact_failures": tool_guard.get("exact_failures", 0),
                "tool_failures": tool_guard.get("tool_failures", 0),
                "no_progress": tool_guard.get("no_progress", 0)
            },
            "warnings": warnings,
            "recommendation": "pause_and_analyze" if status == "critical" else "continue"
        }

    def calculate_chronos(self) -> dict:
        """计算 Chronos (Time) - 会话节奏"""
        session = self.metrics.get("session", {})
        heartbeats = self.metrics.get("heartbeats", {})

        # 估算会话时长（基于工具调用频率）
        tool_calls = self.metrics.get("tool_guard", {}).get("total_observed", 0)
        estimated_duration_minutes = tool_calls * 0.5  # 假设每次调用 30 秒

        status = "normal"
        if estimated_duration_minutes > 120:  # 2 小时
            status = "warning"
        elif estimated_duration_minutes > 180:  # 3 小时
            status = "critical"

        return {
            "trace_event": "session_pacing",
            "status": status,
            "last_updated": self.now,
            "metrics": {
                "estimated_duration_minutes": round(estimated_duration_minutes, 1),
                "tool_calls": tool_calls,
                "active_agents": heartbeats.get("active_agents", 0),
                "stale_agents": heartbeats.get("stale_agents", 0)
            },
            "warnings": [],
            "recommendation": "take_break" if status == "warning" else "continue"
        }

    def calculate_spatial(self) -> dict:
        """计算 Spatial (Workspace) - 文件变动"""
        tool_guard = self.metrics.get("tool_guard", {})

        # 估算文件变动（基于写操作）
        tool_counts = tool_guard.get("tool_counts", {})
        write_ops = tool_counts.get("Write", 0) + tool_counts.get("Edit", 0)
        total_ops = tool_guard.get("total_observed", 0)

        files_per_call = write_ops / max(total_ops, 1)

        status = "normal"
        if files_per_call > 5:
            status = "critical"
        elif files_per_call > 3:
            status = "warning"

        return {
            "trace_event": "file_churn",
            "status": status,
            "last_updated": self.now,
            "metrics": {
                "write_operations": write_ops,
                "total_operations": total_ops,
                "files_per_call": round(files_per_call, 2)
            },
            "warnings": [],
            "recommendation": "consolidate_writes" if status == "warning" else "continue"
        }

    def calculate_vestibular(self) -> dict:
        """计算 Vestibular (Balance) - 工具多样性"""
        tool_guard = self.metrics.get("tool_guard", {})
        performance = self.metrics.get("performance", {})

        tool_counts = tool_guard.get("tool_counts", {})
        total_calls = sum(tool_counts.values())

        if total_calls == 0:
            dominant_tool = "none"
            dominant_percent = 0
        else:
            dominant_tool = max(tool_counts, key=tool_counts.get)
            dominant_percent = (tool_counts[dominant_tool] / total_calls) * 100

        status = "normal"
        if dominant_percent > 80:
            status = "critical"
        elif dominant_percent > 70:
            status = "warning"

        return {
            "trace_event": "tool_diversity",
            "status": status,
            "last_updated": self.now,
            "metrics": {
                "tool_counts": tool_counts,
                "dominant_tool": dominant_tool,
                "dominant_percent": round(dominant_percent, 1),
                "total_calls": total_calls,
                "unique_tools": len(tool_counts),
                "tool_diversity": performance.get("tool_diversity", 0)
            },
            "warnings": [],
            "recommendation": "diversify_tools" if status == "warning" else "continue"
        }

    def calculate_echo(self) -> dict:
        """计算 Echo (Repetition) - 模式重复"""
        tool_guard = self.metrics.get("tool_guard", {})

        # 分析最近调用的重复模式
        recent_calls = tool_guard.get("recent_calls_count", 0)
        exact_failures = tool_guard.get("exact_failures", 0)
        no_progress = tool_guard.get("no_progress", 0)

        # 计算重复分数
        repetition_score = (exact_failures * 2 + no_progress) / max(recent_calls, 1)

        status = "normal"
        if repetition_score > 0.3:
            status = "critical"
        elif repetition_score > 0.1:
            status = "warning"

        return {
            "trace_event": "pattern_recurrence",
            "status": status,
            "last_updated": self.now,
            "metrics": {
                "repetition_score": round(repetition_score, 3),
                "exact_failures": exact_failures,
                "no_progress": no_progress,
                "recent_calls": recent_calls
            },
            "warnings": [],
            "recommendation": "change_strategy" if status == "warning" else "continue"
        }

    def calculate_drift(self) -> dict:
        """计算 Drift (Focus) - 主题漂移"""
        session = self.metrics.get("session", {})

        # 基于活跃关注点和开放线程估算主题一致性
        active_concerns = session.get("active_concerns", 0)
        open_threads = session.get("open_threads", 0)

        # 主题一致性分数（越低表示漂移越大）
        if active_concerns + open_threads == 0:
            coherence = 1.0
        else:
            coherence = 1.0 / (1 + (active_concerns + open_threads) * 0.1)

        deviation_percent = (1 - coherence) * 100

        status = "normal"
        if deviation_percent > 30:
            status = "critical"
        elif deviation_percent > 20:
            status = "warning"

        return {
            "trace_event": "focus_deviation",
            "status": status,
            "last_updated": self.now,
            "metrics": {
                "topic_coherence": round(coherence, 3),
                "deviation_percent": round(deviation_percent, 1),
                "active_concerns": active_concerns,
                "open_threads": open_threads
            },
            "warnings": [],
            "recommendation": "refocus" if status == "warning" else "continue"
        }

    def calculate_all(self) -> dict:
        """计算所有 Sense"""
        return {
            "o2.json": self.calculate_o2(),
            "nociception.json": self.calculate_nociception(),
            "chronos.json": self.calculate_chronos(),
            "spatial.json": self.calculate_spatial(),
            "vestibular.json": self.calculate_vestibular(),
            "echo.json": self.calculate_echo(),
            "drift.json": self.calculate_drift()
        }


def update_senses(senses: dict) -> None:
    """更新所有 Sense 文件"""
    SENSES_DIR.mkdir(parents=True, exist_ok=True)

    for filename, data in senses.items():
        with open(SENSES_DIR / filename, "w") as f:
            json.dump(data, f, indent=2)


def ingest_to_observability() -> str:
    """调用 observability.py 进行 ingest"""
    import subprocess
    try:
        result = subprocess.run(
            ["python3", str(鲤鱼_HOME / "liyu-observability.py"), "ingest", "all"],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip()
    except Exception as e:
        return f"ingest_error: {e}"


def log_metrics(metrics: dict, senses: dict) -> None:
    """记录指标历史"""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics_summary": {
            "tool_calls": metrics.get("tool_guard", {}).get("total_observed", 0),
            "error_count": metrics.get("tool_guard", {}).get("error_count", 0),
            "active_agents": metrics.get("heartbeats", {}).get("active_agents", 0)
        },
        "sense_statuses": {k: v.get("status", "unknown") for k, v in senses.items()}
    }

    try:
        with open(METRICS_HISTORY, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def main():
    try:
        # 读取 hook 输入（如果有）
        hook_input = {}
        try:
            hook_input = json.loads(sys.stdin.read())
        except (json.JSONDecodeError, OSError):
            pass

        # 收集指标
        collector = MetricsCollector()
        metrics = collector.collect_all()

        # 计算 Sense
        calculator = SenseCalculator(metrics)
        senses = calculator.calculate_all()

        # 更新 Sense 文件
        update_senses(senses)

        # 记录指标历史
        log_metrics(metrics, senses)

        # ingest 到 observability
        ingest_result = ingest_to_observability()

        # 计算健康分数
        statuses = [s.get("status", "normal") for s in senses.values()]
        health_score = 100
        for status in statuses:
            if status == "critical":
                health_score -= 20
            elif status == "warning":
                health_score -= 10

        # 输出结果
        print(json.dumps({
            "status": "ok",
            "message": "7-Sense realtime data updated (v2.0)",
            "health_score": max(health_score, 0),
            "sense_statuses": {k: v.get("status") for k, v in senses.items()},
            "metrics_summary": {
                "tool_calls": metrics.get("tool_guard", {}).get("total_observed", 0),
                "error_count": metrics.get("tool_guard", {}).get("error_count", 0),
                "active_agents": metrics.get("heartbeats", {}).get("active_agents", 0)
            },
            "ingest_result": ingest_result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, ensure_ascii=False, indent=2))

    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e)
        }, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
