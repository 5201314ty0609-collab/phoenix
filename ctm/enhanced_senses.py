#!/usr/bin/env python3
"""
鲤鱼 CTM - 增强八感知系统
Enhanced 8-Sense System with CTM

基于 CTM 的连续性、自适应、同步性增强八感知能力
"""

import time
import math
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from ctm.ctm_core import CTMCore, get_ctm_core
from ctm.oscillator_sync import OscillatorSyncModule


@dataclass
class EnhancedSense:
    """增强感知"""
    sense_id: str
    name: str
    description: str
    base_value: float = 0.0
    ctm_boost: float = 0.0
    coherence_factor: float = 1.0
    adaptive_factor: float = 1.0
    last_update: float = field(default_factory=time.time)

    @property
    def enhanced_value(self) -> float:
        """增强后的值"""
        return self.base_value * self.coherence_factor * self.adaptive_factor + self.ctm_boost

    @property
    def status(self) -> str:
        """状态"""
        if self.enhanced_value < 0.3:
            return "critical"
        elif self.enhanced_value < 0.6:
            return "warning"
        else:
            return "normal"

    def to_dict(self) -> Dict:
        return {
            "sense_id": self.sense_id,
            "name": self.name,
            "description": self.description,
            "base_value": round(self.base_value, 4),
            "ctm_boost": round(self.ctm_boost, 4),
            "coherence_factor": round(self.coherence_factor, 4),
            "adaptive_factor": round(self.adaptive_factor, 4),
            "enhanced_value": round(self.enhanced_value, 4),
            "status": self.status,
            "last_update": self.last_update
        }


