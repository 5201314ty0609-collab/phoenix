#!/usr/bin/env python3
"""
PHOENIX Skill: Skill Learn — 技能学习与追踪系统。

追踪技能使用情况，学习模式，自动推荐技能。

Usage:
  skill-learn.py record <skill> [result]    记录一次技能使用
  skill-learn.py recommend <context>         推荐技能
  skill-learn.py stats                       技能使用统计
  skill-learn.py history [--limit N]         使用历史
  skill-learn.py patterns                    检测使用模式
  skill-learn.py score <skill>               查看技能评分
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import math
import sys
import uuid


PHOENIX_HOME = Path.home() / ".claude" / "phoenix"
USAGE_FILE = PHOENIX_HOME / "skill-usage.jsonl"
PATTERNS_FILE = PHOENIX_HOME / "skill-patterns.json"


# ── Context Keywords for Recommendation ─────────────────────────────────────

SKILL_CONTEXT_KEYWORDS = {
    "code-tidy": [
        "clean", "tidy", "format", "import", "unused", "organize",
        "cleanup", "refactor", "imports",
    ],
    "security-audit": [
        "security", "vulnerability", "secret", "injection", "xss",
        "audit", "scan", "secure", "credentials", "auth",
    ],
    "verify-completion": [
        "verify", "check", "validate", "complete", "done",
        "ready", "finish", "syntax",
    ],
    "complexity-analyzer": [
        "complexity", "quality", "metrics", "analyze", "review",
        "maintainability", "cyclomatic", "nesting", "long function",
    ],
    "systematic-debug": [
        "debug", "error", "bug", "crash", "fail", "issue",
        "problem", "trace", "investigate", "diagnose",
    ],
    "dispatch-parallel": [
        "parallel", "concurrent", "multi", "batch", "dispatch",
        "split", "distribute", "async",
    ],
    "knowledge-sync": [
        "sync", "knowledge", "memory", "search", "find",
        "remember", "recall", "database",
    ],
    "health-check": [
        "health", "status", "system", "disk", "memory",
        "environment", "check", "diagnostic",
    ],
    "pr-prep": [
        "pr", "pull request", "merge", "branch", "description",
        "changelog", "summary", "review",
    ],
    "doc-gen": [
        "doc", "documentation", "docstring", "readme", "api",
        "generate", "comment", "describe",
    ],
    "skill-pipeline": [
        "pipeline", "chain", "workflow", "sequence", "batch",
        "combine", "multiple skills",
    ],
}


# ── Data Model ──────────────────────────────────────────────────────────────

@dataclass
class SkillUsage:
    """技能使用记录"""
    id: str
    skill: str
    timestamp: str
    result: str              # success / failure / partial
    duration_ms: int = 0
    context: str = ""        # 使用上下文描述
    target: str = ""         # 操作目标
    error: str = ""          # 失败原因

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "skill": self.skill,
            "timestamp": self.timestamp,
            "result": self.result,
            "duration_ms": self.duration_ms,
            "context": self.context,
            "target": self.target,
            "error": self.error,
        }


@dataclass
class SkillScore:
    """技能评分"""
    skill: str
    total_uses: int
    success_count: int
    failure_count: int
    success_rate: float
    avg_duration_ms: float
    last_used: str
    days_since_last_use: float
    trend: str              # rising / stable / declining
    composite_score: float  # 0-100

    def to_dict(self) -> dict:
        return {
            "skill": self.skill,
            "total_uses": self.total_uses,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": round(self.success_rate, 3),
            "avg_duration_ms": round(self.avg_duration_ms, 1),
            "last_used": self.last_used,
            "days_since_last_use": round(self.days_since_last_use, 1),
            "trend": self.trend,
            "composite_score": round(self.composite_score, 1),
        }


@dataclass
class UsagePattern:
    """使用模式"""
    pattern_type: str       # frequent_combo, time_based, error_cluster
    description: str
    skills: List[str]
    confidence: float
    suggestion: str = ""


# ── Usage Tracker ───────────────────────────────────────────────────────────

class SkillTracker:
    """技能使用追踪器"""

    def __init__(self):
        self.usages: List[SkillUsage] = []
        self._load()

    def _load(self):
        """加载使用记录"""
        if not USAGE_FILE.exists():
            return
        for line in USAGE_FILE.read_text().strip().split("\n"):
            if line.strip():
                try:
                    data = json.loads(line)
                    self.usages.append(SkillUsage(**data))
                except Exception:
                    pass

    def record(self, skill: str, result: str = "success",
               duration_ms: int = 0, context: str = "",
               target: str = "", error: str = ""):
        """记录一次技能使用"""
        usage = SkillUsage(
            id=f"usage-{uuid.uuid4().hex[:8]}",
            skill=skill,
            timestamp=datetime.now(timezone.utc).isoformat(),
            result=result,
            duration_ms=duration_ms,
            context=context,
            target=target,
            error=error,
        )
        self.usages.append(usage)

        with open(USAGE_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(usage.to_dict(), ensure_ascii=False) + "\n")

    def get_skill_usages(self, skill: str) -> List[SkillUsage]:
        """获取某技能的所有使用记录"""
        return [u for u in self.usages if u.skill == skill]

    def get_all_skills(self) -> List[str]:
        """获取所有使用过的技能名"""
        return sorted(set(u.skill for u in self.usages))


# ── Scoring ─────────────────────────────────────────────────────────────────

def calculate_score(tracker: SkillTracker, skill: str) -> SkillScore:
    """计算技能评分"""
    usages = tracker.get_skill_usages(skill)

    if not usages:
        return SkillScore(
            skill=skill, total_uses=0, success_count=0, failure_count=0,
            success_rate=0, avg_duration_ms=0, last_used="", days_since_last_use=999,
            trend="unknown", composite_score=0,
        )

    total = len(usages)
    success = sum(1 for u in usages if u.result == "success")
    failure = sum(1 for u in usages if u.result == "failure")
    success_rate = success / total if total > 0 else 0

    durations = [u.duration_ms for u in usages if u.duration_ms > 0]
    avg_duration = sum(durations) / len(durations) if durations else 0

    # Last used
    timestamps = []
    for u in usages:
        try:
            timestamps.append(datetime.fromisoformat(u.timestamp))
        except Exception:
            pass

    last_used = max(timestamps) if timestamps else datetime.min.replace(tzinfo=timezone.utc)
    days_since = (datetime.now(timezone.utc) - last_used).total_seconds() / 86400

    # Trend: compare recent vs older usage
    now = datetime.now(timezone.utc)
    recent = [u for u in usages if u.timestamp > (now - timedelta(days=7)).isoformat()]
    older = [u for u in usages if u.timestamp <= (now - timedelta(days=7)).isoformat()
             and u.timestamp > (now - timedelta(days=30)).isoformat()]

    recent_rate = sum(1 for u in recent if u.result == "success") / len(recent) if recent else 0
    older_rate = sum(1 for u in older if u.result == "success") / len(older) if older else 0

    if recent and recent_rate > older_rate + 0.1:
        trend = "rising"
    elif older and recent_rate < older_rate - 0.1:
        trend = "declining"
    else:
        trend = "stable"

    # Composite score (0-100)
    # Factors: success rate (40%), recency (25%), frequency (20%), trend (15%)
    recency_score = max(0, 1 - (days_since / 30))  # 1.0 if used today, 0 if >30 days
    frequency_score = min(1, total / 20)  # 1.0 at 20+ uses
    trend_score = {"rising": 1.0, "stable": 0.7, "declining": 0.3, "unknown": 0.5}.get(trend, 0.5)

    composite = (
        success_rate * 40 +
        recency_score * 25 +
        frequency_score * 20 +
        trend_score * 15
    )

    return SkillScore(
        skill=skill,
        total_uses=total,
        success_count=success,
        failure_count=failure,
        success_rate=success_rate,
        avg_duration_ms=avg_duration,
        last_used=last_used.isoformat() if timestamps else "",
        days_since_last_use=days_since,
        trend=trend,
        composite_score=composite,
    )


# ── Recommendation Engine ───────────────────────────────────────────────────

def recommend_skills(context: str, tracker: SkillTracker,
                     limit: int = 5) -> List[Tuple[str, float, str]]:
    """根据上下文推荐技能

    Returns: List of (skill_name, relevance_score, reason)
    """
    context_lower = context.lower()
    words = set(context_lower.split())

    scores: Dict[str, float] = {}
    reasons: Dict[str, str] = {}

    # Keyword matching
    for skill, keywords in SKILL_CONTEXT_KEYWORDS.items():
        matched = [kw for kw in keywords if kw in context_lower or kw in words]
        if matched:
            keyword_score = len(matched) / len(keywords)
            scores[skill] = keyword_score
            reasons[skill] = f"Keywords: {', '.join(matched[:3])}"

    # Boost based on skill history (prefer skills that worked well)
    for skill in scores:
        score = calculate_score(tracker, skill)
        if score.total_uses > 0:
            history_boost = score.composite_score / 200  # 0-0.5 boost
            scores[skill] = scores.get(skill, 0) + history_boost
            if score.trend == "rising":
                reasons[skill] += " (trending up)"

    # Sort by score
    sorted_skills = sorted(scores.items(), key=lambda x: -x[1])

    return [
        (skill, score, reasons.get(skill, ""))
        for skill, score in sorted_skills[:limit]
    ]


# ── Pattern Detection ───────────────────────────────────────────────────────

def detect_patterns(tracker: SkillTracker) -> List[UsagePattern]:
    """检测使用模式"""
    patterns = []

    # Frequent combos: skills used within 5 minutes of each other
    sorted_usages = sorted(tracker.usages, key=lambda u: u.timestamp)
    combo_counts: Dict[Tuple[str, str], int] = defaultdict(int)

    for i in range(len(sorted_usages) - 1):
        u1 = sorted_usages[i]
        u2 = sorted_usages[i + 1]
        try:
            t1 = datetime.fromisoformat(u1.timestamp)
            t2 = datetime.fromisoformat(u2.timestamp)
            if (t2 - t1).total_seconds() < 300 and u1.skill != u2.skill:
                pair = tuple(sorted([u1.skill, u2.skill]))
                combo_counts[pair] += 1
        except Exception:
            pass

    for (s1, s2), count in combo_counts.items():
        if count >= 3:
            patterns.append(UsagePattern(
                pattern_type="frequent_combo",
                description=f"{s1} + {s2} used together {count} times",
                skills=[s1, s2],
                confidence=min(1.0, count / 10),
                suggestion=f"Consider creating a pipeline: {s1} -> {s2}",
            ))

    # Error clusters: skills with high failure rates
    for skill in tracker.get_all_skills():
        usages = tracker.get_skill_usages(skill)
        failures = [u for u in usages if u.result == "failure"]
        if len(usages) >= 5 and len(failures) / len(usages) > 0.3:
            error_msgs = [u.error for u in failures if u.error]
            common_errors = defaultdict(int)
            for msg in error_msgs:
                # Group by first 50 chars
                common_errors[msg[:50]] += 1

            top_error = max(common_errors.items(), key=lambda x: x[1]) if common_errors else ("", 0)

            patterns.append(UsagePattern(
                pattern_type="error_cluster",
                description=f"{skill} fails {len(failures)}/{len(usages)} times",
                skills=[skill],
                confidence=len(failures) / len(usages),
                suggestion=f"Common error: {top_error[0][:80]}" if top_error[0] else "Investigate failure patterns",
            ))

    # Time-based patterns: skills used at specific times
    hour_counts: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for u in tracker.usages:
        try:
            dt = datetime.fromisoformat(u.timestamp)
            hour_counts[u.skill][dt.hour] += 1
        except Exception:
            pass

    for skill, hours in hour_counts.items():
        if sum(hours.values()) >= 10:
            peak_hour = max(hours.items(), key=lambda x: x[1])
            if peak_hour[1] >= sum(hours.values()) * 0.4:
                patterns.append(UsagePattern(
                    pattern_type="time_based",
                    description=f"{skill} peaks at hour {peak_hour[0]} ({peak_hour[1]} uses)",
                    skills=[skill],
                    confidence=peak_hour[1] / sum(hours.values()),
                ))

    return sorted(patterns, key=lambda p: -p.confidence)


# ── Output ──────────────────────────────────────────────────────────────────

def print_stats(tracker: SkillTracker):
    """打印统计"""
    skills = tracker.get_all_skills()
    if not skills:
        print("No skill usage recorded yet.")
        return

    print("Skill Usage Statistics")
    print("=" * 60)

    for skill in skills:
        score = calculate_score(tracker, skill)
        bar = "#" * int(score.composite_score / 5)
        print(f"  {skill}")
        print(f"    Uses: {score.total_uses} (success: {score.success_count}, fail: {score.failure_count})")
        print(f"    Success rate: {score.success_rate * 100:.0f}%")
        print(f"    Score: {score.composite_score:.0f}/100 [{bar}]")
        print(f"    Trend: {score.trend}")
        if score.days_since_last_use < 999:
            print(f"    Last used: {score.days_since_last_use:.1f} days ago")
        print()


def print_history(tracker: SkillTracker, limit: int = 20):
    """打印历史"""
    usages = sorted(tracker.usages, key=lambda u: u.timestamp, reverse=True)[:limit]

    if not usages:
        print("No usage history.")
        return

    print("Skill Usage History")
    print("=" * 60)

    for u in usages:
        status = "OK" if u.result == "success" else "FAIL"
        ts = u.timestamp[:19].replace("T", " ")
        print(f"  [{status}] {u.skill} at {ts}")
        if u.context:
            print(f"    Context: {u.context}")
        if u.error:
            print(f"    Error: {u.error[:80]}")


def print_patterns(patterns: List[UsagePattern]):
    """打印模式"""
    if not patterns:
        print("No patterns detected yet. Need more usage data.")
        return

    print("Detected Patterns")
    print("=" * 60)

    for p in patterns:
        print(f"  [{p.pattern_type}] {p.description}")
        print(f"    Confidence: {p.confidence:.0%}")
        if p.suggestion:
            print(f"    Suggestion: {p.suggestion}")
        print()


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    tracker = SkillTracker()

    if cmd == "record":
        if len(sys.argv) < 3:
            print("Usage: skill-learn.py record <skill> [success|failure] [--context <text>]")
            return

        skill = sys.argv[2]
        result = "success"
        context = ""
        target = ""
        error = ""
        duration = 0

        args = sys.argv[3:]
        if args and args[0] in ("success", "failure", "partial"):
            result = args[0]
            args = args[1:]

        for i, arg in enumerate(args):
            if arg == "--context" and i + 1 < len(args):
                context = args[i + 1]
            elif arg == "--target" and i + 1 < len(args):
                target = args[i + 1]
            elif arg == "--error" and i + 1 < len(args):
                error = args[i + 1]
            elif arg == "--duration" and i + 1 < len(args):
                try:
                    duration = int(args[i + 1])
                except ValueError:
                    pass

        tracker.record(skill, result=result, duration_ms=duration,
                      context=context, target=target, error=error)
        print(f"Recorded: {skill} -> {result}")

    elif cmd == "recommend":
        if len(sys.argv) < 3:
            print("Usage: skill-learn.py recommend <context description>")
            return

        context = " ".join(sys.argv[2:])
        recommendations = recommend_skills(context, tracker)

        if not recommendations:
            print("No skills matched the context.")
            return

        print(f"Recommendations for: {context}")
        print("=" * 60)
        for skill, score, reason in recommendations:
            print(f"  {skill} (relevance: {score:.2f})")
            print(f"    {reason}")
            skill_score = calculate_score(tracker, skill)
            if skill_score.total_uses > 0:
                print(f"    Historical: {skill_score.success_rate * 100:.0f}% success, score {skill_score.composite_score:.0f}/100")
            print()

    elif cmd == "stats":
        print_stats(tracker)

    elif cmd == "history":
        limit = 20
        for i, arg in enumerate(sys.argv):
            if arg == "--limit" and i + 1 < len(sys.argv):
                try:
                    limit = int(sys.argv[i + 1])
                except ValueError:
                    pass
        print_history(tracker, limit=limit)

    elif cmd == "patterns":
        patterns = detect_patterns(tracker)
        print_patterns(patterns)

    elif cmd == "score":
        if len(sys.argv) < 3:
            print("Usage: skill-learn.py score <skill>")
            return

        skill = sys.argv[2]
        score = calculate_score(tracker, skill)

        print(f"Skill Score: {skill}")
        print("=" * 40)
        print(f"  Total uses: {score.total_uses}")
        print(f"  Success: {score.success_count} ({score.success_rate * 100:.0f}%)")
        print(f"  Failure: {score.failure_count}")
        print(f"  Avg duration: {score.avg_duration_ms:.0f}ms")
        print(f"  Last used: {score.days_since_last_use:.1f} days ago")
        print(f"  Trend: {score.trend}")
        print(f"  Composite score: {score.composite_score:.0f}/100")

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
