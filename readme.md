# Online Speech Translator

A real-time speech-to-text and translation tool with a live terminal interface.

## Features

- Real-time speech recognition from microphone
- Asynchronous translation simulation (can be replaced with real translation API)
- Live updating table in the terminal using [rich](https://github.com/Textualize/rich)
- Device selection and device listing via command line

## Quickstart

### 1. Create a Conda Environment

```bash
conda create -n online_speech_translate python=3.12
conda activate online_speech_translate
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
python realtime_stt.py --input_device_index 0
```

Replace `0` with the index of your preferred input device (see device list).

## Command Line Arguments

- `--input_device_index`: Index of the input audio device (default: 0)
- `--list_devices`: Print available audio devices and exit

## Requirements

- Python 3.12
- See `requirements.txt` for Python dependencies

## Example


## License

MIT License

---
