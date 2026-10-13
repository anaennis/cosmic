from google import genai
from google.genai import types

DEFAULT_MODEL = 'gemini-3.8-flash'
DEFAULT_TIMEOUT_SECONDS = 90
DEFAULT_THINKING_LEVEL = 'low'
THINKING_LEVELS = ('minimal', 'low', 'medium', 'high')

class GeminiHandler:
    def __init__(self, api_key, model_id=DEFAULT_MODEL, timeout=DEFAULT_TIMEOUT_SECONDS,
                 thinking_level=DEFAULT_THINKING_LEVEL):
        # The SDK expects the timeout in milliseconds
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=timeout * 1000)
        )
        self.model_id = model_id
        # Summaries don't need deep reasoning; less thinking means faster answers
        self.config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level=thinking_level.upper())
        )

    def summarize_paper(self, text):
        """Generates a concise single-paragraph summary of a paper abstract."""
        # Limit text to avoid token overflow
        prompt = f"""Summarize the following research paper into a single paragraph.
Focus on key findings and significance. Do not use bullet points.

Paper Text: {text[:10000]}
"""
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=self.config
        )
        return response.text.strip()
