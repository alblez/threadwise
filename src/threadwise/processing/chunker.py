"""Thread-aware chunking for RAG ingestion."""

import re

import tiktoken

from threadwise.core.models import Chunk, ChunkMetadata, ProcessedMessage, ProcessedThread
from threadwise.processing.config import ChunkingConfig


class ThreadChunker:
    """Splits processed email threads into chunks for RAG storage."""

    def __init__(self, config: ChunkingConfig | None = None) -> None:
        self._config = config or ChunkingConfig()
        self._encoder = tiktoken.get_encoding(self._config.tokenizer)

    def chunk_thread(self, thread: ProcessedThread, project_id: str) -> list[Chunk]:
        """Split a processed thread into chunks."""
        if not thread.messages:
            return []

        formatted = [self._format_message(m) for m in thread.messages]
        token_counts = [self._count_tokens(f) for f in formatted]
        total_tokens = sum(token_counts)

        # Single chunk path
        if total_tokens <= self._config.chunk_size:
            text = "\n\n".join(formatted)
            return [
                self._build_chunk(
                    thread, project_id, 0, text, thread.messages[0], thread_context=None
                )
            ]

        # Multi-chunk: walk messages and split
        chunks: list[Chunk] = []
        current_texts: list[str] = []
        current_tokens = 0
        current_first_msg_idx = 0

        for i, (fmt, tcount) in enumerate(zip(formatted, token_counts, strict=True)):
            fits = current_tokens + tcount + (2 if current_texts else 0) <= self._config.chunk_size

            if fits:
                current_texts.append(fmt)
                current_tokens += tcount + (2 if len(current_texts) > 1 else 0)
            else:
                # Finalize current chunk if non-empty
                if current_texts:
                    text = "\n\n".join(current_texts)
                    context = self._build_thread_context(
                        thread.messages[:current_first_msg_idx]
                    )
                    chunks.append(
                        self._build_chunk(
                            thread,
                            project_id,
                            len(chunks),
                            text,
                            thread.messages[current_first_msg_idx],
                            thread_context=context,
                        )
                    )

                # Handle oversized single message
                if tcount > self._config.chunk_size:
                    sub_texts = self._split_oversized_text(fmt)
                    context = self._build_thread_context(thread.messages[:i])
                    for j, sub in enumerate(sub_texts):
                        chunks.append(
                            self._build_chunk(
                                thread,
                                project_id,
                                len(chunks),
                                sub,
                                thread.messages[i],
                                thread_context=context if (j == 0 or chunks) else None,
                            )
                        )
                    current_texts = []
                    current_tokens = 0
                    current_first_msg_idx = i + 1
                else:
                    current_texts = [fmt]
                    current_tokens = tcount
                    current_first_msg_idx = i

        # Finalize remaining
        if current_texts:
            text = "\n\n".join(current_texts)
            context = self._build_thread_context(thread.messages[:current_first_msg_idx])
            chunks.append(
                self._build_chunk(
                    thread,
                    project_id,
                    len(chunks),
                    text,
                    thread.messages[current_first_msg_idx],
                    thread_context=context,
                )
            )

        return chunks

    def _count_tokens(self, text: str) -> int:
        return len(self._encoder.encode(text))

    def _format_message_header(self, message: ProcessedMessage) -> str:
        return f"**From: {message.sender} ({message.date:%Y-%m-%d %H:%M})**"

    def _format_message(self, message: ProcessedMessage) -> str:
        header = self._format_message_header(message)
        return f"{header}\n\n{message.content}"

    def _build_thread_context(self, preceding: list[ProcessedMessage]) -> str | None:
        if not preceding:
            return None

        budget = 100
        parts: list[str] = []
        used = self._count_tokens("[Preceding:  | ]")

        for msg in preceding:
            name = self._extract_display_name(msg.sender)
            first_line = msg.content.split("\n", 1)[0][:80]
            date_str = msg.date.strftime("%b %d")
            part = f"{name} ({date_str}): '{first_line}...'"
            part_tokens = self._count_tokens(part)
            if used + part_tokens > budget:
                break
            parts.append(part)
            used += part_tokens

        if not parts:
            return None

        return f"[Preceding: {' | '.join(parts)}]"

    def _extract_display_name(self, sender: str) -> str:
        match = re.match(r"^(.+?)\s*<[^>]+>$", sender)
        if match:
            return match.group(1).strip()
        return sender

    def _split_oversized_text(self, text: str) -> list[str]:
        overlap = self._config.chunk_overlap
        chunk_size = self._config.chunk_size

        # Try paragraph splits first
        paragraphs = text.split("\n\n")
        if len(paragraphs) > 1:
            result = self._merge_segments(paragraphs, "\n\n", chunk_size, overlap)
            if all(self._count_tokens(r) <= chunk_size for r in result):
                return result

        # Try sentence splits
        sentences = re.split(r"(?<=[.?!]) ", text)
        if len(sentences) > 1:
            result = self._merge_segments(sentences, " ", chunk_size, overlap)
            if all(self._count_tokens(r) <= chunk_size for r in result):
                return result

        # Last resort: token boundary
        return self._split_at_token_boundary(text, chunk_size, overlap)

    def _merge_segments(
        self, segments: list[str], separator: str, chunk_size: int, overlap: int
    ) -> list[str]:
        chunks: list[str] = []
        current_parts: list[str] = []
        current_tokens = 0

        for seg in segments:
            seg_tokens = self._count_tokens(seg)
            sep_tokens = self._count_tokens(separator) if current_parts else 0

            if current_tokens + sep_tokens + seg_tokens <= chunk_size:
                current_parts.append(seg)
                current_tokens += sep_tokens + seg_tokens
            else:
                if current_parts:
                    chunks.append(separator.join(current_parts))
                # Apply overlap: take trailing tokens from previous chunk
                if chunks and overlap > 0:
                    prev_tokens = self._encoder.encode(chunks[-1])
                    overlap_tokens = prev_tokens[-overlap:]
                    overlap_text = self._encoder.decode(overlap_tokens)
                    current_parts = [overlap_text, seg]
                    current_tokens = self._count_tokens(overlap_text) + seg_tokens
                else:
                    current_parts = [seg]
                    current_tokens = seg_tokens

        if current_parts:
            chunks.append(separator.join(current_parts))

        return chunks

    def _split_at_token_boundary(
        self, text: str, chunk_size: int, overlap: int
    ) -> list[str]:
        tokens = self._encoder.encode(text)
        chunks: list[str] = []
        start = 0
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_text = self._encoder.decode(tokens[start:end])
            chunks.append(chunk_text)
            # Advance with overlap, but always by ≥1 token to prevent infinite loops
            start = max(end - overlap, start + 1) if end < len(tokens) else end
        return chunks

    def _build_chunk(
        self,
        thread: ProcessedThread,
        project_id: str,
        chunk_index: int,
        text: str,
        first_message: ProcessedMessage,
        thread_context: str | None,
    ) -> Chunk:
        return Chunk(
            id=f"{thread.thread_id}:{chunk_index}",
            text=text,
            embedding=None,
            metadata=ChunkMetadata(
                project_id=project_id,
                source_type="gmail",
                source_id=thread.thread_id,
                chunk_index=chunk_index,
                author=first_message.sender,
                date=first_message.date,
                subject=thread.subject,
                thread_context=thread_context,
                chunk_level="detail",
            ),
        )
