"""
PHOENIX AIOS — Streaming Response Handler

Processes OpenAI streaming responses (SSE) into structured chunks.
Handles content accumulation, tool call assembly, and error recovery.
"""

from aios.ai.streaming.handler import StreamHandler, StreamCollector

__all__ = ["StreamHandler", "StreamCollector"]
