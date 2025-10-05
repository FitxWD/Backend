import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, auth
import time
from datetime import datetime
import logging

# Load environment variables
load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Model Settings
WHISPER_MODEL = "base.en"
GEMINI_TEXT_MODEL = "gemini-2.5-flash"
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"
GEMINI_TTS_VOICE = "Sulafat"  

# App Settings
ALLOWED_AUDIO_EXTENSIONS = [".wav", ".mp3", ".m4a", ".ogg", ".webm"]

# Performance Monitoring Settings
PERFORMANCE_MONITORING_ENABLED = True
SLOW_QUERY_THRESHOLD = 1.0  # seconds
LOG_ALL_QUERIES = True

# Initialize firebase
cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

# Initialize only once
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Performance monitoring decorator
def monitor_db_performance(operation_name):
    """Decorator to monitor database operation performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not PERFORMANCE_MONITORING_ENABLED:
                return func(*args, **kwargs)
            
            start_time = time.time()
            start_timestamp = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                duration = end_time - start_time
                
                # Log performance metrics
                log_performance_metric(
                    operation=operation_name,
                    duration=duration,
                    status="success",
                    timestamp=start_timestamp,
                    function_name=func.__name__
                )
                
                return result
                
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                
                # Log failed operation
                log_performance_metric(
                    operation=operation_name,
                    duration=duration,
                    status="error",
                    error=str(e),
                    timestamp=start_timestamp,
                    function_name=func.__name__
                )
                raise
                
        return wrapper
    return decorator

def log_performance_metric(operation, duration, status, timestamp, function_name, error=None):
    """Log performance metrics"""
    
    # Create performance log entry
    perf_data = {
        "operation": operation,
        "duration_ms": round(duration * 1000, 2),
        "status": status,
        "timestamp": timestamp,
        "function": function_name,
        "is_slow": duration > SLOW_QUERY_THRESHOLD
    }
    
    if error:
        perf_data["error"] = error
    
    # Log to console (ASCII only)
    if LOG_ALL_QUERIES or duration > SLOW_QUERY_THRESHOLD:
        if status == "success":
            print(f"[DB PERF] {operation} completed in {perf_data['duration_ms']}ms")
            if duration > SLOW_QUERY_THRESHOLD:
                print(f"[SLOW QUERY] {operation} took {perf_data['duration_ms']}ms")
        else:
            print(f"[DB ERROR] {operation} failed after {perf_data['duration_ms']}ms - {error}")
    
    # Store in performance collection (optional)
    try:
        db.collection('performance_logs').add(perf_data)
    except Exception as log_error:
        # Don't fail the main operation if logging fails
        print(f"[WARNING] Performance logging failed: {log_error}")