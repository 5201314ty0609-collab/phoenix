"""
Logging callback for PHOENIX AIOS LangChain integration.

Provides logging for all callback events.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from ..core import Config, Logger
from .base import Callback, CallbackEvent


class LoggingCallback(Callback):
    """
    Logging callback that logs all events.

    Example:
        callback = LoggingCallback(level=logging.DEBUG)
        # All events will be logged
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        level: int = logging.INFO,
        logger_name: str = "phoenix.callbacks",
    ):
        self._config = config or Config()
        self._logger = logging.getLogger(logger_name)
        self._logger.setLevel(level)

        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    def on_chain_start(self, event: CallbackEvent) -> None:
        """Log chain start."""
        self._logger.info(f"Chain started: {event.name}")

    def on_chain_end(self, event: CallbackEvent) -> None:
        """Log chain end."""
        self._logger.info(f"Chain ended: {event.name}")

    def on_chain_error(self, event: CallbackEvent) -> None:
        """Log chain error."""
        self._logger.error(f"Chain error: {event.name} - {event.data}")

    def on_step_start(self, event: CallbackEvent) -> None:
        """Log step start."""
        self._logger.debug(f"Step started: {event.name}")

    def on_step_end(self, event: CallbackEvent) -> None:
        """Log step end."""
        self._logger.debug(f"Step ended: {event.name}")

    def on_step_error(self, event: CallbackEvent) -> None:
        """Log step error."""
        self._logger.error(f"Step error: {event.name} - {event.data}")

    def on_tool_start(self, event: CallbackEvent) -> None:
        """Log tool start."""
        self._logger.info(f"Tool started: {event.name}")

    def on_tool_end(self, event: CallbackEvent) -> None:
        """Log tool end."""
        self._logger.info(f"Tool ended: {event.name}")

    def on_tool_error(self, event: CallbackEvent) -> None:
        """Log tool error."""
        self._logger.error(f"Tool error: {event.name} - {event.data}")

    def on_llm_start(self, event: CallbackEvent) -> None:
        """Log LLM start."""
        self._logger.info(f"LLM started: {event.name}")

    def on_llm_end(self, event: CallbackEvent) -> None:
        """Log LLM end."""
        self._logger.info(f"LLM ended: {event.name}")

    def on_llm_error(self, event: CallbackEvent) -> None:
        """Log LLM error."""
        self._logger.error(f"LLM error: {event.name} - {event.data}")

    def on_llm_token(self, event: CallbackEvent) -> None:
        """Log LLM token."""
        self._logger.debug(f"LLM token: {event.data}")

    def on_custom_event(self, event: CallbackEvent) -> None:
        """Log custom event."""
        self._logger.info(f"Custom event: {event.name} - {event.data}")
