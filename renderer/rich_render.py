from .base  import BaseRenderer
from rich.live import Live
from rich.console import Console
from rich.table import Table
from rich.box import SIMPLE_HEAVY

from typing import List, Tuple

class RichRenderer(BaseRenderer):
    """
    Renderer implementation using Rich.
    """
    def __init__(self, refresh_per_second: int = 2):
        super().__init__()
        self.console = Console()
        self._live = Live(
            console=self.console, 
            refresh_per_second=refresh_per_second,
            screen=True, 
            redirect_stderr=False, 
            redirect_stdout=False
        )
        self._table_data = []

    def render(self, translations: List[Tuple[str, str]]):
        """
        Build and update the Rich table from translations.
        """
        # table = Table(title="Translations")
        # table.add_column("Text")
        # table.add_column("Translation")
        
        # # Add rows in reverse order
        # for text, translation in reversed(translations):
        #     table.add_row(text, translation)
        
        # self._live.update(table)
        # self._live.refresh()
        
        header_lines = 3
        term_height = self.console.size.height or 20
        max_visible = term_height - header_lines
        if max_visible < 1:
            max_visible = len(translations)

        visible = translations[-max_visible:]
        visible = list(reversed(visible))

        tbl = Table(
            show_header=True,
            header_style="bold magenta",
            show_lines=True,
            box=SIMPLE_HEAVY,
        )
        tbl.add_column("Text", style="dim", no_wrap=False, overflow="fold")
        tbl.add_column("Translation", style="green", no_wrap=False, overflow="fold")

        for t, tr in visible:
            tbl.add_row(t, tr)

        self._live.update(tbl)
        self._live.refresh()

    def run(self):
        """
        Start the Rich live table rendering and run the recorder.
        """
        self._live.start()

    def stop(self):
        """Останавливаем Live и возвращаем терминал в обычный режим"""
        self._live.stop()

