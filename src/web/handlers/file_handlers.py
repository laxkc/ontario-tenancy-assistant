"""File upload and processing handlers for Chainlit."""
import chainlit as cl
from pathlib import Path
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document
except ImportError:
    Document = None


async def process_uploaded_file(file: cl.File) -> str:
    """Process uploaded file and extract text content.

    Args:
        file: Uploaded file from Chainlit

    Returns:
        Extracted text content
    """
    file_path = Path(file.path)
    file_ext = file_path.suffix.lower()

    try:
        if file_ext == ".pdf":
            return extract_text_from_pdf(file.path)
        elif file_ext in [".docx", ".doc"]:
            return extract_text_from_docx(file.path)
        elif file_ext == ".txt":
            return extract_text_from_txt(file.path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

    except Exception as e:
        raise ValueError(f"Failed to process file: {str(e)}")


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    if PyPDF2 is None:
        raise ImportError("PyPDF2 is not installed. Install with: uv pip install PyPDF2")

    text = ""
    with open(file_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"

    return text.strip()


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    if Document is None:
        raise ImportError("python-docx is not installed. Install with: uv pip install python-docx")

    doc = Document(file_path)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text.strip()


def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file."""
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()
    return text.strip()


async def handle_file_upload(files: list):
    """Handle file upload for contract analysis."""
    if not files:
        return

    file = files[0]

    await cl.Message(
        content=f"📄 Processing {file.name}..."
    ).send()

    try:
        contract_text = await process_uploaded_file(file)

        if len(contract_text) < 100:
            await cl.Message(
                content="⚠️ The uploaded file appears to be too short. Please ensure it contains a valid contract."
            ).send()
            return

        cl.user_session.set("uploaded_contract", {
            "filename": file.name,
            "text": contract_text
        })

        await cl.Message(
            content=f"""✅ Contract uploaded successfully!

**File**: {file.name}
**Size**: {len(contract_text)} characters

📋 Analyzing contract for compliance with Ontario RTA 2006...
This may take a moment.
"""
        ).send()

        await analyze_uploaded_contract()

    except Exception as e:
        await cl.Message(
            content=f"❌ Error processing file: {str(e)}"
        ).send()


async def analyze_uploaded_contract():
    """Analyze the uploaded contract."""
    from rag.langchain import analyze_contract

    contract_data = cl.user_session.get("uploaded_contract")

    if not contract_data:
        await cl.Message(
            content="❌ No contract found. Please upload a contract first."
        ).send()
        return

    response_msg = cl.Message(content="")
    await response_msg.send()

    try:
        await response_msg.stream_token("🔍 Extracting contract clauses...\n\n")

        result = analyze_contract(
            contract_text=contract_data["text"],
            contract_type="Residential Lease"
        )

        response_msg.content = ""
        await response_msg.update()

        analysis_result = result.get("analysis_result", "Analysis failed")

        chunk_size = 50
        for i in range(0, len(analysis_result), chunk_size):
            chunk = analysis_result[i:i+chunk_size]
            await response_msg.stream_token(chunk)

        await response_msg.update()

    except Exception as e:
        response_msg.content = f"❌ **Error analyzing contract:**\n\n```\n{str(e)}\n```"
        await response_msg.update()
