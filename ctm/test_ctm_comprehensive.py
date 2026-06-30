#!/usr/bin/env python3
"""
鲤鱼 CTM 引擎 — 全面测试套件
覆盖：功能测试、边界情况、错误处理、性能、集成
"""

import sys
import time
import math
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ctm import (
    ThinkingStreamEngine, ThinkingStream, ThinkingNode, ThinkingState,
    AdaptiveComputeTimer, ComplexityEstimate, ComputeBudget, ComputeStrategy, STRATEGIES,
    OscillatorSyncModule, OscillatorPhase, SyncEvent, MODULE_OSCILLATORS,
    CTMCore, CTMConfig, CTMState
)

# ─── 测试基础设施 ───────────────────────────────────────────

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.suite_name = ""

    def ok(self, name):
        self.passed += 1
        print(f"    PASS  {name}")

    def fail(self, name, msg):
        self.failed += 1
        self.errors.append((name, msg))
        print(f"    FAIL  {name}: {msg}")

    def summary(self):
        total = self.passed + self.failed
        status = "ALL PASS" if self.failed == 0 else f"{self.failed} FAILED"
        print(f"\n  [{self.suite_name}] {self.passed}/{total} — {status}")
        for name, msg in self.errors:
            print(f"    - {name}: {msg}")
        return self.failed == 0


def assert_eq(result, expected, r: TestResult, name: str):
    if result == expected:
        r.ok(name)
    else:
        r.fail(name, f"expected {expected!r}, got {result!r}")

def assert_true(val, r: TestResult, name: str):
    if val:
        r.ok(name)
    else:
        r.fail(name, f"expected truthy, got {val!r}")

def assert_false(val, r: TestResult, name: str):
    if not val:
        r.ok(name)
    else:
        r.fail(name, f"expected falsy, got {val!r}")

def assert_range(val, lo, hi, r: TestResult, name: str):
    if lo <= val <= hi:
        r.ok(name)
    else:
        r.fail(name, f"expected [{lo}, {hi}], got {val}")

def assert_raises(fn, exc_type, r: TestResult, name: str):
    try:
        fn()
        r.fail(name, f"expected {exc_type.__name__} but no exception raised")
    except exc_type:
        r.ok(name)
    except Exception as e:
        r.fail(name, f"expected {exc_type.__name__}, got {type(e).__name__}: {e}")


# ═════════════════════════════════════════════════════════════
# SUITE 1: ThinkingStream — 功能测试
# ═════════════════════════════════════════════════════════════

def suite_thinking_stream_functional():
    r = TestResult()
    r.suite_name = "ThinkingStream 功能测试"

    # -- 基本创建与状态
    engine = ThinkingStreamEngine()
    stream = engine.create_stream("测试查询", session_id="s1")
    assert_true(stream.stream_id.startswith("stream-"), r, "stream_id 格式")
    assert_eq(stream.session_id, "s1", r, "session_id 传递")
    assert_eq(stream.query, "测试查询", r, "query 传递")
    assert_eq(stream.current_state, ThinkingState.FLOWING, r, "创建后状态为 FLOWING")
    assert_eq(len(stream.nodes), 1, r, "创建时含 1 个初始节点")
    assert_eq(stream.nodes[0].state, ThinkingState.INIT, r, "初始节点状态 INIT")

    # -- 推进思维
    n1 = engine.advance_stream(stream.stream_id, "第一步")
    assert_eq(n1.depth, 1, r, "自动深度递增")
    assert_range(n1.confidence, 0, 1, r, "置信度范围 [0,1]")
    assert_eq(n1.parent_id, stream.nodes[0].id, r, "parent_id 指向初始节点")
    assert_true(n1.id in stream.nodes[0].children_ids, r, "父节点 children_ids 更新")

    n2 = engine.advance_stream(stream.stream_id, "第二步")
    assert_eq(n2.depth, 2, r, "深度继续递增")
    assert_true(n2.confidence > n1.confidence, r, "置信度随深度增长")

    # -- 节点 ID 唯一性
    ids = {n.id for n in stream.nodes}
    assert_eq(len(ids), len(stream.nodes), r, "所有节点 ID 唯一")

    # -- token_estimate
    node_long = engine.advance_stream(stream.stream_id, "A" * 100)
    assert_eq(node_long.token_estimate, 25, r, "token_estimate = len//4")

    # -- get_current_node
    assert_eq(engine.get_stream(stream.stream_id).get_current_node().id, node_long.id, r, "get_current_node 返回最新节点")

    # -- get_depth_nodes
    depth0 = stream.get_depth_nodes(0)
    assert_eq(len(depth0), 1, r, "depth 0 只有初始节点")
    depth1 = stream.get_depth_nodes(1)
    assert_eq(len(depth1), 1, r, "depth 1 有 1 个节点")

    # -- 完成思维流
    summary = engine.complete_stream(stream.stream_id, "最终总结")
    assert_true(summary is not None, r, "complete_stream 返回摘要")
    assert_eq(summary["state"], "completed", r, "完成后状态为 completed")
    assert_true(stream.nodes[-1].metadata.get("type") == "summary", r, "总结节点 metadata 标记")

    # -- 完成后再推进应仍可返回节点（无锁保护，设计如此）
    extra = engine.advance_stream(stream.stream_id, "额外内容")
    assert_true(extra is not None, r, "完成后仍可 advance（无状态锁）")

    return r


