from RealtimeSTT import AudioToTextRecorder
import asyncio
import threading
import queue
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.box import SIMPLE_HEAVY
import argparse
import datetime
from translator import get_translator
from compressor import OpenAICompressor
import logging

console = Console()
rows = []
rows_lock = threading.Lock()
text_queue: queue.Queue[str] = queue.Queue()
live: Live

transcript_log_path = "transcript.log"
transcript_with_translation_log_path = "transcript_with_translation.log"

openai_context = []
openai_context_lock = threading.Lock()

def setup_logging(log_level: str = "INFO"):
    # Set up logging to file with the specified log level
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("app.log", encoding="utf-8"),
            # logging.StreamHandler()
        ]
    )

def build_table():
    # Clear the console only once at the start
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

    return tbl

def log_transcript(text: str):
    # Log original transcript to file and to logger
    with open(transcript_log_path, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().isoformat()} {text}\n")
    logging.info(f"Transcript: {text}")

def log_transcript_with_translation(text: str, translation: str):
    # Log transcript and translation to file and to logger
    with open(transcript_with_translation_log_path, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().isoformat()} {text} | {translation}\n")
    logging.info(f"Transcript+Translation: {text} | {translation}")

def enqueue_text(text: str):
    # Add new text to the rows and queue for translation
    with rows_lock:
        rows.append((text, "..."))
    log_transcript(text)
    live.update(build_table())
    text_queue.put(text)
    logging.debug(f"Enqueued text: {text}")


async def translate_worker():
    # This worker runs in a separate thread and processes text from the queue
    input_lang = translate_worker.input_lang
    translate_lang = translate_worker.translate_lang
    proxy = getattr(translate_worker, "proxy", None)
    translator_type = getattr(translate_worker, "translator_type", "google")
    openai_api_key = getattr(translate_worker, "openai_api_key", None)

    translator = get_translator(
        translator_type,
        input_lang,
        translate_lang,
        proxy=proxy,
        openai_api_key=openai_api_key,
    ) 
    # Attach OpenAICompressor to the translator for context management
    translator.set_compressor(OpenAICompressor(api_key=openai_api_key))

    def translate_func(text: str):
        return translator.translate(text)


    while True:
        # Wait for new text to appear in the queue
        text: str = await asyncio.get_event_loop().run_in_executor(None, text_queue.get)
        try:
            # Run translation in a thread to avoid blocking the event loop
            translation = await asyncio.get_event_loop().run_in_executor(
                None, translate_func, text
            )
        except Exception as e:
            translation = f"<error: {e}>"
            logging.error(f"Translation error: {e}")
        log_transcript_with_translation(text, translation)
        with rows_lock:
            for idx, (t, tr) in enumerate(rows):
                if t == text and tr == "...":
                    rows[idx] = (t, translation)
                    break
        live.update(build_table())

def run_recorder(input_device_index: int, input_lang: str, translate_lang: str):
    # Start the audio-to-text recorder and process audio chunks
    model_name = 'base.en' if input_lang == 'en' else 'base'
    with AudioToTextRecorder(
        input_device_index=input_device_index,
        language=input_lang,
        model=model_name,
        spinner=False,
    ) as recorder:
        while True:
            recorder.text(enqueue_text)
            logging.debug("Audio chunk processed.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_device_index', type=int, default=0, help='Index of input audio device')
    parser.add_argument('--list_devices', action='store_true', help='List available audio devices and exit')
    parser.add_argument('--input_lang', type=str, default='en', choices=['en', 'ru', 'de', 'pt', 'it', 'es', 'fr'], help='Language spoken by the speaker (2-letter code)')
    parser.add_argument('--translate_lang', type=str, default='ru', choices=['en', 'ru', 'de', 'pt', 'it', 'es', 'fr'], help='Target translation language (2-letter code)')
    parser.add_argument('--proxy', type=str, default=None, help='Proxy URL for translation requests (e.g., http://user:pass@host:port)')
    parser.add_argument('--translator_type', type=str, default='google', choices=['google', 'openai'], help='Translator backend: google or openai')
    parser.add_argument('--openai_api_key', type=str, default=None, help='OpenAI API key for openai translator')
    parser.add_argument('--log_level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Logging level')
    args = parser.parse_args()

    setup_logging(args.log_level)
    logging.info("Application started.")

    if args.list_devices:
        # List all available audio devices and exit
        import sounddevice as sd
        print(sd.query_devices())
        logging.info("Listed audio devices.")
        exit(0)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    threading.Thread(target=loop.run_forever, daemon=True).start()
    translate_worker.input_lang = args.input_lang
    translate_worker.translate_lang = args.translate_lang
    if args.proxy:
        translate_worker.proxy = args.proxy
    translate_worker.translator_type = args.translator_type
    if args.openai_api_key:
        translate_worker.openai_api_key = args.openai_api_key
    asyncio.run_coroutine_threadsafe(translate_worker(), loop)
    live = Live(build_table(), console=console, refresh_per_second=10)
    logging.info(f"Using input device index: {args.input_device_index}, input_lang: {args.input_lang}, translate_lang: {args.translate_lang}")
    with live:
        run_recorder(args.input_device_index, args.input_lang, args.translate_lang)