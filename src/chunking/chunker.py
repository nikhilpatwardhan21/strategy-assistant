import os

class DocumentChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> list[str]:
        """
        Splits a long string of text into smaller, overlapping chunks
        to preserve context across boundaries.
        """
        if not text or not text.strip():
            return []
            
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk.strip())
            # Move the window forward by chunk_size minus overlap
            start += (self.chunk_size - self.chunk_overlap)
            
        return chunks