# ═════════════════════════════════════════════════════════════
# SUITE 2: ThinkingStream — 边界情况
# ═════════════════════════════════════════════════════════════

def suite_thinking_stream_edge_cases():
    r = TestResult()
    r.suite_name = "ThinkingStream 边界情况"

    engine = ThinkingStreamEngine()

    # -- 不存在的 stream_id
    assert_true(engine.get_stream("nonexistent") is None, r, "get_stream 不存在返回 None")
    assert_true(engine.advance_stream("nonexistent", "x") is None, r, "advance 不存在返回 None")
    assert_true(engine.complete_stream("nonexistent") is None, r, "complete 不存在返回 None")
    assert_false(engine.interrupt_stream("nonexistent"), r, "interrupt 不存在返回 False")
    assert_false(engine.resume_stream("nonexistent"), r, "resume 不存在返回 False")

    # -- 空内容
    s = engine.create_stream("")
    assert_eq(s.query, "", r, "空查询可创建")
    n = engine.advance_stream(s.stream_id, "")
    assert_eq(n.token_estimate, 0, r, "空内容 token_estimate=0")

    # -- 极长内容
    long_content = "x" * 100000
    n = engine.advance_stream(s.stream_id, long_content)
    assert_eq(n.token_estimate, 25000, r, "极长内容 token_estimate 正确")

    # -- 中断与恢复
    s2 = engine.create_stream("中断测试")
    assert_true(engine.interrupt_stream(s2.stream_id, "用户取消"), r, "中断成功")
    assert_eq(s2.current_state, ThinkingState.INTERRUPTED, r, "中断后状态")
    assert_true(engine.interrupt_stream(s2.stream_id), r, "重复中断不报错")

    assert_true(engine.resume_stream(s2.stream_id), r, "恢复成功")
    assert_eq(s2.current_state, ThinkingState.FLOWING, r, "恢复后状态 FLOWING")

    # -- 非中断状态恢复
    assert_false(engine.resume_stream(s2.stream_id), r, "非中断状态恢复返回 False")

    # -- 分支计数
    s3 = engine.create_stream("分支测试")
    init_node = s3.nodes[0]
    child1 = engine.advance_stream(s3.stream_id, "子1", parent_id=init_node.id)
    child2 = engine.advance_stream(s3.stream_id, "子2", parent_id=init_node.id)
    assert_eq(s3.branch_count, 2, r, "branch_count 正确递增")
    assert_eq(len(init_node.children_ids), 2, r, "父节点有 2 个子节点")

    # -- max_depth 更新
    engine.advance_stream(s3.stream_id, "深层", depth=10)
    assert_eq(s3.max_depth, 10, r, "max_depth 正确更新")

    # -- get_summary 结构完整
    summary = s3.get_summary()
    for key in ["stream_id", "session_id", "query", "state", "nodes_count",
                "total_tokens", "max_depth", "branch_count", "duration_seconds", "last_activity"]:
        assert_true(key in summary, r, f"summary 包含 {key}")

    # -- 清理旧流
    engine2 = ThinkingStreamEngine()
    old_stream = engine2.create_stream("旧流")
    old_stream.last_activity = time.time() - 25 * 3600  # 25 小时前
    new_stream = engine2.create_stream("新流")
    cleaned = engine2.cleanup_old_streams(max_age_hours=24)
    assert_eq(cleaned, 1, r, "清理 1 个旧流")
    assert_true(engine2.get_stream(old_stream.stream_id) is None, r, "旧流已删除")
    assert_true(engine2.get_stream(new_stream.stream_id) is not None, r, "新流保留")

    return r


# ═════════════════════════════════════════════════════════════
# SUITE 3: ThinkingNode — 序列化
# ═════════════════════════════════════════════════════════════

def suite_thinking_node_serialization():
    r = TestResult()
    r.suite_name = "ThinkingNode 序列化"

    node = ThinkingNode(
        id="node-test",
        content="测试内容",
        state=ThinkingState.DEEPENING,
        depth=3,
        confidence=0.75,
        parent_id="node-parent",
        children_ids=["child-1", "child-2"],
        timestamp=1234567890.0,
        token_estimate=5,
        metadata={"key": "value"}
    )

    d = node.to_dict()
    assert_eq(d["id"], "node-test", r, "to_dict id")
    assert_eq(d["state"], "deepening", r, "to_dict state 为 value")
    assert_eq(d["children_ids"], ["child-1", "child-2"], r, "to_dict children_ids")

    # 反序列化
    node2 = ThinkingNode.from_dict(d)
    assert_eq(node2.id, node.id, r, "from_dict id")
    assert_eq(node2.state, node.state, r, "from_dict state")
    assert_eq(node2.depth, node.depth, r, "from_dict depth")
    assert_eq(node2.confidence, node.confidence, r, "from_dict confidence")
    assert_eq(node2.metadata, node.metadata, r, "from_dict metadata")

    # 缺少可选字段
    minimal = {"id": "x", "content": "y", "state": "init", "depth": 0,
               "confidence": 0.5, "timestamp": 0.0, "token_estimate": 0}
    node3 = ThinkingNode.from_dict(minimal)
    assert_true(node3.parent_id is None, r, "from_dict 缺 parent_id 默认 None")
    assert_eq(node3.children_ids, [], r, "from_dict 缺 children_ids 默认 []")
    assert_eq(node3.metadata, {}, r, "from_dict 缺 metadata 默认 {}")

    return r


