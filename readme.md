# Online Speech Translator

A real-time speech-to-text and translation tool with a live terminal interface.

> **Built on top of the excellent [`KoljaB/RealtimeSTT`](https://github.com/KoljaB/RealtimeSTT) library.**

## Features

- Real-time speech recognition from microphone (with available input device listing)
- Asynchronous translation using [deep-translator](https://github.com/nidhaloff/deep-translator) (Google Translate) or OpenAI
- Live updating table in the terminal using [rich](https://github.com/Textualize/rich)
- Device selection and device listing via command line
- Proxy support for translation requests
- Language selection for both input and translation
- Support for multiple languages
- Logging of transcripts and translations (see `app.log`, `transcript.log`, `transcript_with_translation.log`)
- Context management for improved translation accuracy

## Project Structure

```
├── realtime_stt.py              # Main logic for real-time speech translation
├── translator/                  # Translation interfaces and implementations
│   ├── __init__.py
│   ├── base.py
│   ├── factory.py
│   ├── google_translator.py
│   └── openai_translator.py
├── compressor/                  # Context compressor for OpenAI
│   ├── __init__.py
│   ├── base.py
│   └── openai_compressor.py
├── requirements.txt             # Project dependencies
├── readme.md                    # Documentation
├── app.log                      # Application log
├── transcript.log               # Raw transcript log
├── transcript_with_translation.log # Transcript with translation log
└── LICENSE                      # License file
```

## Quickstart

### 1. Create a Python Environment

#### Option A: Using Conda

```bash
conda create -n online_speech_translate python=3.12
conda activate online_speech_translate
```

#### Option B: Using venv

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

### 2. Install Dependencies

#### Linux Installation

Before installing dependencies, run:

```bash
sudo apt-get update
sudo apt-get install python3-dev
sudo apt-get install portaudio19-dev
```

#### MacOS Installation

Before installing dependencies, run:

```bash
brew install portaudio
```

Then install Python dependencies:

```bash
git clone https://github.com/nikkiw/realtime_translator.git
cd realtime_translator
pip install -r requirements.txt
```

### 3. List Available Audio Devices

```bash
python realtime_stt.py --list_devices
```

### 4. Run the Application

To run the real-time speech translator, execute:

```bash
python realtime_stt.py --input_device_index <device_index> --input_lang <source_language> --translate_lang <target_language>
```

### Command Line Arguments

- `--input_device_index`: Index of the audio input device (default is 0).
- `--input_lang`: Language spoken by the speaker (2-letter code, e.g., 'en', one of: `en`, `ru`, `de`, `pt`, `it`, `es`, `fr`).
- `--translate_lang`: Target translation language (2-letter code, e.g., 'ru', one of: `en`, `ru`, `de`, `pt`, `it`, `es`, `fr`).
- `--proxy`: Optional proxy URL for translation requests.
- `--translator_type`: Type of translator to use ('google' or 'openai').
- `--openai_api_key`: OpenAI API key for using the OpenAI translator.
- `--log_level`: Logging level (default: INFO).
- `--list_devices`: List available audio devices and exit.

#### Example with Proxy

```bash
python realtime_stt.py --input_device_index 0 --input_lang en --translate_lang ru --proxy http://user:pass@host:port
```

## Requirements

- Python 3.12
- See `requirements.txt` for Python dependencies

## Logs

- `app.log`: General application log
- `transcript.log`: Raw recognized text
- `transcript_with_translation.log`: Recognized text with translation

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

---
