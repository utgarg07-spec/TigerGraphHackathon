"""
Single Chunker - Always returns the entire content as ONE chunk.
Used for images to preserve markdown image references and prevent splitting.
"""
from common.chunkers.base_chunker import BaseChunker


class SingleChunker(BaseChunker):
    """
    Chunker that NEVER splits content - always returns ONE chunk.
    
    This is critical for image descriptions to:
    1. Keep markdown image references (e.g., ![desc](tg://id)) intact
    2. Prevent losing image references when displayed in UI
    3. Maintain semantic integrity of image descriptions
    """
    
    def chunk(self, text: str) -> list[str]:
        """
        Return the entire text as a single chunk, regardless of length.
        
        Args:
            text: The text to "chunk" (actually just return as-is)
            
        Returns:
            List with single element containing all text
        """
        # Always return ONE chunk with entire content
        return [text] if text and text.strip() else []

