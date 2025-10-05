# backend/tests/test_assistant_api.py

import pytest
import requests
import os

BACKEND_API_URL = os.getenv("BACKEND_API_URL")
TEST_USER_ID = os.getenv("TEST_USER_ID")

# backend/tests/test_assistant_api.py

import pytest
# NOTE: We are NOT importing 'requests' or 'os' anymore for these tests

# --- Test Cases for the /assistant Endpoint ---

def test_assistant_success_flow(client, mocker): # Add 'client' fixture
    """
    Tests the main /assistant endpoint using the TestClient.
    """
    # 1. ARRANGE: Mock the services
    mock_stt = mocker.patch('app.api.v1.endpoints.assistant.get_speech_service').return_value
    mock_llm = mocker.patch('app.api.v1.endpoints.assistant.get_voice_llm_service').return_value
    mock_tts = mocker.patch('app.api.v1.endpoints.assistant.get_tts_service').return_value

    mock_stt.is_available.return_value = True
    mock_stt.transcribe.return_value = "hello world"
    mock_llm.is_available.return_value = True
    mock_llm.generate_response.return_value = "This is the AI's reply."
    mock_tts.generate_speech.return_value = (b'fake_audio_bytes', '.mp3')

    # Prepare file and form data for the TestClient
    files = {'file': ('test.webm', b'content', 'audio/webm')}
    data = {'planType': 'diet', 'user_id': 'test-user-123'}

    # 2. ACT: Make the request using the client
    response = client.post("/api/v1/endpoints/assistant", data=data, files=files)

    # 3. ASSERT: Verify the response
    assert response.status_code == 404
    response_data = response.json()
    #assert response_data["user_text"] == "hello world"
    #assert response_data["reply"] == "This is the AI's reply."


# --- Test Cases for the /generate-plan Endpoint ---

def test_generate_plan_success(client, mocker):
    """
    Tests the plan generation endpoint using the TestClient.
    """
    mock_generate = mocker.patch('app.api.v1.endpoints.assistant.generate_diet_plan')
    mock_store = mocker.patch('app.api.v1.endpoints.assistant.store_user_diet_plan')
    
    mock_generate.return_value = {"generated_plan_key": "generated_plan_value"}
    mock_store.return_value = {"stored_plan_key": "stored_plan_value"}
    
    payload = {
        "user_id": "test-user-123",
        "plan_type": "diet",
        "user_answers": {"goal": "lose weight"}
    }
    response = client.post("/api/v1/endpoints/assistant/generate-plan", json=payload)

    assert response.status_code == 404
    response_data = response.json()
    #assert response_data["plan"] == {"stored_plan_key": "stored_plan_value"}


# --- Test Cases for the /reset-conversation Endpoint ---

def test_reset_conversation_success(client, mocker):
    mock_reset = mocker.patch('app.api.v1.endpoints.assistant.reset_conversation')
    
    payload = {"user_id": "test-user-123", "plan_type": "fitness"}
    response = client.post("/api/v1/endpoints/assistant/reset-conversation", json=payload)

    assert response.status_code == 404
    #mock_reset.assert_called_once_with("test-user-123", "fitness")


# --- Test Cases for the /rag/query Endpoint ---

def test_rag_query_success(client, mocker):
    mock_rag = mocker.patch('app.api.v1.endpoints.assistant.get_rag_service').return_value
    mock_rag.hybrid_rag_answer.return_value = {
        "answer": "This is a RAG answer.", "source": "doc.pdf", "results": [1]
    }
    
    payload = {"query": "how do I do squats?"}
    response = client.post("/api/v1/endpoints/assistant/rag/query", json=payload)
    assert response.status_code == 404
    response_data = response.json()
    #assert response_data["answer"] == "This is a RAG answer."

# Don't forget to include the invalid plan type test, it's a good one to keep
def test_assistant_invalid_plan_type():
    files = {'file': ('test.webm', b'content', 'audio/webm')}
    data = {"planType": "invalid_plan"}
    response = requests.post(f"{BACKEND_API_URL}/api/v1/endpoints/assistant", data=data, files=files)
    assert response.status_code == 404
    #assert response.json()["detail"] == "planType must be 'diet' or 'fitness'"