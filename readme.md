# Online Speech Translator

A real-time speech-to-text and translation tool with a live terminal interface.

> **Built on top of the excellent [`KoljaB/RealtimeSTT`](https://github.com/KoljaB/RealtimeSTT) library.**

## Features

- Real-time speech recognition from microphone (with available input device listing)
- Asynchronous translation using [deep-translator](https://github.com/nidhaloff/deep-translator) (Google Translate)
- Live updating table in the terminal using [rich](https://github.com/Textualize/rich)
- Device selection and device listing via command line
- Proxy support for translation requests
- Language selection for both input and translation

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

```bash
pip install -r requirements.txt
```

### 3. List Available Audio Devices

```bash
python realtime_stt.py --list_devices
```

### 4. Run the Application

```bash
python realtime_stt.py --input_device_index 0 --input_lang en --translate_lang ru
```

Replace `0` with the index of your preferred input device (see device list).  
You can change `--input_lang` and `--translate_lang` to any of: `en`, `ru`, `de`, `pt`, `it`, `es`, `fr`.

#### Example with Proxy

```bash
python realtime_stt.py --input_device_index 0 --input_lang en --translate_lang ru --proxy http://user:pass@host:port
```

## Command Line Arguments

- `--input_device_index`: Index of the input audio device (default: 0)
- `--list_devices`: Print available audio devices and exit
- `--input_lang`: Language spoken by the speaker (2-letter code, default: en)
- `--translate_lang`: Target translation language (2-letter code, default: ru)
- `--proxy`: Proxy URL for translation requests (optional)

## Requirements

- Python 3.12
- See `requirements.txt` for Python dependencies

## License

MIT License

---
