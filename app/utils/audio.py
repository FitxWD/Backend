import wave
import tempfile
import os
import base64

def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    """Create a WAV file from PCM data"""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

def audio_to_base64(audio_content, suffix=".wav"):
    """Convert audio bytes to base64 string"""
    if not audio_content:
        return None
        
    tmp_path = None
    try:
        # Save to temp file first to verify it's valid audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as audio_out:
            tmp_path = audio_out.name
            audio_out.write(audio_content)
        
        # Read back and encode to base64
        with open(tmp_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)