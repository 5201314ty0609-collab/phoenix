#!/usr/bin/env python3
"""
鲤鱼 Rule Manager — 规则生命周期管理工具

管理规则的创建、更新、废弃和删除。

Usage:
  python3 rule_manager.py create <rule-id> <category>  创建新规则
  python3 rule_manager.py update <rule-id>              更新规则
  python3 rule_manager.py deprecate <rule-id>           废弃规则
  python3 rule_manager.py delete <rule-id>              删除规则
  python3 rule_manager.py list                          列出所有规则
  python3 rule_manager.py stats                         统计信息
  python3 rule_manager.py promote <rule-id> <stage>     提升规则阶段
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import json
import re
import sys

# ── 路径配置 ─────────────────────────────────────────────────────────────

鲤鱼_HOME = Path.home() / ".claude" / "liyu"
RULES_DIR = Path.home() / ".claude" / "rules"
鲤鱼_RULES_DIR = RULES_DIR / "liyu"
ENGINE_DIR = 鲤鱼_HOME / "rules-engine"
RULE_REGISTRY = ENGINE_DIR / "rule-registry.json"
MANAGER_LOG = ENGINE_DIR / "manager-log.jsonl"

# ── 数据类 ───────────────────────────────────────────────────────────────

@dataclass
class RuleInfo:
    """规则信息"""
    rule_id: str
    name: str
    file_path: str
    category: str
    stage: str
    priority: int
    layer: str
    version: str
    created_at: str
    updated_at: str
    status: str  # active, deprecated, deleted
    usage_count: int = 0
    success_rate: float = 0.0


# ── 规则管理器 ───────────────────────────────────────────────────────────

class RuleManager:
    """规则管理器"""

    def __init__(self):
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict:
        """加载规则注册表"""
        if RULE_REGISTRY.exists():
            try:
                return json.loads(RULE_REGISTRY.read_text())
            except Exception:
                pass
        return {'rules': []}

    def _save_registry(self):
        """保存规则注册表"""
        ENGINE_DIR.mkdir(parents=True, exist_ok=True)
        RULE_REGISTRY.write_text(json.dumps(self.registry, indent=2, ensure_ascii=False))

    def _log_action(self, action: str, rule_id: str, details: Dict = None):
        """记录操作日志"""
        ENGINE_DIR.mkdir(parents=True, exist_ok=True)
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'action': action,
            'rule_id': rule_id,
            'details': details or {},
        }
        with open(MANAGER_LOG, 'a') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def create_rule(
        self,
        rule_id: str,
        category: str,
        name: str = "",
        layer: str = "liyu",
        languages: List[str] = None,
        priority: int = 5,
    ) -> bool:
        """创建新规则"""
        # 检查是否已存在
        if self.get_rule(rule_id):
            print(f"Rule already exists: {rule_id}")
            return False

        # 确定文件路径
        if layer == "liyu":
            file_path = 鲤鱼_RULES_DIR / f"{rule_id}.md"
        elif layer == "common":
            file_path = RULES_DIR / "common" / f"{rule_id}.md"
        else:
            file_path = 鲤鱼_RULES_DIR / f"{rule_id}.md"

        # 检查文件是否已存在
        if file_path.exists():
            print(f"File already exists: {file_path}")
            return False

        # 生成规则内容
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        content = self._generate_rule_template(
            rule_id=rule_id,
            name=name or rule_id.replace('-', ' ').title(),
            category=category,
            layer=layer,
            languages=languages or ['all'],
            priority=priority,
            created=today,
        )

        # 创建文件
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        # 更新注册表
        rule_info = {
            'rule_id': rule_id,
            'name': name or rule_id.replace('-', ' ').title(),
            'file_path': str(file_path),
            'category': category,
            'stage': 'draft',
            'priority': priority,
            'layer': layer,
            'version': '1.0.0',
            'created_at': today,
            'updated_at': today,
            'status': 'active',
            'usage_count': 0,
            'success_rate': 0.0,
        }
        self.registry['rules'].append(rule_info)
        self._save_registry()

        # 记录日志
        self._log_action('create', rule_id, rule_info)

        print(f"✓ Created rule: {rule_id}")
        print(f"  File: {file_path}")
        print(f"  Category: {category}")
        print(f"  Layer: {layer}")
        print(f"  Priority: {priority}")

        return True

    def update_rule(self, rule_id: str, **kwargs) -> bool:
        """更新规则"""
        rule = self.get_rule(rule_id)
        if not rule:
            print(f"Rule not found: {rule_id}")
            return False

        # 更新字段
        for key, value in kwargs.items():
            if key in rule:
                rule[key] = value

        rule['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        # 保存注册表
        self._save_registry()

        # 记录日志
        self._log_action('update', rule_id, kwargs)

        print(f"✓ Updated rule: {rule_id}")
        for key, value in kwargs.items():
            print(f"  {key}: {value}")

        return True

    def deprecate_rule(self, rule_id: str, reason: str = "") -> bool:
        """废弃规则"""
        rule = self.get_rule(rule_id)
        if not rule:
            print(f"Rule not found: {rule_id}")
            return False

        rule['status'] = 'deprecated'
        rule['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        # 保存注册表
        self._save_registry()

        # 记录日志
        self._log_action('deprecate', rule_id, {'reason': reason})

        print(f"✓ Deprecated rule: {rule_id}")
        if reason:
            print(f"  Reason: {reason}")

        return True

    def delete_rule(self, rule_id: str, force: bool = False) -> bool:
        """删除规则"""
        rule = self.get_rule(rule_id)
        if not rule:
            print(f"Rule not found: {rule_id}")
            return False

        # 检查是否可以删除
        if not force:
            if rule.get('usage_count', 0) > 0:
                print(f"Rule {rule_id} has been used {rule['usage_count']} times")
                print("Use --force to delete anyway")
                return False

            if rule.get('stage') in ['validated', 'hardened']:
                print(f"Rule {rule_id} is in '{rule['stage']}' stage")
                print("Use --force to delete anyway")
                return False

        # 删除文件
        file_path = Path(rule.get('file_path', ''))
        if file_path.exists():
            file_path.unlink()

        # 从注册表中移除
        self.registry['rules'] = [
            r for r in self.registry['rules']
            if r.get('rule_id') != rule_id
        ]
        self._save_registry()

        # 记录日志
        self._log_action('delete', rule_id, {'force': force})

        print(f"✓ Deleted rule: {rule_id}")

        return True

    def get_rule(self, rule_id: str) -> Optional[Dict]:
        """获取规则信息"""
        for rule in self.registry.get('rules', []):
            if rule.get('rule_id') == rule_id:
                return rule
        return None

    def list_rules(
        self,
        category: str = "",
        layer: str = "",
        stage: str = "",
        status: str = "active",
    ) -> List[Dict]:
        """列出规则"""
        rules = self.registry.get('rules', [])

        # 过滤
        if category:
            rules = [r for r in rules if r.get('category') == category]
        if layer:
            rules = [r for r in rules if r.get('layer') == layer]
        if stage:
            rules = [r for r in rules if r.get('stage') == stage]
        if status:
            rules = [r for r in rules if r.get('status') == status]

        return rules

    def get_stats(self) -> Dict:
        """获取统计信息"""
        rules = self.registry.get('rules', [])

        stats = {
            'total': len(rules),
            'by_status': {},
            'by_category': {},
            'by_layer': {},
            'by_stage': {},
            'total_usage': 0,
            'avg_priority': 0,
        }

        for rule in rules:
            # 按状态统计
            status = rule.get('status', 'unknown')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1

            # 按分类统计
            category = rule.get('category', 'unknown')
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1

            # 按层级统计
            layer = rule.get('layer', 'unknown')
            stats['by_layer'][layer] = stats['by_layer'].get(layer, 0) + 1

            # 按阶段统计
            stage = rule.get('stage', 'unknown')
            stats['by_stage'][stage] = stats['by_stage'].get(stage, 0) + 1

            # 使用统计
            stats['total_usage'] += rule.get('usage_count', 0)

        # 计算平均优先级
        priorities = [r.get('priority', 5) for r in rules]
        stats['avg_priority'] = sum(priorities) / len(priorities) if priorities else 0

        return stats

    def promote_rule(self, rule_id: str, new_stage: str) -> bool:
        """提升规则阶段"""
        rule = self.get_rule(rule_id)
        if not rule:
            print(f"Rule not found: {rule_id}")
            return False

        # 验证阶段转换
        valid_transitions = {
            'draft': ['active'],
            'active': ['observed'],
            'observed': ['validated'],
            'validated': ['hardened'],
            'hardened': [],
        }

        current_stage = rule.get('stage', 'draft')
        if new_stage not in valid_transitions.get(current_stage, []):
            print(f"Invalid transition: {current_stage} → {new_stage}")
            print(f"Valid transitions: {valid_transitions.get(current_stage, [])}")
            return False

        rule['stage'] = new_stage
        rule['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        # 保存注册表
        self._save_registry()

        # 记录日志
        self._log_action('promote', rule_id, {
            'from': current_stage,
            'to': new_stage,
        })

        print(f"✓ Promoted rule: {rule_id}")
        print(f"  {current_stage} → {new_stage}")

        return True

    def _generate_rule_template(
        self,
        rule_id: str,
        name: str,
        category: str,
        layer: str,
        languages: List[str],
        priority: int,
        created: str,
    ) -> str:
        """生成规则模板"""
        return f"""# {name} (鲤鱼 Rule)

