from abc import ABC, abstractmethod
from typing import List, Tuple

class BaseRenderer(ABC):
    """
    Abstract base class for renderers.
    """
    @abstractmethod
    def render(self, translations: List[Tuple[str, str]]):
        """
        Render the translations table.
        """
        pass

    @abstractmethod
    def run(self):
        """
        Base run method for renderer. Should be overridden if needed.
        """
        pass

    @abstractmethod
    def stop(self):
        """
        Stop the renderer.
        """
        pass
    

    def __enter__(self):
        self.run()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        # не подавляем исключения
        return False