from unstructured.partition.docx import partition_docx
import json
import re
from typing import Dict, Any


def is_amendment_entry(text: str, section_number: str) -> bool:
    """Check if this is an amendment citation, not a real section."""
    # Amendment years are typically 4 digits (2013, 2017, etc.)
    if len(section_number) == 4 and section_number.isdigit():
        return True
    # Check for amendment patterns like ", c. 3, s. 20"
    if re.search(r'[,\s]c\.\s*\d+[,\s]s\.\s*\d+', text):
        return True
    return False


def clean_section_title(title: str) -> str:
    """Clean up section title by removing leading punctuation."""
    # Remove leading commas, spaces, dashes
    title = re.sub(r'^[,\s\-–—]+', '', title)
    return title.strip()


def split_merged_content(text: str) -> tuple[str, str | None]:
    """Split text if it contains merged PART declarations."""
    # Look for patterns like "...text. PART II – TITLE"
    match = re.search(r'(.+?)\s+(PART\s+[IVXLC]+\s*[–-]\s*.+)$', text, re.IGNORECASE)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return text, None


def extract_amendment_info(text: str) -> tuple[str, dict | None]:
    """
    Extract amendment citation from text.
    Returns: (cleaned_text, amendment_dict or None)

    Patterns:
    - "2013, c. 3, s. 20 - 01/06/2014"
    - "2024, c. 28, Sched. 24."
    - "Section Amendments with date in force (d/m/y)"
    """
    # Pattern for amendment citations
    amendment_pattern = r'(\d{4}),\s*c\.\s*(\d+)(?:,\s*(?:s\.|Sched\.)\s*(\d+))?\s*(?:-\s*(\d{2}/\d{2}/\d{4}))?'

    match = re.search(amendment_pattern, text)
    if match:
        year = match.group(1)
        chapter = match.group(2)
        section_or_schedule = match.group(3)
        effective_date = match.group(4)

        # Build amendment info
        amendment_info = {
            "year": year,
            "chapter": chapter,
            "citation": match.group(0).strip()
        }

        if section_or_schedule:
            if "Sched." in text:
                amendment_info["schedule"] = section_or_schedule
            else:
                amendment_info["section"] = section_or_schedule

        if effective_date:
            amendment_info["effective_date"] = effective_date

        # Remove amendment from text
        cleaned_text = text[:match.start()].strip()
        # Also remove trailing punctuation/whitespace
        cleaned_text = re.sub(r'[,\s\-–—]+$', '', cleaned_text).strip()

        return cleaned_text, amendment_info

    # Check for amendment header text
    if re.search(r'Section Amendments with date in force', text, re.IGNORECASE):
        return "", None  # Skip these header lines

    return text, None


