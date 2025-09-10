from google import genai
from google.genai import types
from fastapi import HTTPException
from app.config import GOOGLE_API_KEY, GEMINI_TEXT_MODEL

# Global singleton instance
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
        
    def generate_response(self, user_text):
        """Generate a response to user text input"""
        if not self.is_available():
            raise HTTPException(status_code=500, detail="Language model service not available")
            
        prompt = f"""
        You are a friendly voice assistant. Your responses must be in plain text only.
        - Keep responses under 50 words
        - Do not use any formatting like Markdown, HTML, or special characters
        - Do not use bullet points, headings, or other structural elements
        - Just provide simple, conversational text
        
        User: "{user_text}"
        Assistant:
        """
        
        try:
            response = self.client.models.generate_content(
                model=GEMINI_TEXT_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)  # Disables thinking
                )
            )
            
            return response.text.strip() if response.text else "Sorry, I couldn't think of a reply."
        except Exception as e:
            print(f"Gemini error: {e}")
            return "I'm having trouble responding right now."

# Singleton getter function
def get_language_model_service():
    global _language_model_instance
    if _language_model_instance is None:
        _language_model_instance = LanguageModelService()
    return _language_model_instance