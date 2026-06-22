#!/usr/bin/env python3
"""
PHOENIX CTM - 同步振荡协调
Oscillator Sync Module - 多模块节奏同步

基于 CTM 的神经同步概念，实现多模块协调
"""

import math
import time
import json
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class OscillatorPhase:
    """振荡器相位"""
    module_id: str
    phase: float            # 当前相位 (0-2π)
    frequency: float        # 振荡频率 (Hz)
    amplitude: float        # 振幅 (影响强度)
    last_sync: float        # 上次同步时间

    def to_dict(self) -> Dict:
        return {
            "module_id": self.module_id,
            "phase": round(self.phase, 4),
            "frequency": round(self.frequency, 4),
            "amplitude": round(self.amplitude, 4),
            "last_sync": self.last_sync
        }


@dataclass
class SyncEvent:
    """同步事件"""
    timestamp: float
    coherence: float
    modules: List[str]
    phase_offsets: Dict[str, float]

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "coherence": round(self.coherence, 4),
            "modules": self.modules,
            "phase_offsets": {k: round(v, 4) for k, v in self.phase_offsets.items()}
        }


# 模块振荡配置
MODULE_OSCILLATORS = {
    "thinking_stream": {"base_freq": 1.0, "phase": 0.0, "amplitude": 1.0},
    "context_mapper": {"base_freq": 0.5, "phase": math.pi / 4, "amplitude": 0.8},
    "event_bus": {"base_freq": 2.0, "phase": 0.0, "amplitude": 1.0},
    "nociception": {"base_freq": 0.1, "phase": math.pi / 2, "amplitude": 0.5},
    "chronos": {"base_freq": 0.01, "phase": 0.0, "amplitude": 0.3},
    "memory": {"base_freq": 0.2, "phase": math.pi, "amplitude": 0.6},
    "rules": {"base_freq": 0.05, "phase": math.pi / 3, "amplitude": 0.4},
    "skills": {"base_freq": 0.3, "phase": 2 * math.pi / 3, "amplitude": 0.7},
}


