from RealtimeSTT import AudioToTextRecorder
import asyncio
import threading
import queue
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.box import SIMPLE_HEAVY
import argparse
from deep_translator import GoogleTranslator

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
    # Получаем параметры перевода и прокси из глобальных переменных
    input_lang = translate_worker.input_lang
    translate_lang = translate_worker.translate_lang
    proxy = getattr(translate_worker, "proxy", None)

    translator_kwargs = {
        "source": input_lang,
        "target": translate_lang,
    }
    if proxy:
        translator_kwargs["proxies"] = {"http": proxy, "https": proxy}

    translator = GoogleTranslator(**translator_kwargs)

    while True:
        text = await asyncio.get_event_loop().run_in_executor(None, text_queue.get)
        try:
            translation = await asyncio.get_event_loop().run_in_executor(
                None, translator.translate, text
            )
        except Exception as e:
            translation = f"<error: {e}>"
        with rows_lock:
            for idx, (t, tr) in enumerate(rows):
                if t == text and tr == "...":
                    rows[idx] = (t, translation)
                    break
        live.update(build_table())

def run_recorder(input_device_index, input_lang, translate_lang):
    if input_lang == 'en':
        model_name = 'tiny.en'
    else:
        model_name = 'tiny'
    with AudioToTextRecorder(
        input_device_index=input_device_index,
        language=input_lang,
        model=model_name,
        spinner=False,
    ) as recorder:
        while True:
            recorder.text(enqueue_text)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_device_index', type=int, default=0, help='Index of input audio device')
    parser.add_argument('--list_devices', action='store_true', help='List available audio devices and exit')
    parser.add_argument('--input_lang', type=str, default='en', choices=['en', 'ru', 'de', 'pt', 'it', 'es', 'fr'], help='Language spoken by the speaker (2-letter code)')
    parser.add_argument('--translate_lang', type=str, default='ru', choices=['en', 'ru', 'de', 'pt', 'it', 'es', 'fr'], help='Target translation language (2-letter code)')
    parser.add_argument('--proxy', type=str, default=None, help='Proxy URL for translation requests (e.g., http://user:pass@host:port)')
    args = parser.parse_args()

    if args.list_devices:
        import sounddevice as sd
        print(sd.query_devices())
        exit(0)

    # Запускаем asyncio-loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    threading.Thread(target=loop.run_forever, daemon=True).start()
    # Передаём параметры языков и прокси в translate_worker
    translate_worker.input_lang = args.input_lang
    translate_worker.translate_lang = args.translate_lang
    if args.proxy:
        translate_worker.proxy = args.proxy
    # Стартуем воркер-переводчик
    asyncio.run_coroutine_threadsafe(translate_worker(), loop)
    # Запускаем live-режим
    live = Live(build_table(), console=console, refresh_per_second=10)
    with live:
        run_recorder(args.input_device_index, args.input_lang, args.translate_lang)
