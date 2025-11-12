"""
Flatten parsed legal document JSON into RAG-ready format.

Takes the nested parsed_output_final.json and creates a flat list
of chunks where each subsection (or section without subsections)
becomes one retrievable document.
"""

import json
import sys
from pathlib import Path

# Add root directory to path for config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import (
    JURISDICTION_ABBR,
    ACT_ABBR,
    CHUNK_LEVEL,
    MAX_TOKENS_PER_CHUNK,
    MIN_CHUNK_LENGTH,
    RAG_READY_JSON,
    OUTPUT_FINAL as INPUT_JSON,
)


def generate_chunk_id(jurisdiction_abbr, act_abbr, part_num, section_num, subsection_num=None):
    """
    Generate unique ID for a chunk.
    Format: ONT_RTA_2006_I_2_3
    """
    if subsection_num:
        # Remove parentheses from subsection number: "(3)" -> "3"
        subsection_clean = subsection_num.strip("()")
        return f"{jurisdiction_abbr}_{act_abbr}_{part_num}_{section_num}_{subsection_clean}"
    else:
        return f"{jurisdiction_abbr}_{act_abbr}_{part_num}_{section_num}"


def estimate_tokens(text):
    """Rough token estimate: 1 token ≈ 4 characters."""
    return len(text) // 4


def flatten_to_rag_chunks(document):
    """
    Flatten nested document structure into RAG chunks.

    Strategy:
    - If section has subsections: each subsection = 1 chunk
    - If section has no subsections: section itself = 1 chunk
    """
    chunks = []

    act_name = document.get("act_name", "")
    jurisdiction = document.get("jurisdiction", "")
    citation = document.get("citation", "")
    source_url = document.get("source_url", "")

    for part in document.get("parts", []):
        part_number = part.get("part_number", "")
        part_title = part.get("part_title", "")

        for section in part.get("sections", []):
            section_id = section.get("section_id", "")
            section_number = section.get("section_number", "")
            section_title = section.get("section_title", "")
            section_text = section.get("section_text", "")
            section_amendment_info = section.get("amendment_info")

            subsections = section.get("subsections", [])

            if subsections:
                # Create chunks from subsections
                for subsection in subsections:
                    subsection_number = subsection.get("subsection_number", "")
                    subsection_text = subsection.get("subsection_text", "")
                    subsection_amendment_info = subsection.get("amendment_info")

                    # Skip empty subsections
                    if not subsection_text or len(subsection_text) < MIN_CHUNK_LENGTH:
                        continue

                    chunk_id = generate_chunk_id(
                        JURISDICTION_ABBR,
                        ACT_ABBR,
                        part_number,
                        section_number,
                        subsection_number
                    )

                    chunk = {
                        "id": chunk_id,
                        "text": subsection_text,
                        "metadata": {
                            "act_name": act_name,
                            "jurisdiction": jurisdiction,
                            "citation": citation,
                            "part_number": part_number,
                            "part_title": part_title,
                            "section_id": section_id,
                            "section_number": section_number,
                            "section_title": section_title,
                            "subsection_number": subsection_number,
                            "source_url": source_url,
                            "tokens": estimate_tokens(subsection_text),
                            "chunk_type": "subsection"
                        }
                    }

                    # Add amendment info if present
                    if subsection_amendment_info:
                        chunk["metadata"]["amendment_info"] = subsection_amendment_info
                    elif section_amendment_info:
                        # Fallback to section amendment info
                        chunk["metadata"]["amendment_info"] = section_amendment_info

                    chunks.append(chunk)

            else:
                # No subsections: use section itself as chunk
                if not section_text or len(section_text) < MIN_CHUNK_LENGTH:
                    continue

                chunk_id = generate_chunk_id(
                    JURISDICTION_ABBR,
                    ACT_ABBR,
                    part_number,
                    section_number
                )

                chunk = {
                    "id": chunk_id,
                    "text": section_text,
                    "metadata": {
                        "act_name": act_name,
                        "jurisdiction": jurisdiction,
                        "citation": citation,
                        "part_number": part_number,
                        "part_title": part_title,
                        "section_id": section_id,
                        "section_number": section_number,
                        "section_title": section_title,
                        "source_url": source_url,
                        "tokens": estimate_tokens(section_text),
                        "chunk_type": "section"
                    }
                }

                # Add amendment info if present
                if section_amendment_info:
                    chunk["metadata"]["amendment_info"] = section_amendment_info

                chunks.append(chunk)

    return chunks


def main():
    """Main execution function."""

    print("=" * 70)
    print("📋 FLATTEN JSON FOR RAG")
    print("=" * 70)

    # Check input file exists
    if not INPUT_JSON.exists():
        print(f"\n❌ Error: Input file not found: {INPUT_JSON}")
        print(f"\nRun the parser first:")
        print(f"  cd data && python parse_document.py")
        return 1

    print(f"\n📄 Input:  {INPUT_JSON}")
    print(f"📁 Output: {RAG_READY_JSON}")
    print()

    # Load parsed document
    print("🔧 Loading parsed document...")
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        document = json.load(f)

    # Flatten to RAG chunks
    print("🔧 Flattening to RAG chunks...")
    chunks = flatten_to_rag_chunks(document)

    # Statistics
    print(f"\n📊 Chunking Statistics:")
    print(f"   Total chunks: {len(chunks)}")

    chunk_types = {}
    total_tokens = 0
    for chunk in chunks:
        chunk_type = chunk["metadata"]["chunk_type"]
        chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        total_tokens += chunk["metadata"]["tokens"]

    for chunk_type, count in chunk_types.items():
        print(f"   - {chunk_type.capitalize()} chunks: {count}")

    print(f"\n   Total estimated tokens: {total_tokens:,}")
    print(f"   Average tokens per chunk: {total_tokens // len(chunks) if chunks else 0}")

    # Check for oversized chunks
    oversized = [c for c in chunks if c["metadata"]["tokens"] > MAX_TOKENS_PER_CHUNK]
    if oversized:
        print(f"   ⚠️  Chunks exceeding {MAX_TOKENS_PER_CHUNK} tokens: {len(oversized)}")
        for chunk in oversized[:3]:  # Show first 3
            print(f"      - {chunk['id']}: {chunk['metadata']['tokens']} tokens")

    # Save RAG-ready JSON
    print(f"\n💾 Saving RAG-ready JSON...")
    rag_data = {
        "metadata": {
            "source_file": str(INPUT_JSON),
            "act_name": document.get("act_name"),
            "jurisdiction": document.get("jurisdiction"),
            "citation": document.get("citation"),
            "total_chunks": len(chunks),
            "chunk_strategy": CHUNK_LEVEL,
        },
        "chunks": chunks
    }

    with open(RAG_READY_JSON, "w", encoding="utf-8") as f:
        json.dump(rag_data, f, indent=2, ensure_ascii=False)

    print(f"✓ RAG-ready file created: {RAG_READY_JSON}")
    print(f"  Size: {RAG_READY_JSON.stat().st_size / 1024:.1f} KB")

    # Show sample chunk
    print(f"\n📌 Sample Chunk:")
    print("-" * 70)
    sample = chunks[5] if len(chunks) > 5 else chunks[0]
    print(json.dumps(sample, indent=2, ensure_ascii=False)[:500] + "...")

    print(f"\n✅ Flattening complete!")
    print(f"\nNext step: Generate embeddings and upsert to Pinecone")
    print(f"  python scripts/upsert_to_pinecone.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
