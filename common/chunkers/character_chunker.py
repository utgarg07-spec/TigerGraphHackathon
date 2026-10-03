from common.chunkers.base_chunker import BaseChunker

_DEFAULT_CHUNK_SIZE = 2048


class CharacterChunker(BaseChunker):
    def __init__(self, chunk_size=0, overlap_size=-1):
        self.chunk_size = chunk_size if chunk_size > 0 else _DEFAULT_CHUNK_SIZE
        self.overlap_size = overlap_size if overlap_size >= 0 else self.chunk_size // 8

    def chunk(self, input_string):
        if self.chunk_size <= self.overlap_size:
            raise ValueError("Chunk size must be larger than overlap size")

        chunks = []
        i = 0
        while i < len(input_string):
            chunk = input_string[i : i + self.chunk_size]
            chunks.append(chunk)

            i += self.chunk_size - self.overlap_size
            if i + self.overlap_size >= len(input_string):
                break
        return chunks

    def __call__(self, input_string):
        return self.chunk(input_string)
