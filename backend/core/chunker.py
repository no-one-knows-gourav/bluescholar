"""Document chunking strategies for the processing pipeline."""


class TextChunker:
    """Recursive character text splitter with configurable chunk size and overlap.

    Default config matches prototype spec: chunk_size=512, overlap=64.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._separators = ["\n\n", "\n", ". ", " ", ""]

    def split(self, text: str) -> list[str]:
        """Split text into overlapping chunks using recursive character splitting."""
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        chunks = []
        self._recursive_split(text, chunks, self._separators)
        return chunks

    def _recursive_split(self, text: str, chunks: list[str], separators: list[str]) -> None:
        """Recursively split text by trying separators in order."""
        if len(text) <= self.chunk_size:
            stripped = text.strip()
            if stripped:
                chunks.append(stripped)
            return

        separator = separators[0] if separators else ""
        remaining_separators = separators[1:] if len(separators) > 1 else [""]

        if separator:
            parts = text.split(separator)
        else:
            # Last resort: hard split by character count
            for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
                chunk = text[i : i + self.chunk_size].strip()
                if chunk:
                    chunks.append(chunk)
            return

        current_chunk = ""
        for i, part in enumerate(parts):
            candidate = (current_chunk + separator + part).strip() if current_chunk else part.strip()

            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                # Flush current chunk
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())

                # If this single part exceeds chunk_size, try next separator
                if len(part) > self.chunk_size:
                    self._recursive_split(part, chunks, remaining_separators)
                    current_chunk = ""
                else:
                    current_chunk = part.strip()

        # Flush remaining
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

    def split_with_metadata(self, text: str, base_metadata: dict | None = None) -> list[dict]:
        """Split text and attach chunk index metadata to each piece."""
        raw_chunks = self.split(text)
        result = []
        for i, chunk in enumerate(raw_chunks):
            meta = {"chunk_index": i, "text": chunk}
            if base_metadata:
                meta.update(base_metadata)
            result.append(meta)
        return result


# Default chunker instance
chunker = TextChunker()
