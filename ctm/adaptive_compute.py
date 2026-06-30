#!/usr/bin/env python3
"""
鲤鱼 CTM - 自适应计算时间
Adaptive Compute Timer - 根据问题复杂度动态分配计算资源

基于 CTM 的自适应计算概念，实现动态资源分配
"""

import re
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
from .utils import estimate_tokens

# ── Precompiled Regex Patterns ───────────────────────────────────────────
# Avoid recompiling these on every call to estimate_complexity().
_RE_SPLIT_SENTENCES = re.compile(r'[.!?。！？]')
_RE_SPLIT_CLAUSES = re.compile(r'[,，;；:：]')


class ComputeStrategy(Enum):
    """计算策略枚举"""
    QUICK = "quick"           # 快速响应
    STANDARD = "standard"     # 标准处理
    DEEP = "deep"             # 深度思考
    EXHAUSTIVE = "exhaustive" # 穷尽分析


@dataclass
class ComplexityEstimate:
    """问题复杂度评估"""
    lexical_complexity: float    # 词汇复杂度 (0-1)
    syntactic_complexity: float  # 句法复杂度 (0-1)
    semantic_depth: int          # 语义深度需求 (1-5)
    domain_specificity: float    # 领域专业性 (0-1)
    requires_reasoning: bool     # 是否需要推理
    estimated_tokens: int        # 预估 token 消耗
    confidence: float            # 评估置信度 (0-1)

    def to_dict(self) -> Dict:
        return {
            "lexical_complexity": round(self.lexical_complexity, 3),
            "syntactic_complexity": round(self.syntactic_complexity, 3),
            "semantic_depth": self.semantic_depth,
            "domain_specificity": round(self.domain_specificity, 3),
            "requires_reasoning": self.requires_reasoning,
            "estimated_tokens": self.estimated_tokens,
            "confidence": round(self.confidence, 3)
        }

    @property
    def overall_complexity(self) -> float:
        """综合复杂度分数"""
        return (
            self.lexical_complexity * 0.2 +
            self.syntactic_complexity * 0.2 +
            (self.semantic_depth / 5.0) * 0.3 +
            self.domain_specificity * 0.2 +
            (0.1 if self.requires_reasoning else 0.0)
        )


@dataclass
class ComputeBudget:
    """计算预算"""
    strategy: ComputeStrategy
    max_tokens: int
    max_depth: int
    timeout_seconds: int
    early_stop_threshold: float  # 提前停止阈值

    def to_dict(self) -> Dict:
        return {
            "strategy": self.strategy.value,
            "max_tokens": self.max_tokens,
            "max_depth": self.max_depth,
            "timeout_seconds": self.timeout_seconds,
            "early_stop_threshold": self.early_stop_threshold
        }

    def __post_init__(self):
        """确保 strategy 字段为枚举类型"""
        if isinstance(self.strategy, str):
            self.strategy = ComputeStrategy(self.strategy)


# 预定义策略
STRATEGIES = {
    ComputeStrategy.QUICK: ComputeBudget(
        strategy=ComputeStrategy.QUICK,
        max_tokens=500,
        max_depth=1,
        timeout_seconds=5,
        early_stop_threshold=0.9
    ),
    ComputeStrategy.STANDARD: ComputeBudget(
        strategy=ComputeStrategy.STANDARD,
        max_tokens=2000,
        max_depth=3,
        timeout_seconds=30,
        early_stop_threshold=0.85
    ),
    ComputeStrategy.DEEP: ComputeBudget(
        strategy=ComputeStrategy.DEEP,
        max_tokens=8000,
        max_depth=5,
        timeout_seconds=120,
        early_stop_threshold=0.8
    ),
    ComputeStrategy.EXHAUSTIVE: ComputeBudget(
        strategy=ComputeStrategy.EXHAUSTIVE,
        max_tokens=32000,
        max_depth=10,
        timeout_seconds=300,
        early_stop_threshold=0.75
    ),
}