class EnhancedSensesSystem:
    """增强八感知系统"""

    def __init__(self, ctm_core: CTMCore = None):
        self.ctm = ctm_core or get_ctm_core()
        self.oscillator = self.ctm.oscillator

        # 初始化八感知
        self.senses: Dict[str, EnhancedSense] = {
            "o2": EnhancedSense(
                sense_id="o2",
                name="O2 (Vitality)",
                description="上下文生命力 - Token 使用率和上下文压力"
            ),
            "nociception": EnhancedSense(
                sense_id="nociception",
                name="Nociception (Pain)",
                description="痛觉 - 错误级联和异常检测"
            ),
            "chronos": EnhancedSense(
                sense_id="chronos",
                name="Chronos (Time)",
                description="时间感知 - 会话节奏和空闲时间"
            ),
            "spatial": EnhancedSense(
                sense_id="spatial",
                name="Spatial (Workspace)",
                description="空间感知 - 文件变动和工作区状态"
            ),
            "vestibular": EnhancedSense(
                sense_id="vestibular",
                name="Vestibular (Balance)",
                description="平衡感知 - 工具使用多样性"
            ),
            "echo": EnhancedSense(
                sense_id="echo",
                name="Echo (Repetition)",
                description="回响感知 - 模式重复检测"
            ),
            "drift": EnhancedSense(
                sense_id="drift",
                name="Drift (Focus)",
                description="漂移感知 - 主题连贯性"
            ),
            "ctm": EnhancedSense(
                sense_id="ctm",
                name="CTM (Continuity)",
                description="连续性感知 - 思维流连续性和连贯性"
            ),
        }

    def update_base_value(self, sense_id: str, value: float):
        """更新基础值"""
        if sense_id in self.senses:
            self.senses[sense_id].base_value = value
            self.senses[sense_id].last_update = time.time()

    def apply_ctm_enhancement(self):
        """应用 CTM 增强"""
        # 获取 CTM 状态
        ctm_state = self.ctm.get_ctm_state()
        coherence = ctm_state.current_coherence

        # 计算 CTM 增强因子
        for sense_id, sense in self.senses.items():
            # 相位一致性影响所有感知
            sense.coherence_factor = 0.5 + coherence * 0.5

            # 自适应计算影响
            if ctm_state.compute_stats:
                avg_complexity = ctm_state.compute_stats.get("avg_complexity", 0.5)
                sense.adaptive_factor = 0.8 + avg_complexity * 0.4

            # CTM 特定增强
            if sense_id == "ctm":
                # CTM 感知直接从 CTM 状态获取
                sense.ctm_boost = coherence * 0.3
            elif sense_id == "chronos":
                # 时间感知受 CTM 自适应计算影响
                sense.ctm_boost = 0.1 if ctm_state.active_streams > 0 else 0
            elif sense_id == "drift":
                # 漂移感知受思维流连贯性影响
                sense.ctm_boost = coherence * 0.2

    def update_from_sense_files(self, senses_dir: Path):
        """从 sense 文件更新"""
        for sense_file in senses_dir.glob("*.json"):
            sense_id = sense_file.stem
            if sense_id in self.senses:
                try:
                    data = json.loads(sense_file.read_text())
                    metrics = data.get("metrics", {})

                    # 根据 sense 类型提取值
                    if sense_id == "o2":
                        value = metrics.get("usage_percent", 0) / 100
                    elif sense_id == "nociception":
                        value = min(1.0, metrics.get("errors_per_window", 0) / 5)
                    elif sense_id == "chronos":
                        value = min(1.0, metrics.get("idle_seconds", 0) / 600)
                    elif sense_id == "spatial":
                        value = min(1.0, metrics.get("files_per_call", 0) / 10)
                    elif sense_id == "vestibular":
                        value = metrics.get("dominant_percent", 0) / 100
                    elif sense_id == "echo":
                        value = min(1.0, metrics.get("repeated_signatures", 0) / 3)
                    elif sense_id == "drift":
                        value = metrics.get("deviation_percent", 0) / 100
                    else:
                        value = 0

                    self.update_base_value(sense_id, value)
                except Exception:
                    pass

    def get_enhanced_senses(self) -> List[Dict]:
        """获取增强后的感知数据"""
        self.apply_ctm_enhancement()
        return [sense.to_dict() for sense in self.senses.values()]

    def get_overall_health(self) -> float:
        """获取整体健康度"""
        values = [s.enhanced_value for s in self.senses.values()]
        return sum(values) / len(values) if values else 0

    def get_sense_summary(self) -> Dict:
        """获取感知摘要"""
        senses = self.get_enhanced_senses()
        normal = sum(1 for s in senses if s["status"] == "normal")
        warning = sum(1 for s in senses if s["status"] == "warning")
        critical = sum(1 for s in senses if s["status"] == "critical")

        return {
            "total": len(senses),
            "normal": normal,
            "warning": warning,
            "critical": critical,
            "overall_health": self.get_overall_health(),
            "ctm_coherence": self.ctm.get_ctm_state().current_coherence,
            "senses": senses
        }

    def to_radar_data(self) -> Dict:
        """转换为雷达图数据"""
        senses = self.get_enhanced_senses()
        return {
            "labels": [s["name"] for s in senses],
            "values": [s["enhanced_value"] for s in senses],
            "statuses": [s["status"] for s in senses]
        }


def main():
    """CLI 入口"""
    import sys

    if len(sys.argv) < 2:
        print("用法: enhanced_senses.py <command>")
        print("命令:")
        print("  status    - 查看增强感知状态")
        print("  radar     - 雷达图数据")
        print("  summary   - 感知摘要")
        return

    senses = EnhancedSensesSystem()
    command = sys.argv[1]

    # 尝试从文件更新
    senses_dir = Path.home() / ".claude" / "liyu" / "senses"
    if senses_dir.exists():
        senses.update_from_sense_files(senses_dir)

    if command == "status":
        summary = senses.get_sense_summary()
        print(f"增强八感知状态:")
        print(f"  总体健康: {summary['overall_health']:.4f}")
        print(f"  CTM 相位一致性: {summary['ctm_coherence']:.4f}")
        print(f"  正常: {summary['normal']}, 警告: {summary['warning']}, 严重: {summary['critical']}")
        print()
        for s in summary["senses"]:
            status_icon = "✓" if s["status"] == "normal" else "⚠" if s["status"] == "warning" else "✗"
            print(f"  {status_icon} {s['name']}: {s['enhanced_value']:.4f} ({s['status']})")

    elif command == "radar":
        data = senses.to_radar_data()
        print(json.dumps(data, indent=2, ensure_ascii=False))

    elif command == "summary":
        summary = senses.get_sense_summary()
        print(json.dumps(summary, indent=2, ensure_ascii=False))

    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
