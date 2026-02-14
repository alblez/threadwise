"""Thread summarization for hierarchical RAG retrieval."""

import tiktoken

from threadwise.core.models import Chunk, ChunkMetadata, ProcessedThread
from threadwise.processing.config import SummarizationConfig


class ThreadSummarizer:
    """Generates a single summary chunk per thread."""

    def __init__(self, config: SummarizationConfig) -> None:
        self._config = config
        self._encoder = tiktoken.get_encoding("cl100k_base")

    def summarize_thread(self, thread: ProcessedThread, project_id: str) -> Chunk:
        """Produce a summary chunk for the given thread."""
        if self._config.method == "llm":
            summary_text = self._llm_summary(thread)
        else:
            summary_text = self._extractive_summary(thread)
        return self._build_summary_chunk(thread, project_id, summary_text)

    def _count_tokens(self, text: str) -> int:
        return len(self._encoder.encode(text))

    def _llm_summary(self, thread: ProcessedThread) -> str:
        formatted_parts: list[str] = []
        for msg in thread.messages:
            header = f"**From: {msg.sender} ({msg.date:%Y-%m-%d %H:%M})**"
            formatted_parts.append(f"{header}\n\n{msg.content}")

        budget = self._config.context_window - self._config.max_summary_tokens - 500
        combined = "\n\n".join(formatted_parts)

        if self._count_tokens(combined) > budget:
            # Keep recent messages, drop oldest first
            kept: list[str] = []
            used = 0
            for part in reversed(formatted_parts):
                part_tokens = self._count_tokens(part)
                if used + part_tokens + 2 > budget:
                    break
                kept.insert(0, part)
                used += part_tokens + 2
            combined = "[Earlier messages truncated]\n\n" + "\n\n".join(kept)

        prompt = (
            "Summarize the following email thread in a concise paragraph. "
            "Focus on the key topics, decisions, and action items.\n\n"
            f"{combined}"
        )

        return self._config.llm_provider.generate(prompt)  # type: ignore[union-attr]

    def _extractive_summary(self, thread: ProcessedThread) -> str:
        def first_paragraph(content: str, max_tokens: int = 150) -> str:
            para = content.split("\n\n")[0]
            tokens = self._encoder.encode(para)
            if len(tokens) > max_tokens:
                para = self._encoder.decode(tokens[:max_tokens])
            return para

        if len(thread.messages) == 1:
            excerpt = first_paragraph(thread.messages[0].content)
            return f"Thread: {thread.subject}\n\n{excerpt}"

        first_excerpt = first_paragraph(thread.messages[0].content)
        last_excerpt = first_paragraph(thread.messages[-1].content)
        return (
            f"Thread: {thread.subject}\n\n"
            f"{first_excerpt}\n\n"
            f"[...]\n\n"
            f"{last_excerpt}"
        )

    def _build_summary_chunk(
        self, thread: ProcessedThread, project_id: str, summary_text: str
    ) -> Chunk:
        first_msg = thread.messages[0]
        return Chunk(
            id=f"{thread.thread_id}:summary",
            text=summary_text,
            embedding=None,
            metadata=ChunkMetadata(
                project_id=project_id,
                source_type="gmail",
                source_id=thread.thread_id,
                chunk_index=-1,
                chunk_level="summary",
                author=first_msg.sender,
                date=first_msg.date,
                subject=thread.subject,
                thread_context=None,
            ),
        )
