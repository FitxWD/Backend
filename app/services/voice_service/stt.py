import whisper
from fastapi import HTTPException
from app.config import WHISPER_MODEL

# Global instance (singleton)
_speech_service_instance = None

class SpeechToTextService:
    def __init__(self):
        try:
            self.model = whisper.load_model(WHISPER_MODEL)
            print("Whisper model loaded successfully")
        except Exception as e:
            print(f"Whisper error: {e}")
            self.model = None
            
    def is_available(self):
        return self.model is not None
        
    def transcribe(self, audio_path):
        """Transcribe audio file to text"""
        if not self.is_available():
            raise HTTPException(status_code=500, detail="Speech-to-text service not available")
            
        try:
            result = self.model.transcribe(audio_path, fp16=False)
            user_text = result.get("text", "").strip()
            
            if not user_text:
                raise HTTPException(status_code=400, detail="Could not transcribe audio")
                
            return user_text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Speech-to-text error: {str(e)}")

# Create a function to get or create the service instance
def get_speech_service():
    global _speech_service_instance
    if _speech_service_instance is None:
        _speech_service_instance = SpeechToTextService()
    return _speech_service_instance