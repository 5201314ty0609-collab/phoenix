"""
PHOENIX CTM - 连续思维机器
Continuous Thought Machine Engine

基于 Sakana AI 的 CTM 概念，实现思维流的连续演化
"""

from .thinking_stream import (
    ThinkingStreamEngine,
    ThinkingStream,
    ThinkingNode,
    ThinkingState,
    get_thinking_engine
)

from .adaptive_compute import (
    AdaptiveComputeTimer,
    ComplexityEstimate,
    ComputeBudget,
    ComputeStrategy,
    STRATEGIES
)

from .oscillator_sync import (
    OscillatorSyncModule,
    OscillatorPhase,
    SyncEvent,
    MODULE_OSCILLATORS
)

from .ctm_core import (
    CTMCore,
    CTMConfig,
    CTMState,
    get_ctm_core
)

from .utils import estimate_tokens

__version__ = "1.0.0"
__all__ = [
    # Thinking Stream
    "ThinkingStreamEngine",
    "ThinkingStream",
    "ThinkingNode",
    "ThinkingState",
    "get_thinking_engine",

    # Adaptive Compute
    "AdaptiveComputeTimer",
    "ComplexityEstimate",
    "ComputeBudget",
    "ComputeStrategy",
    "STRATEGIES",

    # Oscillator Sync
    "OscillatorSyncModule",
    "OscillatorPhase",
    "SyncEvent",
    "MODULE_OSCILLATORS",

    # CTM Core
    "CTMCore",
    "CTMConfig",
    "CTMState",
    "get_ctm_core",

    # Utils
    "estimate_tokens",
]
