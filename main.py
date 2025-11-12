"""Main application entry point integrating FastAPI and Chainlit."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from chainlit.utils import mount_chainlit
import google.generativeai as genai

# Import config early to ensure .env is loaded
import config

from src.web.api_routes import router as api_router

# Get configuration from environment variables
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]

# Configure Google Generative AI API key
genai.configure(api_key=config.GEMINI_API_KEY)

# Initialize FastAPI app
app = FastAPI(
    title="AI Agent for Tenancies",
    description="Backend API with integrated Chainlit chat interface",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api", tags=["api"])

# Mount Chainlit app
try:
    mount_chainlit(app=app, target="src/web/app.py", path="/chainlit")
    print("Available Gemini models:")
    # for m in genai.list_models():
    #     print(f"Model: {m.name}")
except Exception as e:
    print(f"Warning: Failed to mount Chainlit app: {e}")
    print("Chainlit interface may not be available.")


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)