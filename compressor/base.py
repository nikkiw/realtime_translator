from abc import ABC, abstractmethod
from typing import List

class BaseCompressor(ABC):
    """
    Base class for context compressors.
    Responsible for accumulating and compressing context history for translators.
    """
    
    def __init__(self, compression_threshold: int = 800):
        """
        Initializes the compressor.
        
        Args:
            compression_threshold: Character count threshold to trigger compression
        """
        self.compression_threshold = compression_threshold
        self.context: List[str] = []
        self.current_size = 0
    
    def add_text(self, text: str | list[str]) -> None:
        """
        Adds new text to the context.
        Triggers compression if the size exceeds the threshold.
        """
        if isinstance(text, list):
            text = "\n ".join(text)
        else:
            text = str(text)
            
        self.context.append(text)
        self.current_size += len(text)
        
        if self.current_size > self.compression_threshold:
            self.compress()
    
    @abstractmethod
    def compress(self) -> None:
        """
        Compresses the context.
        Must be implemented by subclasses.
        """
        pass
    
    @abstractmethod
    def get_context(self) -> str:
        """
        Returns the current context as a string.
        """
        pass
