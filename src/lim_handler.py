import os
from google import genai
from google.genai import types

class GeminiHandler:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model_id = 'gemini-2.0-flash'

    def summarize_paper(self, text):
        """Generates a concise paragraph summary of a paper using few-shot prompting."""
        prompt = f"""Summarize the following research paper into a single paragraph. 
        Focus on key findings and significance. Do not use bullet points.
        
        Paper Text: {text[:10000]}  # Limit text to avoid token overflow
        """
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt
        )
        return response.text
