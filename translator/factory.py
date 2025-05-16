from .google_translator import GoogleTranslator
from .openai_translator import OpenAITranslator


def get_translator(translator_type: str, input_lang: str, translate_lang: str, proxy: str | None = None, openai_api_key: str | None = None):
    if translator_type == "google":
        kwargs = {"source": input_lang, "target": translate_lang}
        if proxy:
            kwargs["proxy"] = proxy
        translator = GoogleTranslator(**kwargs)
    elif translator_type == "openai":
        translator = OpenAITranslator(input_lang, translate_lang, openai_api_key)
    else:
        raise ValueError(f"Unknown translator type: {translator_type}")
    
    return translator
