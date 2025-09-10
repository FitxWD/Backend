from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import users  
from app.api.v1.endpoints import assistant

app = FastAPI(
    title="Wellness Assistant API",
    description="API for wellness and voice-based interactions with AI assistants",
    version="1.0.0"
)

origins = [
    "http://localhost:3000",  # Your Next.js frontend
    "*",  # Allow all origins for testing
]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(assistant.router, prefix="/api/v1", tags=["assistant"])

@app.get("/")
async def root():
    return {
        "message": "Wellness Assistant API is running!",
        "status": "healthy",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Wellness Assistant API...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
