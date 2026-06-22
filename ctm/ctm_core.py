#!/usr/bin/env python3
"""
PHOENIX CTM - 核心协调器
CTM Core Coordinator - 统一管理三大模块

整合思维流、自适应计算、同步振荡
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from .thinking_stream import ThinkingStreamEngine, ThinkingStream, ThinkingNode, ThinkingState
from .adaptive_compute import AdaptiveComputeTimer, ComplexityEstimate, ComputeBudget
from .oscillator_sync import OscillatorSyncModule, SyncEvent


@dataclass
class CTMConfig:
    """CTM 配置"""
    enable_thinking_stream: bool = True
    enable_adaptive_compute: bool = True
    enable_oscillator_sync: bool = True
    max_concurrent_streams: int = 10
    cleanup_interval_hours: int = 24

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CTMState:
    """CTM 状态"""
    active_streams: int
    total_streams_created: int
    current_coherence: float
    compute_stats: Dict
    oscillator_stats: Dict

    def to_dict(self) -> Dict:
        return asdict(self)


class CTMCore:
    """CTM 核心协调器"""

    def __init__(self, config: CTMConfig = None):
        self.config = config or CTMConfig()

        # 初始化子模块
        self.thinking_engine = ThinkingStreamEngine() if self.config.enable_thinking_stream else None
        self.compute_timer = AdaptiveComputeTimer() if self.config.enable_adaptive_compute else None
        self.oscillator = OscillatorSyncModule() if self.config.enable_oscillator_sync else None

        # 状态追踪
        self.total_streams_created = 0
        self.event_log: List[Dict] = []

    def start_thinking(self, query: str, session_id: str = "default",
                       context: Dict = None) -> Optional[str]:
        """启动思维流

        Args:
            query: 查询内容
            session_id: 会话 ID
            context: 上下文信息

        Returns:
            stream_id 或 None
        """
        if not self.thinking_engine:
            return None

        # 检查并发限制
        active = len(self.thinking_engine.streams)
        if active >= self.config.max_concurrent_streams:
            self._log_event("warning", "达到并发限制", {"active": active})
            return None

        # 评估复杂度
        complexity = None
        budget = None
        if self.compute_timer:
            complexity = self.compute_timer.estimate_complexity(query, context)
            budget = self.compute_timer.allocate_budget(complexity, context)

        # 创建思维流
        stream = self.thinking_engine.create_stream(
            query=query,
            session_id=session_id,
            budget=budget.to_dict() if budget else None
        )

        # 存储复杂度评估到初始节点 metadata（供 complete_thinking 使用）
        if complexity:
            stream.nodes[0].metadata["complexity"] = complexity.to_dict()

        self.total_streams_created += 1

        # 注册振荡器
        if self.oscillator and budget:
            self.oscillator.register_module(f"thinking_{stream.stream_id}", {
                "base_freq": 1.0 / budget.max_depth,  # 深度越深，频率越低
                "phase": 0.0,
                "amplitude": 0.5
            })

        self._log_event("info", "思维流启动", {
            "stream_id": stream.stream_id,
            "query": query[:50],
            "complexity": complexity.to_dict() if complexity else None,
            "budget": budget.to_dict() if budget else None
        })

        return stream.stream_id

    def advance_thinking(self, stream_id: str, content: str,
                         depth: int = None, confidence: float = None) -> Optional[Dict]:
        """推进思维流

        Args:
            stream_id: 思维流 ID
            content: 新内容
            depth: 思维深度
            confidence: 置信度

        Returns:
            节点信息或 None
        """
        if not self.thinking_engine:
            return None

        # 检查是否应该继续
        stream = self.thinking_engine.get_stream(stream_id)
        if not stream:
            return None

        # 自适应计算检查
        if self.compute_timer and stream.nodes:
            current_node = stream.get_current_node()
            if current_node:
                # 获取预算
                budget_data = stream.nodes[0].metadata.get("budget")
                if budget_data:
                    budget = ComputeBudget(**budget_data)
                    should_continue, reason = self.compute_timer.should_continue(
                        current_depth=current_node.depth,
                        current_tokens=stream.total_tokens,
                        current_confidence=current_node.confidence,
                        elapsed_seconds=time.time() - stream.start_time,
                        budget=budget
                    )

                    if not should_continue:
                        self._log_event("info", "思维流自动收敛", {
                            "stream_id": stream_id,
                            "reason": reason
                        })
                        stream.current_state = ThinkingState.CONVERGING

        # 推进思维
        node = self.thinking_engine.advance_stream(
            stream_id=stream_id,
            content=content,
            depth=depth,
            confidence=confidence
        )

        if node:
            # 同步振荡
            if self.oscillator:
                self.oscillator.sync_tick()

            return node.to_dict()

        return None

    def complete_thinking(self, stream_id: str, summary: str = None) -> Optional[Dict]:
        """完成思维流

        Args:
            stream_id: 思维流 ID
            summary: 总结内容

        Returns:
            思维流摘要
        """
        if not self.thinking_engine:
            return None

        result = self.thinking_engine.complete_stream(stream_id, summary)

        if result:
            # 注销振荡器
            if self.oscillator:
                self.oscillator.unregister_module(f"thinking_{stream_id}")

            # 记录结果
            if self.compute_timer:
                stream = self.thinking_engine.get_stream(stream_id)
                if stream and stream.nodes:
                    budget_data = stream.nodes[0].metadata.get("budget")
                    if budget_data:
                        complexity_data = stream.nodes[0].metadata.get("complexity")
                        if complexity_data:
                            self.compute_timer.record_outcome(
                                stream.query,
                                ComplexityEstimate(**complexity_data),
                                ComputeBudget(**budget_data)
                            )

            self._log_event("info", "思维流完成", result)

        return result

    def interrupt_thinking(self, stream_id: str, reason: str = None) -> bool:
        """中断思维流"""
        if not self.thinking_engine:
            return False

        result = self.thinking_engine.interrupt_stream(stream_id, reason)

        if result:
            self._log_event("info", "思维流中断", {
                "stream_id": stream_id,
                "reason": reason
            })

        return result

    def get_thinking_state(self, stream_id: str) -> Optional[Dict]:
        """获取思维流状态"""
        if not self.thinking_engine:
            return None

        stream = self.thinking_engine.get_stream(stream_id)
        if not stream:
            return None

        state = stream.get_summary()

        # 添加同步信息
        if self.oscillator:
            state["coherence"] = self.oscillator.compute_phase_coherence()

        return state

    def get_all_streams(self) -> List[Dict]:
        """获取所有思维流"""
        if not self.thinking_engine:
            return []

        return self.thinking_engine.get_all_streams()

    def get_ctm_state(self) -> CTMState:
        """获取 CTM 状态"""
        active_streams = len(self.thinking_engine.streams) if self.thinking_engine else 0

        return CTMState(
            active_streams=active_streams,
            total_streams_created=self.total_streams_created,
            current_coherence=self.oscillator.compute_phase_coherence() if self.oscillator else 1.0,
            compute_stats=self.compute_timer.get_statistics() if self.compute_timer else {},
            oscillator_stats=self.oscillator.get_sync_stats() if self.oscillator else {}
        )

    def cleanup(self) -> int:
        """清理旧数据"""
        cleaned = 0

        if self.thinking_engine:
            cleaned += self.thinking_engine.cleanup_old_streams(self.config.cleanup_interval_hours)

        return cleaned

    def _log_event(self, level: str, message: str, data: Dict = None):
        """记录事件"""
        self.event_log.append({
            "timestamp": time.time(),
            "level": level,
            "message": message,
            "data": data
        })

        # 保留最近 1000 个事件
        if len(self.event_log) > 1000:
            self.event_log = self.event_log[-1000:]

    def get_event_log(self, limit: int = 50) -> List[Dict]:
        """获取事件日志"""
        return self.event_log[-limit:]


# 全局实例
_ctm_core = None

def get_ctm_core(config: CTMConfig = None) -> CTMCore:
    """获取全局 CTM 核心实例"""
    global _ctm_core
    if _ctm_core is None:
        _ctm_core = CTMCore(config)
    return _ctm_core


def main():
    """CLI 入口"""
    import sys

    if len(sys.argv) < 2:
        print("用法: ctm_core.py <command>")
        print("命令:")
        print("  status           - 查看 CTM 状态")
        print("  start <query>    - 启动思维流")
        print("  streams          - 列出所有思维流")
        print("  events           - 查看事件日志")
        print("  cleanup          - 清理旧数据")
        return

    ctm = get_ctm_core()
    command = sys.argv[1]

    if command == "status":
        state = ctm.get_ctm_state()
        print("CTM 状态:")
        print(f"  活跃思维流: {state.active_streams}")
        print(f"  总创建数: {state.total_streams_created}")
        print(f"  相位一致性: {state.current_coherence:.4f}")
        print(f"  计算统计: {state.compute_stats}")
        print(f"  振荡统计: {state.oscillator_stats}")

    elif command == "start":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "默认查询"
        stream_id = ctm.start_thinking(query)
        if stream_id:
            print(f"✓ 启动思维流: {stream_id}")
        else:
            print("✗ 启动失败")

    elif command == "streams":
        streams = ctm.get_all_streams()
        if streams:
            print(f"思维流列表 ({len(streams)} 个):")
            for s in streams:
                print(f"  - {s['stream_id']}: {s['state']} ({s['nodes_count']} 节点)")
        else:
            print("无思维流")

    elif command == "events":
        events = ctm.get_event_log()
        if events:
            print(f"事件日志 ({len(events)} 条):")
            for e in events[-10:]:
                print(f"  [{e['level']}] {e['message']}")
        else:
            print("无事件")

    elif command == "cleanup":
        cleaned = ctm.cleanup()
        print(f"清理了 {cleaned} 个旧数据")

    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
