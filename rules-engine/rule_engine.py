#!/usr/bin/env python3
"""
PHOENIX Rules Engine — 智能规则管理系统

特性：
1. 动态规则加载 - 根据上下文智能加载规则
2. 规则冲突检测 - 检测相互矛盾的规则
3. 规则依赖管理 - 显式声明规则依赖
4. 规则版本控制 - 追踪规则演变历史
5. 语义规则匹配 - 基于语义理解的规则匹配
6. 规则优先级 - 当规则冲突时有明确的优先级

Usage:
  python3 rule_engine.py analyze                  分析规则系统
  python3 rule_engine.py conflicts                检测规则冲突
  python3 rule_engine.py deps <rule-id>           查看规则依赖
  python3 rule_engine.py context <task-type>      获取上下文相关规则
  python3 rule_engine.py validate                 验证规则完整性
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import json
import re
import sys

# ── 路径配置 ─────────────────────────────────────────────────────────────

PHOENIX_HOME = Path.home() / ".claude" / "phoenix"
RULES_DIR = Path.home() / ".claude" / "rules"
PHOENIX_RULES_DIR = RULES_DIR / "phoenix"
ENGINE_DIR = PHOENIX_HOME / "rules-engine"
RULE_REGISTRY = ENGINE_DIR / "rule-registry.json"
CONFLICT_LOG = ENGINE_DIR / "conflicts.jsonl"

# ── 数据类 ───────────────────────────────────────────────────────────────

@dataclass
class RuleMetadata:
    """规则元数据"""
    rule_id: str
    name: str
    file_path: str
    layer: str                      # common, phoenix, language-specific
    category: str                   # coding-style, testing, security, etc.
    stage: str                      # draft, active, observed, validated, hardened
    enforcement_level: int          # 1-7
    priority: int                   # 1-10, 10 = highest
    domains: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    conflicts_with: List[str] = field(default_factory=list)
    supersedes: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)  # 适用语言
    triggers: List[str] = field(default_factory=list)    # 触发条件
    token_cost: int = 0
    version: str = "1.0.0"
    created_at: str = ""
    updated_at: str = ""
    status: str = "active"  # active, deprecated, deleted
    usage_count: int = 0
    success_rate: float = 0.0


@dataclass
class RuleConflict:
    """规则冲突"""
    rule_a: str
    rule_b: str
    conflict_type: str              # contradictory, overlapping, priority
    description: str
    severity: str                   # low, medium, high, critical
    resolution: str = ""


@dataclass
class ContextMatch:
    """上下文匹配结果"""
    rule_id: str
    relevance_score: float          # 0.0 - 1.0
    match_reasons: List[str]
    should_load: bool


# ── 规则解析器 ───────────────────────────────────────────────────────────

class RuleParser:
    """规则文件解析器"""

    @staticmethod
    def parse_rule_file(file_path: Path) -> Optional[RuleMetadata]:
        """解析规则文件，提取元数据"""
        if not file_path.exists():
            return None

        content = file_path.read_text(encoding="utf-8")
        rule_id = file_path.stem

        # 提取基本信息
        name = RuleParser._extract_title(content)
        stage = RuleParser._extract_field(content, r'Stage:\s*(\w+)', "active")
        enforcement = RuleParser._extract_int(content, r'Enforcement:.*Level\s*(\d)', 1)
        domains = RuleParser._extract_domains(content)
        dependencies = RuleParser._extract_list(content, r'Dependencies:\s*\n((?:- .+\n)+)')
        conflicts = RuleParser._extract_list(content, r'Conflicts?:\s*\n((?:- .+\n)+)')
        supersedes = RuleParser._extract_list(content, r'Supersedes?:\s*\n((?:- .+\n)+)')
        languages = RuleParser._extract_list(content, r'Languages?:\s*\n((?:- .+\n)+)')
        triggers = RuleParser._extract_triggers(content)

        # 确定层级
        layer = RuleParser._determine_layer(file_path)

        # 确定分类
        category = RuleParser._determine_category(content, domains, str(file_path))

        # 确定优先级
        priority = RuleParser._determine_priority(stage, enforcement, layer)

        # 估算 token 成本
        token_cost = RuleParser._estimate_tokens(content)

        # 提取版本和时间
        version = RuleParser._extract_field(content, r'Version:\s*([\d.]+)', "1.0.0")
        created_at = RuleParser._extract_field(content, r'Created:\s*(\d{4}-\d{2}-\d{2})', "")
        updated_at = RuleParser._extract_field(content, r'Updated:\s*(\d{4}-\d{2}-\d{2})', created_at)

        return RuleMetadata(
            rule_id=rule_id,
            name=name or rule_id,
            file_path=str(file_path),
            layer=layer,
            category=category,
            stage=stage,
            enforcement_level=enforcement,
            priority=priority,
            domains=domains,
            dependencies=dependencies,
            conflicts_with=conflicts,
            supersedes=supersedes,
            languages=languages,
            triggers=triggers,
            token_cost=token_cost,
            version=version,
            created_at=created_at,
            updated_at=updated_at,
        )

    @staticmethod
    def _extract_title(content: str) -> str:
        match = re.search(r'^#\s+(.+?)(?:\s*—|\s*\(|$)', content, re.MULTILINE)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _extract_field(content: str, pattern: str, default: str) -> str:
        match = re.search(pattern, content)
        return match.group(1) if match else default

    @staticmethod
    def _extract_int(content: str, pattern: str, default: int) -> int:
        match = re.search(pattern, content)
        return int(match.group(1)) if match else default

    @staticmethod
    def _extract_domains(content: str) -> List[str]:
        match = re.search(r'## Domains\s*\n(.+?)(?:\n##|\Z)', content, re.DOTALL)
        if match:
            text = match.group(1).strip()
            return [d.strip() for d in text.split(',') if d.strip()]
        return []

    @staticmethod
    def _extract_list(content: str, pattern: str) -> List[str]:
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            lines = match.group(1).strip().split('\n')
            return [line.strip().lstrip('- ') for line in lines if line.strip()]
        return []

    @staticmethod
    def _extract_triggers(content: str) -> List[str]:
        match = re.search(r'## Trigger\s*\n(.+?)(?:\n##|\Z)', content, re.DOTALL)
        if match:
            text = match.group(1).strip()
            # 提取关键短语
            phrases = re.findall(r'[A-Z][a-z]+(?:\s+[a-z]+)+', text)
            return phrases[:5]  # 最多 5 个触发条件
        return []

    @staticmethod
    def _determine_layer(file_path: Path) -> str:
        parts = file_path.parts
        if "phoenix" in parts:
            return "phoenix"
        elif "common" in parts:
            return "common"
        elif "zh" in parts:
            return "translation"
        else:
            return "language-specific"

    @staticmethod
    def _determine_category(content: str, domains: List[str], file_path: str = "") -> str:
        # 基于域名、内容和文件名判断分类
        domain_str = ' '.join(domains).lower()
        content_lower = content.lower()
        file_lower = file_path.lower()
        combined = f"{domain_str} {content_lower} {file_lower}"

        if 'security' in combined or 'safety' in combined or 'guard' in combined:
            return 'security'
        elif 'testing' in combined or 'tdd' in combined or 'mutation' in combined or 'e2e' in combined:
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
    def _determine_priority(stage: str, enforcement: int, layer: str) -> int:
        """确定规则优先级 (1-10)"""
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
        if layer == 'phoenix':
            base += 1
        elif layer == 'common':
            base += 0

        return min(10, max(1, base))

    @staticmethod
    def _estimate_tokens(content: str) -> int:
        """估算 token 成本"""
        chinese_chars = len(re.findall(r'[一-鿿]', content))
        english_words = len(re.findall(r'[a-zA-Z]+', content))
        return int(chinese_chars * 1.3 + english_words * 0.75)


# ── 规则注册表 ───────────────────────────────────────────────────────────

class RuleRegistry:
    """规则注册表管理"""

    def __init__(self):
        self.rules: Dict[str, RuleMetadata] = {}
        self.conflicts: List[RuleConflict] = []
        self._load_registry()

    def _load_registry(self):
        """加载规则注册表"""
        if RULE_REGISTRY.exists():
            try:
                data = json.loads(RULE_REGISTRY.read_text())
                for rule_data in data.get('rules', []):
                    # 兼容旧数据：确保 status 字段存在
                    if 'status' not in rule_data:
                        rule_data['status'] = 'active'
                    rule = RuleMetadata(**rule_data)
                    self.rules[rule.rule_id] = rule
            except Exception as e:
                print(f"Warning: Failed to load registry: {e}")

    def save_registry(self):
        """保存规则注册表"""
        ENGINE_DIR.mkdir(parents=True, exist_ok=True)
        rules_data = []
        for rule in self.rules.values():
            d = vars(rule)
            # 确保 status 字段存在
            if 'status' not in d or not d['status']:
                d['status'] = 'active'
            rules_data.append(d)
        data = {
            'version': '2.0.0',
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'rules': rules_data,
        }
        RULE_REGISTRY.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def scan_rules(self) -> int:
        """扫描所有规则文件，更新注册表"""
        scanned = 0

        # 扫描所有规则目录
        for rules_dir in [RULES_DIR]:
            if not rules_dir.exists():
                continue

            for rule_file in rules_dir.rglob("*.md"):
                if rule_file.name == "README.md":
                    continue

                rule = RuleParser.parse_rule_file(rule_file)
                if rule:
                    # 保留使用统计
                    if rule.rule_id in self.rules:
                        old_rule = self.rules[rule.rule_id]
                        rule.usage_count = old_rule.usage_count
                        rule.success_rate = old_rule.success_rate

                    self.rules[rule.rule_id] = rule
                    scanned += 1

        return scanned

    def get_rule(self, rule_id: str) -> Optional[RuleMetadata]:
        """获取规则"""
        return self.rules.get(rule_id)

    def get_rules_by_category(self, category: str) -> List[RuleMetadata]:
        """按分类获取规则"""
        return [r for r in self.rules.values() if r.category == category]

    def get_rules_by_layer(self, layer: str) -> List[RuleMetadata]:
        """按层级获取规则"""
        return [r for r in self.rules.values() if r.layer == layer]

    def get_rules_by_domain(self, domain: str) -> List[RuleMetadata]:
        """按域名获取规则"""
        return [r for r in self.rules.values() if domain in r.domains]

    def get_rules_for_language(self, language: str) -> List[RuleMetadata]:
        """获取适用于特定语言的规则"""
        return [
            r for r in self.rules.values()
            if not r.languages or language in r.languages
        ]


# ── 冲突检测器 ───────────────────────────────────────────────────────────

class ConflictDetector:
    """规则冲突检测器"""

    def __init__(self, registry: RuleRegistry):
        self.registry = registry

    def detect_all_conflicts(self) -> List[RuleConflict]:
        """检测所有规则冲突"""
        conflicts = []
        rules = list(self.registry.rules.values())

        for i in range(len(rules)):
            for j in range(i + 1, len(rules)):
                rule_a = rules[i]
                rule_b = rules[j]

                # 检测显式冲突
                if rule_b.rule_id in rule_a.conflicts_with:
                    conflicts.append(RuleConflict(
                        rule_a=rule_a.rule_id,
                        rule_b=rule_b.rule_id,
                        conflict_type="explicit",
                        description=f"Rule {rule_a.rule_id} explicitly conflicts with {rule_b.rule_id}",
                        severity="high",
                    ))

                # 检测同域冲突
                domain_conflicts = self._detect_domain_conflicts(rule_a, rule_b)
                conflicts.extend(domain_conflicts)

                # 检测重叠规则
                overlaps = self._detect_overlaps(rule_a, rule_b)
                conflicts.extend(overlaps)

                # 检测优先级冲突
                priority_conflicts = self._detect_priority_conflicts(rule_a, rule_b)
                conflicts.extend(priority_conflicts)

        return conflicts

    def _detect_domain_conflicts(self, rule_a: RuleMetadata, rule_b: RuleMetadata) -> List[RuleConflict]:
        """检测同域规则冲突"""
        conflicts = []

        # 同域 + 同分类 = 可能冲突
        common_domains = set(rule_a.domains) & set(rule_b.domains)
        if common_domains and rule_a.category == rule_b.category:
            # 检查是否内容矛盾
            if self._content_contradicts(rule_a, rule_b):
                conflicts.append(RuleConflict(
                    rule_a=rule_a.rule_id,
                    rule_b=rule_b.rule_id,
                    conflict_type="contradictory",
                    description=f"Rules in same domain {common_domains} may contradict",
                    severity="medium",
                ))

        return conflicts

    def _detect_overlaps(self, rule_a: RuleMetadata, rule_b: RuleMetadata) -> List[RuleConflict]:
        """检测重叠规则"""
        conflicts = []

        # 触发条件重叠
        common_triggers = set(rule_a.triggers) & set(rule_b.triggers)
        if common_triggers:
            conflicts.append(RuleConflict(
                rule_a=rule_a.rule_id,
                rule_b=rule_b.rule_id,
                conflict_type="overlapping",
                description=f"Rules share triggers: {common_triggers}",
                severity="low",
            ))

        return conflicts

    def _detect_priority_conflicts(self, rule_a: RuleMetadata, rule_b: RuleMetadata) -> List[RuleConflict]:
        """检测优先级冲突"""
        conflicts = []

        # 如果一个规则 supersedes 另一个，但优先级更低
        if rule_b.rule_id in rule_a.supersedes:
            if rule_a.priority < rule_b.priority:
                conflicts.append(RuleConflict(
                    rule_a=rule_a.rule_id,
                    rule_b=rule_b.rule_id,
                    conflict_type="priority",
                    description=f"Rule {rule_a.rule_id} supersedes {rule_b.rule_id} but has lower priority",
                    severity="high",
                ))

        return conflicts

    def _content_contradicts(self, rule_a: RuleMetadata, rule_b: RuleMetadata) -> bool:
        """检查内容是否矛盾（简化版本）"""
        # 这里可以扩展为更复杂的语义分析
        return False


# ── 上下文匹配器 ─────────────────────────────────────────────────────────

class ContextMatcher:
    """上下文相关规则匹配器"""

    def __init__(self, registry: RuleRegistry):
        self.registry = registry

    def get_relevant_rules(
        self,
        task_type: str = "",
        language: str = "",
        domains: List[str] = None,
        max_rules: int = 20,
        max_tokens: int = 5000,
    ) -> List[ContextMatch]:
        """获取与上下文相关的规则"""
        matches = []

        for rule in self.registry.rules.values():
            score, reasons = self._calculate_relevance(
                rule, task_type, language, domains or []
            )

            if score > 0.1:  # 最低相关性阈值
                matches.append(ContextMatch(
                    rule_id=rule.rule_id,
                    relevance_score=score,
                    match_reasons=reasons,
                    should_load=score > 0.5,
                ))

        # 按相关性排序
        matches.sort(key=lambda m: m.relevance_score, reverse=True)

        # 应用限制
        selected = []
        total_tokens = 0

        for match in matches:
            rule = self.registry.get_rule(match.rule_id)
            if not rule:
                continue

            if len(selected) >= max_rules:
                break

            if total_tokens + rule.token_cost > max_tokens:
                # 尝试找到更小的规则
                continue

            selected.append(match)
            total_tokens += rule.token_cost

        return selected

    def _calculate_relevance(
        self,
        rule: RuleMetadata,
        task_type: str,
        language: str,
        domains: List[str],
    ) -> Tuple[float, List[str]]:
        """计算规则相关性分数"""
        score = 0.0
        reasons = []

        # 基础分数（基于优先级）
        score += rule.priority / 10.0 * 0.2

        # 语言匹配
        if language and (not rule.languages or language in rule.languages):
            score += 0.3
            reasons.append(f"Language match: {language}")

        # 域名匹配
        if domains:
            common_domains = set(rule.domains) & set(domains)
            if common_domains:
                score += len(common_domains) / len(domains) * 0.3
                reasons.append(f"Domain match: {common_domains}")

        # 任务类型匹配
        if task_type:
            task_lower = task_type.lower()
            if task_lower in rule.category:
                score += 0.2
                reasons.append(f"Task type match: {task_type}")

            # 触发条件匹配
            for trigger in rule.triggers:
                if trigger.lower() in task_lower or task_lower in trigger.lower():
                    score += 0.1
                    reasons.append(f"Trigger match: {trigger}")
                    break

        # Stage 加成
        stage_bonus = {
            'hardened': 0.15,
            'validated': 0.1,
            'observed': 0.05,
            'active': 0.0,
        }
        score += stage_bonus.get(rule.stage, 0)

        # Layer 加成（phoenix 规则优先）
        if rule.layer == 'phoenix':
            score += 0.1
            reasons.append("Phoenix layer rule")

        return min(1.0, score), reasons


# ── 规则验证器 ───────────────────────────────────────────────────────────

class RuleValidator:
    """规则完整性验证器"""

    def __init__(self, registry: RuleRegistry):
        self.registry = registry
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> Tuple[List[str], List[str]]:
        """验证所有规则"""
        self.errors = []
        self.warnings = []

        for rule in self.registry.rules.values():
            self._validate_rule(rule)

        self._validate_dependencies()
        self._validate_conflicts()
        self._validate_supersedes()

        return self.errors, self.warnings

    def _validate_rule(self, rule: RuleMetadata):
        """验证单个规则"""
        # 检查必填字段
        if not rule.name:
            self.errors.append(f"{rule.rule_id}: Missing name")

        if not rule.file_path:
            self.errors.append(f"{rule.rule_id}: Missing file path")

        if rule.enforcement_level < 1 or rule.enforcement_level > 7:
            self.errors.append(f"{rule.rule_id}: Invalid enforcement level {rule.enforcement_level}")

        if rule.priority < 1 or rule.priority > 10:
            self.errors.append(f"{rule.rule_id}: Invalid priority {rule.priority}")

        # 检查文件是否存在
        if not Path(rule.file_path).exists():
            self.warnings.append(f"{rule.rule_id}: File not found: {rule.file_path}")

        # 检查 stage 有效性
        valid_stages = ['draft', 'active', 'observed', 'validated', 'hardened']
        if rule.stage not in valid_stages:
            self.warnings.append(f"{rule.rule_id}: Invalid stage '{rule.stage}'")

    def _validate_dependencies(self):
        """验证规则依赖"""
        for rule in self.registry.rules.values():
            for dep_id in rule.dependencies:
                if dep_id not in self.registry.rules:
                    self.errors.append(f"{rule.rule_id}: Missing dependency '{dep_id}'")

    def _validate_conflicts(self):
        """验证规则冲突声明"""
        for rule in self.registry.rules.values():
            for conflict_id in rule.conflicts_with:
                if conflict_id not in self.registry.rules:
                    self.warnings.append(f"{rule.rule_id}: Conflict target '{conflict_id}' not found")

    def _validate_supersedes(self):
        """验证规则 supersede 声明"""
        for rule in self.registry.rules.values():
            for superseded_id in rule.supersedes:
                if superseded_id not in self.registry.rules:
                    self.warnings.append(f"{rule.rule_id}: Superseded rule '{superseded_id}' not found")


# ── 规则引擎主类 ─────────────────────────────────────────────────────────

class RuleEngine:
    """PHOENIX 规则引擎"""

    def __init__(self):
        self.registry = RuleRegistry()
        self.conflict_detector = ConflictDetector(self.registry)
        self.context_matcher = ContextMatcher(self.registry)
        self.validator = RuleValidator(self.registry)

    def analyze(self):
        """分析规则系统"""
        print("=" * 72)
        print("  PHOENIX Rules Engine Analysis")
        print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("=" * 72)
        print()

        # 扫描规则
        scanned = self.registry.scan_rules()
        print(f"Scanned {scanned} rule files")
        print(f"Total rules in registry: {len(self.registry.rules)}")
        print()

        # 统计信息
        self._print_statistics()

        # 保存注册表
        self.registry.save_registry()
        print(f"\nRegistry saved to: {RULE_REGISTRY}")

    def _print_statistics(self):
        """打印统计信息"""
        rules = list(self.registry.rules.values())

        # 按层级统计
        print("── Rules by Layer ──")
        layers = {}
        for rule in rules:
            layers[rule.layer] = layers.get(rule.layer, 0) + 1
        for layer, count in sorted(layers.items()):
            print(f"  {layer:20s}: {count}")
        print()

        # 按分类统计
        print("── Rules by Category ──")
        categories = {}
        for rule in rules:
            categories[rule.category] = categories.get(rule.category, 0) + 1
        for category, count in sorted(categories.items()):
            print(f"  {category:20s}: {count}")
        print()

        # 按 Stage 统计
        print("── Rules by Stage ──")
        stages = {}
        for rule in rules:
            stages[rule.stage] = stages.get(rule.stage, 0) + 1
        for stage, count in sorted(stages.items()):
            print(f"  {stage:20s}: {count}")
        print()

        # Token 成本统计
        total_tokens = sum(r.token_cost for r in rules)
        avg_tokens = total_tokens / len(rules) if rules else 0
        print("── Token Cost ──")
        print(f"  Total: {total_tokens:,}")
        print(f"  Average: {avg_tokens:,.0f}")
        print(f"  Max: {max(r.token_cost for r in rules) if rules else 0:,}")
        print()

        # 高优先级规则
        print("── Top 10 Priority Rules ──")
        top_rules = sorted(rules, key=lambda r: r.priority, reverse=True)[:10]
        for i, rule in enumerate(top_rules, 1):
            print(f"  {i:2d}. [{rule.priority}] {rule.rule_id}")
        print()

    def detect_conflicts(self):
        """检测规则冲突"""
        print("=" * 72)
        print("  PHOENIX Rules Conflict Detection")
        print("=" * 72)
        print()

        self.registry.scan_rules()
        conflicts = self.conflict_detector.detect_all_conflicts()

        if not conflicts:
            print("No conflicts detected.")
            return

        print(f"Found {len(conflicts)} potential conflicts:")
        print()

        # 按严重程度分组
        by_severity = {}
        for conflict in conflicts:
            by_severity.setdefault(conflict.severity, []).append(conflict)

        for severity in ['critical', 'high', 'medium', 'low']:
            if severity not in by_severity:
                continue

            print(f"── {severity.upper()} Severity ──")
            for conflict in by_severity[severity]:
                print(f"  {conflict.rule_a} ↔ {conflict.rule_b}")
                print(f"    Type: {conflict.conflict_type}")
                print(f"    {conflict.description}")
                if conflict.resolution:
                    print(f"    Resolution: {conflict.resolution}")
                print()

        # 保存冲突日志
        self._save_conflict_log(conflicts)

    def _save_conflict_log(self, conflicts: List[RuleConflict]):
        """保存冲突日志"""
        ENGINE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFLICT_LOG, 'a') as f:
            for conflict in conflicts:
                entry = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    **vars(conflict),
                }
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def get_dependencies(self, rule_id: str):
        """查看规则依赖"""
        rule = self.registry.get_rule(rule_id)
        if not rule:
            print(f"Rule not found: {rule_id}")
            return

        print(f"Rule: {rule.rule_id}")
        print(f"Name: {rule.name}")
        print()

        # 直接依赖
        print("── Direct Dependencies ──")
        if rule.dependencies:
            for dep_id in rule.dependencies:
                dep = self.registry.get_rule(dep_id)
                if dep:
                    print(f"  → {dep_id}: {dep.name}")
                else:
                    print(f"  → {dep_id}: NOT FOUND")
        else:
            print("  (none)")
        print()

        # 被依赖（反向依赖）
        print("── Depended By ──")
        dependents = [
            r.rule_id for r in self.registry.rules.values()
            if rule_id in r.dependencies
        ]
        if dependents:
            for dep_id in dependents:
                print(f"  ← {dep_id}")
        else:
            print("  (none)")
        print()

        # 冲突规则
        print("── Conflicts With ──")
        if rule.conflicts_with:
            for conflict_id in rule.conflicts_with:
                print(f"  ✗ {conflict_id}")
        else:
            print("  (none)")
        print()

        # Supersedes
        print("── Supersedes ──")
        if rule.supersedes:
            for superseded_id in rule.supersedes:
                print(f"  ⊃ {superseded_id}")
        else:
            print("  (none)")

    def get_context_rules(self, task_type: str, language: str = "", domains: List[str] = None):
        """获取上下文相关规则"""
        print("=" * 72)
        print("  PHOENIX Context-Aware Rule Loading")
        print(f"  Task: {task_type}")
        print(f"  Language: {language or 'any'}")
        print(f"  Domains: {domains or 'any'}")
        print("=" * 72)
        print()

        self.registry.scan_rules()
        matches = self.context_matcher.get_relevant_rules(
            task_type=task_type,
            language=language,
            domains=domains,
        )

        if not matches:
            print("No relevant rules found.")
            return

        print(f"Found {len(matches)} relevant rules:")
        print()

        # 分为应该加载和可选
        should_load = [m for m in matches if m.should_load]
        optional = [m for m in matches if not m.should_load]

        if should_load:
            print("── Should Load (High Relevance) ──")
            print(f"{'Score':>7}  {'Rule':30s}  Reasons")
            print("-" * 70)
            for match in should_load:
                rule = self.registry.get_rule(match.rule_id)
                reasons = ', '.join(match.match_reasons[:2])
                print(f"{match.relevance_score:7.3f}  {match.rule_id:30s}  {reasons}")
            print()

        if optional:
            print("── Optional (Lower Relevance) ──")
            print(f"{'Score':>7}  {'Rule':30s}  Reasons")
            print("-" * 70)
            for match in optional[:10]:  # 最多显示 10 个
                rule = self.registry.get_rule(match.rule_id)
                reasons = ', '.join(match.match_reasons[:2])
                print(f"{match.relevance_score:7.3f}  {match.rule_id:30s}  {reasons}")
            print()

        # Token 统计
        total_tokens = sum(
            self.registry.get_rule(m.rule_id).token_cost
            for m in should_load
            if self.registry.get_rule(m.rule_id)
        )
        print(f"Total tokens for loaded rules: {total_tokens:,}")

    def validate(self):
        """验证规则完整性"""
        print("=" * 72)
        print("  PHOENIX Rules Validation")
        print("=" * 72)
        print()

        self.registry.scan_rules()
        errors, warnings = self.validator.validate_all()

        if not errors and not warnings:
            print("All rules are valid!")
            return

        if errors:
            print(f"── ERRORS ({len(errors)}) ──")
            for error in errors:
                print(f"  ✗ {error}")
            print()

        if warnings:
            print(f"── WARNINGS ({len(warnings)}) ──")
            for warning in warnings:
                print(f"  ⚠ {warning}")
            print()

        print(f"Summary: {len(errors)} errors, {len(warnings)} warnings")


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    engine = RuleEngine()
    cmd = sys.argv[1]

    if cmd == "analyze":
        engine.analyze()

    elif cmd == "conflicts":
        engine.detect_conflicts()

    elif cmd == "deps":
        if len(sys.argv) < 3:
            print("Usage: python3 rule_engine.py deps <rule-id>")
            return
        engine.get_dependencies(sys.argv[2])

    elif cmd == "context":
        if len(sys.argv) < 3:
            print("Usage: python3 rule_engine.py context <task-type> [language] [domains...]")
            return
        task_type = sys.argv[2]
        language = sys.argv[3] if len(sys.argv) > 3 else ""
        domains = sys.argv[4:] if len(sys.argv) > 4 else []
        engine.get_context_rules(task_type, language, domains)

    elif cmd == "validate":
        engine.validate()

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
