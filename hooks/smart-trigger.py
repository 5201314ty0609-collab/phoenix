#!/usr/bin/env python3
"""
PHOENIX Smart Trigger Engine — 智能触发条件引擎
根据上下文、错误状态、时间间隔等因素智能决定是否触发钩子

功能：
  1. 条件匹配引擎
  2. 上下文压力检测
  3. 时间间隔触发
  4. 错误级联检测
  5. 工具使用模式分析

用法：
  smart-trigger.py evaluate <hook_name> <context_json>
    评估是否应该触发指定钩子

  smart-trigger.py conditions
    列出所有已配置的触发条件

  smart-trigger.py stats
    查看触发统计
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

PHOENIX_HOME = Path.home() / ".claude" / "phoenix"
CONFIG_FILE = PHOENIX_HOME / "smart-trigger-config.json"
STATE_FILE = PHOENIX_HOME / "smart-trigger-state.json"
HISTORY_FILE = PHOENIX_HOME / "smart-trigger-history.jsonl"


# 默认触发条件配置
DEFAULT_CONDITIONS = {
    "version": "1.0.0",
    "conditions": {
        "tool_error": {
            "description": "工具执行错误时触发",
            "trigger": "ToolError",
            "rules": [
                {
                    "name": "error_cascade",
                    "condition": "error_count >= 3",
                    "description": "错误级联：3 次以上错误",
                    "priority": "high"
                },
                {
                    "name": "permission_error",
                    "condition": "error_type == 'permission'",
                    "description": "权限错误",
                    "priority": "medium"
                },
                {
                    "name": "timeout_error",
                    "condition": "error_type == 'timeout'",
                    "description": "超时错误",
                    "priority": "medium"
                }
            ]
        },
        "context_pressure": {
            "description": "上下文压力触发",
            "trigger": "ContextCompaction",
            "rules": [
                {
                    "name": "high_usage",
                    "condition": "context_usage > 80",
                    "description": "上下文使用率超过 80%",
                    "priority": "high"
                },
                {
                    "name": "critical_usage",
                    "condition": "context_usage > 90",
                    "description": "上下文使用率超过 90%",
                    "priority": "critical"
                },
                {
                    "name": "message_overflow",
                    "condition": "message_count > 100",
                    "description": "消息数量超过 100",
                    "priority": "medium"
                }
            ]
        },
        "time_based": {
            "description": "基于时间的触发",
            "trigger": "varies",
            "rules": [
                {
                    "name": "idle_timeout",
                    "condition": "idle_seconds > 300",
                    "description": "空闲超过 5 分钟",
                    "priority": "low"
                },
                {
                    "name": "long_session",
                    "condition": "session_duration > 3600",
                    "description": "会话超过 1 小时",
                    "priority": "low"
                },
                {
                    "name": "heartbeat_stale",
                    "condition": "heartbeat_age > 120",
                    "description": "心跳超过 2 分钟未更新",
                    "priority": "high"
                }
            ]
        },
        "tool_patterns": {
            "description": "工具使用模式触发",
            "trigger": "PostToolUse",
            "rules": [
                {
                    "name": "repeated_calls",
                    "condition": "same_tool_count >= 5",
                    "description": "同一工具连续调用 5 次",
                    "priority": "medium"
                },
                {
                    "name": "no_progress",
                    "condition": "no_progress_count >= 3",
                    "description": "连续 3 次无进展",
                    "priority": "high"
                },
                {
                    "name": "tool_diversity_low",
                    "condition": "dominant_tool_percent > 80",
                    "description": "单一工具使用率超过 80%",
                    "priority": "medium"
                }
            ]
        },
        "agent_coordination": {
            "description": "Agent 协调触发",
            "trigger": "AgentSpawn/AgentComplete",
            "rules": [
                {
                    "name": "too_many_agents",
                    "condition": "active_agents > 5",
                    "description": "活跃 Agent 超过 5 个",
                    "priority": "high"
                },
                {
                    "name": "agent_timeout",
                    "condition": "agent_age > 7200",
                    "description": "Agent 运行超过 2 小时",
                    "priority": "high"
                }
            ]
        }
    },
    "global_settings": {
        "evaluation_interval": 10,
        "max_history_size": 1000,
        "enable_debug": False,
        "cooldown_seconds": 30
    }
}


def load_config() -> dict:
    """加载配置"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_CONDITIONS.copy()


