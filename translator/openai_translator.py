import os
from openai import OpenAI
from translator.base import BaseTranslator


class OpenAITranslator(BaseTranslator):
    def __init__(self, source: str, target: str, api_key: str | None = None):
        super().__init__() 
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OpenAI API key must be provided")
        self.api_key = api_key
        self.source = source
        self.target = target
        self.client = OpenAI(api_key=api_key)

    def translate_with_context(self, text: str, context: str| None) -> str:
        if not text:
            return ""
        
        # Compose the prompt for the OpenAI model, including context if available
        prompt = (
            f"You are a translator. The input is a transcription of speech from an online recording. "
            f"Translate the text from {self.source} to {self.target}, and output only the translated text without any additional commentary or formatting."
        )

        
        if context:
            # If context is provided, include it in the prompt for better translation quality
            prompt += f"\n\nPrevious context:\n{context}\n\nNew text to translate:\n{text}"
        else:
            prompt += f"\n\nText to translate:\n{text}"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
            )
            
            # Add text to context before returning translation
            if self.compressor:
                self.compressor.add_text(text)
                
            # Extract the translated content from the OpenAI response
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content or ""
            return ""
            
        except Exception as e:
            # Print error for debugging and return error message as translation result
            print(f"Error during translation: {e}")
            return f"Error: {str(e)}"