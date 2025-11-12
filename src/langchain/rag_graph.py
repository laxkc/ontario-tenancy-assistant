"""LangGraph workflow for advanced RAG with routing and multi-step processing."""

import sys
from pathlib import Path

# Add root directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from src.core.retriever import get_retriever
from src.core.llm import get_llm
from src.langchain.chains import format_docs


class RAGState(TypedDict):
    """State for the RAG graph."""
    question: str
    context: str
    answer: str
    messages: Annotated[Sequence[BaseMessage], "Chat history"]
    retrieved_docs: list
    needs_clarification: bool
    chat_history: list
    previous_context: str
    is_relevant: bool
    topic: str
    summarized_context: str


def classify_question(state: RAGState) -> RAGState:
    """Classify if the question is relevant to Ontario tenancy law."""
    question = state["question"]

    print("🔍 Classifying question relevance...")

    llm = get_llm()

    prompt = f"""You are a question classifier for an Ontario tenancy law assistant.

Determine if the following question is related to:
- Ontario rental/tenancy law
- Residential Tenancies Act (RTA) 2006
- Landlord-tenant relationships in Ontario
- Housing rights in Ontario
- Lease agreements in Ontario
- Rent, evictions, maintenance, deposits, etc. in Ontario

Question: "{question}"

Respond with ONLY:
- "RELEVANT" if the question is about Ontario tenancy/rental law
- "IRRELEVANT" if the question is about anything else (weather, sports, general chat, other provinces, other countries, non-housing topics, etc.)

Your response:"""

    response = llm.invoke(prompt)
    
    # Extract content from response
    if hasattr(response, 'content'):
        classification = response.content.strip().upper()
    elif isinstance(response, str):
        classification = response.strip().upper()
    else:
        classification = str(response).strip().upper()

    if "RELEVANT" in classification:
        state["is_relevant"] = True
        state["topic"] = "ontario_tenancy_law"
        print("✓ Question is relevant to Ontario tenancy law")
    else:
        state["is_relevant"] = False
        state["topic"] = "off_topic"
        print("⚠ Question is not relevant to Ontario tenancy law")

    return state


def retrieve_documents(state: RAGState) -> RAGState:
    """Retrieve relevant documents from vector store with metadata filtering."""
    question = state["question"]
    chat_history = state.get("chat_history", [])

    print(f"🔍 Retrieving documents for: {question}")

    metadata_filter = {"jurisdiction": "Ontario"}
    retriever = get_retriever(k=7, filter=metadata_filter)

    enhanced_query = question
    if chat_history:
        last_messages = chat_history[-3:]
        history_context = "\n".join([
            f"{msg['role']}: {msg['content'][:100]}"
            for msg in last_messages
        ])
        enhanced_query = f"Given this conversation:\n{history_context}\n\nCurrent question: {question}"

    docs = retriever.invoke(enhanced_query)

    seen_sections = set()
    unique_docs = []
    for doc in docs:
        section_key = (
            doc.metadata.get("section_number"),
            doc.metadata.get("subsection_number")
        )
        if section_key not in seen_sections:
            seen_sections.add(section_key)
            unique_docs.append(doc)

    state["retrieved_docs"] = unique_docs
    state["context"] = format_docs(unique_docs)

    print(f"✓ Retrieved {len(unique_docs)} unique documents")

    return state


def summarize_context(state: RAGState) -> RAGState:
    """Summarize retrieved context for cleaner, shorter input."""
    context = state["context"]
    retrieved_docs = state["retrieved_docs"]

    if not retrieved_docs:
        state["summarized_context"] = ""
        return state

    print("📝 Summarizing context...")

    llm = get_llm()

    prompt = f"""Summarize the following legal sections from the Ontario Residential Tenancies Act.
Focus on key points, requirements, and conditions. Keep citations intact.

Legal Context:
{context[:2000]}

Provide a concise summary maintaining all section numbers and key legal points."""

    response = llm.invoke(prompt)
    
    # Extract content from response
    if hasattr(response, 'content'):
        state["summarized_context"] = response.content
    elif isinstance(response, str):
        state["summarized_context"] = response
    else:
        state["summarized_context"] = str(response)

    print("✓ Context summarized")

    return state


def check_relevance(state: RAGState) -> RAGState:
    """Check if retrieved documents are relevant to the question."""
    if len(state.get("retrieved_docs", [])) > 0:
        state["needs_clarification"] = False
    else:
        state["needs_clarification"] = True

    return state