# ═════════════════════════════════════════════════════════════
# SUITE 4: ThinkingStreamEngine — 中断/恢复/多流
# ═════════════════════════════════════════════════════════════

def suite_thinking_stream_engine_advanced():
    r = TestResult()
    r.suite_name = "ThinkingStreamEngine 高级功能"

    engine = ThinkingStreamEngine()

    # -- 多流并存
    s1 = engine.create_stream("流1", session_id="a")
    s2 = engine.create_stream("流2", session_id="b")
    s3 = engine.create_stream("流3", session_id="a")
    assert_eq(len(engine.streams), 3, r, "3 个流并存")

    all_summaries = engine.get_all_streams()
    assert_eq(len(all_summaries), 3, r, "get_all_streams 返回 3 个")

    # -- 中断带 reason
    engine.interrupt_stream(s1.stream_id, "timeout")
    assert_eq(s1.current_state, ThinkingState.INTERRUPTED, r, "中断状态")
    last_node = s1.nodes[-1]
    assert_true("timeout" in last_node.content, r, "中断原因写入节点")
    assert_eq(last_node.metadata["type"], "interruption", r, "中断节点 metadata")
    assert_eq(last_node.confidence, 0.0, r, "中断节点置信度=0")

    # -- 恢复
    assert_true(engine.resume_stream(s1.stream_id), r, "恢复成功")
    assert_eq(s1.current_state, ThinkingState.FLOWING, r, "恢复后 FLOWING")

    # -- advance 自动计算深度和置信度
    node = engine.advance_stream(s2.stream_id, "自动深度")
    assert_true(node.depth > 0, r, "自动深度 > 0")
    assert_range(node.confidence, 0, 1, r, "自动置信度在范围内")

    # -- 深度 > 3 触发 DEEPENING
    deep_stream = engine.create_stream("深度测试")
    engine.advance_stream(deep_stream.stream_id, "d1", depth=1)
    engine.advance_stream(deep_stream.stream_id, "d2", depth=2)
    engine.advance_stream(deep_stream.stream_id, "d3", depth=3)
    engine.advance_stream(deep_stream.stream_id, "d4", depth=4)
    assert_eq(deep_stream.current_state, ThinkingState.DEEPENING, r, "depth>3 触发 DEEPENING")

    # -- 高置信度触发 CONVERGING
    conv_stream = engine.create_stream("收敛测试")
    engine.advance_stream(conv_stream.stream_id, "高置信", confidence=0.85)
    assert_eq(conv_stream.current_state, ThinkingState.CONVERGING, r, "confidence>0.8 触发 CONVERGING")

    return r


# ═════════════════════════════════════════════════════════════
# SUITE 5: AdaptiveComputeTimer — 功能测试
# ═════════════════════════════════════════════════════════════

def suite_adaptive_compute_functional():
    r = TestResult()
    r.suite_name = "AdaptiveComputeTimer 功能测试"

    timer = AdaptiveComputeTimer()

    # -- 简单查询
    c = timer.estimate_complexity("查看代码")
    assert_range(c.overall_complexity, 0, 0.5, r, "简单查询复杂度 < 0.5")
    assert_false(c.requires_reasoning, r, "简单查询不需要推理")

    # -- 复杂查询
    c = timer.estimate_complexity("分析并优化系统架构，比较不同策略的性能，评估可扩展性")
    assert_true(c.overall_complexity > 0.3, r, "复杂查询复杂度较高")
    assert_true(c.semantic_depth >= 3, r, "复杂查询语义深度 >= 3")

    # -- 推理查询
    c = timer.estimate_complexity("如果 A 那么 B，因为 C 所以 D，证明 E")
    assert_true(c.requires_reasoning, r, "推理查询标记正确")

    # -- 领域专业性
    c = timer.estimate_complexity("优化数据库查询的索引策略")
    assert_true(c.domain_specificity > 0, r, "领域关键词命中")

    # -- 策略分配
    for strategy in ComputeStrategy:
        budget = STRATEGIES[strategy]
        assert_true(budget.max_tokens > 0, r, f"{strategy.value} max_tokens > 0")
        assert_true(budget.max_depth > 0, r, f"{strategy.value} max_depth > 0")
        assert_true(budget.timeout_seconds > 0, r, f"{strategy.value} timeout > 0")
        assert_range(budget.early_stop_threshold, 0, 1, r, f"{strategy.value} threshold [0,1]")

    # -- 策略梯度：QUICK < STANDARD < DEEP < EXHAUSTIVE
    assert_true(STRATEGIES[ComputeStrategy.QUICK].max_tokens < STRATEGIES[ComputeStrategy.STANDARD].max_tokens, r, "QUICK < STANDARD tokens")
    assert_true(STRATEGIES[ComputeStrategy.STANDARD].max_tokens < STRATEGIES[ComputeStrategy.DEEP].max_tokens, r, "STANDARD < DEEP tokens")
    assert_true(STRATEGIES[ComputeStrategy.DEEP].max_tokens < STRATEGIES[ComputeStrategy.EXHAUSTIVE].max_tokens, r, "DEEP < EXHAUSTIVE tokens")

    # -- should_continue 边界
    budget = STRATEGIES[ComputeStrategy.STANDARD]
    cont, reason = timer.should_continue(0, 0, 0.5, 0.0, budget)
    assert_true(cont, r, "初始状态应继续")

    cont, reason = timer.should_continue(budget.max_depth, 0, 0.5, 0.0, budget)
    assert_false(cont, r, "达到最大深度应停止")

    cont, reason = timer.should_continue(0, budget.max_tokens, 0.5, 0.0, budget)
    assert_false(cont, r, "达到 token 限制应停止")

    cont, reason = timer.should_continue(0, 0, 0.5, budget.timeout_seconds, budget)
    assert_false(cont, r, "超时应停止")

    cont, reason = timer.should_continue(0, 0, budget.early_stop_threshold, 0.0, budget)
    assert_false(cont, r, "达到置信度阈值应停止")

    # -- overall_complexity 计算验证
    ce = ComplexityEstimate(
        lexical_complexity=1.0, syntactic_complexity=1.0,
        semantic_depth=5, domain_specificity=1.0,
        requires_reasoning=True, estimated_tokens=100, confidence=1.0
    )
    assert_range(ce.overall_complexity, 0.9, 1.1, r, "最大复杂度 ~1.0")

    ce_min = ComplexityEstimate(
        lexical_complexity=0.0, syntactic_complexity=0.0,
        semantic_depth=1, domain_specificity=0.0,
        requires_reasoning=False, estimated_tokens=10, confidence=0.0
    )
    assert_range(ce_min.overall_complexity, 0.0, 0.1, r, "最小复杂度 ~0.06")

    return r


