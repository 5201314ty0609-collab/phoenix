"""
Memory Compressor — Text compression and summarization.

Provides utilities for compressing memory content while preserving
key information. Used by the consolidation engine and STM summarization.

Compression strategies:
1. Extractive summarization (select key sentences)
2. Message group summarization (merge related messages)
3. Token budget compression (fit content into token limits)
4. Deduplication (remove near-duplicate content)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .memory_types import MemoryMessage, _estimate_tokens


@dataclass(frozen=True)
class CompressionResult:
    """
    Result of a compression operation.

    Attributes:
        original: Original text.
        compressed: Compressed/summarized text.
        original_tokens: Token count before compression.
        compressed_tokens: Token count after compression.
        ratio: Compression ratio (compressed / original).
        strategy: Which compression strategy was used.
    """
    original: str
    compressed: str
    original_tokens: int
    compressed_tokens: int
    ratio: float
    strategy: str


class MemoryCompressor:
    """
    Text compression utilities for memory content.

    Uses rule-based extractive summarization (no LLM dependency).
    Suitable for compressing conversation history and memory entries
    to fit within token budgets.

    Example:
        compressor = MemoryCompressor()

        # Compress a long text to fit a token budget
        result = compressor.compress_to_budget(
            text="Very long text...",
            max_tokens=500,
        )
        print(result.compressed)
        print(f"Compression ratio: {result.ratio:.2f}")
    """

    # ── Sentence Extraction ─────────────────────────────────────

    def extract_key_sentences(
        self,
        text: str,
        max_sentences: int = 3,
    ) -> list[str]:
        """
        Extract the most important sentences from text.

        Scoring heuristic:
        - Position: first and last sentences get bonus
        - Length: medium-length sentences preferred (10-30 words)
        - Keywords: sentences with important-looking terms scored higher
        - Question marks: questions get a small bonus

        Args:
            text: Input text.
            max_sentences: Maximum sentences to extract.

        Returns:
            List of key sentences in original order.
        """
        sentences = self._split_sentences(text)
        if len(sentences) <= max_sentences:
            return sentences

        # Score each sentence
        scored: list[tuple[int, float, str]] = []
        for i, sentence in enumerate(sentences):
            score = self._score_sentence(sentence, i, len(sentences))
            scored.append((i, score, sentence))

        # Select top sentences, preserve original order
        scored.sort(key=lambda x: x[1], reverse=True)
        selected = sorted(scored[:max_sentences], key=lambda x: x[0])

        return [s[2] for s in selected]

    # ── Compression Strategies ──────────────────────────────────

    def compress_to_budget(
        self,
        text: str,
        max_tokens: int,
        strategy: str = "auto",
    ) -> CompressionResult:
        """
        Compress text to fit within a token budget.

        Args:
            text: Input text.
            max_tokens: Maximum allowed tokens.
            strategy: "extractive", "truncate", or "auto".

        Returns:
            CompressionResult with the compressed text.
        """
        original_tokens = _estimate_tokens(text)

        if original_tokens <= max_tokens:
            return CompressionResult(
                original=text,
                compressed=text,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                ratio=1.0,
                strategy="none",
            )

        if strategy == "auto":
            strategy = "extractive" if original_tokens > max_tokens * 2 else "truncate"

        if strategy == "extractive":
            # Extract key sentences to fit budget
            sentences = self._split_sentences(text)
            selected: list[str] = []
            used_tokens = 0

            # Score all sentences
            scored = [
                (i, self._score_sentence(s, i, len(sentences)), s)
                for i, s in enumerate(sentences)
            ]
            scored.sort(key=lambda x: x[1], reverse=True)

            for _, _, sentence in scored:
                st = _estimate_tokens(sentence)
                if used_tokens + st <= max_tokens:
                    selected.append(sentence)
                    used_tokens += st
                if used_tokens >= max_tokens * 0.9:
                    break

            # Restore original order
            selected_set = set(selected)
            ordered = [s for s in sentences if s in selected_set]
            compressed = " ".join(ordered)
        else:
            # Simple truncation
            compressed = self._truncate_to_tokens(text, max_tokens)

        compressed_tokens = _estimate_tokens(compressed)

        return CompressionResult(
            original=text,
            compressed=compressed,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            ratio=compressed_tokens / original_tokens if original_tokens > 0 else 1.0,
            strategy=strategy,
        )

    def compress_messages(
        self,
        messages: list[MemoryMessage],
        max_tokens: int,
    ) -> tuple[list[MemoryMessage], CompressionResult]:
        """
        Compress a list of messages to fit within a token budget.

        Strategy:
        1. If within budget, return unchanged
        2. Group consecutive messages by role
        3. Merge groups into condensed messages
        4. Extract key content if still over budget

        Args:
            messages: List of messages to compress.
            max_tokens: Maximum total token budget.

        Returns:
            Tuple of (compressed messages, compression result).
        """
        total_tokens = sum(m.token_count for m in messages)

        if total_tokens <= max_tokens:
            return messages, CompressionResult(
                original=f"{len(messages)} messages",
                compressed=f"{len(messages)} messages",
                original_tokens=total_tokens,
                compressed_tokens=total_tokens,
                ratio=1.0,
                strategy="none",
            )

        # Group consecutive messages by role
        groups: list[list[MemoryMessage]] = []
        current_group: list[MemoryMessage] = []
        current_role: str | None = None

        for msg in messages:
            if msg.role != current_role and current_group:
                groups.append(current_group)
                current_group = []
            current_group.append(msg)
            current_role = msg.role
        if current_group:
            groups.append(current_group)

        # Merge each group into a single message
        merged: list[MemoryMessage] = []
        for group in groups:
            if len(group) == 1:
                merged.append(group[0])
            else:
                # Merge: combine content, keep max importance
                combined_content = "\n".join(m.content for m in group)
                max_importance = max(m.importance for m in group)
                merged.append(MemoryMessage.create(
                    role=group[0].role,
                    content=combined_content,
                    importance=max_importance,
                ))

        # If still over budget, use extractive compression
        merged_tokens = sum(m.token_count for m in merged)
        if merged_tokens > max_tokens:
            # Budget per message
            per_msg_budget = max_tokens // len(merged)
            compressed_msgs: list[MemoryMessage] = []
            for msg in merged:
                if msg.token_count > per_msg_budget:
                    result = self.compress_to_budget(msg.content, per_msg_budget)
                    compressed_msgs.append(MemoryMessage.create(
                        role=msg.role,
                        content=result.compressed,
                        importance=msg.importance,
                    ))
                else:
                    compressed_msgs.append(msg)
            merged = compressed_msgs

        final_tokens = sum(m.token_count for m in merged)

        return merged, CompressionResult(
            original=f"{len(messages)} messages ({total_tokens} tokens)",
            compressed=f"{len(merged)} messages ({final_tokens} tokens)",
            original_tokens=total_tokens,
            compressed_tokens=final_tokens,
            ratio=final_tokens / total_tokens if total_tokens > 0 else 1.0,
            strategy="group+extractive",
        )

    def deduplicate(
        self,
        texts: list[str],
        similarity_threshold: float = 0.8,
    ) -> tuple[list[str], int]:
        """
        Remove near-duplicate texts.

        Uses token-based Jaccard similarity to detect duplicates.

        Args:
            texts: List of texts to deduplicate.
            similarity_threshold: Jaccard threshold for duplicate detection.

        Returns:
            Tuple of (deduplicated texts, number removed).
        """
        if len(texts) <= 1:
            return texts, 0

        kept: list[str] = []
        kept_tokens: list[set[str]] = []
        removed = 0

        for text in texts:
            tokens = self._tokenize(text)
            is_duplicate = False

            for existing_tokens in kept_tokens:
                jaccard = self._jaccard(tokens, existing_tokens)
                if jaccard >= similarity_threshold:
                    is_duplicate = True
                    removed += 1
                    break

            if not is_duplicate:
                kept.append(text)
                kept_tokens.append(tokens)

        return kept, removed

    # ── Internal ────────────────────────────────────────────────

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        # Handle multiple sentence delimiters
        sentences = re.split(r'(?<=[.!?。！？])\s+', text)
        # Also split on newlines for multi-line content
        result: list[str] = []
        for s in sentences:
            parts = s.strip().split('\n')
            for p in parts:
                p = p.strip()
                if p:
                    result.append(p)
        return result

    def _score_sentence(
        self,
        sentence: str,
        position: int,
        total: int,
    ) -> float:
        """
        Score a sentence for importance.

        Heuristics:
        - Position: first and last sentences get bonus
        - Length: medium sentences (5-30 words) preferred
        - Keywords: presence of important terms
        """
        score = 0.0

        # Position bonus: first and last
        if position == 0:
            score += 0.3
        elif position == total - 1:
            score += 0.15
        elif position <= total * 0.2:
            score += 0.1

        # Length scoring
        word_count = len(sentence.split())
        if 5 <= word_count <= 30:
            score += 0.2
        elif word_count < 3:
            score -= 0.2

        # Keyword presence
        important_patterns = [
            r'\b(important|critical|key|must|should|never|always)\b',
            r'\b(error|warning|issue|problem|fix)\b',
            r'\b(decision|chose|decided|concluded)\b',
            r'\b(prefer|like|want|need)\b',
            r'\b结论|决定|重要|关键|必须|问题|修复\b',
        ]
        for pattern in important_patterns:
            if re.search(pattern, sentence, re.IGNORECASE):
                score += 0.1

        # Question bonus
        if sentence.rstrip().endswith('?'):
            score += 0.05

        return score

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to approximately fit token budget."""
        # Rough: 4 chars per token
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text

        # Try to break at sentence boundary
        truncated = text[:max_chars]
        last_period = max(
            truncated.rfind('.'),
            truncated.rfind('!'),
            truncated.rfind('?'),
            truncated.rfind('。'),
        )
        if last_period > max_chars * 0.5:
            return truncated[:last_period + 1]

        return truncated + "..."

    def _tokenize(self, text: str) -> set[str]:
        """Tokenize text into lowercase terms."""
        return {t.lower() for t in text.split() if len(t) >= 2}

    def _jaccard(self, set_a: set[str], set_b: set[str]) -> float:
        """Compute Jaccard similarity between two token sets."""
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0
