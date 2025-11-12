"""Configuration for RAG ingestion pipeline."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Fix LangChain global settings compatibility issue
try:
    from langchain import globals as langchain_globals
    langchain_globals.set_debug(False)
    langchain_globals.set_verbose(False)
except ImportError:
    pass

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
DATA_DIR = BASE_DIR.parent / "data" / "output"

# Input file
INPUT_JSON = DATA_DIR / "parsed_output_final.json"

# Output files
RAG_READY_JSON = OUTPUT_DIR / "rag_ready.json"

# API Keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Pinecone Settings
PINECONE_INDEX_NAME = "tenancy-law"

# Embedding Settings (BAAI/bge-m3)
LOCAL_MODEL_NAME = "BAAI/bge-m3"
LOCAL_MODEL_DEVICE = "cpu"
EMBEDDING_DIMENSION = 1024
NORMALIZE_EMBEDDINGS = True

# Chunking Strategy
CHUNK_LEVEL = "subsection"  # Options: "section", "subsection"
MAX_TOKENS_PER_CHUNK = 800
MIN_CHUNK_LENGTH = 20  # Skip chunks shorter than this

# Document ID Settings
JURISDICTION_ABBR = "ONT"
ACT_ABBR = "RTA_2006"

# Batch Settings
UPSERT_BATCH_SIZE = 100

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

