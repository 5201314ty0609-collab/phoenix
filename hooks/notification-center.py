#!/usr/bin/env python3
"""
PHOENIX Notification Center — 用户通知系统
管理错误恢复建议、性能警告、进化状态更新等通知

功能：
  1. 通知队列管理
  2. 优先级排序
  3. 通知去重
  4. 历史记录
  5. 用户偏好设置

用法：
  notification-center.py add <type> <priority> <message> [--data <json>]
    添加通知

  notification-center.py list [--priority <level>] [--limit <n>]
    列出通知

  notification-center.py dismiss <notification_id>
    忽略通知

  notification-center.py clear [--type <type>]
    清除通知

  notification-center.py stats
    通知统计
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

PHOENIX_HOME = Path.home() / ".claude" / "phoenix"
NOTIFICATIONS_FILE = PHOENIX_HOME / "notifications.json"
NOTIFICATION_HISTORY = PHOENIX_HOME / "notification-history.jsonl"
PREFERENCES_FILE = PHOENIX_HOME / "notification-preferences.json"


class NotificationType(Enum):
    """通知类型"""
    ERROR_RECOVERY = "error_recovery"  # 错误恢复建议
    PERFORMANCE_WARNING = "performance_warning"  # 性能警告
    EVOLUTION_UPDATE = "evolution_update"  # 进化状态更新
    MEMORY_SYNC = "memory_sync"  # 记忆同步状态
    AGENT_COORDINATION = "agent_coordination"  # Agent 协调
    CONTEXT_PRESSURE = "context_pressure"  # 上下文压力
    SECURITY_ALERT = "security_alert"  # 安全警报
    SYSTEM_STATUS = "system_status"  # 系统状态


class NotificationPriority(Enum):
    """通知优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# 默认通知偏好
DEFAULT_PREFERENCES = {
    "enabled_types": [t.value for t in NotificationType],
    "min_priority": "low",
    "max_notifications": 50,
    "auto_dismiss_after_hours": 24,
    "sound_enabled": False,
    "desktop_enabled": False,
    "quiet_hours": {
        "enabled": False,
        "start": "22:00",
        "end": "08:00"
    }
}


