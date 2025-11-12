"""Chainlit event handlers for chat and file uploads."""

import chainlit as cl
from pathlib import Path

from src.core.qa import get_answer
from src.langchain.rag_graph import create_rag_graph
from src.langchain import analyze_contract

# File processing imports
try:
    import pypdf
    PyPDF2 = pypdf  # Alias for compatibility
except ImportError:
    try:
        import PyPDF2
    except ImportError:
        PyPDF2 = None

try:
    from docx import Document
except ImportError:
    Document = None


# ============================================================================
# File Processing Functions
# ============================================================================

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


async def process_uploaded_file(file: cl.File) -> str:
    """Process uploaded file and extract text content."""
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


async def handle_file_upload(files: list):
    """Handle file upload for contract analysis."""
    if not files:
        return

    file = files[0]

    await cl.Message(content=f"📄 Processing {file.name}...").send()

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
        await cl.Message(content=f"❌ Error processing file: {str(e)}").send()


async def analyze_uploaded_contract():
    """Analyze the uploaded contract."""
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

        result = analyze_contract(contract_text=contract_data["text"])

        analysis_result = result.get("analysis_result", "")
        
        if not analysis_result:
            analysis_result = "⚠️ Analysis completed but no report was generated. Please try again."
        
        # Stream the analysis result
        chunk_size = 50
        for i in range(0, len(analysis_result), chunk_size):
            chunk = analysis_result[i:i+chunk_size]
            await response_msg.stream_token(chunk)

        await response_msg.update()

    except Exception as e:
        response_msg.content = f"❌ **Error analyzing contract:**\n\n```\n{str(e)}\n```"
        await response_msg.update()


# ============================================================================
# Chat Handlers
# ============================================================================

