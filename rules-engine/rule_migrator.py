#!/usr/bin/env python3
"""
鲤鱼 Rule Migrator — 规则格式迁移工具

将现有规则文件迁移到新格式，添加元数据。

Usage:
  python3 rule_migrator.py scan                    扫描需要迁移的规则
  python3 rule_migrator.py migrate <rule-id>       迁移单个规则
  python3 rule_migrator.py migrate-all             迁移所有规则
  python3 rule_migrator.py validate <rule-id>      验证迁移结果
"""

from dataclasses import dataclass
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
MIGRATION_LOG = 鲤鱼_HOME / "rules-engine" / "migration-log.jsonl"

# ── 数据类 ───────────────────────────────────────────────────────────────

@dataclass
class MigrationResult:
    """迁移结果"""
    rule_id: str
    file_path: str
    success: bool
    changes: List[str]
    errors: List[str]


# ── 规则分析器 ───────────────────────────────────────────────────────────

class RuleAnalyzer:
    """规则分析器"""

    @staticmethod
    def analyze_rule(file_path: Path) -> Dict:
        """分析规则文件，提取现有元数据"""
        if not file_path.exists():
            return {}

        content = file_path.read_text(encoding="utf-8")
        rule_id = file_path.stem

        # 提取现有元数据
        metadata = {
            'rule_id': rule_id,
            'file_path': str(file_path),
            'has_metadata_section': '## Metadata' in content,
            'has_version': 'Version:' in content,
            'has_created': 'Created:' in content,
            'has_updated': 'Updated:' in content,
            'has_dependencies': '## Dependencies' in content,
            'has_conflicts': '## Conflicts' in content or 'Conflicts With' in content,
            'has_supersedes': '## Supersedes' in content or 'Supersedes:' in content,
            'has_languages': '## Languages' in content or 'Languages:' in content,
            'has_priority': '## Priority' in content or 'Priority:' in content,
            'has_category': '## Category' in content or 'Category:' in content,
            'has_layer': '## Layer' in content or 'Layer:' in content,
        }

        # 提取标题
        title_match = re.search(r'^#\s+(.+?)(?:\s*—|\s*\(|$)', content, re.MULTILINE)
        metadata['title'] = title_match.group(1).strip() if title_match else rule_id

        # 提取 stage
        stage_match = re.search(r'Stage:\s*(\w+)', content)
        metadata['stage'] = stage_match.group(1) if stage_match else 'active'

        # 提取 enforcement
        enforcement_match = re.search(r'Enforcement:.*Level\s*(\d)', content)
        metadata['enforcement_level'] = int(enforcement_match.group(1)) if enforcement_match else 4

        # 提取 domains
        domains_match = re.search(r'## Domains\s*\n(.+?)(?:\n##|\Z)', content, re.DOTALL)
        if domains_match:
            domains_text = domains_match.group(1).strip()
            metadata['domains'] = [d.strip() for d in domains_text.split(',') if d.strip()]
        else:
            metadata['domains'] = []

        # 提取触发条件
        trigger_match = re.search(r'## Trigger\s*\n(.+?)(?:\n##|\Z)', content, re.DOTALL)
        if trigger_match:
            trigger_text = trigger_match.group(1).strip()
            metadata['triggers'] = re.findall(r'[A-Z][a-z]+(?:\s+[a-z]+)+', trigger_text)[:5]
        else:
            metadata['triggers'] = []

        return metadata

    @staticmethod
    def determine_category(metadata: Dict) -> str:
        """确定规则分类"""
        domains = metadata.get('domains', [])
        title = metadata.get('title', '').lower()
        file_path = metadata.get('file_path', '').lower()

        domain_str = ' '.join(domains).lower()
        combined = f"{domain_str} {title} {file_path}"

        if 'security' in combined or 'safety' in combined or 'guard' in combined:
            return 'security'
        elif 'testing' in combined or 'test' in combined or 'tdd' in combined or 'mutation' in combined or 'e2e' in combined:
            return 'testing'
        elif 'performance' in combined or 'optimization' in combined:
            return 'performance'
        elif 'coding' in combined or 'style' in combined or 'immutability' in combined:
            return 'coding-style'
        elif 'pattern' in combined:
            return 'patterns'
        elif 'hook' in combined:
            return 'hooks'
        elif 'design' in combined or 'ui' in combined or 'ux' in combined:
            return 'design'
        elif 'memory' in combined or 'evolution' in combined or 'knowledge' in combined or 'hybrid' in combined:
            return 'evolution'
        elif 'observability' in combined or 'tracing' in combined or 'monitoring' in combined:
            return 'observability'
        elif 'planning' in combined or 'task' in combined:
            return 'planning'
        elif 'diary' in combined or 'reflection' in combined:
            return 'evolution'
        elif 'agent' in combined or 'multi-agent' in combined or 'coordination' in combined:
            return 'agents'
        elif 'git' in combined or 'commit' in combined or 'workflow' in combined:
            return 'git-workflow'
        elif 'refactor' in combined or 'review' in combined:
            return 'code-review'
        else:
            return 'general'

    @staticmethod
    def determine_layer(file_path: Path) -> str:
        """确定规则层级"""
        parts = file_path.parts
        if "liyu" in parts:
            return "liyu"
        elif "common" in parts:
            return "common"
        elif "zh" in parts:
            return "translation"
        else:
            return "language-specific"

    @staticmethod
    def determine_priority(metadata: Dict) -> int:
        """确定规则优先级"""
        stage = metadata.get('stage', 'active')
        enforcement = metadata.get('enforcement_level', 4)
        layer = metadata.get('layer', 'common')

        base = 5

        # Stage 加成
        stage_bonus = {
            'hardened': 4,
            'validated': 3,
            'observed': 2,
            'active': 1,
            'draft': 0,
        }
        base += stage_bonus.get(stage, 0)

        # Enforcement 加成
        if enforcement >= 6:
            base += 2
        elif enforcement >= 4:
            base += 1

        # Layer 加成
        if layer == 'liyu':
            base += 1

        return min(10, max(1, base))

    @staticmethod
    def determine_languages(metadata: Dict) -> List[str]:
        """确定适用语言"""
        file_path = metadata.get('file_path', '')
        parts = Path(file_path).parts

        # 从目录名推断语言
        language_dirs = {
            'typescript': ['typescript', 'ts'],
            'python': ['python', 'py'],
            'go': ['golang', 'go'],
            'rust': ['rust', 'rs'],
            'swift': ['swift'],
            'php': ['php'],
            'perl': ['perl'],
            'cpp': ['cpp', 'c++'],
            'csharp': ['csharp', 'c#'],
            'kotlin': ['kotlin'],
        }

        for lang, aliases in language_dirs.items():
            for part in parts:
                if part.lower() in aliases:
                    return [lang]

        return ['all']