def load_state() -> dict:
    """加载状态"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "last_evaluation": {},
        "trigger_counts": {},
        "cooldowns": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }


def save_state(state: dict) -> None:
    """保存状态"""
    PHOENIX_HOME.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def evaluate_condition(condition: str, context: dict) -> bool:
    """评估条件表达式"""
    try:
        # 安全的条件评估
        # 替换变量
        expr = condition
        for key, value in context.items():
            if isinstance(value, str):
                expr = expr.replace(f"{key}", f"'{value}'")
            else:
                expr = expr.replace(f"{key}", str(value))

        # 评估表达式
        return bool(eval(expr))
    except Exception as e:
        if load_config().get("global_settings", {}).get("enable_debug", False):
            print(f"条件评估错误: {condition} -> {e}", file=sys.stderr)
        return False


def check_cooldown(rule_name: str, state: dict, cooldown_seconds: int) -> bool:
    """检查冷却时间"""
    cooldowns = state.get("cooldowns", {})
    last_triggered = cooldowns.get(rule_name)

    if not last_triggered:
        return True

    try:
        last_time = datetime.fromisoformat(last_triggered)
        now = datetime.now(timezone.utc)
        elapsed = (now - last_time).total_seconds()
        return elapsed >= cooldown_seconds
    except:
        return True


def update_cooldown(rule_name: str, state: dict) -> None:
    """更新冷却时间"""
    if "cooldowns" not in state:
        state["cooldowns"] = {}
    state["cooldowns"][rule_name] = datetime.now(timezone.utc).isoformat()


def log_trigger(rule_name: str, hook_name: str, context: dict, triggered: bool) -> None:
    """记录触发历史"""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rule": rule_name,
        "hook": hook_name,
        "triggered": triggered,
        "context_summary": {k: v for k, v in context.items() if k != "full_input"}
    }

    try:
        with open(HISTORY_FILE, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


class SmartTrigger:
    """智能触发引擎"""

    def __init__(self):
        self.config = load_config()
        self.state = load_state()

    def evaluate(self, hook_name: str, context: dict) -> dict:
        """评估是否应该触发指定钩子"""
        conditions = self.config.get("conditions", {})
        global_settings = self.config.get("global_settings", {})
        cooldown_seconds = global_settings.get("cooldown_seconds", 30)

        results = []
        should_trigger = False
        max_priority = "low"
        priority_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}

        # 遍历所有条件组
        for group_name, group in conditions.items():
            trigger_hooks = group.get("trigger", "").split("/")

            # 检查是否匹配当前钩子
            if hook_name not in trigger_hooks and "varies" not in trigger_hooks:
                continue

            # 评估每个规则
            for rule in group.get("rules", []):
                rule_name = f"{group_name}.{rule['name']}"
                condition = rule["condition"]
                priority = rule.get("priority", "low")

                # 检查冷却
                if not check_cooldown(rule_name, self.state, cooldown_seconds):
                    results.append({
                        "rule": rule_name,
                        "condition": condition,
                        "result": False,
                        "reason": "冷却中"
                    })
                    continue

                # 评估条件
                condition_result = evaluate_condition(condition, context)

                results.append({
                    "rule": rule_name,
                    "condition": condition,
                    "result": condition_result,
                    "priority": priority,
                    "description": rule.get("description", "")
                })

                if condition_result:
                    should_trigger = True
                    update_cooldown(rule_name, self.state)

                    # 更新最高优先级
                    if priority_levels.get(priority, 0) > priority_levels.get(max_priority, 0):
                        max_priority = priority

        # 更新状态
        self.state["last_evaluation"][hook_name] = datetime.now(timezone.utc).isoformat()
        if should_trigger:
            trigger_count = self.state.get("trigger_counts", {}).get(hook_name, 0)
            if "trigger_counts" not in self.state:
                self.state["trigger_counts"] = {}
            self.state["trigger_counts"][hook_name] = trigger_count + 1

        save_state(self.state)

        # 记录历史
        log_trigger(hook_name, hook_name, context, should_trigger)

        return {
            "should_trigger": should_trigger,
            "hook_name": hook_name,
            "max_priority": max_priority,
            "triggered_rules": [r for r in results if r.get("result")],
            "evaluated_rules": results,
            "evaluation_time": datetime.now(timezone.utc).isoformat()
        }

    def get_conditions(self) -> dict:
        """获取所有条件配置"""
        return self.config.get("conditions", {})

    def get_stats(self) -> dict:
        """获取触发统计"""
        return {
            "total_evaluations": sum(self.state.get("trigger_counts", {}).values()),
            "trigger_counts": self.state.get("trigger_counts", {}),
            "last_evaluations": self.state.get("last_evaluation", {}),
            "active_cooldowns": len(self.state.get("cooldowns", {}))
        }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    trigger = SmartTrigger()

    if cmd == "evaluate":
        if len(sys.argv) < 4:
            print("用法: smart-trigger.py evaluate <hook_name> <context_json>")
            sys.exit(1)

        hook_name = sys.argv[2]
        try:
            context = json.loads(sys.argv[3])
        except json.JSONDecodeError:
            context = {"raw": sys.argv[3]}

        result = trigger.evaluate(hook_name, context)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif cmd == "conditions":
        conditions = trigger.get_conditions()
        print(json.dumps(conditions, ensure_ascii=False, indent=2))

    elif cmd == "stats":
        stats = trigger.get_stats()
        print("═══ PHOENIX Smart Trigger ───")
        print(f"  总评估次数: {stats['total_evaluations']}")
        print(f"  活跃冷却: {stats['active_cooldowns']}")
        print()
        if stats["trigger_counts"]:
            print("  触发统计:")
            for hook, count in sorted(stats["trigger_counts"].items(), key=lambda x: -x[1]):
                print(f"    {hook}: {count} 次")
        print()
        if stats["last_evaluations"]:
            print("  最近评估:")
            for hook, time in sorted(stats["last_evaluations"].items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"    {hook}: {time[:19]}")

    elif cmd == "reset":
        STATE_FILE.unlink(missing_ok=True)
        print("✅ 状态已重置")

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