# ═════════════════════════════════════════════════════════════
# SUITE 6: AdaptiveComputeTimer — 边界情况
# ═════════════════════════════════════════════════════════════

def suite_adaptive_compute_edge_cases():
    r = TestResult()
    r.suite_name = "AdaptiveComputeTimer 边界情况"

    timer = AdaptiveComputeTimer()

    # -- 空字符串
    c = timer.estimate_complexity("")
    assert_eq(c.lexical_complexity, 0.0, r, "空字符串词汇复杂度=0")
    assert_eq(c.syntactic_complexity, 0.0, r, "空字符串句法复杂度=0")

    # -- 单字符
    c = timer.estimate_complexity("a")
    assert_true(c.lexical_complexity >= 0, r, "单字符词汇复杂度 >= 0")

    # -- 上下文调整：O2 压力
    c = timer.estimate_complexity("测试查询")
    budget_normal = timer.allocate_budget(c)
    budget_stressed = timer.allocate_budget(c, context={"o2_pressure": 80})
    assert_true(budget_stressed.max_tokens < budget_normal.max_tokens, r, "O2 压力高时减少 tokens")

    # -- 上下文调整：时间压力
    budget_time = timer.allocate_budget(c, context={"time_pressure": 0.9})
    assert_eq(budget_time.strategy, ComputeStrategy.QUICK, r, "时间压力高时 QUICK 策略")

    # -- 统计
    assert_eq(timer.get_statistics()["total"], 0, r, "初始统计 total=0")
    timer.record_outcome("q1", c, budget_normal)
    stats = timer.get_statistics()
    assert_eq(stats["total"], 1, r, "记录后 total=1")
    assert_true("avg_complexity" in stats, r, "统计包含 avg_complexity")

    # -- ComplexityEstimate.to_dict 四舍五入
    ce = ComplexityEstimate(
        lexical_complexity=0.123456, syntactic_complexity=0.789012,
        semantic_depth=3, domain_specificity=0.555555,
        requires_reasoning=True, estimated_tokens=100, confidence=0.999999
    )
    d = ce.to_dict()
    assert_eq(d["lexical_complexity"], 0.123, r, "to_dict 四舍五入 3 位")
    assert_eq(d["confidence"], 1.0, r, "to_dict confidence 四舍五入")

    return r


# ═════════════════════════════════════════════════════════════
# SUITE 7: OscillatorSyncModule — 功能测试
# ═════════════════════════════════════════════════════════════

