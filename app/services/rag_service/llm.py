from google import genai
from google.genai import types
from fastapi import HTTPException
from app.config import GOOGLE_API_KEY, GEMINI_TEXT_MODEL

_language_model_instance = None

class LanguageModelService:
    def __init__(self):
        try:
            self.client = genai.Client(api_key=GOOGLE_API_KEY)
            print("Gemini models configured successfully")
        except Exception as e:
            print(f"Gemini error: {e}")
            self.client = None

    def is_available(self):
        return self.client is not None

    def generate_answer(self, query, context):
        if not self.is_available():
            raise HTTPException(status_code=500, detail="Language model service not available")
            
        prompt = f"""
        You are a helpful fitness assistant. Respond ONLY in plain text.
        Do not use Markdown, HTML, bullet points, headings, or any special formatting.
        Keep your answer concise, clear, and under 50 words.

        Use the context below to answer the question.
        If the context is insufficient, you may provide a general answer based on fitness/health knowledge.
        
        Context:
        {context}

        Question: {query}
        Answer:
        """

        # print(prompt)
        try:
            response = self.client.models.generate_content(
                model=GEMINI_TEXT_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            return response.text.strip() if response.text else "Sorry, I couldn't generate an answer."
        except Exception as e:
            print(f"Gemini error: {e}")
            return "I'm having trouble responding right now."

def get_language_model_service():
    global _language_model_instance
    if _language_model_instance is None:
        _language_model_instance = LanguageModelService()
    return _language_model_instance