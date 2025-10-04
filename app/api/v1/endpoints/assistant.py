from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body, Form
import tempfile
import os
from app.services.voice_service.stt import get_speech_service
from app.services.voice_service.llm import get_language_model_service as get_voice_llm_service
from app.services.voice_service.tts import get_tts_service
from app.utils.audio import audio_to_base64
from app.config import ALLOWED_AUDIO_EXTENSIONS
from app.services.rag_service.rag import get_rag_service
from app.api.v1.schemas.query import QueryRequest
from app.services.voice_service.plan_generator import generate_diet_plan, generate_fitness_plan
from app.services.voice_service.conversation import reset_conversation, get_user_answers
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# Add new schema for plan generation
class PlanRequest(BaseModel):
    user_answers: dict
    plan_type: str  # "diet" or "fitness"

@router.post("/assistant")
async def assistant(
    file: UploadFile = File(...),
    planType: str = Form("diet"),  # Changed from plan_type to planType to match frontend
    user_id: str = Form("default")  # Add user_id support
):
    # Get service instances (already initialized)
    stt_service = get_speech_service()
    llm_service = get_voice_llm_service()
    tts_service = get_tts_service()
    
    tmp_audio_path = None
    
    try:
        # Convert planType to plan_type for internal use
        plan_type = planType.lower()  # Ensure lowercase
        print(f"Received planType: {planType}, using plan_type: {plan_type}")
        
        # Validate plan_type
        if plan_type not in ["diet", "fitness"]:
            raise HTTPException(status_code=400, detail="planType must be 'diet' or 'fitness'")
            
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

        # Step 2: Language Model (pass plan_type and user_id)
        reply_text = llm_service.generate_response(user_text, user_id=user_id, plan_type=plan_type)
        print(f"Assistant reply: {reply_text}")

        # Step 3: Text-to-Speech
        audio_content, suffix = tts_service.generate_speech(reply_text)
        audio_base64 = audio_to_base64(audio_content, suffix)

        return {
            "user_text": user_text,
            "reply": reply_text,
            "audio_base64": audio_base64,
            "plan_type": plan_type,  # Return as plan_type for consistency
            "planType": planType,    # Also return original planType for frontend
            "user_id": user_id,
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

@router.post("/generate-plan")
async def generate_plan(request: PlanRequest):
    """Generate diet or fitness plan from form submission answers"""
    try:
        # Validate plan_type
        if request.plan_type not in ["diet", "fitness"]:
            raise HTTPException(status_code=400, detail="plan_type must be 'diet' or 'fitness'")
        
        # Validate user_answers
        if not request.user_answers:
            raise HTTPException(status_code=400, detail="user_answers cannot be empty")
        
        # Generate plan based on type
        if request.plan_type == "diet":
            plan = generate_diet_plan(request.user_answers)
        else:  # fitness
            plan = generate_fitness_plan(request.user_answers)
        
        return {
            "plan": plan,
            "plan_type": request.plan_type,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Plan generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Plan generation error: {str(e)}")

@router.post("/reset-conversation")
async def reset_user_conversation(
    user_id: str = "default",
    plan_type: str = "diet"
):
    """Reset conversation for a user and plan type"""
    try:
        if plan_type not in ["diet", "fitness"]:
            raise HTTPException(status_code=400, detail="plan_type must be 'diet' or 'fitness'")
        
        reset_conversation(user_id, plan_type)
        return {
            "message": f"Conversation reset for user {user_id} and plan type {plan_type}",
            "status": "success"
        }
    except Exception as e:
        print(f"Reset conversation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Reset conversation error: {str(e)}")

# ...existing rag endpoint...
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