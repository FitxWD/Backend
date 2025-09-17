from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body
import tempfile
import os
from app.services.voice_service.stt import get_speech_service
from app.services.voice_service.llm_old import get_voice_llm_service
from app.services.voice_service.tts import get_tts_service
from app.utils.audio import audio_to_base64
from app.config import ALLOWED_AUDIO_EXTENSIONS
from app.services.rag_service.rag import get_rag_service
from app.api.v1.schemas.query import QueryRequest

router = APIRouter()

@router.post("/assistant")
async def assistant(
    file: UploadFile = File(...),
):
    # Get service instances (already initialized)
    stt_service = get_speech_service()
    llm_service = get_voice_llm_service()
    tts_service = get_tts_service()
    
    tmp_audio_path = None
    
    try:
        # Validate audio
        ext = os.path.splitext(file.filename)[1].lower() or ".webm"
        if ext not in ALLOWED_AUDIO_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Unsupported audio format")
            
        # Validate services
        if not stt_service.is_available():
            raise HTTPException(status_code=500, detail="Speech-to-text service not available")
        if not llm_service.is_available():
            raise HTTPException(status_code=500, detail="Language model service not available")

        # Save uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            content = await file.read()
            if not content:
                raise HTTPException(status_code=400, detail="Empty audio file")
            tmp.write(content)
            tmp_audio_path = tmp.name
            
        print(f"Processing audio file: {tmp_audio_path}")

        # Step 1: Speech-to-Text
        user_text = stt_service.transcribe(tmp_audio_path)
        print(f"Transcribed text: {user_text}")

        # Step 2: Language Model
        reply_text = llm_service.generate_response(user_text)
        print(f"Assistant reply: {reply_text}")

        # Step 3: Text-to-Speech
        audio_content, suffix = tts_service.generate_speech(reply_text)
        audio_base64 = audio_to_base64(audio_content, suffix)

        return {
            "user_text": user_text,
            "reply": reply_text,
            "audio_base64": audio_base64,
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
        
    finally:
        # Cleanup temp files
        if tmp_audio_path and os.path.exists(tmp_audio_path):
            try:
                os.unlink(tmp_audio_path)
            except Exception as e:
                print(f"Cleanup warning: {e}")

@router.post("/rag/query")
async def rag_query(request: QueryRequest):
    try:
        # Get RAG service using the singleton pattern
        rag = get_rag_service()
        result = rag.hybrid_rag_answer(query=request.query, top_k=request.top_k)
        
        # Determine if we got a real answer
        if result["source"] == "none":
            return {
                "answer": result["answer"],
                "source": "none",
                "results_count": 0,
                "status": "out_of_domain"
            }
        
        return {
            "answer": result["answer"],
            "source": result["source"],
            "results_count": len(result["results"]),
            "status": "success"
        }
    except Exception as e:
        print(f"RAG service error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG service error: {str(e)}")