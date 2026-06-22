"""
Vector store retriever memory implementation.

Uses vector similarity to retrieve relevant memories.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..core import Config, Logger
from .base import Memory, MemoryType


@dataclass(frozen=True)
class VectorEntry:
    """
    A vector memory entry.

    Attributes:
        id: Entry ID
        text: Text content
        vector: Embedding vector
        metadata: Additional metadata
        timestamp: Creation timestamp
    """
    id: str
    text: str
    vector: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class VectorStore:
    """
    Simple in-memory vector store.

    Stores vectors and supports similarity search.
    """

    def __init__(self, dimension: int = 768):
        self._dimension = dimension
        self._entries: List[VectorEntry] = []
        self._logger = Logger("VectorStore")

    @property
    def dimension(self) -> int:
        """Get vector dimension."""
        return self._dimension

    @property
    def size(self) -> int:
        """Get number of entries."""
        return len(self._entries)

    def add(
        self,
        id: str,
        text: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a vector entry.

        Args:
            id: Entry ID
            text: Text content
            vector: Embedding vector
            metadata: Additional metadata
        """
        if len(vector) != self._dimension:
            raise ValueError(
                f"Vector dimension mismatch: expected {self._dimension}, got {len(vector)}"
            )

        entry = VectorEntry(
            id=id,
            text=text,
            vector=vector,
            metadata=metadata or {},
        )
        self._entries.append(entry)
        self._logger.debug(f"Added entry: {id}")

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> List[Tuple[VectorEntry, float]]:
        """
        Search for similar vectors.

        Args:
            query_vector: Query vector
            top_k: Number of results
            threshold: Minimum similarity threshold

        Returns:
            List of (entry, similarity) tuples
        """
        if len(query_vector) != self._dimension:
            raise ValueError(
                f"Query vector dimension mismatch: expected {self._dimension}, got {len(query_vector)}"
            )

        # Calculate similarities
        results = []
        for entry in self._entries:
            similarity = self._cosine_similarity(query_vector, entry.vector)
            if similarity >= threshold:
                results.append((entry, similarity))

        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def delete(self, id: str) -> bool:
        """
        Delete an entry by ID.

        Args:
            id: Entry ID

        Returns:
            True if deleted
        """
        for i, entry in enumerate(self._entries):
            if entry.id == id:
                self._entries.pop(i)
                self._logger.debug(f"Deleted entry: {id}")
                return True
        return False

    def clear(self) -> None:
        """Clear all entries."""
        self._entries.clear()
        self._logger.debug("Cleared all entries")

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)


