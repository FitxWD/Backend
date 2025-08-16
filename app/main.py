from fastapi import FastAPI
from app.api.v1.endpoints import users  

app = FastAPI(title="Wellness Assistant API")

# Include router
app.include_router(users.router, prefix="/api/v1", tags=["users"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
