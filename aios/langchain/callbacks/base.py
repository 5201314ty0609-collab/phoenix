"""
Base callback module for PHOENIX AIOS LangChain integration.

Provides abstract base class for callbacks.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ..core import Config, Logger


class CallbackEventType(Enum):
    """Types of callback events."""
    CHAIN_START = "chain_start"
    CHAIN_END = "chain_end"
    CHAIN_ERROR = "chain_error"
    STEP_START = "step_start"
    STEP_END = "step_end"
    STEP_ERROR = "step_error"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    TOOL_ERROR = "tool_error"
    LLM_START = "llm_start"
    LLM_END = "llm_end"
    LLM_ERROR = "llm_error"
    LLM_TOKEN = "llm_token"
    MEMORY_START = "memory_start"
    MEMORY_END = "memory_end"
    CUSTOM = "custom"


@dataclass(frozen=True)
class CallbackEvent:
    """
    Callback event.

    Attributes:
        event_type: Type of event
        name: Event name
        data: Event data
        timestamp: Event timestamp
        metadata: Additional metadata
    """
    event_type: CallbackEventType
    name: str
    data: Any = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def with_data(self, data: Any) -> CallbackEvent:
        """Create new event with updated data."""
        from dataclasses import replace
        return replace(self, data=data)

    def with_metadata(self, **kwargs: Any) -> CallbackEvent:
        """Create new event with additional metadata."""
        from dataclasses import replace
        new_metadata = {**self.metadata, **kwargs}
        return replace(self, metadata=new_metadata)


class Callback(ABC):
    """
    Abstract base class for callbacks.

    Callbacks are called at various points during execution.

    Example:
        class MyCallback(Callback):
            def on_chain_start(self, event: CallbackEvent) -> None:
                print(f"Chain started: {event.name}")

            def on_chain_end(self, event: CallbackEvent) -> None:
                print(f"Chain ended: {event.name}")
    """

    @abstractmethod
    def on_chain_start(self, event: CallbackEvent) -> None:
        """Called when chain starts."""
        pass

    @abstractmethod
    def on_chain_end(self, event: CallbackEvent) -> None:
        """Called when chain ends."""
        pass

    @abstractmethod
    def on_chain_error(self, event: CallbackEvent) -> None:
        """Called when chain errors."""
        pass

    @abstractmethod
    def on_step_start(self, event: CallbackEvent) -> None:
        """Called when step starts."""
        pass

    @abstractmethod
    def on_step_end(self, event: CallbackEvent) -> None:
        """Called when step ends."""
        pass

    @abstractmethod
    def on_step_error(self, event: CallbackEvent) -> None:
        """Called when step errors."""
        pass

    @abstractmethod
    def on_tool_start(self, event: CallbackEvent) -> None:
        """Called when tool starts."""
        pass

    @abstractmethod
    def on_tool_end(self, event: CallbackEvent) -> None:
        """Called when tool ends."""
        pass

    @abstractmethod
    def on_tool_error(self, event: CallbackEvent) -> None:
        """Called when tool errors."""
        pass

    @abstractmethod
    def on_llm_start(self, event: CallbackEvent) -> None:
        """Called when LLM starts."""
        pass

    @abstractmethod
    def on_llm_end(self, event: CallbackEvent) -> None:
        """Called when LLM ends."""
        pass

    @abstractmethod
    def on_llm_error(self, event: CallbackEvent) -> None:
        """Called when LLM errors."""
        pass

    @abstractmethod
    def on_llm_token(self, event: CallbackEvent) -> None:
        """Called when LLM generates a token."""
        pass

    def on_custom_event(self, event: CallbackEvent) -> None:
        """Called for custom events."""
        pass


class CallbackManager:
    """
    Manager for callbacks.

    Manages multiple callbacks and dispatches events.

    Example:
        manager = CallbackManager()
        manager.add_callback(LoggingCallback())
        manager.add_callback(MetricsCallback())

        # Dispatch events
        manager.dispatch(CallbackEvent(
            event_type=CallbackEventType.CHAIN_START,
            name="my_chain",
        ))
    """

    def __init__(self, config: Optional[Config] = None):
        self._config = config or Config()
        self._logger = Logger("CallbackManager")
        self._callbacks: List[Callback] = []
        self._event_history: List[CallbackEvent] = []

    @property
    def callbacks(self) -> List[Callback]:
        """Get registered callbacks."""
        return self._callbacks.copy()

    @property
    def event_history(self) -> List[CallbackEvent]:
        """Get event history."""
        return self._event_history.copy()

    def add_callback(self, callback: Callback) -> None:
        """
        Add a callback.

        Args:
            callback: Callback to add
        """
        self._callbacks.append(callback)
        self._logger.debug(f"Added callback: {callback.__class__.__name__}")

    def remove_callback(self, callback: Callback) -> bool:
        """
        Remove a callback.

        Args:
            callback: Callback to remove

        Returns:
            True if removed
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            self._logger.debug(f"Removed callback: {callback.__class__.__name__}")
            return True
        return False

    def clear_callbacks(self) -> None:
        """Remove all callbacks."""
        self._callbacks.clear()
        self._logger.debug("Cleared all callbacks")

    def dispatch(self, event: CallbackEvent) -> None:
        """
        Dispatch an event to all callbacks.

        Args:
            event: Event to dispatch
        """
        self._event_history.append(event)

        for callback in self._callbacks:
            try:
                self._dispatch_to_callback(callback, event)
            except Exception as e:
                self._logger.error(
                    f"Callback {callback.__class__.__name__} failed: {e}"
                )

    def _dispatch_to_callback(self, callback: Callback, event: CallbackEvent) -> None:
        """Dispatch event to a specific callback."""
        event_type = event.event_type

        if event_type == CallbackEventType.CHAIN_START:
            callback.on_chain_start(event)
        elif event_type == CallbackEventType.CHAIN_END:
            callback.on_chain_end(event)
        elif event_type == CallbackEventType.CHAIN_ERROR:
            callback.on_chain_error(event)
        elif event_type == CallbackEventType.STEP_START:
            callback.on_step_start(event)
        elif event_type == CallbackEventType.STEP_END:
            callback.on_step_end(event)
        elif event_type == CallbackEventType.STEP_ERROR:
            callback.on_step_error(event)
        elif event_type == CallbackEventType.TOOL_START:
            callback.on_tool_start(event)
        elif event_type == CallbackEventType.TOOL_END:
            callback.on_tool_end(event)
        elif event_type == CallbackEventType.TOOL_ERROR:
            callback.on_tool_error(event)
        elif event_type == CallbackEventType.LLM_START:
            callback.on_llm_start(event)
        elif event_type == CallbackEventType.LLM_END:
            callback.on_llm_end(event)
        elif event_type == CallbackEventType.LLM_ERROR:
            callback.on_llm_error(event)
        elif event_type == CallbackEventType.LLM_TOKEN:
            callback.on_llm_token(event)
        elif event_type == CallbackEventType.CUSTOM:
            callback.on_custom_event(event)

    def get_events_by_type(
        self, event_type: CallbackEventType
    ) -> List[CallbackEvent]:
        """
        Get events by type.

        Args:
            event_type: Event type to filter

        Returns:
            List of matching events
        """
        return [e for e in self._event_history if e.event_type == event_type]

    def get_events_by_name(self, name: str) -> List[CallbackEvent]:
        """
        Get events by name.

        Args:
            name: Event name to filter

        Returns:
            List of matching events
        """
        return [e for e in self._event_history if e.name == name]

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()

    def __len__(self) -> int:
        """Get number of callbacks."""
        return len(self._callbacks)

    def __repr__(self) -> str:
        """String representation."""
        callback_names = [c.__class__.__name__ for c in self._callbacks]
        return f"CallbackManager(callbacks={callback_names})"


