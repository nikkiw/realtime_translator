from RealtimeSTT import AudioToTextRecorder
import asyncio
import threading
import queue
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.box import SIMPLE_HEAVY
import argparse

console = Console()
rows = []
rows_lock = threading.Lock()
text_queue = queue.Queue()
live: Live

def build_table():
    # Очищаем консоль при первом вызове build_table
    if not hasattr(build_table, "_cleared"):
        console.clear()
        build_table._cleared = True

    header_lines = 3
    term_height = console.size.height or 20
    max_visible = term_height - header_lines
    if max_visible < 1:
        max_visible = len(rows)

    with rows_lock:
        visible = rows[-max_visible:]
        visible = list(reversed(visible))  # Показать последние строки сверху

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

    return tbl


def enqueue_text(text: str):
    with rows_lock:
        rows.append((text, "..."))
    live.update(build_table())
    text_queue.put(text)

async def translate_worker():
    while True:
        text = await asyncio.get_event_loop().run_in_executor(None, text_queue.get)
        await asyncio.sleep(1)
        translation = f"<перевод для: {text}>"
        with rows_lock:
            for idx, (t, tr) in enumerate(rows):
                if t == text and tr == "...":
                    rows[idx] = (t, translation)
                    break
        live.update(build_table())

def run_recorder(input_device_index):
    with AudioToTextRecorder(
        input_device_index=input_device_index,
        language='en',
        model='tiny.en',
        spinner=False,
    ) as recorder:
        while True:
            recorder.text(enqueue_text)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_device_index', type=int, default=0, help='Index of input audio device')
    parser.add_argument('--list_devices', action='store_true', help='List available audio devices and exit')
    args = parser.parse_args()

    if args.list_devices:
        import sounddevice as sd
        print(sd.query_devices())
        exit(0)

    # Запускаем asyncio-loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    threading.Thread(target=loop.run_forever, daemon=True).start()
    # Стартуем воркер-переводчик
    asyncio.run_coroutine_threadsafe(translate_worker(), loop)
    # Запускаем live-режим
    live = Live(build_table(), console=console, refresh_per_second=10)
    with live:
        run_recorder(args.input_device_index)
