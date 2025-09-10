from google import genai
from google.genai import types
from fastapi import HTTPException
from app.config import GOOGLE_API_KEY, GEMINI_TEXT_MODEL
from .conversation import get_next_prompt, questions, conversation_state

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
        def llm_answer_func(user_text, current_question):
            return answer_side_question(user_text, current_question, self.client, GEMINI_TEXT_MODEL)

        reply_text = get_next_prompt(user_text, llm_answer_func=llm_answer_func)
        print(f"Assistant reply (flow): {reply_text}")

        if reply_text == "Thanks! I have all the information I need. I’ll now generate your diet recommendation plan.":
            pass

        return reply_text
        
def answer_side_question(user_text, current_question, client, model):
        prompt = (
            f"The user asked a question about the following intake prompt:\n"
            f"Prompt: {current_question}\n"
            f"User's question: {user_text}\n"
            "Answer the user's question in a friendly, concise way (max 2 sentences)."
        )
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            return response.text.strip() if response.text else "Sorry, I don't know."
        except Exception as e:
            print(f"Gemini error (side question): {e}")
            return "Sorry, I couldn't answer that."
            

# Singleton getter function
def get_language_model_service():
    global _language_model_instance
    if _language_model_instance is None:
        _language_model_instance = LanguageModelService()
    return _language_model_instance