def suite_oscillator_functional():
    r = TestResult()
    r.suite_name = "OscillatorSyncModule 功能测试"

    sync = OscillatorSyncModule()

    # -- 默认注册 8 个模块
    assert_eq(len(sync.oscillators), len(MODULE_OSCILLATORS), r, "默认注册 8 个振荡器")
    for mid in MODULE_OSCILLATORS:
        assert_true(mid in sync.oscillators, r, f"注册模块 {mid}")

    # -- sync_tick 推进相位
    old_phases = {mid: osc.phase for mid, osc in sync.oscillators.items()}
    sync.sync_tick(0.1)
    for mid, osc in sync.oscillators.items():
        if osc.frequency > 0:
            assert_true(osc.phase != old_phases[mid] or osc.frequency == 0, r, f"{mid} 相位变化")

    # -- 相位归一化到 [0, 2π)
    for _ in range(100):
        sync.sync_tick(1.0)
    for mid, osc in sync.oscillators.items():
        assert_range(osc.phase, 0.0, 2 * math.pi + 0.001, r, f"{mid} 相位在 [0, 2π)")

    # -- compute_phase_coherence 范围
    coherence = sync.compute_phase_coherence()
    assert_range(coherence, 0.0, 1.0, r, "coherence 范围 [0, 1]")

    # -- 单模块一致性 = 1.0
    single = OscillatorSyncModule()
    single.oscillators = {"only": OscillatorPhase("only", 1.0, 1.0, 1.0, time.time())}
    assert_eq(single.compute_phase_coherence(), 1.0, r, "单模块 coherence=1.0")

    # -- 空振荡器一致性 = 1.0
    empty = OscillatorSyncModule()
    empty.oscillators = {}
    assert_eq(empty.compute_phase_coherence(), 1.0, r, "空模块 coherence=1.0")

    # -- register / unregister
    sync.register_module("new_module", {"base_freq": 1.0, "phase": 0.0, "amplitude": 0.5})
    assert_true("new_module" in sync.oscillators, r, "register 成功")
    sync.unregister_module("new_module")
    assert_false("new_module" in sync.oscillators, r, "unregister 成功")
    sync.unregister_module("nonexistent")  # 不应报错

    # -- adjust_frequency / adjust_amplitude
    sync.adjust_frequency("thinking_stream", 5.0)
    assert_eq(sync.oscillators["thinking_stream"].frequency, 5.0, r, "adjust_frequency 成功")
    sync.adjust_amplitude("thinking_stream", 0.1)
    assert_eq(sync.oscillators["thinking_stream"].amplitude, 0.1, r, "adjust_amplitude 成功")

    # -- get_phase_offsets 归一化到 [-π, π]
    offsets = sync.get_phase_offsets()
    for mid, offset in offsets.items():
        assert_range(offset, -math.pi - 0.001, math.pi + 0.001, r, f"{mid} offset in [-π, π]")

    # -- emit_sync_event
    event = sync.emit_sync_event()
    assert_true(isinstance(event, SyncEvent), r, "emit_sync_event 返回 SyncEvent")
    assert_true(0 <= event.coherence <= 1, r, "event coherence 范围")
    assert_true(len(event.modules) > 0, r, "event modules 非空")

    # -- sync_history 上限 100
    for _ in range(110):
        sync.emit_sync_event()
    assert_true(len(sync.sync_history) <= 100, r, "sync_history 上限 100")

    return r


# ═════════════════════════════════════════════════════════════
# SUITE 8: OscillatorSyncModule — 漂移检测与持久化
# ═════════════════════════════════════════════════════════════

def suite_oscillator_advanced():
    r = TestResult()
    r.suite_name = "OscillatorSyncModule 高级功能"

    # -- 漂移检测
    sync = OscillatorSyncModule()
    # 人为制造大偏移
    sync.oscillators["thinking_stream"].phase = 0.0
    sync.oscillators["chronos"].phase = math.pi
    drifts = sync.detect_drift(threshold=0.5)
    assert_true(len(drifts) > 0, r, "检测到漂移")
    for d in drifts:
        assert_true("module" in d, r, "漂移包含 module")
        assert_true("offset" in d, r, "漂移包含 offset")
        assert_true("severity" in d, r, "漂移包含 severity")
        assert_true(d["severity"] in ("high", "medium"), r, "severity 合法")

    # -- get_sync_stats 空历史
    sync2 = OscillatorSyncModule()
    stats = sync2.get_sync_stats()
    assert_eq(stats["sync_events"], 0, r, "空历史 sync_events=0")
    assert_true("modules" in stats, r, "stats 包含 modules")

    # -- get_sync_stats 有历史
    sync2.emit_sync_event()
    sync2.emit_sync_event()
    stats = sync2.get_sync_stats()
    assert_eq(stats["sync_events"], 2, r, "sync_events=2")
    assert_true("avg_coherence" in stats, r, "stats 包含 avg_coherence")
    assert_true("min_coherence" in stats, r, "stats 包含 min_coherence")
    assert_true("max_coherence" in stats, r, "stats 包含 max_coherence")

    # -- 持久化 save/load
    sync3 = OscillatorSyncModule()
    sync3.sync_tick(0.5)
    sync3.emit_sync_event()

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        tmppath = f.name
    try:
        sync3.save_state(tmppath)
        assert_true(Path(tmppath).exists(), r, "save_state 创建文件")

        sync4 = OscillatorSyncModule()
        sync4.load_state(tmppath)
        assert_eq(len(sync4.oscillators), len(sync3.oscillators), r, "load_state 恢复振荡器数")
        for mid in sync3.oscillators:
            assert_true(mid in sync4.oscillators, r, f"load_state 恢复 {mid}")
            assert_eq(round(sync4.oscillators[mid].phase, 4),
                      round(sync3.oscillators[mid].phase, 4), r, f"load_state 恢复 {mid} 相位")
    finally:
        Path(tmppath).unlink(missing_ok=True)

    # -- load 不存在的文件
    sync5 = OscillatorSyncModule()
    sync5.load_state("/tmp/nonexistent_liyu_ctm_test.json")
    assert_true(True, r, "load 不存在文件不崩溃")

    return r