@cl.on_chat_start
async def on_chat_start():
    """Handle new chat session initialization."""
    cl.user_session.set("chat_history", [])

    try:
        # Initialize LangGraph RAG system
        rag_graph = create_rag_graph()
        cl.user_session.set("rag_graph", rag_graph)

        welcome_msg = """### Welcome to Ontario Tenancy Assistant

Hi there 👋  
I'm here to help you understand your **rental rights and responsibilities** in Ontario.  
Ask me anything — like:

> "Can my landlord raise the rent?"  
> "How do I end my lease?"  
> "What form do I need to give notice?"

"""
        await cl.Message(content=welcome_msg).send()

    except Exception as e:
        error_msg = f"❌ Failed to initialize RAG system: {str(e)}\n\nPlease check your configuration and try again."
        await cl.Message(content=error_msg).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages with streaming response using LangGraph."""
    if message.elements:
        await handle_file_upload(message.elements)
        return

    chat_history = cl.user_session.get("chat_history", [])
    rag_graph = cl.user_session.get("rag_graph")

    if not rag_graph:
        await cl.Message(
            content="❌ RAG system not initialized. Please refresh the page."
        ).send()
        return

    chat_history.append({"role": "user", "content": message.content})

    response_msg = cl.Message(content="")
    await response_msg.send()

    try:
        await response_msg.stream_token("🔍 Searching through Ontario Tenancy Law documents...\n\n")

        initial_state = {
            "question": message.content,
            "context": "",
            "answer": "",
            "messages": [],
            "retrieved_docs": [],
            "needs_clarification": False,
            "chat_history": chat_history,
            "previous_context": "",
            "is_relevant": True,
            "topic": "",
            "summarized_context": "",
        }

        final_result = None
        is_off_topic = False
        answer_streamed = False

        # Stream through the graph execution and capture final state
        async for event in rag_graph.astream(initial_state):
            for node_name, node_state in event.items():
                print(f"📊 Graph node: {node_name}, has answer: {bool(node_state.get('answer'))}")
                
                # Always update final_result with latest state from ending nodes
                if node_name in ["generate", "off_topic", "clarification"]:
                    final_result = node_state
                    print(f"📌 Captured final state from {node_name}")
                
                if node_name == "classify":
                    if not node_state.get("is_relevant", True):
                        is_off_topic = True
                        await response_msg.stream_token("⚠️ Question may not be related to Ontario tenancy law...\n\n")
                
                elif node_name == "retrieve":
                    await response_msg.stream_token("✓ Retrieved relevant sections\n\n")
                
                elif node_name == "summarize":
                    await response_msg.stream_token("📝 Summarizing context...\n\n")
                
                elif node_name == "generate":
                    await response_msg.stream_token("💬 Generating answer...\n\n")
                    # Get the answer from state and stream it
                    answer = node_state.get("answer", "")
                    print(f"📝 Generated answer length: {len(answer) if answer else 0}")
                    if answer:
                        # Stream answer in chunks
                        chunk_size = 50
                        for i in range(0, len(answer), chunk_size):
                            chunk = answer[i:i+chunk_size]
                            await response_msg.stream_token(chunk)
                        answer_streamed = True
                    else:
                        print("⚠️ Warning: generate node completed but answer is empty")
                
                elif node_name == "off_topic":
                    answer = node_state.get("answer", "")
                    print(f"📝 Off-topic answer length: {len(answer) if answer else 0}")
                    if answer:
                        await response_msg.stream_token(answer)
                        answer_streamed = True
                
                elif node_name == "clarification":
                    answer = node_state.get("answer", "")
                    print(f"📝 Clarification answer length: {len(answer) if answer else 0}")
                    if answer:
                        await response_msg.stream_token(answer)
                        answer_streamed = True

        # After graph completes, add sources and metadata
        print(f"🔍 Final result check: {final_result is not None}")
        if final_result:
            needs_clarification = final_result.get("needs_clarification", False)
            is_relevant = final_result.get("is_relevant", True)
            answer = final_result.get("answer", "")
            print(f"📊 Final answer length: {len(answer) if answer else 0}, streamed: {answer_streamed}")

            if answer and not answer_streamed:
                # Stream answer if it wasn't streamed during graph execution
                print("📤 Streaming answer that wasn't streamed during execution...")
                chunk_size = 50
                for i in range(0, len(answer), chunk_size):
                    chunk = answer[i:i+chunk_size]
                    await response_msg.stream_token(chunk)
                answer_streamed = True

            if answer:
                if is_relevant and not is_off_topic:
                    if needs_clarification:
                        await response_msg.stream_token("\n\n---\n\n**💡 Need more specific information?**\n\nTry rephrasing with:\n")
                        await response_msg.stream_token("- Specific section numbers (e.g., \"Section 12\")\n")
                        await response_msg.stream_token("- More context about your situation\n")
                        await response_msg.stream_token("- Legal terms related to your question")

                    retrieved_docs = final_result.get("retrieved_docs", [])
                    if retrieved_docs and len(retrieved_docs) > 0:
                        await response_msg.stream_token("\n\n---\n\n**📚 Sources:**\n")

                        for i, doc in enumerate(retrieved_docs[:3], 1):
                            metadata = doc.metadata
                            section_info = f"Section {metadata.get('section_number', 'N/A')}"
                            if metadata.get('subsection_number'):
                                section_info += f" - Subsection {metadata.get('subsection_number')}"

                            source_text = f"\n{i}. **{section_info}** - {metadata.get('section_title', '')}"

                            url = metadata.get('url') or metadata.get('source_file')
                            if url:
                                source_text += f" [[View Source]({url})]"

                            await response_msg.stream_token(source_text)

                # Update chat history
                chat_history.append({"role": "assistant", "content": answer})
                cl.user_session.set("chat_history", chat_history)
                print(f"✓ Answer saved to chat history (length: {len(answer)})")
            else:
                print("⚠️ Warning: final_result exists but answer is empty")
                await response_msg.stream_token("\n\n⚠️ Answer was generated but is empty. Please try again.")
        else:
            print("❌ Error: No final result from graph execution")
            await response_msg.stream_token("\n\n⚠️ No response generated. Please try again.")

        await response_msg.update()

    except Exception as e:
        response_msg.content = f"❌ **Error processing your question:**\n\n```\n{str(e)}\n```\n\nPlease try rephrasing your question or check if the system is configured correctly."
        await response_msg.update()


@cl.on_chat_end
async def on_chat_end():
    """Handle chat session cleanup."""
    pass


@cl.on_chat_resume
async def on_chat_resume(thread: dict):
    """Handle chat session resume."""
    print(f"Resuming chat thread: {thread.get('id', 'unknown')}")
    pass
