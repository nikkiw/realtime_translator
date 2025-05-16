from abc import ABC, abstractmethod
from typing import Optional
from compressor.base import BaseCompressor      

class BaseTranslator(ABC):
    def __init__(self):
        self.compressor: Optional[BaseCompressor] = None

    def set_compressor(self, compressor: BaseCompressor) -> None:
        """
        Sets the compressor for managing translation context.
        """
        self.compressor = compressor

    def get_context(self) -> str:
        """
        Retrieves the accumulated context from the compressor.
        """
        if self.compressor:
            return self.compressor.get_context()
        return ""

    def translate(self, text: str) -> str:
        """
        Translates text, possibly using the accumulated context.
        """
        context: str | None = None
        if self.compressor:
            context = self.compressor.get_context()
        translated_text = self.translate_with_context(text, context)
        if self.compressor:
            self.compressor.add_text(text)
        return translated_text
    
    @abstractmethod
    def translate_with_context(self, text: str, context: str| None) -> str:
        """
        Translates text using the provided context.
        """
        pass


