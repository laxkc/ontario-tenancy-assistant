"""FastAPI API routes and endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    message: str


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    session_id: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="API is running"
    )


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Agent for Tenancies API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "chat_ui": "/chainlit",
        }
    }


# Add more API routes here for your backend logic
# Example: RAG queries, data processing, etc.

