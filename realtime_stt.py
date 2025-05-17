from RealtimeSTT import AudioToTextRecorder
import asyncio
import threading
import queue
import argparse
import datetime
from translator import get_translator
from renderer import get_renderer
from compressor import OpenAICompressor
import logging


rows = []
rows_lock = threading.Lock()
text_queue: queue.Queue[str] = queue.Queue()

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
    renderer = enqueue_text.renderer
    with rows_lock:
        rows.append((text, "..."))
        render_rows = rows.copy()
    log_transcript(text)
    logging.debug(f"Calling renderer.render with rows: {render_rows}")
    renderer.render(render_rows)
    text_queue.put(text)
    logging.debug(f"Enqueued text: {text}")


async def translate_worker():
    # This worker runs in a separate thread and processes text from the queue
    input_lang = translate_worker.input_lang
    translate_lang = translate_worker.translate_lang
    proxy = getattr(translate_worker, "proxy", None)
    translator_type = getattr(translate_worker, "translator_type", "google")
    openai_api_key = getattr(translate_worker, "openai_api_key", None)
    renderer = translate_worker.renderer
    
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


    logging.info("translate_worker started")
    while True:
        # Wait for new text to appear in the queue
        text: str = await asyncio.get_event_loop().run_in_executor(None, text_queue.get)
        logging.debug(f"Got text from queue: {text}")
        try:
            # Run translation in a thread to avoid blocking the event loop
            translation = await asyncio.get_event_loop().run_in_executor(
                None, translate_func, text
            )
            logging.debug(f"Translation result: {translation}")
        except Exception as e:
            translation = f"<error: {e}>"
            logging.error(f"Translation error: {e}")
        log_transcript_with_translation(text, translation)
        with rows_lock:
            for idx, (t, tr) in enumerate(rows):
                if t == text and tr == "...":
                    rows[idx] = (t, translation)
                    logging.debug(f"Updated row {idx} with translation")
                    break
        with rows_lock:
            render_rows = rows.copy()
        logging.debug(f"Calling renderer.render with rows: {render_rows}")
        renderer.render(render_rows)    

def run_recorder(input_device_index: int, input_lang: str, translate_lang: str):
    # Start the audio-to-text recorder and process audio chunks
    logging.info(f"run_recorder started with device {input_device_index}, lang {input_lang}, translate_lang {translate_lang}")
    model_name = 'base.en' if input_lang == 'en' else 'base'
    with AudioToTextRecorder(
        input_device_index=input_device_index,
        language=input_lang,
        model=model_name,
        spinner=False,
        silero_deactivity_detection=True,
        pre_recording_buffer_duration=0.5,
    ) as recorder:
        while True:
            recorder.text(enqueue_text)
            logging.debug("Audio chunk processed.")

def run_all(input_device_index: int, input_lang: str, translate_lang: str, renderer):
    logging.info("Starting run_all (worker thread for recognition and translation)")
    worker_thread = threading.Thread(
        target=lambda: asyncio.run(run_worker(input_device_index, input_lang, translate_lang, renderer)),
        daemon=True
    )
    worker_thread.start()
    return worker_thread

async def run_worker(input_device_index: int, input_lang: str, translate_lang: str, renderer):
    logging.info("run_worker started")
    loop = asyncio.get_event_loop()
    asyncio.create_task(translate_worker())
    await loop.run_in_executor(None, run_recorder, input_device_index, input_lang, translate_lang)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_device_index', type=int, default=0, help='Index of input audio device')
    parser.add_argument('--list_devices', action='store_true', help='List available audio devices and exit')
    parser.add_argument('--input_lang', type=str, default='en', choices=['en', 'ru', 'de', 'pt', 'it', 'es', 'fr'], help='Language spoken by the speaker (2-letter code)')
    parser.add_argument('--translate_lang', type=str, default='ru', choices=['en', 'ru', 'de', 'pt', 'it', 'es', 'fr'], help='Target translation language (2-letter code)')
    parser.add_argument('--proxy', type=str, default=None, help='Proxy URL for translation requests (e.g., http://user:pass@host:port)')
    parser.add_argument('--translator_type', type=str, default='google', choices=['google', 'openai'], help='Translator backend: google or openai')
    parser.add_argument('--renderer', type=str, default='rich', choices=['rich', 'html_fastaip'], help='Rendering engine: rich or textual')
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

    translate_worker.input_lang = args.input_lang
    translate_worker.translate_lang = args.translate_lang
    if args.proxy:
        translate_worker.proxy = args.proxy
    translate_worker.translator_type = args.translator_type
    if args.openai_api_key:
        translate_worker.openai_api_key = args.openai_api_key   
             

    with get_renderer(
        engine = args.renderer, 
        target = args.translate_lang
    ) as renderer:
        logging.info("Renderer context entered")
        translate_worker.renderer = renderer
        enqueue_text.renderer = renderer
        logging.info(f"Using input device index: {args.input_device_index}, input_lang: {args.input_lang}, translate_lang: {args.translate_lang}, renderer: {args.renderer}")

        loop = asyncio.new_event_loop()
        loop_thread = threading.Thread(target=loop.run_forever, daemon=True)
        loop_thread.start()
        asyncio.set_event_loop(loop)

        worker_thread = run_all(args.input_device_index, args.input_lang, args.translate_lang, renderer)
        try:
            worker_thread.join()
        except KeyboardInterrupt:
            logging.info("Shutting down...")