class OscillatorSyncModule:
    """多模块同步振荡器"""

    def __init__(self):
        self.oscillators: Dict[str, OscillatorPhase] = {}
        self.sync_history: List[SyncEvent] = []

        # 初始化默认振荡器
        for module_id, config in MODULE_OSCILLATORS.items():
            self.register_module(module_id, config)

    def register_module(self, module_id: str, config: Dict):
        """注册模块振荡器"""
        self.oscillators[module_id] = OscillatorPhase(
            module_id=module_id,
            phase=config.get("phase", 0.0),
            frequency=config.get("base_freq", 1.0),
            amplitude=config.get("amplitude", 1.0),
            last_sync=time.time()
        )

    def unregister_module(self, module_id: str):
        """注销模块振荡器"""
        if module_id in self.oscillators:
            del self.oscillators[module_id]

    def sync_tick(self, delta_time: float = 0.1) -> Dict[str, float]:
        """同步 tick - 所有振荡器推进一步"""
        phases = {}

        for module_id, osc in self.oscillators.items():
            # 更新相位: φ(t+Δt) = φ(t) + 2π·f·Δt
            osc.phase += 2 * math.pi * osc.frequency * delta_time
            # 归一化到 [0, 2π)
            osc.phase = osc.phase % (2 * math.pi)
            osc.last_sync = time.time()

            phases[module_id] = osc.phase

        return phases

    def compute_phase_coherence(self) -> float:
        """计算相位一致性 - 0=完全失步, 1=完美同步"""
        if len(self.oscillators) < 2:
            return 1.0

        # 计算所有模块的平均相位
        phases = [osc.phase for osc in self.oscillators.values()]
        avg_phase = sum(phases) / len(phases)

        # 计算相位差的标准差
        phase_diffs = [(p - avg_phase) ** 2 for p in phases]
        std_dev = math.sqrt(sum(phase_diffs) / len(phase_diffs))

        # 转换为一致性分数 (0-1)
        coherence = max(0, 1 - std_dev / math.pi)
        return coherence

    def adjust_frequency(self, module_id: str, new_freq: float):
        """动态调整模块频率"""
        if module_id in self.oscillators:
            self.oscillators[module_id].frequency = new_freq

    def adjust_amplitude(self, module_id: str, new_amplitude: float):
        """动态调整模块振幅"""
        if module_id in self.oscillators:
            self.oscillators[module_id].amplitude = new_amplitude

    def get_phase_offsets(self) -> Dict[str, float]:
        """获取相位偏移"""
        if not self.oscillators:
            return {}

        # 以第一个模块为基准
        reference_phase = list(self.oscillators.values())[0].phase

        offsets = {}
        for module_id, osc in self.oscillators.items():
            offset = osc.phase - reference_phase
            # 归一化到 [-π, π]
            if offset > math.pi:
                offset -= 2 * math.pi
            elif offset < -math.pi:
                offset += 2 * math.pi
            offsets[module_id] = offset

        return offsets

    def emit_sync_event(self) -> SyncEvent:
        """发布同步事件"""
        coherence = self.compute_phase_coherence()
        offsets = self.get_phase_offsets()

        event = SyncEvent(
            timestamp=time.time(),
            coherence=coherence,
            modules=list(self.oscillators.keys()),
            phase_offsets=offsets
        )

        self.sync_history.append(event)

        # 保留最近 100 个事件
        if len(self.sync_history) > 100:
            self.sync_history = self.sync_history[-100:]

        return event

    def detect_drift(self, threshold: float = 0.5) -> List[Dict]:
        """检测漂移"""
        drifts = []
        offsets = self.get_phase_offsets()

        for module_id, offset in offsets.items():
            if abs(offset) > threshold:
                drifts.append({
                    "module": module_id,
                    "offset": round(offset, 4),
                    "severity": "high" if abs(offset) > 1.0 else "medium"
                })

        return drifts

    def get_sync_stats(self) -> Dict:
        """获取同步统计"""
        if not self.sync_history:
            return {
                "modules": len(self.oscillators),
                "coherence": 1.0,
                "sync_events": 0
            }

        coherences = [e.coherence for e in self.sync_history]
        return {
            "modules": len(self.oscillators),
            "coherence": round(self.compute_phase_coherence(), 4),
            "sync_events": len(self.sync_history),
            "avg_coherence": round(sum(coherences) / len(coherences), 4),
            "min_coherence": round(min(coherences), 4),
            "max_coherence": round(max(coherences), 4)
        }

    def save_state(self, path: str):
        """保存状态"""
        state = {
            "oscillators": {k: v.to_dict() for k, v in self.oscillators.items()},
            "sync_history": [e.to_dict() for e in self.sync_history[-50:]]
        }
        Path(path).write_text(json.dumps(state, indent=2))

    def load_state(self, path: str):
        """加载状态"""
        if not Path(path).exists():
            return

        state = json.loads(Path(path).read_text())

        for module_id, osc_data in state.get("oscillators", {}).items():
            self.oscillators[module_id] = OscillatorPhase(
                module_id=osc_data["module_id"],
                phase=osc_data["phase"],
                frequency=osc_data["frequency"],
                amplitude=osc_data["amplitude"],
                last_sync=osc_data["last_sync"]
            )


def main():
    """CLI 入口"""
    import sys

    if len(sys.argv) < 2:
        print("用法: oscillator_sync.py <command>")
        print("命令:")
        print("  status          - 查看同步状态")
        print("  coherence       - 计算一致性")
        print("  drift           - 检测漂移")
        print("  stats           - 统计信息")
        return

    sync = OscillatorSyncModule()
    command = sys.argv[1]

    if command == "status":
        print("振荡器状态:")
        for module_id, osc in sync.oscillators.items():
            print(f"  {module_id}: freq={osc.frequency:.3f}Hz, phase={osc.phase:.3f}, amp={osc.amplitude:.3f}")

    elif command == "coherence":
        coherence = sync.compute_phase_coherence()
        print(f"相位一致性: {coherence:.4f}")
        if coherence > 0.8:
            print("  状态: 同步良好")
        elif coherence > 0.5:
            print("  状态: 轻微漂移")
        else:
            print("  状态: 严重失步")

    elif command == "drift":
        drifts = sync.detect_drift()
        if drifts:
            print("检测到漂移:")
            for d in drifts:
                print(f"  {d['module']}: offset={d['offset']:.4f} ({d['severity']})")
        else:
            print("无漂移")

    elif command == "stats":
        stats = sync.get_sync_stats()
        print(f"同步统计: {json.dumps(stats, indent=2)}")

    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