# 复杂度关键词
COMPLEXITY_INDICATORS = {
    "high": [
        "分析", "比较", "评估", "设计", "优化", "重构", "架构",
        "为什么", "如何", "解释", "证明", "推导", "策略",
        "analyze", "compare", "evaluate", "design", "optimize",
        "why", "how", "explain", "prove", "derive", "strategy"
    ],
    "medium": [
        "实现", "创建", "修改", "更新", "添加", "修复",
        "implement", "create", "modify", "update", "add", "fix"
    ],
    "low": [
        "查看", "列出", "显示", "获取", "检查",
        "show", "list", "display", "get", "check"
    ]
}

REASONING_INDICATORS = [
    "因为", "所以", "如果", "那么", "否则", "虽然", "但是",
    "because", "therefore", "if", "then", "else", "although", "but",
    "推理", "逻辑", "证明", "推导", "reasoning", "logic", "proof"
]

DOMAIN_KEYWORDS = {
    "programming": ["代码", "函数", "类", "模块", "API", "code", "function", "class", "module"],
    "architecture": ["架构", "设计模式", "系统", "微服务", "architecture", "design pattern", "system"],
    "ai_ml": ["机器学习", "深度学习", "神经网络", "模型", "machine learning", "deep learning", "neural"],
    "security": ["安全", "加密", "认证", "授权", "security", "encryption", "authentication"],
    "database": ["数据库", "SQL", "查询", "索引", "database", "query", "index"]
}


