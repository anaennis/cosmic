from google import genai

DEFAULT_MODEL = 'gemini-2.5-flash'

class GeminiHandler:
    def __init__(self, api_key, model_id=DEFAULT_MODEL):
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id

    def summarize_paper(self, text):
        """Generates a concise single-paragraph summary of a paper abstract."""
        # Limit text to avoid token overflow
        prompt = f"""Summarize the following research paper into a single paragraph.
Focus on key findings and significance. Do not use bullet points.

Paper Text: {text[:10000]}
"""
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt
        )
        return response.text.strip()