class VectorStoreRetrieverMemory(Memory):
    """
    Vector store retriever memory.

    Uses vector similarity to retrieve relevant memories.

    Example:
        def embedder(text):
            # Your embedding logic here
            return [0.1, 0.2, ...]

        memory = VectorStoreRetrieverMemory(embedder=embedder)
        memory.add_user_message("I love Python programming")
        memory.add_ai_message("Python is great!")

        # Later, retrieve relevant memories
        relevant = memory.search("What programming language do I like?")
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        embedder: Optional[Callable[[str], List[float]]] = None,
        vector_store: Optional[VectorStore] = None,
        dimension: int = 768,
        top_k: int = 5,
        threshold: float = 0.5,
    ):
        super().__init__(config)
        self._embedder = embedder
        self._vector_store = vector_store or VectorStore(dimension)
        self._top_k = top_k
        self._threshold = threshold
        self._messages: List[Dict[str, str]] = []
        self._logger = Logger("VectorStoreRetrieverMemory")

    @property
    def memory_type(self) -> MemoryType:
        """Get memory type."""
        return MemoryType.VECTOR

    @property
    def vector_store(self) -> VectorStore:
        """Get vector store."""
        return self._vector_store

    def add_user_message(self, message: str) -> None:
        """
        Add a user message.

        Args:
            message: User message
        """
        self._messages.append({"role": "user", "content": message})
        self._add_to_vector_store(message, "user")
        self._logger.debug(f"Added user message: {message[:50]}...")

    def add_ai_message(self, message: str) -> None:
        """
        Add an AI message.

        Args:
            message: AI message
        """
        self._messages.append({"role": "ai", "content": message})
        self._add_to_vector_store(message, "ai")
        self._logger.debug(f"Added AI message: {message[:50]}...")

    def _add_to_vector_store(self, text: str, role: str) -> None:
        """Add text to vector store."""
        if not self._embedder:
            self._logger.warning("No embedder provided, skipping vector storage")
            return

        try:
            vector = self._embedder(text)
            id = f"{role}_{len(self._messages)}_{int(time.time())}"
            self._vector_store.add(
                id=id,
                text=text,
                vector=vector,
                metadata={"role": role, "timestamp": time.time()},
            )
        except Exception as e:
            self._logger.error(f"Failed to add to vector store: {e}")

    def get_messages(self) -> List[Dict[str, str]]:
        """
        Get all messages.

        Returns:
            List of message dicts
        """
        return self._messages.copy()

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> List[Tuple[str, float]]:
        """
        Search for relevant memories.

        Args:
            query: Search query
            top_k: Number of results
            threshold: Minimum similarity threshold

        Returns:
            List of (text, similarity) tuples
        """
        if not self._embedder:
            self._logger.warning("No embedder provided, cannot search")
            return []

        try:
            query_vector = self._embedder(query)
            results = self._vector_store.search(
                query_vector=query_vector,
                top_k=top_k or self._top_k,
                threshold=threshold or self._threshold,
            )
            return [(entry.text, similarity) for entry, similarity in results]
        except Exception as e:
            self._logger.error(f"Search failed: {e}")
            return []

    def get_relevant_context(
        self,
        query: str,
        max_entries: int = 5,
    ) -> str:
        """
        Get relevant context for a query.

        Args:
            query: Query text
            max_entries: Maximum entries to include

        Returns:
            Formatted context string
        """
        results = self.search(query, top_k=max_entries)

        if not results:
            return ""

        lines = ["Relevant memories:"]
        for text, similarity in results:
            lines.append(f"- {text} (similarity: {similarity:.2f})")

        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all messages and vectors."""
        self._messages.clear()
        self._vector_store.clear()
        self._logger.debug("Cleared all messages and vectors")

    def invoke(self, input_data: Dict[str, Any]) -> Any:
        """
        Execute memory operation.

        Args:
            input_data: Input data

        Returns:
            ExecutionResult
        """
        action = input_data.get("action", "get_messages")

        if action == "search":
            from ..core import ExecutionResult
            results = self.search(
                query=input_data["query"],
                top_k=input_data.get("top_k"),
                threshold=input_data.get("threshold"),
            )
            return ExecutionResult.success_result(data=results)

        if action == "get_relevant_context":
            from ..core import ExecutionResult
            context = self.get_relevant_context(
                query=input_data["query"],
                max_entries=input_data.get("max_entries", 5),
            )
            return ExecutionResult.success_result(data=context)

        return super().invoke(input_data)

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """
        Save context from interaction.

        Args:
            inputs: Input data
            outputs: Output data
        """
        user_message = inputs.get("input", "")
        ai_message = outputs.get("output", "")

        if user_message:
            self.add_user_message(user_message)
        if ai_message:
            self.add_ai_message(ai_message)

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load memory variables.

        Args:
            inputs: Input data

        Returns:
            Dict with 'history' and 'relevant_context' keys
        """
        query = inputs.get("input", "")
        relevant_context = self.get_relevant_context(query) if query else ""

        return {
            "history": self.get_messages(),
            "relevant_context": relevant_context,
        }

    def __len__(self) -> int:
        """Get number of messages."""
        return len(self._messages)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"VectorStoreRetrieverMemory("
            f"messages={len(self._messages)}, "
            f"vectors={self._vector_store.size}, "
            f"top_k={self._top_k})"
        )


def vector_memory(
    embedder: Optional[Callable[[str], List[float]]] = None,
    dimension: int = 768,
    top_k: int = 5,
    threshold: float = 0.5,
    config: Optional[Config] = None,
) -> VectorStoreRetrieverMemory:
    """
    Create a vector store retriever memory.

    Args:
        embedder: Embedding function
        dimension: Vector dimension
        top_k: Number of results to retrieve
        threshold: Minimum similarity threshold
        config: Configuration

    Returns:
        VectorStoreRetrieverMemory

    Example:
        def my_embedder(text):
            # Your embedding logic
            return [0.1, 0.2, ...]

        memory = vector_memory(embedder=my_embedder)
        memory.add_user_message("I love Python")
        results = memory.search("What language do I like?")
    """
    return VectorStoreRetrieverMemory(
        config=config,
        embedder=embedder,
        dimension=dimension,
        top_k=top_k,
        threshold=threshold,
    )
