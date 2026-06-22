#!/usr/bin/env python3
"""
PHOENIX CTM - 连续思维引擎
Thinking Stream Engine - 思维流状态机

基于 Continuous Thought Machine 概念，实现思维流的连续演化
"""

import time
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from .utils import estimate_tokens


class ThinkingState(Enum):
    """思维状态枚举"""
    INIT = "init"               # 思维初始化
    FLOWING = "flowing"         # 思维流动中
    DEEPENING = "deepening"     # 深化思考
    CONVERGING = "converging"   # 收敛结论
    INTERRUPTED = "interrupted" # 被中断（可恢复）
    COMPLETED = "completed"     # 思维完成
    DIVERGING = "diverging"     # 发散探索


@dataclass
class ThinkingNode:
    """思维节点 - 思维流的基本单元"""
    id: str
    content: str
    state: ThinkingState
    depth: int                  # 思维深度 (0=表层, >3=深层)
    confidence: float           # 置信度 (0-1)
    parent_id: Optional[str]    # 父节点（支持思维分支）
    children_ids: List[str]     # 子节点
    timestamp: float
    token_estimate: int
    metadata: Dict[str, Any]    # 关联的上下文、记忆等

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "state": self.state.value,
            "depth": self.depth,
            "confidence": self.confidence,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "timestamp": self.timestamp,
            "token_estimate": self.token_estimate,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ThinkingNode':
        """从字典创建"""
        return cls(
            id=data["id"],
            content=data["content"],
            state=ThinkingState(data["state"]),
            depth=data["depth"],
            confidence=data["confidence"],
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            timestamp=data["timestamp"],
            token_estimate=data["token_estimate"],
            metadata=data.get("metadata", {})
        )


@dataclass
class ThinkingStream:
    """连续思维流"""
    stream_id: str
    session_id: str
    query: str
    nodes: List[ThinkingNode] = field(default_factory=list)
    current_state: ThinkingState = ThinkingState.INIT
    start_time: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    total_tokens: int = 0
    max_depth: int = 0
    branch_count: int = 0

    def add_node(self, content: str, depth: int = 0,
                 confidence: float = 0.5, parent_id: Optional[str] = None,
                 metadata: Dict = None) -> ThinkingNode:
        """添加思维节点"""
        node = ThinkingNode(
            id=f"node-{uuid.uuid4().hex[:8]}",
            content=content,
            state=self.current_state,
            depth=depth,
            confidence=confidence,
            parent_id=parent_id,
            children_ids=[],
            timestamp=time.time(),
            token_estimate=estimate_tokens(content),
            metadata=metadata or {}
        )

        # 更新父节点
        if parent_id:
            for n in self.nodes:
                if n.id == parent_id:
                    n.children_ids.append(node.id)
                    break

        # 更新流状态
        self.nodes.append(node)
        self.total_tokens += node.token_estimate
        self.max_depth = max(self.max_depth, depth)
        self.last_activity = time.time()

        if parent_id and len(self.nodes) > 1:
            self.branch_count += 1

        return node

    def get_current_node(self) -> Optional[ThinkingNode]:
        """获取当前节点"""
        return self.nodes[-1] if self.nodes else None

    def get_depth_nodes(self, depth: int) -> List[ThinkingNode]:
        """获取指定深度的节点"""
        return [n for n in self.nodes if n.depth == depth]

    def get_summary(self) -> Dict:
        """获取思维流摘要"""
        return {
            "stream_id": self.stream_id,
            "session_id": self.session_id,
            "query": self.query,
            "state": self.current_state.value,
            "nodes_count": len(self.nodes),
            "total_tokens": self.total_tokens,
            "max_depth": self.max_depth,
            "branch_count": self.branch_count,
            "duration_seconds": time.time() - self.start_time,
            "last_activity": self.last_activity
        }