# ═════════════════════════════════════════════════════════════
# SUITE 9: CTMCore — 功能测试
# ═════════════════════════════════════════════════════════════

def suite_ctm_core_functional():
    r = TestResult()
    r.suite_name = "CTMCore 功能测试"

    config = CTMConfig(
        enable_thinking_stream=True,
        enable_adaptive_compute=True,
        enable_oscillator_sync=True,
        max_concurrent_streams=5
    )
    ctm = CTMCore(config)

    # -- 启动思维流
    sid = ctm.start_thinking("测试查询", session_id="s1")
    assert_true(sid is not None, r, "start_thinking 返回 stream_id")
    assert_true(sid.startswith("stream-"), r, "stream_id 格式")

    # -- 推进思维
    node = ctm.advance_thinking(sid, "步骤1")
    assert_true(node is not None, r, "advance_thinking 返回节点")
    assert_true("depth" in node, r, "节点包含 depth")
    assert_true("confidence" in node, r, "节点包含 confidence")

    # -- 获取状态
    state = ctm.get_thinking_state(sid)
    assert_true(state is not None, r, "get_thinking_state 返回状态")
    assert_true("coherence" in state, r, "状态包含 coherence")

    # -- 完成思维
    summary = ctm.complete_thinking(sid, "总结")
    assert_true(summary is not None, r, "complete_thinking 返回摘要")

    # -- 完成后获取状态
    state2 = ctm.get_thinking_state(sid)
    assert_true(state2 is not None, r, "完成后仍可获取状态")

    # -- 事件日志
    events = ctm.get_event_log()
    assert_true(len(events) > 0, r, "事件日志非空")
    for e in events:
        assert_true("timestamp" in e, r, "事件包含 timestamp")
        assert_true("level" in e, r, "事件包含 level")
        assert_true("message" in e, r, "事件包含 message")

    # -- CTM 状态
    ctm_state = ctm.get_ctm_state()
    assert_true(isinstance(ctm_state, CTMState), r, "get_ctm_state 返回 CTMState")
    assert_true(ctm_state.active_streams >= 0, r, "active_streams >= 0")
    assert_true(ctm_state.total_streams_created >= 1, r, "total_streams_created >= 1")

    # -- 事件日志上限
    for i in range(1010):
        ctm._log_event("test", f"event {i}")
    assert_true(len(ctm.event_log) <= 1000, r, "事件日志上限 1000")

    return r


# ═════════════════════════════════════════════════════════════
# SUITE 10: CTMCore — 边界情况与错误处理
# ═════════════════════════════════════════════════════════════

def suite_ctm_core_edge_cases():
    r = TestResult()
    r.suite_name = "CTMCore 边界情况"

    # -- 并发限制
    config = CTMConfig(max_concurrent_streams=2)
    ctm = CTMCore(config)
    s1 = ctm.start_thinking("流1")
    s2 = ctm.start_thinking("流2")
    s3 = ctm.start_thinking("流3")
    assert_true(s1 is not None, r, "第 1 个流启动成功")
    assert_true(s2 is not None, r, "第 2 个流启动成功")
    assert_true(s3 is None, r, "第 3 个流被限制拒绝")

    # -- 禁用子模块
    config_no_ts = CTMConfig(enable_thinking_stream=False)
    ctm2 = CTMCore(config_no_ts)
    assert_true(ctm2.start_thinking("test") is None, r, "禁用 thinking_stream 返回 None")
    assert_true(ctm2.advance_thinking("x", "y") is None, r, "禁用时 advance 返回 None")
    assert_true(ctm2.complete_thinking("x") is None, r, "禁用时 complete 返回 None")
    assert_false(ctm2.interrupt_thinking("x"), r, "禁用时 interrupt 返回 False")
    assert_true(ctm2.get_thinking_state("x") is None, r, "禁用时 get_state 返回 None")
    assert_eq(ctm2.get_all_streams(), [], r, "禁用时 get_all_streams 返回 []")

    config_no_ac = CTMConfig(enable_adaptive_compute=False)
    ctm3 = CTMCore(config_no_ac)
    sid3 = ctm3.start_thinking("无自适应计算")
    assert_true(sid3 is not None, r, "禁用 adaptive_compute 仍可启动流")

    config_no_os = CTMConfig(enable_oscillator_sync=False)
    ctm4 = CTMCore(config_no_os)
    sid4 = ctm4.start_thinking("无振荡同步")
    assert_true(sid4 is not None, r, "禁用 oscillator_sync 仍可启动流")

    # -- 不存在的 stream_id
    assert_true(ctm.advance_thinking("nonexistent", "x") is None, r, "advance 不存在返回 None")
    assert_true(ctm.complete_thinking("nonexistent") is None, r, "complete 不存在返回 None")
    assert_false(ctm.interrupt_thinking("nonexistent"), r, "interrupt 不存在返回 False")
    assert_true(ctm.get_thinking_state("nonexistent") is None, r, "get_state 不存在返回 None")

    # -- cleanup
    cleaned = ctm.cleanup()
    assert_true(isinstance(cleaned, int), r, "cleanup 返回 int")

    # -- get_event_log limit
    ctm._log_event("test", "msg")
    limited = ctm.get_event_log(limit=1)
    assert_eq(len(limited), 1, r, "get_event_log limit=1")

    # -- CTMConfig.to_dict
    cfg = CTMConfig()
    d = cfg.to_dict()
    assert_true("enable_thinking_stream" in d, r, "config to_dict 包含 enable_thinking_stream")
    assert_true("max_concurrent_streams" in d, r, "config to_dict 包含 max_concurrent_streams")

    return r