def load_preferences() -> dict:
    """加载通知偏好"""
    if PREFERENCES_FILE.exists():
        try:
            with open(PREFERENCES_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_PREFERENCES.copy()


def save_preferences(prefs: dict) -> None:
    """保存通知偏好"""
    PHOENIX_HOME.mkdir(parents=True, exist_ok=True)
    PREFERENCES_FILE.write_text(json.dumps(prefs, ensure_ascii=False, indent=2))


def load_notifications() -> List[dict]:
    """加载通知列表"""
    if NOTIFICATIONS_FILE.exists():
        try:
            with open(NOTIFICATIONS_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return []


def save_notifications(notifications: List[dict]) -> None:
    """保存通知列表"""
    PHOENIX_HOME.mkdir(parents=True, exist_ok=True)

    # 限制数量
    prefs = load_preferences()
    max_notifications = prefs.get("max_notifications", 50)
    if len(notifications) > max_notifications:
        notifications = notifications[-max_notifications:]

    NOTIFICATIONS_FILE.write_text(json.dumps(notifications, ensure_ascii=False, indent=2))


def log_notification(notification: dict) -> None:
    """记录通知历史"""
    try:
        with open(NOTIFICATION_HISTORY, "a") as f:
            f.write(json.dumps(notification, ensure_ascii=False) + "\n")
    except OSError:
        pass


class NotificationCenter:
    """通知中心"""

    def __init__(self):
        self.notifications = load_notifications()
        self.preferences = load_preferences()

    def add(self, notification_type: str, priority: str, message: str,
            data: Optional[dict] = None) -> dict:
        """添加通知"""
        # 验证类型和优先级
        try:
            ntype = NotificationType(notification_type)
        except ValueError:
            return {"status": "error", "message": f"无效的通知类型: {notification_type}"}

        try:
            npriority = NotificationPriority(priority)
        except ValueError:
            return {"status": "error", "message": f"无效的优先级: {priority}"}

        # 检查是否启用该类型
        if notification_type not in self.preferences.get("enabled_types", []):
            return {"status": "skipped", "reason": f"通知类型 {notification_type} 已禁用"}

        # 检查优先级
        min_priority = self.preferences.get("min_priority", "low")
        priority_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        if priority_levels.get(priority, 0) < priority_levels.get(min_priority, 0):
            return {"status": "skipped", "reason": f"优先级 {priority} 低于最低要求 {min_priority}"}

        # 检查静默时间
        if self._is_quiet_time():
            if npriority != NotificationPriority.CRITICAL:
                return {"status": "skipped", "reason": "当前为静默时间"}

        # 检查重复
        if self._is_duplicate(message, notification_type):
            return {"status": "skipped", "reason": "重复通知"}

        # 创建通知
        notification = {
            "id": f"notif_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.notifications)}",
            "type": notification_type,
            "priority": priority,
            "message": message,
            "data": data or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "dismissed": False,
            "read": False
        }

        self.notifications.append(notification)
        save_notifications(self.notifications)
        log_notification(notification)

        return {"status": "added", "notification_id": notification["id"]}

    def list(self, priority: Optional[str] = None, limit: int = 20,
             include_dismissed: bool = False) -> List[dict]:
        """列出通知"""
        filtered = self.notifications

        # 过滤已忽略
        if not include_dismissed:
            filtered = [n for n in filtered if not n.get("dismissed", False)]

        # 过滤优先级
        if priority:
            priority_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
            min_level = priority_levels.get(priority, 0)
            filtered = [n for n in filtered if priority_levels.get(n.get("priority", "low"), 0) >= min_level]

        # 排序：优先级高的在前，时间新的在前
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        filtered.sort(key=lambda x: (priority_order.get(x.get("priority", "low"), 3), x.get("created_at", "")))

        return filtered[-limit:]

    def dismiss(self, notification_id: str) -> dict:
        """忽略通知"""
        for notification in self.notifications:
            if notification.get("id") == notification_id:
                notification["dismissed"] = True
                notification["dismissed_at"] = datetime.now(timezone.utc).isoformat()
                save_notifications(self.notifications)
                return {"status": "dismissed", "notification_id": notification_id}

        return {"status": "error", "message": f"通知 {notification_id} 不存在"}

    def mark_read(self, notification_id: str) -> dict:
        """标记为已读"""
        for notification in self.notifications:
            if notification.get("id") == notification_id:
                notification["read"] = True
                save_notifications(self.notifications)
                return {"status": "read", "notification_id": notification_id}

        return {"status": "error", "message": f"通知 {notification_id} 不存在"}

    def clear(self, notification_type: Optional[str] = None) -> dict:
        """清除通知"""
        if notification_type:
            self.notifications = [n for n in self.notifications
                                  if n.get("type") != notification_type]
        else:
            self.notifications = []

        save_notifications(self.notifications)
        return {"status": "cleared", "type": notification_type or "all"}

    def auto_dismiss(self) -> int:
        """自动忽略过期通知"""
        prefs = load_preferences()
        dismiss_hours = prefs.get("auto_dismiss_after_hours", 24)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=dismiss_hours)

        dismissed_count = 0
        for notification in self.notifications:
            if notification.get("dismissed", False):
                continue

            created_at = notification.get("created_at", "")
            if created_at:
                try:
                    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    if created < cutoff:
                        notification["dismissed"] = True
                        notification["dismissed_at"] = datetime.now(timezone.utc).isoformat()
                        dismissed_count += 1
                except:
                    pass

        if dismissed_count > 0:
            save_notifications(self.notifications)

        return dismissed_count

    def stats(self) -> dict:
        """通知统计"""
        total = len(self.notifications)
        active = len([n for n in self.notifications if not n.get("dismissed", False)])
        unread = len([n for n in self.notifications if not n.get("read", False)])

        by_type = {}
        by_priority = {}

        for notification in self.notifications:
            if notification.get("dismissed", False):
                continue

            ntype = notification.get("type", "unknown")
            priority = notification.get("priority", "low")

            by_type[ntype] = by_type.get(ntype, 0) + 1
            by_priority[priority] = by_priority.get(priority, 0) + 1

        return {
            "total": total,
            "active": active,
            "unread": unread,
            "by_type": by_type,
            "by_priority": by_priority
        }

    def _is_quiet_time(self) -> bool:
        """检查是否为静默时间"""
        prefs = load_preferences()
        quiet_hours = prefs.get("quiet_hours", {})

        if not quiet_hours.get("enabled", False):
            return False

        now = datetime.now().strftime("%H:%M")
        start = quiet_hours.get("start", "22:00")
        end = quiet_hours.get("end", "08:00")

        if start <= end:
            return start <= now <= end
        else:
            return now >= start or now <= end

    def _is_duplicate(self, message: str, notification_type: str) -> bool:
        """检查是否为重复通知"""
        # 检查最近 1 小时内的相同消息
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

        for notification in self.notifications:
            if notification.get("dismissed", False):
                continue

            if (notification.get("message") == message and
                    notification.get("type") == notification_type):

                created_at = notification.get("created_at", "")
                if created_at:
                    try:
                        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        if created > cutoff:
                            return True
                    except:
                        pass

        return False


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    center = NotificationCenter()

    if cmd == "add":
        if len(sys.argv) < 5:
            print("用法: notification-center.py add <type> <priority> <message> [--data <json>]")
            sys.exit(1)

        ntype = sys.argv[2]
        priority = sys.argv[3]
        message = sys.argv[4]

        data = None
        if "--data" in sys.argv:
            data_idx = sys.argv.index("--data")
            if data_idx + 1 < len(sys.argv):
                try:
                    data = json.loads(sys.argv[data_idx + 1])
                except json.JSONDecodeError:
                    data = {"raw": sys.argv[data_idx + 1]}

        result = center.add(ntype, priority, message, data)
        print(json.dumps(result, ensure_ascii=False))

    elif cmd == "list":
        priority = None
        limit = 20

        if "--priority" in sys.argv:
            idx = sys.argv.index("--priority")
            if idx + 1 < len(sys.argv):
                priority = sys.argv[idx + 1]

        if "--limit" in sys.argv:
            idx = sys.argv.index("--limit")
            if idx + 1 < len(sys.argv):
                limit = int(sys.argv[idx + 1])

        notifications = center.list(priority=priority, limit=limit)
        print(json.dumps(notifications, ensure_ascii=False, indent=2))

    elif cmd == "dismiss":
        if len(sys.argv) < 3:
            print("用法: notification-center.py dismiss <notification_id>")
            sys.exit(1)

        notification_id = sys.argv[2]
        result = center.dismiss(notification_id)
        print(json.dumps(result, ensure_ascii=False))

    elif cmd == "read":
        if len(sys.argv) < 3:
            print("用法: notification-center.py read <notification_id>")
            sys.exit(1)

        notification_id = sys.argv[2]
        result = center.mark_read(notification_id)
        print(json.dumps(result, ensure_ascii=False))

    elif cmd == "clear":
        ntype = None
        if "--type" in sys.argv:
            idx = sys.argv.index("--type")
            if idx + 1 < len(sys.argv):
                ntype = sys.argv[idx + 1]

        result = center.clear(ntype)
        print(json.dumps(result, ensure_ascii=False))

    elif cmd == "auto-dismiss":
        count = center.auto_dismiss()
        print(json.dumps({"status": "ok", "dismissed_count": count}))

    elif cmd == "stats":
        stats = center.stats()
        print("═══ PHOENIX Notification Center ───")
        print(f"  总通知数: {stats['total']}")
        print(f"  活跃通知: {stats['active']}")
        print(f"  未读通知: {stats['unread']}")
        print()
        if stats['by_priority']:
            print("  按优先级:")
            for priority, count in sorted(stats['by_priority'].items()):
                icon = "🔴" if priority == "critical" else "🟡" if priority == "high" else "🟢"
                print(f"    {icon} {priority}: {count}")
        print()
        if stats['by_type']:
            print("  按类型:")
            for ntype, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
                print(f"    {ntype}: {count}")

    elif cmd == "preferences":
        prefs = load_preferences()
        print(json.dumps(prefs, ensure_ascii=False, indent=2))

    elif cmd == "update-preferences":
        if len(sys.argv) < 3:
            print("用法: notification-center.py update-preferences <json>")
            sys.exit(1)

        try:
            updates = json.loads(sys.argv[2])
            prefs = load_preferences()
            prefs.update(updates)
            save_preferences(prefs)
            print(json.dumps({"status": "updated", "preferences": prefs}, ensure_ascii=False))
        except json.JSONDecodeError:
            print("错误: 无效的 JSON")
            sys.exit(1)

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
