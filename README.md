# Voice Assistant Backend

Instructions for setting up and running the voice assistant backend.

## Prerequisites

- Python 3.7 or higher
- Chocolatey (for Windows users)

## Setup Instructions

### 1. Create Virtual Environment

```bash
python -m venv .venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Whisper Model

Choose one of the following options:

**Option 1: Direct installation**
```bash
pip install git+https://github.com/openai/whisper.git
```

**Option 2: Follow official repository**
Visit [OpenAI Whisper Repository](https://github.com/openai/whisper) for detailed installation instructions.

### 5. Install FFmpeg

**Windows (using Chocolatey):**
```bash
choco install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

### 6. Run the Server

```bash
python -m app.main
```

## Notes

- Ensure your virtual environment is activated before running the server
- FFmpeg is required for audio processing with Whisper
- Check that all dependencies are properly installed before starting the server

## Folder Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration settings
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── users.py     # User-related endpoints
│   │   │   │   └── assistant.py # Assistant endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── voice_service/
│   │   │   ├── stt.py       # Speech-to-text service
│   │   │   ├── llm.py       # Language model service
│   │   │   └── tts.py       # Text-to-speech service
│   └── utils/
│       ├── __init__.py
│       └── audio.py         # Audio processing utilities
├── .env                     # Environment variables
└── requirements.txt         # Dependencies
```

## Troubleshooting

### Common Issues

1. **ImportError or ModuleNotFoundError**:
   - Ensure you're running the server from the project root directory
   - Verify that all packages are installed correctly
   - Check if your virtual environment is activated

2. **FFmpeg not found**:
   - Ensure FFmpeg is installed and added to your system PATH
   - Restart your terminal after installation

3. **Whisper model issues**:
   - Make sure you have sufficient disk space for model downloads
   - Check your internet connection for initial model download

## API Documentation

When the server is running, visit:
- http://localhost:8000/docs for Swagger UI documentation
- http://localhost:8000/redoc for ReDoc documentation