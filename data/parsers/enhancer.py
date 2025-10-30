"""Final enhancements for RAG pipeline readiness."""

import json
import re
from typing import Dict, Any, List


def add_hierarchical_section_ids(document: Dict[str, Any]) -> None:
    """
    Add hierarchical section IDs in format: PART.SECTION
    Example: "I.1", "II.5", "V.47"

    This prevents confusion when multiple parts have section "1".
    """
    for part in document["parts"]:
        part_number = part["part_number"]

        for section in part["sections"]:
            section_number = section["section_number"]

            # Add hierarchical ID
            section["section_id"] = f"{part_number}.{section_number}"

            # Add hierarchical subsection IDs
            for subsection in section.get("subsections", []):
                subsection_number = subsection["subsection_number"]
                subsection["subsection_id"] = f"{part_number}.{section_number}.{subsection_number}"


def extract_bilingual_terms(document: Dict[str, Any]) -> None:
    """
    Extract French terms that appear in parentheses.
    Pattern: "term" ... ("French term")
    """
    bilingual_terms = []

    for part in document["parts"]:
        for section in part["sections"]:
            # Search in section text
            text = section.get("section_text", "")

            # Pattern: "English term" ... ("French term")
            # Example: "Board" means the Landlord and Tenant Board; ("Commission")
            matches = re.findall(r'"([^"]+)"[^(]*\("([^)]+)"\)', text)

            for english, french in matches:
                bilingual_terms.append({
                    "english": english.strip(),
                    "french": french.strip(),
                    "section_id": section.get("section_id", f"{part['part_number']}.{section['section_number']}")
                })

    # Add to document
    document["bilingual_terms"] = bilingual_terms


def estimate_token_counts(document: Dict[str, Any]) -> None:
    """
    Add token count estimates (rough: 1 token ≈ 4 chars).
    Flag sections > 1500 tokens for chunking.
    """
    chunking_recommendations = []

    for part in document["parts"]:
        for section in part["sections"]:
            section_text = section.get("section_text", "")

            # Rough token estimate
            estimated_tokens = len(section_text) // 4
            section["estimated_tokens"] = estimated_tokens

            # If section is large, recommend chunking
            if estimated_tokens > 1500:
                chunking_recommendations.append({
                    "section_id": section.get("section_id"),
                    "section_number": section["section_number"],
                    "section_title": section["section_title"],
                    "estimated_tokens": estimated_tokens,
                    "recommendation": "Split by subsections for better retrieval"
                })

            # Add token counts to subsections
            for subsection in section.get("subsections", []):
                subsection_text = subsection.get("subsection_text", "")
                subsection["estimated_tokens"] = len(subsection_text) // 4

    # Add chunking recommendations to metadata
    if chunking_recommendations:
        if "metadata" not in document:
            document["metadata"] = {}
        document["metadata"]["chunking_recommendations"] = chunking_recommendations


def add_part_summaries(document: Dict[str, Any]) -> None:
    """
    Add part-level summaries based on first few sections.
    """
    for part in document["parts"]:
        sections = part.get("sections", [])

        # Get first section title as part summary hint
        if sections:
            first_section_titles = [s["section_title"] for s in sections[:3] if s.get("section_title")]
            part["summary_hint"] = f"Covers: {', '.join(first_section_titles[:2])}"

        # Count statistics
        part["total_sections"] = len(sections)
        part["total_subsections"] = sum(len(s.get("subsections", [])) for s in sections)


def add_retrieval_metadata(document: Dict[str, Any]) -> None:
    """
    Add metadata useful for RAG retrieval.
    """
    # Overall statistics
    total_sections = sum(len(part['sections']) for part in document['parts'])
    total_subsections = sum(
        len(section.get('subsections', []))
        for part in document['parts']
        for section in part['sections']
    )

    total_text = sum(
        len(section.get('section_text', ''))
        for part in document['parts']
        for section in part['sections']
    )

    if "metadata" not in document:
        document["metadata"] = {}

    document["metadata"].update({
        "total_parts": len(document["parts"]),
        "total_sections": total_sections,
        "total_subsections": total_subsections,
        "total_characters": total_text,
        "estimated_total_tokens": total_text // 4,
        "recommended_chunk_strategy": "section or subsection level",
        "optimal_for": ["semantic search", "RAG retrieval", "legal citation lookup"]
    })


def enhance_document(input_file: str, output_file: str) -> Dict[str, Any]:
    """Apply all enhancements."""

    print(f"Loading {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        document = json.load(f)

    print("\n🔧 Applying enhancements...")

    print("  1. Adding hierarchical section IDs (Part.Section format)...")
    add_hierarchical_section_ids(document)

    print("  2. Extracting bilingual terms (English/French)...")
    extract_bilingual_terms(document)

    print("  3. Estimating token counts and chunking needs...")
    estimate_token_counts(document)

    print("  4. Adding part-level summaries...")
    add_part_summaries(document)

    print("  5. Adding retrieval metadata...")
    add_retrieval_metadata(document)

    # Save enhanced document
    print(f"\n💾 Saving enhanced document to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(document, f, indent=2, ensure_ascii=False)

    # Print statistics
    print("\n📊 Enhancement Summary:")
    print(f"  ✓ Hierarchical section IDs added to {document['metadata']['total_sections']} sections")
    print(f"  ✓ Bilingual terms extracted: {len(document.get('bilingual_terms', []))}")
    print(f"  ✓ Token counts estimated for all sections/subsections")

    chunking_recs = document.get("metadata", {}).get("chunking_recommendations", [])
    if chunking_recs:
        print(f"  ⚠ Large sections needing chunking: {len(chunking_recs)}")
    else:
        print(f"  ✓ All sections within optimal size (<1500 tokens)")

    print(f"\n  Total estimated tokens: {document['metadata']['estimated_total_tokens']:,}")
    print(f"  Recommended strategy: {document['metadata']['recommended_chunk_strategy']}")

    return document


def main():
    input_file = "parsed_output_clean.json"
    output_file = "parsed_output_final.json"

    try:
        enhance_document(input_file, output_file)
        print(f"\n✅ Enhancement complete!")
        print(f"   Final RAG-ready file: {output_file}")
        print(f"\n🚀 Ready for:")
        print(f"   • Vector database ingestion (Pinecone/pgvector)")
        print(f"   • Semantic chunking and embeddings")
        print(f"   • Legal citation lookup")
        print(f"   • Multi-lingual retrieval")
    except FileNotFoundError:
        print(f"❌ Error: {input_file} not found. Please run post_process.py first.")
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {input_file}: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
