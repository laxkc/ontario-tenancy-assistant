"""Chainlit web app configuration."""
from pathlib import Path

# Web app settings
WEB_APP_TITLE = "AI Agent for Tenancies"
WEB_APP_DESCRIPTION = "Your AI-powered assistant"

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CHAINLIT_APP_PATH = Path(__file__).parent / "app.py"

# UI Settings
THEME_SETTINGS = {
    "default_theme": "light",
    "hide_cot": False,  # Chain of Thought
}

# Feature flags
ENABLE_AUTHENTICATION = False
ENABLE_DATA_PERSISTENCE = False
