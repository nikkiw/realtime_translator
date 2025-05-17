from .base import BaseRenderer
from .rich_render import RichRenderer
from .html_fastaip_renderer import BrowserModalRenderer

def get_renderer(engine: str, target: str,  api_key: str | None = None) -> BaseRenderer:
    """
    Factory function to get the appropriate renderer.
    """
    if engine == "rich":
        return RichRenderer()
    elif engine == "html_fastaip":
        return BrowserModalRenderer(api_key=api_key, target=target)
    else:
        raise ValueError(f"Unknown rendering engine: {engine}")