# ═════════════════════════════════════════════════════════════
# SUITE 11: CTMCore — 集成测试（完整工作流）
# ═════════════════════════════════════════════════════════════

def suite_ctm_core_integration():
    r = TestResult()
    r.suite_name = "CTMCore 集成测试"

    ctm = CTMCore(CTMConfig())

    # -- record_outcome 验证（complexity 存储修复）
    assert_eq(ctm.compute_timer.get_statistics()["total"], 0, r, "集成: 初始记录数=0")
    sid_r = ctm.start_thinking("分析系统架构")
    ctm.advance_thinking(sid_r, "步骤1")
    ctm.complete_thinking(sid_r, "完成")
    stats = ctm.compute_timer.get_statistics()
    assert_eq(stats["total"], 1, r, "集成: complete 后 record_outcome 被调用")

    # -- 完整工作流：启动 -> 推进 -> 完成
    sid = ctm.start_thinking("如何设计高可用架构？")
    assert_true(sid is not None, r, "集成: 启动成功")

    for i in range(5):
        node = ctm.advance_thinking(sid, f"思考步骤 {i+1}")
        assert_true(node is not None, r, f"集成: 推进步骤 {i+1}")

    state = ctm.get_thinking_state(sid)
    assert_eq(state["nodes_count"], 6, r, "集成: 6 个节点（1 初始 + 5 推进）")

    summary = ctm.complete_thinking(sid, "综合分析完成")
    assert_true(summary is not None, r, "集成: 完成成功")

    # -- 完整工作流：启动 -> 中断 -> 恢复 -> 完成
    sid2 = ctm.start_thinking("中断恢复测试")
    ctm.advance_thinking(sid2, "步骤1")
    ctm.advance_thinking(sid2, "步骤2")

    assert_true(ctm.interrupt_thinking(sid2, "用户暂停"), r, "集成: 中断成功")
    state2 = ctm.get_thinking_state(sid2)
    assert_eq(state2["state"], "interrupted", r, "集成: 中断状态")

    # 恢复（通过底层 engine）
    stream = ctm.thinking_engine.get_stream(sid2)
    stream.current_state = ThinkingState.FLOWING
    ctm.advance_thinking(sid2, "恢复后继续")
    summary2 = ctm.complete_thinking(sid2)
    assert_true(summary2 is not None, r, "集成: 中断恢复后完成")

    # -- 多流并存
    streams = []
    for i in range(3):
        sid = ctm.start_thinking(f"并行流 {i}")
        streams.append(sid)

    all_streams = ctm.get_all_streams()
    assert_eq(len(all_streams), 6, r, "集成: 6 个流并存（3 已完成 + 3 活跃）")

    # -- CTM 状态包含所有信息
    ctm_state = ctm.get_ctm_state()
    assert_true(ctm_state.total_streams_created >= 5, r, "集成: 总创建数 >= 5")
    assert_range(ctm_state.current_coherence, 0, 1, r, "集成: coherence 范围")

    return r


# ═════════════════════════════════════════════════════════════
# SUITE 12: 性能测试
# ═════════════════════════════════════════════════════════════

def suite_performance():
    r = TestResult()
    r.suite_name = "性能测试"

    # -- 思维流创建性能：1000 个流 < 2 秒
    engine = ThinkingStreamEngine()
    t0 = time.time()
    for i in range(1000):
        engine.create_stream(f"查询 {i}")
    elapsed = time.time() - t0
    assert_true(elapsed < 2.0, r, f"创建 1000 流耗时 {elapsed:.3f}s < 2s")

    # -- 节点添加性能：10000 个节点 < 2 秒
    stream = engine.create_stream("性能测试流")
    t0 = time.time()
    for i in range(10000):
        engine.advance_stream(stream.stream_id, f"节点 {i}")
    elapsed = time.time() - t0
    assert_true(elapsed < 2.0, r, f"添加 10000 节点耗时 {elapsed:.3f}s < 2s")

    # -- 复杂度评估性能：1000 次 < 1 秒
    timer = AdaptiveComputeTimer()
    t0 = time.time()
    for i in range(1000):
        timer.estimate_complexity("分析并优化系统架构，比较不同策略的性能")
    elapsed = time.time() - t0
    assert_true(elapsed < 1.0, r, f"1000 次复杂度评估耗时 {elapsed:.3f}s < 1s")

    # -- 振荡器同步性能：10000 次 tick < 2 秒
    sync = OscillatorSyncModule()
    t0 = time.time()
    for i in range(10000):
        sync.sync_tick(0.01)
    elapsed = time.time() - t0
    assert_true(elapsed < 2.0, r, f"10000 次 sync_tick 耗时 {elapsed:.3f}s < 2s")

    # -- 相位一致性计算性能：10000 次 < 2 秒
    t0 = time.time()
    for i in range(10000):
        sync.compute_phase_coherence()
    elapsed = time.time() - t0
    assert_true(elapsed < 2.0, r, f"10000 次 coherence 计算耗时 {elapsed:.3f}s < 2s")

    # -- CTM 完整流程性能：100 次完整生命周期 < 5 秒
    ctm = CTMCore(CTMConfig())
    t0 = time.time()
    for i in range(100):
        sid = ctm.start_thinking(f"性能测试 {i}")
        if sid:
            for j in range(5):
                ctm.advance_thinking(sid, f"步骤 {j}")
            ctm.complete_thinking(sid, f"总结 {i}")
    elapsed = time.time() - t0
    assert_true(elapsed < 5.0, r, f"100 次完整流程耗时 {elapsed:.3f}s < 5s")

    # -- get_all_streams 性能
    t0 = time.time()
    for _ in range(1000):
        engine.get_all_streams()
    elapsed = time.time() - t0
    assert_true(elapsed < 1.0, r, f"1000 次 get_all_streams 耗时 {elapsed:.3f}s < 1s")

    return r


