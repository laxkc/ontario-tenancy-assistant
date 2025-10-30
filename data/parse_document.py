#!/usr/bin/env python3
"""
Main entry point for parsing legal documents.

Usage:
    python parse_document.py [input_file]

If no input file is specified, uses the default from config.py
"""

import sys
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from parsers.docx_parser import parse_legal_document
from parsers.post_processor import post_process_document
from parsers.enhancer import enhance_document
import config


def main(input_file=None):
    """Run the complete parsing pipeline."""

    # Determine input file
    if input_file:
        input_path = Path(input_file)
    else:
        input_path = config.INPUT_DOCX

    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        print(f"\nExpected location: {config.INPUT_DOCX}")
        return 1

    print("=" * 70)
    print("🏛️  LEGAL DOCUMENT PARSER - Modular Pipeline")
    print("=" * 70)
    print(f"\n📄 Input:  {input_path}")
    print(f"📁 Output: {config.OUTPUT_DIR}/")
    print()

    # Stage 1: Parse DOCX
    print("🔧 STAGE 1: Parsing DOCX...")
    print("-" * 70)
    try:
        document = parse_legal_document(str(input_path))

        # Save raw output
        with open(config.OUTPUT_RAW, "w", encoding="utf-8") as f:
            json.dump(document, f, indent=2, ensure_ascii=False)

        print(f"✓ Raw parse complete: {config.OUTPUT_RAW.name}")
        print(f"  - Parts: {len(document['parts'])}")
        print(f"  - Sections: {sum(len(p['sections']) for p in document['parts'])}")

    except Exception as e:
        print(f"❌ Error during parsing: {e}")
        return 1

    # Stage 2: Post-process
    print("\n🔧 STAGE 2: Post-processing...")
    print("-" * 70)
    try:
        document = post_process_document(
            str(config.OUTPUT_RAW),
            str(config.OUTPUT_CLEAN)
        )
        print(f"✓ Post-processing complete: {config.OUTPUT_CLEAN.name}")

    except Exception as e:
        print(f"❌ Error during post-processing: {e}")
        return 1

    # Stage 3: Enhance for RAG
    print("\n🔧 STAGE 3: RAG Enhancement...")
    print("-" * 70)
    try:
        document = enhance_document(
            str(config.OUTPUT_CLEAN),
            str(config.OUTPUT_FINAL)
        )
        print(f"✓ Enhancement complete: {config.OUTPUT_FINAL.name}")

    except Exception as e:
        print(f"❌ Error during enhancement: {e}")
        return 1

    # Summary
    print("\n" + "=" * 70)
    print("✅ PIPELINE COMPLETE")
    print("=" * 70)
    print(f"\n📊 Final Statistics:")
    print(f"   Act: {document['act_name']}")
    print(f"   Citation: {document['citation']}")
    print(f"   Parts: {len(document['parts'])}")
    print(f"   Sections: {document['metadata']['total_sections']}")
    print(f"   Subsections: {document['metadata']['total_subsections']}")
    print(f"   Estimated Tokens: {document['metadata']['estimated_total_tokens']:,}")

    print(f"\n🎯 Use this file for RAG:")
    print(f"   📁 {config.OUTPUT_FINAL}")
    print(f"   📦 Size: {config.OUTPUT_FINAL.stat().st_size / 1024:.1f} KB")

    print("\n🚀 Ready for:")
    print("   • Vector database ingestion (Pinecone/pgvector)")
    print("   • Semantic chunking and embeddings")
    print("   • Legal citation lookup")
    print()

    return 0


if __name__ == "__main__":
    # Get input file from command line if provided
    input_file = sys.argv[1] if len(sys.argv) > 1 else None

    sys.exit(main(input_file))
