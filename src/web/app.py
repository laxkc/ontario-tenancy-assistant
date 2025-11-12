"""Main Chainlit application entry point."""
import chainlit as cl
from src.web.handlers.chat_handlers import (
    on_chat_start,
    on_message,
    on_chat_end,
    on_chat_resume,
)

# All event handlers are imported and registered via decorators
# This file serves as the entry point for Chainlit

if __name__ == "__main__":
    # This allows running the Chainlit app standalone
    # Run with: chainlit run src/web/app.py
    pass
