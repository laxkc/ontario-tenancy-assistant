"""Post-process parsed legal document JSON to fix issues and enhance metadata."""

import json
import re
from collections import defaultdict
from typing import Dict, Any, List


def add_metadata(document: Dict[str, Any]) -> None:
    """Add missing metadata fields like citation and source URL."""

    # Add citation if missing
    if not document.get("citation"):
        if "2006" in str(document.get("act_name", "")):
            document["citation"] = "S.O. 2006, c. 17"

    # Add source URL
    document["source_url"] = "https://www.ontario.ca/laws/statute/06r17"

    # Add processing metadata
    document["metadata"] = {
        "processed_date": None,  # Will be set when ingested
        "version": "1.0",
        "parser": "unstructured-docx"
    }


def fix_duplicate_section_numbers(parts: List[Dict[str, Any]]) -> None:
    """
    Fix duplicate section numbers by using composite numbering.
    E.g., multiple section "5" becomes "5", "5.1", "5.2", etc.
    """

    for part in parts:
        sections = part.get("sections", [])
        if not sections:
            continue

        # Track section number occurrences
        section_counter = defaultdict(int)

        for section in sections:
            section_num = section.get("section_number", "")

            # Check if this is a decimal number already (e.g., "5.1")
            if "." in section_num:
                continue

            # Count occurrences
            section_counter[section_num] += 1
            occurrence = section_counter[section_num]

            # If this is the second+ occurrence, append .1, .2, etc.
            if occurrence > 1:
                section["section_number"] = f"{section_num}.{occurrence - 1}"


def split_merged_section_titles(parts: List[Dict[str, Any]]) -> None:
    """
    Split section titles that have merged content from next sections.
    E.g., "Title text. 10 Next Title" should be split.
    """

    for part in parts:
        sections = part.get("sections", [])

        for section in sections:
            title = section.get("section_title", "")

            # Look for pattern: "...text. NUMBER CAPITAL_LETTER"
            # This suggests merged content
            match = re.search(r'^(.+?)\.\s+(\d+)\s+([A-Z].*)$', title)

            if match:
                # Keep only the first part as the title
                section["section_title"] = match.group(1).strip()

                # Store the detected merge for manual review
                if "merge_detected" not in section:
                    section["merge_detected"] = {
                        "original_title": title,
                        "split_at": f"{match.group(2)} {match.group(3)}"
                    }


def clean_section_text_whitespace(parts: List[Dict[str, Any]]) -> None:
    """Clean up excessive whitespace in all text fields."""

    for part in parts:
        # Clean part description if exists
        if "description" in part:
            part["description"] = re.sub(r'\s+', ' ', part["description"]).strip()

        for section in part.get("sections", []):
            # Clean section text
            if section.get("section_text"):
                section["section_text"] = re.sub(r'\s+', ' ', section["section_text"]).strip()

            # Clean section title
            if section.get("section_title"):
                section["section_title"] = re.sub(r'\s+', ' ', section["section_title"]).strip()

            for subsection in section.get("subsections", []):
                # Clean subsection text
                if subsection.get("subsection_text"):
                    subsection["subsection_text"] = re.sub(r'\s+', ' ', subsection["subsection_text"]).strip()

                for paragraph in subsection.get("paragraphs", []):
                    # Clean paragraph text
                    if paragraph.get("text"):
                        paragraph["text"] = re.sub(r'\s+', ' ', paragraph["text"]).strip()


def remove_empty_fields(parts: List[Dict[str, Any]]) -> None:
    """Remove empty text fields to reduce JSON size."""

    for part in parts:
        for section in part.get("sections", []):
            # Remove empty section_text
            if not section.get("section_text"):
                section.pop("section_text", None)

            for subsection in section.get("subsections", []):
                # Remove empty subsection_text
                if not subsection.get("subsection_text"):
                    subsection.pop("subsection_text", None)

                # Remove empty paragraphs array
                if not subsection.get("paragraphs"):
                    subsection.pop("paragraphs", None)


