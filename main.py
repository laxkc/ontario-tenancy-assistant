"""Main application entry point integrating FastAPI and Chainlit."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from chainlit.utils import mount_chainlit

from src.api.routes import router as api_router

# Initialize FastAPI app
app = FastAPI(
    title="AI Agent for Tenancies",
    description="Backend API with integrated Chainlit chat interface",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api", tags=["api"])

# Mount Chainlit app
mount_chainlit(app=app, target="src/web/app.py", path="/chainlit")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)