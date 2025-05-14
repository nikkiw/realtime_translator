# Создание окружения 
Для создания окружения `online_speech_translate` на базе **Python 3.12** с помощью **conda** используй следующую команду:

```bash
conda create -n online_speech_translate python=3.12
```

### 🔹 **Объяснение команды:**
- `conda create` — команда для создания нового окружения.
- `-n online_speech_translate` — имя окружения (`online_speech_translate`).
- `python=3.12` — версия Python, которая будет установлена в окружении.

После создания окружения его можно активировать командой:

```bash
conda activate online_speech_translate
```  

Чтобы установить зависимости, перечисленные в **`requirements.txt`**, выполни следующую команду в терминале:

```bash
pip install -r requirements.txt
```

Установка nexa sdk:
```bash
conda create -n nexasdk python=3.10
conda activate nexasdk
export CPLUS_INCLUDE_PATH=/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include/c++/v1
export CMAKE_ARGS="-DCMAKE_VERBOSE_MAKEFILE=ON \
                   -DGGML_METAL=ON \
                   -DLLAMA_BUILD_EXAMPLES=OFF"
				   				   
pip install -vv . --prefer-binary --no-cache-dir   --config-settings=build-dir="build/llama_build"

```