def validate_structure(document: Dict[str, Any]) -> List[str]:
    """Validate the document structure and return list of issues."""

    issues = []

    # Check required fields
    required_fields = ["act_name", "jurisdiction", "parts"]
    for field in required_fields:
        if field not in document or not document[field]:
            issues.append(f"Missing required field: {field}")

    # Check parts
    parts = document.get("parts", [])
    if not parts:
        issues.append("No parts found in document")

    # Check sections
    total_sections = 0
    for i, part in enumerate(parts):
        if "sections" not in part:
            issues.append(f"Part {i} missing 'sections' field")
            continue

        sections = part["sections"]
        total_sections += len(sections)

        for j, section in enumerate(sections):
            # Check required section fields
            if "section_number" not in section:
                issues.append(f"Part {i}, Section {j} missing 'section_number'")

    if total_sections == 0:
        issues.append("No sections found in document")

    return issues


def post_process_document(input_file: str, output_file: str) -> Dict[str, Any]:
    """Main post-processing function."""

    print(f"Loading {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        document = json.load(f)

    print("Running post-processing steps...")

    # Step 1: Add metadata
    print("  1. Adding citation and source URL...")
    add_metadata(document)

    # Step 2: Fix duplicate section numbers
    print("  2. Fixing duplicate section numbers...")
    fix_duplicate_section_numbers(document["parts"])

    # Step 3: Split merged section titles
    print("  3. Splitting merged section titles...")
    split_merged_section_titles(document["parts"])

    # Step 4: Clean whitespace
    print("  4. Cleaning whitespace...")
    clean_section_text_whitespace(document["parts"])

    # Step 5: Remove empty fields
    print("  5. Removing empty fields...")
    remove_empty_fields(document["parts"])

    # Step 6: Validate
    print("  6. Validating structure...")
    issues = validate_structure(document)

    if issues:
        print("\n⚠️  Validation issues found:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  ✓ Structure is valid")

    # Save cleaned document
    print(f"\nSaving to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(document, f, indent=2, ensure_ascii=False)

    # Print statistics
    print("\n📊 Document Statistics:")
    print(f"  - Act: {document['act_name']}")
    print(f"  - Citation: {document['citation']}")
    print(f"  - Source: {document['source_url']}")
    print(f"  - Parts: {len(document['parts'])}")

    total_sections = sum(len(part['sections']) for part in document['parts'])
    total_subsections = sum(
        len(section.get('subsections', []))
        for part in document['parts']
        for section in part['sections']
    )

    # Count sections with amendment info
    sections_with_amendments = sum(
        1 for part in document['parts']
        for section in part['sections']
        if 'amendment_info' in section
    )

    # Count subsections with amendment info
    subsections_with_amendments = sum(
        1 for part in document['parts']
        for section in part['sections']
        for subsection in section.get('subsections', [])
        if 'amendment_info' in subsection
    )

    print(f"  - Total Sections: {total_sections}")
    print(f"  - Total Subsections: {total_subsections}")
    print(f"  - Sections with amendment info: {sections_with_amendments}")
    print(f"  - Subsections with amendment info: {subsections_with_amendments}")
    print(f"  - Definitions: {len(document.get('definitions', []))}")
    print(f"  - Schedules: {len(document.get('schedules', []))}")
    print(f"  - Standalone Amendments: {len(document.get('amendments', []))}")

    # Show part breakdown
    print("\n📚 Parts Breakdown:")
    for part in document['parts']:
        print(f"  • {part['part_number']}: {part['part_title']} ({len(part['sections'])} sections)")

    return document


def main():
    input_file = "parsed_output.json"
    output_file = "parsed_output_clean.json"

    try:
        post_process_document(input_file, output_file)
        print(f"\n✅ Post-processing complete!")
        print(f"   Cleaned file saved to: {output_file}")
    except FileNotFoundError:
        print(f"❌ Error: {input_file} not found. Please run data_pre.py first.")
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {input_file}: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