> Auto-generated rule from 鲤鱼 Evolution Engine
> Stage: draft | Enforcement: rule file (Level 4)
> Version: 1.0.0
> Created: {created}
> Updated: {created}

## Metadata

- **Rule ID**: {rule_id}
- **Category**: {category}
- **Priority**: {priority}
- **Layer**: {layer}
- **Languages**: {', '.join(languages)}

## Trigger

When [specific condition or context].

## Action

[Detailed rule content]

## Examples

```code
// Good example
const good = ...;

// Bad example
const bad = ...;
```

## Rationale

[Why this rule exists]

## Domains

{category}

## Evolution History

- Created: {created} from 鲤鱼 Evolution Engine
"""


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    manager = RuleManager()
    cmd = sys.argv[1]

    if cmd == "create":
        if len(sys.argv) < 4:
            print("Usage: python3 rule_manager.py create <rule-id> <category>")
            return
        rule_id = sys.argv[2]
        category = sys.argv[3]
        name = sys.argv[4] if len(sys.argv) > 4 else ""
        layer = sys.argv[5] if len(sys.argv) > 5 else "liyu"
        priority = int(sys.argv[6]) if len(sys.argv) > 6 else 5
        manager.create_rule(rule_id, category, name, layer, priority=priority)

    elif cmd == "update":
        if len(sys.argv) < 3:
            print("Usage: python3 rule_manager.py update <rule-id> [key=value...]")
            return
        rule_id = sys.argv[2]
        updates = {}
        for arg in sys.argv[3:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                updates[key] = value
        manager.update_rule(rule_id, **updates)

    elif cmd == "deprecate":
        if len(sys.argv) < 3:
            print("Usage: python3 rule_manager.py deprecate <rule-id> [reason]")
            return
        rule_id = sys.argv[2]
        reason = sys.argv[3] if len(sys.argv) > 3 else ""
        manager.deprecate_rule(rule_id, reason)

    elif cmd == "delete":
        if len(sys.argv) < 3:
            print("Usage: python3 rule_manager.py delete <rule-id> [--force]")
            return
        rule_id = sys.argv[2]
        force = '--force' in sys.argv
        manager.delete_rule(rule_id, force)

    elif cmd == "list":
        category = sys.argv[2] if len(sys.argv) > 2 else ""
        layer = sys.argv[3] if len(sys.argv) > 3 else ""
        stage = sys.argv[4] if len(sys.argv) > 4 else ""
        rules = manager.list_rules(category, layer, stage)
        print(f"Found {len(rules)} rules:")
        for rule in rules:
            print(f"  - {rule.get('rule_id')}: {rule.get('name')} [{rule.get('stage')}]")

    elif cmd == "stats":
        stats = manager.get_stats()
        print("=" * 72)
        print("  鲤鱼 Rule Manager Statistics")
        print("=" * 72)
        print()
        print(f"Total rules: {stats['total']}")
        print(f"Total usage: {stats['total_usage']}")
        print(f"Average priority: {stats['avg_priority']:.1f}")
        print()
        print("── By Status ──")
        for status, count in stats['by_status'].items():
            print(f"  {status:20s}: {count}")
        print()
        print("── By Category ──")
        for category, count in stats['by_category'].items():
            print(f"  {category:20s}: {count}")
        print()
        print("── By Layer ──")
        for layer, count in stats['by_layer'].items():
            print(f"  {layer:20s}: {count}")
        print()
        print("── By Stage ──")
        for stage, count in stats['by_stage'].items():
            print(f"  {stage:20s}: {count}")

    elif cmd == "promote":
        if len(sys.argv) < 4:
            print("Usage: python3 rule_manager.py promote <rule-id> <stage>")
            return
        rule_id = sys.argv[2]
        new_stage = sys.argv[3]
        manager.promote_rule(rule_id, new_stage)

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
