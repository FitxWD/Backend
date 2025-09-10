from google.genai import types
from gtts import gTTS
import tempfile
import os
from app.utils.audio import wave_file
from app.config import GEMINI_TTS_MODEL, GEMINI_TTS_VOICE
from app.services.voice_service.llm import get_language_model_service

# Global singleton instance
_tts_service_instance = None

class TextToSpeechService:
    def __init__(self, client):
        self.client = client
        
    def generate_speech(self, text):
        """Generate speech audio from text, with fallback to gTTS"""
        try:
            # First try Gemini TTS
            print("Generating speech with Gemini TTS...")
            audio_content = self._gemini_tts(text)
            
            if audio_content and isinstance(audio_content, bytes) and len(audio_content) > 0:
                print(f"Gemini TTS audio generated successfully ({len(audio_content)} bytes)")
                return audio_content, ".wav"
            else:
                raise Exception(f"Gemini TTS returned invalid audio: {type(audio_content)}")
                
        except Exception as e:
            # Fallback to gTTS
            print(f"Falling back to gTTS: {e}")
            return self._gtts_fallback(text), ".mp3"
            
    def _gemini_tts(self, text):
        """Generate TTS using Gemini's TTS capabilities"""
        if not self.client:
            raise Exception("Gemini client not initialized")
            
        # Format the text for TTS
        tts_prompt = f"Say naturally: {text}"
        
        # Configure TTS settings
        tts_config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=GEMINI_TTS_VOICE,
                    )
                )
            ),
        )
        
        # Generate speech
        response = self.client.models.generate_content(
            model=GEMINI_TTS_MODEL,
            contents=tts_prompt,
            config=tts_config
        )
        
        # Extract audio data
        audio_data = response.candidates[0].content.parts[0].inline_data.data
        
        # Convert to WAV
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
            wave_file(temp_wav.name, audio_data)
            temp_wav_path = temp_wav.name
        
        # Read back as bytes
        with open(temp_wav_path, 'rb') as f:
            audio_bytes = f.read()
            
        # Clean up temp file
        try:
            os.unlink(temp_wav_path)
        except:
            pass
            
        return audio_bytes
        
    def _gtts_fallback(self, text):
        """Fallback to gTTS for speech generation"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as audio_out:
                tmp_output_path = audio_out.name
                tts = gTTS(text, lang="en")
                tts.save(tmp_output_path)

            # Read the file as bytes
            with open(tmp_output_path, "rb") as f:
                audio_bytes = f.read()
                
            # Clean up
            os.unlink(tmp_output_path)
            
            print("Fallback gTTS audio generated successfully")
            return audio_bytes
            
        except Exception as e:
            print(f"gTTS also failed: {e}")
            raise Exception(f"Text-to-speech error: {str(e)}")

# Singleton getter function that depends on the LLM service
def get_tts_service():
    global _tts_service_instance
    if _tts_service_instance is None:
        # Get the LLM service to use its client
        llm_service = get_language_model_service()
        _tts_service_instance = TextToSpeechService(llm_service.client)
    return _tts_service_instance