# ── 规则迁移器 ───────────────────────────────────────────────────────────

class RuleMigrator:
    """规则迁移器"""

    def __init__(self):
        self.analyzer = RuleAnalyzer()

    def scan_rules(self) -> List[Dict]:
        """扫描需要迁移的规则"""
        rules_to_migrate = []

        for rules_dir in [RULES_DIR]:
            if not rules_dir.exists():
                continue

            for rule_file in rules_dir.rglob("*.md"):
                if rule_file.name == "README.md":
                    continue

                metadata = self.analyzer.analyze_rule(rule_file)

                # 检查是否需要迁移（只检查关键字段：Metadata 段是否存在）
                needs_migration = not metadata.get('has_metadata_section')

                if needs_migration:
                    metadata['needs_migration'] = True
                    rules_to_migrate.append(metadata)

        return rules_to_migrate

    def migrate_rule(self, rule_id: str) -> MigrationResult:
        """迁移单个规则"""
        # 查找规则文件
        rule_file = None
        for rules_dir in [RULES_DIR]:
            for f in rules_dir.rglob(f"{rule_id}.md"):
                rule_file = f
                break
            if rule_file:
                break

        if not rule_file:
            return MigrationResult(
                rule_id=rule_id,
                file_path="",
                success=False,
                changes=[],
                errors=[f"Rule file not found: {rule_id}"],
            )

        return self._migrate_file(rule_file)

    def migrate_all(self) -> List[MigrationResult]:
        """迁移所有规则"""
        results = []
        rules_to_migrate = self.scan_rules()

        print(f"Found {len(rules_to_migrate)} rules to migrate")
        print()

        for metadata in rules_to_migrate:
            rule_file = Path(metadata['file_path'])
            result = self._migrate_file(rule_file)
            results.append(result)

            # 打印结果
            status = "✓" if result.success else "✗"
            print(f"{status} {result.rule_id}")
            if result.changes:
                for change in result.changes:
                    print(f"    + {change}")
            if result.errors:
                for error in result.errors:
                    print(f"    ! {error}")

        # 保存迁移日志
        self._save_migration_log(results)

        # 打印摘要
        success_count = sum(1 for r in results if r.success)
        print(f"\nMigration complete: {success_count}/{len(results)} successful")

        return results

    def _migrate_file(self, file_path: Path) -> MigrationResult:
        """迁移单个文件"""
        rule_id = file_path.stem
        content = file_path.read_text(encoding="utf-8")
        changes = []
        errors = []

        try:
            # 分析现有元数据
            metadata = self.analyzer.analyze_rule(file_path)

            # 确定新元数据
            category = self.analyzer.determine_category(metadata)
            layer = self.analyzer.determine_layer(file_path)
            priority = self.analyzer.determine_priority(metadata)
            languages = self.analyzer.determine_languages(metadata)
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

            # 构建元数据部分
            metadata_section = self._build_metadata_section(
                rule_id=rule_id,
                category=category,
                priority=priority,
                layer=layer,
                languages=languages,
                created=metadata.get('created', today),
                updated=today,
            )

            # 检查是否已有元数据部分
            if '## Metadata' in content:
                # 替换现有元数据部分
                new_content = re.sub(
                    r'## Metadata.*?(?=\n##|\Z)',
                    metadata_section,
                    content,
                    flags=re.DOTALL,
                )
                changes.append("Updated metadata section")
            else:
                # 在标题后插入元数据部分
                # 找到第一个 ## 标题
                first_h2 = re.search(r'\n## ', content)
                if first_h2:
                    insert_pos = first_h2.start()
                    new_content = content[:insert_pos] + '\n' + metadata_section + '\n' + content[insert_pos:]
                else:
                    # 没有 ## 标题，添加到末尾
                    new_content = content + '\n\n' + metadata_section

                changes.append("Added metadata section")

            # 确保有 Version
            if 'Version:' not in new_content:
                # 在 Stage 行后添加 Version
                new_content = re.sub(
                    r'(> Stage:.*?\n)',
                    r'\1> Version: 1.0.0\n',
                    new_content,
                )
                changes.append("Added version")

            # 确保有 Created/Updated
            if 'Created:' not in new_content:
                new_content = re.sub(
                    r'(> Version:.*?\n)',
                    r'\1> Created: ' + today + '\n> Updated: ' + today + '\n',
                    new_content,
                )
                changes.append("Added created/updated dates")

            # 写入文件
            file_path.write_text(new_content, encoding="utf-8")

            return MigrationResult(
                rule_id=rule_id,
                file_path=str(file_path),
                success=True,
                changes=changes,
                errors=errors,
            )

        except Exception as e:
            errors.append(str(e))
            return MigrationResult(
                rule_id=rule_id,
                file_path=str(file_path),
                success=False,
                changes=changes,
                errors=errors,
            )

    def _build_metadata_section(
        self,
        rule_id: str,
        category: str,
        priority: int,
        layer: str,
        languages: List[str],
        created: str,
        updated: str,
    ) -> str:
        """构建元数据部分"""
        return f"""## Metadata

- **Rule ID**: {rule_id}
- **Category**: {category}
- **Priority**: {priority}
- **Layer**: {layer}
- **Languages**: {', '.join(languages)}
- **Version**: 1.0.0
- **Created**: {created}
- **Updated**: {updated}"""

    def _save_migration_log(self, results: List[MigrationResult]):
        """保存迁移日志"""
        MIGRATION_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(MIGRATION_LOG, 'a') as f:
            for result in results:
                entry = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    **vars(result),
                }
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')