# ═════════════════════════════════════════════════════════════
# SUITE 13: ThinkingState 枚举完整性
# ═════════════════════════════════════════════════════════════

def suite_enums():
    r = TestResult()
    r.suite_name = "枚举与常量完整性"

    # -- ThinkingState 所有值
    expected_states = {"init", "flowing", "deepening", "converging", "interrupted", "completed", "diverging"}
    actual_states = {s.value for s in ThinkingState}
    assert_eq(actual_states, expected_states, r, "ThinkingState 枚举值完整")

    # -- ComputeStrategy 所有值
    expected_strategies = {"quick", "standard", "deep", "exhaustive"}
    actual_strategies = {s.value for s in ComputeStrategy}
    assert_eq(actual_strategies, expected_strategies, r, "ComputeStrategy 枚举值完整")

    # -- STRATEGIES 覆盖所有策略
    for strategy in ComputeStrategy:
        assert_true(strategy in STRATEGIES, r, f"STRATEGIES 包含 {strategy.value}")

    # -- MODULE_OSCILLATORS 包含所有预期模块
    expected_modules = {"thinking_stream", "context_mapper", "event_bus", "nociception",
                        "chronos", "memory", "rules", "skills"}
    assert_eq(set(MODULE_OSCILLATORS.keys()), expected_modules, r, "MODULE_OSCILLATORS 模块完整")

    return r


# ═════════════════════════════════════════════════════════════
# SUITE 14: 全局单例
# ═════════════════════════════════════════════════════════════

def suite_singletons():
    r = TestResult()
    r.suite_name = "全局单例"

    from ctm.thinking_stream import get_thinking_engine, _engine as _ts_engine
    from ctm.ctm_core import get_ctm_core, _ctm_core as _ctm_instance

    # 重置单例
    import ctm.thinking_stream as ts_mod
    import ctm.ctm_core as ctm_mod
    ts_mod._engine = None
    ctm_mod._ctm_core = None

    e1 = get_thinking_engine()
    e2 = get_thinking_engine()
    assert_true(e1 is e2, r, "get_thinking_engine 返回同一实例")

    c1 = get_ctm_core()
    c2 = get_ctm_core()
    assert_true(c1 is c2, r, "get_ctm_core 返回同一实例")

    return r


# ═════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 70)
    print("鲤鱼 CTM 引擎 — 全面测试套件")
    print("=" * 70 + "\n")

    suites = [
        suite_thinking_stream_functional,
        suite_thinking_stream_edge_cases,
        suite_thinking_node_serialization,
        suite_thinking_stream_engine_advanced,
        suite_adaptive_compute_functional,
        suite_adaptive_compute_edge_cases,
        suite_oscillator_functional,
        suite_oscillator_advanced,
        suite_ctm_core_functional,
        suite_ctm_core_edge_cases,
        suite_ctm_core_integration,
        suite_performance,
        suite_enums,
        suite_singletons,
    ]

    all_results = []
    for suite_fn in suites:
        try:
            result = suite_fn()
            result.summary()
            all_results.append(result)
        except Exception as e:
            print(f"\n  [{suite_fn.__name__}] CRASHED: {e}")
            import traceback
            traceback.print_exc()
            all_results.append(None)

    # 总汇总
    print("\n" + "=" * 70)
    print("总汇总")
    print("=" * 70)

    total_pass = 0
    total_fail = 0
    total_suites = len(all_results)
    passed_suites = 0

    for result in all_results:
        if result is None:
            continue
        total_pass += result.passed
        total_fail += result.failed
        if result.failed == 0:
            passed_suites += 1

    print(f"\n  测试套件: {passed_suites}/{total_suites} 全部通过")
    print(f"  测试用例: {total_pass}/{total_pass + total_fail} 通过")

    if total_fail > 0:
        print(f"\n  失败用例:")
        for result in all_results:
            if result and result.errors:
                for name, msg in result.errors:
                    print(f"    [{result.suite_name}] {name}: {msg}")

    print()
    return total_fail == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
