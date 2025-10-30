"""Configuration for legal document parser."""

from pathlib import Path

# Directories
BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR.parent / "docs"
OUTPUT_DIR = BASE_DIR / "output"

# Input/Output files
INPUT_DOCX = DOCS_DIR / "06r17_e.docx"
OUTPUT_RAW = OUTPUT_DIR / "parsed_output.json"
OUTPUT_CLEAN = OUTPUT_DIR / "parsed_output_clean.json"
OUTPUT_FINAL = OUTPUT_DIR / "parsed_output_final.json"

# Document metadata
DEFAULT_JURISDICTION = "Ontario"
DEFAULT_ACT_CITATION = "S.O. 2006, c. 17"
SOURCE_URL = "https://www.ontario.ca/laws/statute/06r17"

# Processing options
SKIP_TABLE_OF_CONTENTS = True
MAX_SECTION_TITLE_LENGTH = 300
TOKEN_ESTIMATION_RATIO = 4  # 1 token ≈ 4 characters
LARGE_SECTION_TOKEN_THRESHOLD = 1500

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)
