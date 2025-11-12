"""Web interface components for the tenancy agent.

This package contains:
- Chainlit handlers for chat and file uploads
- FastAPI routes for REST API endpoints
- Application entry point for Chainlit
"""

from .api_routes import router as api_router

__all__ = ["api_router"]
