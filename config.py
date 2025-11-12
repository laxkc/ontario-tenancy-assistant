"""Configuration for AI Agent for Tenancies."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Fix LangChain global settings compatibility issue
try:
    from langchain import globals as langchain_globals
    langchain_globals.set_debug(False)
    langchain_globals.set_verbose(False)
except ImportError:
    pass

# ============================================================================
# API Keys
# ============================================================================
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ============================================================================
# LLM Configuration (Gemini)
# ============================================================================
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", None)  # None uses "gemini-2.5-flash"
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))  # Default temperature

# ============================================================================
# Pinecone Settings
# ============================================================================
PINECONE_INDEX_NAME = "tenancy-law"

# ============================================================================
# Embedding Settings (BAAI/bge-m3)
# ============================================================================
LOCAL_MODEL_NAME = "BAAI/bge-m3"
LOCAL_MODEL_DEVICE = "cpu"
EMBEDDING_DIMENSION = 1024
NORMALIZE_EMBEDDINGS = True

# ============================================================================
# Data Pipeline Settings
# ============================================================================
DATA_DIR = Path(__file__).parent / "data"
DOCS_DIR = DATA_DIR.parent / "docs"
DATA_OUTPUT_DIR = DATA_DIR / "output"

# Input/Output files
INPUT_DOCX = DOCS_DIR / "06r17_e.docx"
OUTPUT_RAW = DATA_OUTPUT_DIR / "parsed_output.json"
OUTPUT_CLEAN = DATA_OUTPUT_DIR / "parsed_output_clean.json"
OUTPUT_FINAL = DATA_OUTPUT_DIR / "parsed_output_final.json"

# Document metadata
DEFAULT_JURISDICTION = "Ontario"
DEFAULT_ACT_CITATION = "S.O. 2006, c. 17"
SOURCE_URL = "https://www.ontario.ca/laws/statute/06r17"

# Processing options
SKIP_TABLE_OF_CONTENTS = True
MAX_SECTION_TITLE_LENGTH = 300
TOKEN_ESTIMATION_RATIO = 4  # 1 token ≈ 4 characters
LARGE_SECTION_TOKEN_THRESHOLD = 1500

# ============================================================================
# RAG Settings
# ============================================================================
OUTPUT_DIR = Path(__file__).parent / "output"
RAG_READY_JSON = OUTPUT_DIR / "rag_ready.json"

# Chunking Strategy
CHUNK_LEVEL = "subsection"  # Options: "section", "subsection"
MAX_TOKENS_PER_CHUNK = 800
MIN_CHUNK_LENGTH = 20  # Skip chunks shorter than this

# Document ID Settings
JURISDICTION_ABBR = "ONT"
ACT_ABBR = "RTA_2006"

# Batch Settings
UPSERT_BATCH_SIZE = 100

# Ensure output directories exist
DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

