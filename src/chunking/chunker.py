import re
from typing import List

class DocumentChunker:
    """
    Advanced semantic chunker that respects sentence and paragraph boundaries
    to preserve context and meaning in chunks.
    """
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences while preserving structure."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        paragraphs = re.split(r'\n\n+', text)
        return [p.strip() for p in paragraphs if p.strip()]

    def chunk_text(self, text: str) -> List[str]:
        """
        Intelligently chunk text by respecting paragraph and sentence boundaries.
        Combines paragraphs into semantic chunks while preserving context.
        """
        if not text or not text.strip():
            return []

        paragraphs = self._split_into_paragraphs(text)
        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            if current_chunk and len(current_chunk) + len(paragraph) > self.chunk_size:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # Add context overlap between chunks
        if len(chunks) > 1:
            enhanced_chunks = []
            for i, chunk in enumerate(chunks):
                if i == 0:
                    enhanced_chunks.append(chunk)
                else:
                    prev_sentences = self._split_into_sentences(chunks[i-1])
                    overlap_text = " ".join(prev_sentences[-2:]) if len(prev_sentences) >= 2 else chunks[i-1][:self.chunk_overlap]
                    enhanced_chunks.append(overlap_text + "\n\n" + chunk)
            return enhanced_chunks

        return chunks