def generate_answer(state: RAGState) -> RAGState:
    """Generate answer using LLM with legal reasoning structure."""
    question = state["question"]
    summarized_context = state.get("summarized_context", state["context"])
    chat_history = state.get("chat_history", [])

    print("💬 Generating answer with legal reasoning...")

    llm = get_llm(temperature=0.1)

    history_text = ""
    if chat_history:
        recent_history = chat_history[-4:]
        history_text = "\n\nConversation History:\n"
        for msg in recent_history:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content'][:150]}...\n"

    prompt = f"""You are a compassionate legal assistant specializing in Ontario tenancy law (Residential Tenancies Act, 2006).

Your response structure:
1. **Direct Answer**: State the answer clearly and empathetically
2. **Legal Basis**: Cite specific RTA sections (e.g., "Section 120(1)")
3. **Practical Implications**: Explain what this means in practice
4. **Important Notes**: Highlight key conditions or exceptions

Guidelines:
- Use empathetic, human language (not robotic)
- Always cite section numbers
- Acknowledge the user's situation
- Be precise but accessible{history_text}

Legal Context:
{summarized_context}

Question: {question}

Your Response:"""

    response = llm.invoke(prompt)
    
    # Extract content from response (handles both string and message types)
    if hasattr(response, 'content'):
        answer_content = response.content
    elif isinstance(response, str):
        answer_content = response
    else:
        answer_content = str(response)

    state["answer"] = answer_content
    state["messages"] = [
        HumanMessage(content=question),
        AIMessage(content=answer_content)
    ]

    print(f"✓ Answer generated with legal reasoning and empathy (length: {len(answer_content)})")

    return state


def handle_off_topic(state: RAGState) -> RAGState:
    """Handle questions that are not related to Ontario tenancy law."""
    question = state["question"]

    answer = """I'm specialized in **Ontario tenancy law** and the **Residential Tenancies Act, 2006**. I can only help with questions about:

🏠 **Rental & Housing in Ontario:**
- Landlord-tenant rights and responsibilities
- Rent increases, deposits, and payments
- Lease agreements and terminations
- Evictions and disputes
- Maintenance and repairs
- Specific sections of the RTA 2006

**Please ask a question related to Ontario rental/tenancy law**, and I'll be happy to help!

Examples:
- "Can my landlord increase rent without notice?"
- "What are the rules for security deposits in Ontario?"
- "How much notice is required to terminate a lease?"
"""

    state["answer"] = answer
    state["messages"] = [
        HumanMessage(content=question),
        AIMessage(content=answer)
    ]

    return state


def request_clarification(state: RAGState) -> RAGState:
    """Request clarification when no relevant documents found."""
    question = state["question"]

    answer = f"""I couldn't find specific information in the Ontario Residential Tenancies Act, 2006 directly related to your question: "{question}"

Could you please:
1. Rephrase your question with more specific legal terms
2. Provide more context about your situation
3. Ask about a specific section or aspect of tenancy law

For example, instead of "What are my rights?", you could ask "What are a tenant's rights regarding rent increases?"
"""

    state["answer"] = answer
    state["messages"] = [
        HumanMessage(content=question),
        AIMessage(content=answer)
    ]

    return state


def route_after_classification(state: RAGState) -> str:
    """Route based on question relevance."""
    if not state.get("is_relevant", True):
        return "off_topic"
    return "retrieve"


def route_after_retrieval(state: RAGState) -> str:
    """Route based on whether clarification is needed."""
    if state.get("needs_clarification", False):
        return "clarification"
    return "summarize"


def create_rag_graph():
    """Create the enhanced RAG workflow graph with routing.

    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(RAGState)

    workflow.add_node("classify", classify_question)
    workflow.add_node("off_topic", handle_off_topic)
    workflow.add_node("retrieve", retrieve_documents)
    workflow.add_node("check_relevance", check_relevance)
    workflow.add_node("summarize", summarize_context)
    workflow.add_node("generate", generate_answer)
    workflow.add_node("clarification", request_clarification)

    workflow.set_entry_point("classify")

    workflow.add_conditional_edges(
        "classify",
        route_after_classification,
        {
            "off_topic": "off_topic",
            "retrieve": "retrieve",
        }
    )

    workflow.add_edge("off_topic", END)
    workflow.add_edge("retrieve", "check_relevance")

    workflow.add_conditional_edges(
        "check_relevance",
        route_after_retrieval,
        {
            "summarize": "summarize",
            "clarification": "clarification",
        }
    )

    workflow.add_edge("summarize", "generate")
    workflow.add_edge("generate", END)
    workflow.add_edge("clarification", END)

    app = workflow.compile()

    print("✓ Enhanced RAG graph compiled")

    return app


def query_with_graph(question: str, chat_history: list = None) -> dict:
    """Query using the LangGraph workflow.

    Args:
        question: User's question
        chat_history: Optional conversation history for context

    Returns:
        Final state with answer
    """
    print("=" * 70)
    print("🔍 RAG GRAPH QUERY")
    print("=" * 70)
    print(f"\nQuestion: {question}")
    if chat_history:
        print(f"With {len(chat_history)} previous messages\n")
    else:
        print()

    app = create_rag_graph()

    initial_state = {
        "question": question,
        "context": "",
        "answer": "",
        "messages": [],
        "retrieved_docs": [],
        "needs_clarification": False,
        "chat_history": chat_history or [],
        "previous_context": "",
        "is_relevant": True,
        "topic": "",
        "summarized_context": "",
    }

    result = app.invoke(initial_state)

    print("\n" + "=" * 70)
    print("💡 ANSWER")
    print("=" * 70)
    print(result["answer"])
    print("\n")

    return result

