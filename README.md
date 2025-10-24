# Backend

Instructions for setting up and running backend.

## Prerequisites

- Python 3.7 or higher
- Chocolatey (for Windows users)

## Setup Instructions

### 1. Create Virtual Environment

bash
python -m venv .venv


### 2. Activate Virtual Environment

*Windows:*
bash
.venv\Scripts\activate


*macOS/Linux:*
bash
source .venv/bin/activate


### 3. Install Dependencies

bash
pip install -r requirements.txt


### 4. Install Whisper Model

Choose one of the following options:

*Option 1: Direct installation*
bash
pip install git+https://github.com/openai/whisper.git


*Option 2: Follow official repository*
Visit [OpenAI Whisper Repository](https://github.com/openai/whisper) for detailed installation instructions.

### 5. Install FFmpeg

*Windows (using Chocolatey):*
bash
choco install ffmpeg


*macOS:*
bash
brew install ffmpeg


*Linux:*
bash
sudo apt update
sudo apt install ffmpeg


### 6. Run the Server

bash
python -m app.main


## Notes

- Ensure your virtual environment is activated before running the server
- FFmpeg is required for audio processing with Whisper
- Check that all dependencies are properly installed before starting the server

## Folder Structure



backend/
├── app/
├── serviceAccountKey.json     
└── requirements.txt         # Dependencies


## API Documentation

When the server is running, visit:
- http://localhost:8000/docs for Swagger UI documentation
- http://localhost:8000/redoc for ReDoc documentation