class NoOpCallback(Callback):
    """No-op callback that does nothing."""

    def on_chain_start(self, event: CallbackEvent) -> None:
        pass

    def on_chain_end(self, event: CallbackEvent) -> None:
        pass

    def on_chain_error(self, event: CallbackEvent) -> None:
        pass

    def on_step_start(self, event: CallbackEvent) -> None:
        pass

    def on_step_end(self, event: CallbackEvent) -> None:
        pass

    def on_step_error(self, event: CallbackEvent) -> None:
        pass

    def on_tool_start(self, event: CallbackEvent) -> None:
        pass

    def on_tool_end(self, event: CallbackEvent) -> None:
        pass

    def on_tool_error(self, event: CallbackEvent) -> None:
        pass

    def on_llm_start(self, event: CallbackEvent) -> None:
        pass

    def on_llm_end(self, event: CallbackEvent) -> None:
        pass

    def on_llm_error(self, event: CallbackEvent) -> None:
        pass

    def on_llm_token(self, event: CallbackEvent) -> None:
        pass


class LambdaCallback(Callback):
    """
    Callback that delegates to lambda functions.

    Example:
        callback = LambdaCallback(
            on_chain_start=lambda e: print(f"Started: {e.name}"),
            on_chain_end=lambda e: print(f"Ended: {e.name}"),
        )
    """

    def __init__(
        self,
        on_chain_start: Optional[Callable[[CallbackEvent], None]] = None,
        on_chain_end: Optional[Callable[[CallbackEvent], None]] = None,
        on_chain_error: Optional[Callable[[CallbackEvent], None]] = None,
        on_step_start: Optional[Callable[[CallbackEvent], None]] = None,
        on_step_end: Optional[Callable[[CallbackEvent], None]] = None,
        on_step_error: Optional[Callable[[CallbackEvent], None]] = None,
        on_tool_start: Optional[Callable[[CallbackEvent], None]] = None,
        on_tool_end: Optional[Callable[[CallbackEvent], None]] = None,
        on_tool_error: Optional[Callable[[CallbackEvent], None]] = None,
        on_llm_start: Optional[Callable[[CallbackEvent], None]] = None,
        on_llm_end: Optional[Callable[[CallbackEvent], None]] = None,
        on_llm_error: Optional[Callable[[CallbackEvent], None]] = None,
        on_llm_token: Optional[Callable[[CallbackEvent], None]] = None,
        on_custom: Optional[Callable[[CallbackEvent], None]] = None,
    ):
        self._on_chain_start = on_chain_start
        self._on_chain_end = on_chain_end
        self._on_chain_error = on_chain_error
        self._on_step_start = on_step_start
        self._on_step_end = on_step_end
        self._on_step_error = on_step_error
        self._on_tool_start = on_tool_start
        self._on_tool_end = on_tool_end
        self._on_tool_error = on_tool_error
        self._on_llm_start = on_llm_start
        self._on_llm_end = on_llm_end
        self._on_llm_error = on_llm_error
        self._on_llm_token = on_llm_token
        self._on_custom = on_custom

    def on_chain_start(self, event: CallbackEvent) -> None:
        if self._on_chain_start:
            self._on_chain_start(event)

    def on_chain_end(self, event: CallbackEvent) -> None:
        if self._on_chain_end:
            self._on_chain_end(event)

    def on_chain_error(self, event: CallbackEvent) -> None:
        if self._on_chain_error:
            self._on_chain_error(event)

    def on_step_start(self, event: CallbackEvent) -> None:
        if self._on_step_start:
            self._on_step_start(event)

    def on_step_end(self, event: CallbackEvent) -> None:
        if self._on_step_end:
            self._on_step_end(event)

    def on_step_error(self, event: CallbackEvent) -> None:
        if self._on_step_error:
            self._on_step_error(event)

    def on_tool_start(self, event: CallbackEvent) -> None:
        if self._on_tool_start:
            self._on_tool_start(event)

    def on_tool_end(self, event: CallbackEvent) -> None:
        if self._on_tool_end:
            self._on_tool_end(event)

    def on_tool_error(self, event: CallbackEvent) -> None:
        if self._on_tool_error:
            self._on_tool_error(event)

    def on_llm_start(self, event: CallbackEvent) -> None:
        if self._on_llm_start:
            self._on_llm_start(event)

    def on_llm_end(self, event: CallbackEvent) -> None:
        if self._on_llm_end:
            self._on_llm_end(event)

    def on_llm_error(self, event: CallbackEvent) -> None:
        if self._on_llm_error:
            self._on_llm_error(event)

    def on_llm_token(self, event: CallbackEvent) -> None:
        if self._on_llm_token:
            self._on_llm_token(event)

    def on_custom_event(self, event: CallbackEvent) -> None:
        if self._on_custom:
            self._on_custom(event)
