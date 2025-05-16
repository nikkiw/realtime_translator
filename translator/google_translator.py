from .base import BaseTranslator
from deep_translator import GoogleTranslator as gt

class GoogleTranslator(BaseTranslator):
    def __init__(self, source: str = "en", target: str = "ru", proxy: str | None = None):
        super().__init__()
        self.source = source
        self.target = target
        self.proxy = proxy
        # You can initialize a Google Translate API client or another mechanism here if needed

    def translate_with_context(self, text: str, context: str| None) -> str:        
        # Prepare arguments for the deep_translator GoogleTranslator
        kwargs: dict[str, str | dict[str, str] | None] = {"source": self.source, "target": self.target}
        if self.proxy:
            # If a proxy is specified, add it to the translator arguments
            kwargs["proxies"] = {'http': self.proxy, 'https': self.proxy}
        translator = gt(**kwargs)
        return translator.translate(text)

