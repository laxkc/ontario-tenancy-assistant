"""Chat event handlers for Chainlit."""
import chainlit as cl
from rag.langchain import create_rag_graph, analyze_contract
from .file_handlers import handle_file_upload


@cl.on_chat_start
async def on_chat_start():
    """Handle new chat session initialization."""
    cl.user_session.set("chat_history", [])

    try:
        rag_graph = create_rag_graph()
        cl.user_session.set("rag_graph", rag_graph)

        welcome_msg = """### Welcome to Ontario Tenancy Assistant

Hi there 👋  
I’m here to help you understand your **rental rights and responsibilities** in Ontario.  
Ask me anything — like:

> “Can my landlord raise the rent?”  
> “How do I end my lease?”  
> “What form do I need to give notice?”

"""
        await cl.Message(content=welcome_msg).send()

    except Exception as e:
        error_msg = f"❌ Failed to initialize RAG system: {str(e)}\n\nPlease check your configuration and try again."
        await cl.Message(content=error_msg).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages with streaming response."""
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
            "quality_score": 10.0,
            "has_citations": False,
        }

        result = None
        is_off_topic = False

        async for event in rag_graph.astream(initial_state):
            for node_name, node_state in event.items():
                if node_name == "classify":
                    if not node_state.get("is_relevant", True):
                        is_off_topic = True
                elif node_name == "off_topic":
                    result = node_state
                    response_msg.content = ""
                    await response_msg.update()
                elif node_name == "retrieve":
                    await response_msg.stream_token("✓ Retrieved relevant sections\n\n")
                    await response_msg.stream_token("💬 Generating answer...\n\n")
                elif node_name == "generate" or node_name == "clarification":
                    result = node_state
                    response_msg.content = ""
                    await response_msg.update()

        if result and result.get("answer"):
            answer = result["answer"]
            needs_clarification = result.get("needs_clarification", False)
            is_relevant = result.get("is_relevant", True)

            chunk_size = 30
            for i in range(0, len(answer), chunk_size):
                chunk = answer[i:i+chunk_size]
                await response_msg.stream_token(chunk)

            if is_relevant and not is_off_topic:
                if needs_clarification:
                    await response_msg.stream_token("\n\n---\n\n**💡 Need more specific information?**\n\nTry rephrasing with:\n")
                    await response_msg.stream_token("- Specific section numbers (e.g., \"Section 12\")\n")
                    await response_msg.stream_token("- More context about your situation\n")
                    await response_msg.stream_token("- Legal terms related to your question")

                retrieved_docs = result.get("retrieved_docs", [])
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

            chat_history.append({"role": "assistant", "content": answer})
            cl.user_session.set("chat_history", chat_history)

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