# ── 验证器 ───────────────────────────────────────────────────────────────

class MigrationValidator:
    """迁移验证器"""

    def validate_rule(self, rule_id: str) -> bool:
        """验证迁移结果"""
        # 查找规则文件
        rule_file = None
        for rules_dir in [RULES_DIR]:
            for f in rules_dir.rglob(f"{rule_id}.md"):
                rule_file = f
                break
            if rule_file:
                break

        if not rule_file:
            print(f"Rule file not found: {rule_id}")
            return False

        content = rule_file.read_text(encoding="utf-8")

        # 检查必需的部分
        checks = [
            ('Metadata section', '## Metadata' in content),
            ('Rule ID', '**Rule ID**:' in content),
            ('Category', '**Category**:' in content),
            ('Priority', '**Priority**:' in content),
            ('Layer', '**Layer**:' in content),
            ('Version', 'Version:' in content),
            ('Created', 'Created:' in content),
            ('Updated', 'Updated:' in content),
        ]

        all_passed = True
        for check_name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False

        return all_passed


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    migrator = RuleMigrator()
    validator = MigrationValidator()
    cmd = sys.argv[1]

    if cmd == "scan":
        rules = migrator.scan_rules()
        print(f"Found {len(rules)} rules to migrate:")
        for rule in rules:
            print(f"  - {rule['rule_id']}: {rule['title']}")

    elif cmd == "migrate":
        if len(sys.argv) < 3:
            print("Usage: python3 rule_migrator.py migrate <rule-id>")
            return
        result = migrator.migrate_rule(sys.argv[2])
        if result.success:
            print(f"✓ {result.rule_id} migrated successfully")
            for change in result.changes:
                print(f"  + {change}")
        else:
            print(f"✗ {result.rule_id} migration failed")
            for error in result.errors:
                print(f"  ! {error}")

    elif cmd == "migrate-all":
        migrator.migrate_all()

    elif cmd == "validate":
        if len(sys.argv) < 3:
            print("Usage: python3 rule_migrator.py validate <rule-id>")
            return
        print(f"Validating {sys.argv[2]}...")
        passed = validator.validate_rule(sys.argv[2])
        print(f"\nResult: {'PASS' if passed else 'FAIL'}")

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