class AdaptiveComputeTimer:
    """自适应计算时间管理器"""

    def __init__(self):
        self.history: List[Tuple[str, ComplexityEstimate, ComputeBudget]] = []

    def estimate_complexity(self, query: str, context: Dict = None) -> ComplexityEstimate:
        """评估问题复杂度"""
        query_lower = query.lower()
        words = query.split()

        # 1. 词汇复杂度
        avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
        unique_ratio = len(set(words)) / max(len(words), 1)
        lexical_complexity = min(1.0, (avg_word_len / 10 + unique_ratio) / 2)

        # 2. 句法复杂度 (uses precompiled regex)
        sentence_count = max(0, len(_RE_SPLIT_SENTENCES.split(query)) - 1)
        clause_count = max(0, len(_RE_SPLIT_CLAUSES.split(query)) - 1)
        syntactic_complexity = min(1.0, (sentence_count / 5 + clause_count / 10) / 2)

        # 3. 语义深度 (high=4, medium=3, low=2, none=1)
        _depth_map = {"high": 4, "medium": 3, "low": 2}
        semantic_depth = 1
        for level_name, keywords in COMPLEXITY_INDICATORS.items():
            if any(kw in query_lower for kw in keywords):
                semantic_depth = max(semantic_depth, _depth_map[level_name])

        # 4. 领域专业性
        domain_matches = 0
        for domain, keywords in DOMAIN_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                domain_matches += 1
        domain_specificity = min(1.0, domain_matches / 3)

        # 5. 是否需要推理
        requires_reasoning = any(kw in query_lower for kw in REASONING_INDICATORS)

        # 6. 估算 token（基于统一估算函数，再乘以推理倍数）
        estimated_tokens = estimate_tokens(query)
        if requires_reasoning:
            estimated_tokens *= 3
        if semantic_depth > 3:
            estimated_tokens *= 2

        # 7. 置信度
        confidence = 0.7
        if len(words) > 10:
            confidence += 0.1
        if context:
            confidence += 0.1

        return ComplexityEstimate(
            lexical_complexity=lexical_complexity,
            syntactic_complexity=syntactic_complexity,
            semantic_depth=semantic_depth,
            domain_specificity=domain_specificity,
            requires_reasoning=requires_reasoning,
            estimated_tokens=estimated_tokens,
            confidence=min(confidence, 1.0)
        )

    def allocate_budget(self, complexity: ComplexityEstimate,
                        context: Dict = None) -> ComputeBudget:
        """根据复杂度分配计算预算"""
        overall = complexity.overall_complexity

        # 选择策略
        if overall < 0.3:
            strategy = ComputeStrategy.QUICK
        elif overall < 0.5:
            strategy = ComputeStrategy.STANDARD
        elif overall < 0.7:
            strategy = ComputeStrategy.DEEP
        else:
            strategy = ComputeStrategy.EXHAUSTIVE

        budget = STRATEGIES[strategy]

        # 根据上下文调整
        if context:
            # O2 压力调整
            o2_pressure = context.get("o2_pressure", 0)
            if o2_pressure > 70:
                # 上下文紧张，减少预算
                budget = ComputeBudget(
                    strategy=budget.strategy,
                    max_tokens=int(budget.max_tokens * 0.7),
                    max_depth=max(1, budget.max_depth - 1),
                    timeout_seconds=int(budget.timeout_seconds * 0.7),
                    early_stop_threshold=budget.early_stop_threshold + 0.05
                )

            # 时间压力调整
            time_pressure = context.get("time_pressure", 0)
            if time_pressure > 0.8:
                budget = ComputeBudget(
                    strategy=ComputeStrategy.QUICK,
                    max_tokens=500,
                    max_depth=1,
                    timeout_seconds=5,
                    early_stop_threshold=0.9
                )

        return budget

    def should_continue(self, current_depth: int, current_tokens: int,
                        current_confidence: float, elapsed_seconds: float,
                        budget: ComputeBudget) -> Tuple[bool, str]:
        """判断是否应继续思考"""
        # 深度限制
        if current_depth >= budget.max_depth:
            return False, "达到最大深度"

        # Token 限制
        if current_tokens >= budget.max_tokens:
            return False, "达到 Token 限制"

        # 超时限制
        if elapsed_seconds >= budget.timeout_seconds:
            return False, "超时"

        # 提前停止（置信度足够高）
        if current_confidence >= budget.early_stop_threshold:
            return False, f"置信度足够 ({current_confidence:.2f})"

        return True, "继续思考"

    def record_outcome(self, query: str, complexity: ComplexityEstimate,
                       budget: ComputeBudget):
        """记录结果用于学习"""
        self.history.append((query, complexity, budget))

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self.history:
            return {"total": 0}

        strategies = {}
        for _, _, budget in self.history:
            s = budget.strategy.value if isinstance(budget.strategy, ComputeStrategy) else budget.strategy
            strategies[s] = strategies.get(s, 0) + 1

        return {
            "total": len(self.history),
            "strategies": strategies,
            "avg_complexity": sum(c.overall_complexity for _, c, _ in self.history) / len(self.history)
        }


def main():
    """CLI 入口"""
    import sys

    if len(sys.argv) < 2:
        print("用法: adaptive_compute.py <command>")
        print("命令:")
        print("  estimate <query>  - 评估问题复杂度")
        print("  stats             - 查看统计")
        return

    timer = AdaptiveComputeTimer()
    command = sys.argv[1]

    if command == "estimate":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "默认查询"
        complexity = timer.estimate_complexity(query)
        budget = timer.allocate_budget(complexity)

        print(f"查询: {query}")
        print(f"复杂度评估:")
        print(f"  词汇复杂度: {complexity.lexical_complexity:.3f}")
        print(f"  句法复杂度: {complexity.syntactic_complexity:.3f}")
        print(f"  语义深度: {complexity.semantic_depth}")
        print(f"  领域专业性: {complexity.domain_specificity:.3f}")
        print(f"  需要推理: {complexity.requires_reasoning}")
        print(f"  综合复杂度: {complexity.overall_complexity:.3f}")
        print(f"计算预算:")
        print(f"  策略: {budget.strategy.value}")
        print(f"  最大 Token: {budget.max_tokens}")
        print(f"  最大深度: {budget.max_depth}")
        print(f"  超时: {budget.timeout_seconds}s")

    elif command == "stats":
        stats = timer.get_statistics()
        print(f"统计: {stats}")

    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
