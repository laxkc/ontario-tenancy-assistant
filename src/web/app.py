"""Main Chainlit application entry point.

This module serves as the entry point for the Chainlit web interface.
All event handlers are imported from chainlit_handlers and registered
via decorators when this module is loaded.
"""
import chainlit as cl

# Import handlers to register them via decorators
# Using absolute import to avoid module resolution issues
from src.web.chainlit_handlers import (
    on_chat_start,
    on_message,
    on_chat_end,
    on_chat_resume,
)

# All event handlers are automatically registered when imported
# This file serves as the entry point for Chainlit when mounted in main.py