class ThinkingStreamEngine:
    """思维流引擎 - 管理思维流的创建和演化"""

    def __init__(self):
        self.streams: Dict[str, ThinkingStream] = {}

    def create_stream(self, query: str, session_id: str = "default",
                      budget: Dict = None) -> ThinkingStream:
        """创建新的思维流"""
        stream = ThinkingStream(
            stream_id=f"stream-{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            query=query
        )

        # 创建初始节点
        stream.add_node(
            content=f"开始思考: {query}",
            depth=0,
            confidence=0.1,
            metadata={"type": "init", "budget": budget}
        )

        stream.current_state = ThinkingState.FLOWING
        self.streams[stream.stream_id] = stream

        return stream

    def advance_stream(self, stream_id: str, content: str,
                       depth: int = None, confidence: float = None,
                       parent_id: Optional[str] = None) -> Optional[ThinkingNode]:
        """推进思维流"""
        stream = self.streams.get(stream_id)
        if not stream:
            return None

        # 自动计算深度
        if depth is None:
            current = stream.get_current_node()
            depth = current.depth + 1 if current else 0

        # 自动计算置信度
        if confidence is None:
            # 基于深度的置信度增长
            confidence = min(0.5 + depth * 0.1, 0.95)

        node = stream.add_node(
            content=content,
            depth=depth,
            confidence=confidence,
            parent_id=parent_id or stream.get_current_node().id if stream.get_current_node() else None
        )

        # 更新状态
        if depth > 3:
            stream.current_state = ThinkingState.DEEPENING
        elif confidence > 0.8:
            stream.current_state = ThinkingState.CONVERGING

        return node

    def complete_stream(self, stream_id: str, summary: str = None) -> Optional[Dict]:
        """完成思维流"""
        stream = self.streams.get(stream_id)
        if not stream:
            return None

        stream.current_state = ThinkingState.COMPLETED

        if summary:
            stream.add_node(
                content=summary,
                depth=0,
                confidence=0.95,
                metadata={"type": "summary"}
            )

        return stream.get_summary()

    def interrupt_stream(self, stream_id: str, reason: str = None) -> bool:
        """中断思维流"""
        stream = self.streams.get(stream_id)
        if not stream:
            return False

        stream.current_state = ThinkingState.INTERRUPTED

        if reason:
            stream.add_node(
                content=f"思维被中断: {reason}",
                depth=stream.get_current_node().depth if stream.get_current_node() else 0,
                confidence=0.0,
                metadata={"type": "interruption", "reason": reason}
            )

        return True

    def resume_stream(self, stream_id: str) -> bool:
        """恢复中断的思维流"""
        stream = self.streams.get(stream_id)
        if not stream or stream.current_state != ThinkingState.INTERRUPTED:
            return False

        stream.current_state = ThinkingState.FLOWING
        return True

    def get_stream(self, stream_id: str) -> Optional[ThinkingStream]:
        """获取思维流"""
        return self.streams.get(stream_id)

    def get_all_streams(self) -> List[Dict]:
        """获取所有思维流摘要"""
        return [s.get_summary() for s in self.streams.values()]

    def cleanup_old_streams(self, max_age_hours: int = 24) -> int:
        """清理旧的思维流"""
        cutoff = time.time() - (max_age_hours * 3600)
        to_remove = [
            sid for sid, stream in self.streams.items()
            if stream.last_activity < cutoff
        ]
        for sid in to_remove:
            del self.streams[sid]
        return len(to_remove)


# 全局引擎实例
_engine = None

def get_thinking_engine() -> ThinkingStreamEngine:
    """获取全局思维流引擎"""
    global _engine
    if _engine is None:
        _engine = ThinkingStreamEngine()
    return _engine


def main():
    """CLI 入口"""
    import sys

    if len(sys.argv) < 2:
        print("用法: thinking_stream.py <command>")
        print("命令:")
        print("  create <query>  - 创建思维流")
        print("  list            - 列出所有思维流")
        print("  get <stream_id> - 获取思维流详情")
        return

    engine = get_thinking_engine()
    command = sys.argv[1]

    if command == "create":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "默认查询"
        stream = engine.create_stream(query)
        print(f"✓ 创建思维流: {stream.stream_id}")
        print(f"  查询: {stream.query}")
        print(f"  状态: {stream.current_state.value}")

    elif command == "list":
        streams = engine.get_all_streams()
        if streams:
            print(f"思维流列表 ({len(streams)} 个):")
            for s in streams:
                print(f"  - {s['stream_id']}: {s['state']} ({s['nodes_count']} 节点)")
        else:
            print("无思维流")

    elif command == "get":
        if len(sys.argv) < 3:
            print("用法: thinking_stream.py get <stream_id>")
            return
        stream = engine.get_stream(sys.argv[2])
        if stream:
            print(f"思维流: {stream.stream_id}")
            print(f"  查询: {stream.query}")
            print(f"  状态: {stream.current_state.value}")
            print(f"  节点数: {len(stream.nodes)}")
            print(f"  最大深度: {stream.max_depth}")
            print(f"  总 Token: {stream.total_tokens}")
        else:
            print(f"思维流 {sys.argv[2]} 不存在")

    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