def parse_legal_document(file_path: str) -> Dict[str, Any]:
    """Parse a legal document (DOCX) into hierarchical JSON structure."""

    elements = partition_docx(file_path, strategy="fast")

    # Initialize the document structure
    document = {
        "act_name": None,
        "jurisdiction": "Ontario",
        "citation": None,
        "consolidation_date": None,
        "last_amendment": None,
        "parts": [],
        "definitions": [],
        "schedules": [],
        "amendments": []  # Store amendment entries separately
    }

    current_part = None
    current_section = None
    current_subsection = None
    current_schedule = None
    pending_part_text = None  # Store split PART text
    pending_part_number = None  # Store PART number when title comes on next line

    for element in elements:
        text = element.text.strip()
        if not text:
            continue

        # Skip table of contents (appears as large Table element)
        if element.category == "Table" and len(text) > 1000:
            continue

        # Check if we have pending PART text from previous split
        if pending_part_text:
            text = pending_part_text
            pending_part_text = None

        # Detect Act metadata (title, citation)
        if not document["act_name"] and ("Act" in text or "S.O." in text):
            if "S.O." in text and len(text) < 300:
                document["citation"] = text
            if len(text) < 200 and "Act" in text and "PART" not in text.upper():
                document["act_name"] = text

        # Detect consolidation/amendment info
        if "Consolidation Period" in text or "Last amendment" in text:
            if "Consolidation" in text:
                document["consolidation_date"] = text
            elif "amendment" in text:
                document["last_amendment"] = text

        # Detect SCHEDULE (e.g., "SCHEDULE A", "SCHEDULE 1")
        schedule_match = re.match(r'^SCHEDULE\s+([A-Z0-9]+)\s*[–-]?\s*(.*)$', text, re.IGNORECASE)
        if schedule_match:
            current_schedule = {
                "schedule_id": schedule_match.group(1),
                "schedule_title": schedule_match.group(2).strip(),
                "content": ""
            }
            document["schedules"].append(current_schedule)
            current_part = None
            current_section = None
            current_subsection = None
            continue

        # If we're in a schedule, append content (but check for PART)
        if current_schedule:
            # Check if PART starts within schedule
            if re.match(r'^PART\s+[IVXLC]+', text, re.IGNORECASE):
                current_schedule = None
            else:
                current_schedule["content"] += " " + text
                continue

        # Detect PART - handles multiple formats:
        # Format 1: "PART I – INTRODUCTION" (single line with dash)
        # Format 2: "part i" followed by "introduction" on next line
        # Format 3: "part i\nintroduction" (multiline in same element)

        # First check if we have a pending part number waiting for a title
        if pending_part_number:
            # This line should be the part title
            current_part = {
                "part_number": pending_part_number,
                "part_title": text.strip().upper(),
                "sections": []
            }
            document["parts"].append(current_part)
            current_section = None
            current_subsection = None
            current_schedule = None
            pending_part_number = None
            continue

        # Check for single-line PART with dash (e.g., "PART I – INTRODUCTION")
        part_match = re.match(r'^PART\s+([IVXLC]+|[\d]+)\s*[–-]\s*(.+)$', text, re.IGNORECASE)
        if part_match:
            current_part = {
                "part_number": part_match.group(1).upper(),
                "part_title": part_match.group(2).strip().upper(),
                "sections": []
            }
            document["parts"].append(current_part)
            current_section = None
            current_subsection = None
            current_schedule = None
            continue

        # Check for multi-line PART within same element (e.g., "part i\nintroduction")
        multiline_part_match = re.match(r'^part\s+([ivxlc]+|[\d]+)\s*[\n\r]+\s*(.+)$', text, re.IGNORECASE)
        if multiline_part_match:
            current_part = {
                "part_number": multiline_part_match.group(1).upper(),
                "part_title": multiline_part_match.group(2).strip().upper(),
                "sections": []
            }
            document["parts"].append(current_part)
            current_section = None
            current_subsection = None
            current_schedule = None
            continue

        # Check for PART number only (title will come in next element)
        part_number_only = re.match(r'^part\s+([ivxlc]+|[\d]+)\s*$', text, re.IGNORECASE)
        if part_number_only:
            pending_part_number = part_number_only.group(1).upper()
            continue

        # Skip "Section Amendments with date in force" headers
        if re.search(r'Section Amendments with date in force', text, re.IGNORECASE):
            continue

        # Skip standalone amendment lines (these are metadata, not content)
        # Pattern: Just an amendment citation with no other content
        _, potential_amendment = extract_amendment_info(text)
        if potential_amendment and len(text) < 100:
            # This is likely a standalone amendment line, skip it
            continue

        # Detect definitions (e.g., ""landlord" means...")
        definition_match = re.match(r'^["""]([^"""]+)["""]?\s+means\s+(.+)$', text)
        if definition_match:
            term = definition_match.group(1).strip()
            definition = definition_match.group(2).strip()
            document["definitions"].append({
                "term": term,
                "definition": definition
            })
            continue

        # Detect Section (e.g., "1. Purposes of Act" or "Section 1")
        section_match = re.match(r'^(?:Section\s+)?(\d+)\.?\s*(.*)$', text)
        if section_match and len(text) < 300:  # Increased limit
            section_number = section_match.group(1)
            section_title = section_match.group(2).strip()

            # Check if this is an amendment entry
            if is_amendment_entry(text, section_number):
                document["amendments"].append({
                    "year": section_number if len(section_number) == 4 else None,
                    "citation": clean_section_title(section_title) if section_title else text,
                    "full_text": text
                })
                continue

            # Extract amendment info from section title if present
            section_title, amendment_info = extract_amendment_info(section_title)

            # Clean the title
            section_title = clean_section_title(section_title)

            # Create a part if none exists (this should rarely happen now)
            if not current_part:
                current_part = {
                    "part_number": "PRELIMINARY",
                    "part_title": "Preliminary Sections",
                    "sections": []
                }
                document["parts"].insert(0, current_part)

            current_section = {
                "section_number": section_number,
                "section_title": section_title,
                "section_text": "",
                "subsections": []
            }

            # Add amendment info if found
            if amendment_info:
                current_section["amendment_info"] = amendment_info

            current_part["sections"].append(current_section)
            current_subsection = None
            continue

        # Detect Subsection (e.g., "(1)", "(2)")
        subsection_match = re.match(r'^\((\d+)\)\s*(.*)$', text)
        if subsection_match and current_section:
            subsection_number = subsection_match.group(1)
            subsection_text = subsection_match.group(2).strip()

            # Extract amendment info from subsection text if present
            subsection_text, amendment_info = extract_amendment_info(subsection_text)

            current_subsection = {
                "subsection_number": f"({subsection_number})",
                "subsection_text": subsection_text,
                "paragraphs": []
            }

            # Add amendment info if found
            if amendment_info:
                current_subsection["amendment_info"] = amendment_info

            current_section["subsections"].append(current_subsection)
            continue

        # Detect Paragraph (e.g., "(a)", "(b)")
        paragraph_match = re.match(r'^\(([a-z])\)\s*(.*)$', text, re.IGNORECASE)
        if paragraph_match and current_subsection:
            paragraph_label = paragraph_match.group(1)
            paragraph_text = paragraph_match.group(2).strip()

            current_subsection["paragraphs"].append({
                "label": f"({paragraph_label})",
                "text": paragraph_text
            })
            continue

        # Otherwise, append to current context (with split detection)
        # Check for merged PART in the text
        main_text, split_part = split_merged_content(text)

        if split_part:
            pending_part_text = split_part
            text = main_text

        # Append text to appropriate context
        if current_subsection:
            # Add to last paragraph or subsection text
            if current_subsection["paragraphs"]:
                current_subsection["paragraphs"][-1]["text"] += " " + text
            else:
                current_subsection["subsection_text"] += " " + text
        elif current_section:
            if not current_section["subsections"]:
                current_section["section_text"] += " " + text
            else:
                # Append to last subsection
                current_section["subsections"][-1]["subsection_text"] += " " + text
        elif current_part:
            # Content without section (rare, but possible)
            if not current_part["sections"]:
                if "description" not in current_part:
                    current_part["description"] = text
                else:
                    current_part["description"] += " " + text

    # Post-process: clean up empty text fields
    for part in document["parts"]:
        for section in part["sections"]:
            section["section_text"] = section["section_text"].strip()
            for subsection in section["subsections"]:
                subsection["subsection_text"] = subsection["subsection_text"].strip()

    return document


def main():
    file_path = "../docs/06r17_e.docx"

    print("Parsing legal document...")
    structured_data = parse_legal_document(file_path)

    # Save to JSON
    output_file = "parsed_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(structured_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Parsed document saved to {output_file}")
    print(f"  - Act: {structured_data['act_name']}")
    print(f"  - Citation: {structured_data['citation']}")
    print(f"  - Parts: {len(structured_data['parts'])}")

    total_sections = sum(len(part['sections']) for part in structured_data['parts'])
    print(f"  - Total Sections: {total_sections}")

    # Show part breakdown
    for part in structured_data['parts']:
        print(f"    • Part {part['part_number']}: {len(part['sections'])} sections")

    print(f"  - Definitions: {len(structured_data['definitions'])}")
    print(f"  - Schedules: {len(structured_data['schedules'])}")
    print(f"  - Amendments: {len(structured_data['amendments'])}")


if __name__ == "__main__":
    main()
