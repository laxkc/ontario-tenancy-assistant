"""LangGraph workflow for advanced RAG with routing and multi-step processing."""

from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
import sys
from pathlib import Path

# Add parent directory to path for config import
sys.path.append(str(Path(__file__).parent.parent))
import config
from .retriever import get_retriever
from .chains import format_docs


class RAGState(TypedDict):
    """State for the RAG graph."""
    question: str
    context: str
    answer: str
    messages: Annotated[Sequence[BaseMessage], "Chat history"]
    retrieved_docs: list
    needs_clarification: bool


def retrieve_documents(state: RAGState) -> RAGState:
    """Retrieve relevant documents from vector store."""
    question = state["question"]

    print(f"🔍 Retrieving documents for: {question}")

    # Get retriever
    retriever = get_retriever(k=5)

    # Retrieve documents
    docs = retriever.invoke(question)

    state["retrieved_docs"] = docs
    state["context"] = format_docs(docs)

    print(f"✓ Retrieved {len(docs)} documents")

    return state


def check_relevance(state: RAGState) -> RAGState:
    """Check if retrieved documents are relevant to the question."""
    # Simple heuristic: if we have documents, they're relevant
    # In a more advanced system, you could use LLM to judge relevance
    if len(state.get("retrieved_docs", [])) > 0:
        state["needs_clarification"] = False
    else:
        state["needs_clarification"] = True

    return state


def generate_answer(state: RAGState) -> RAGState:
    """Generate answer using LLM."""
    question = state["question"]
    context = state["context"]

    print("💬 Generating answer...")

    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
        api_key=config.OPENAI_API_KEY,
    )

    # Create prompt
    prompt = f"""You are an expert legal assistant specializing in Ontario tenancy law, specifically the Residential Tenancies Act, 2006.

Use the following context from the Act to answer the question. Be precise, cite specific sections when relevant, and explain the legal implications clearly.

Context from the Residential Tenancies Act:
{context}

Question: {question}

Answer:"""

    # Generate response
    response = llm.invoke(prompt)

    state["answer"] = response.content
    state["messages"] = [
        HumanMessage(content=question),
        AIMessage(content=response.content)
    ]

    print("✓ Answer generated")

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


def route_after_retrieval(state: RAGState) -> str:
    """Route based on whether clarification is needed."""
    if state.get("needs_clarification", False):
        return "clarification"
    return "generate"


def create_rag_graph():
    """Create the RAG workflow graph.

    Returns:
        Compiled LangGraph workflow
    """
    # Create graph
    workflow = StateGraph(RAGState)

    # Add nodes
    workflow.add_node("retrieve", retrieve_documents)
    workflow.add_node("check_relevance", check_relevance)
    workflow.add_node("generate", generate_answer)
    workflow.add_node("clarification", request_clarification)

    # Add edges
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "check_relevance")

    # Conditional routing after relevance check
    workflow.add_conditional_edges(
        "check_relevance",
        route_after_retrieval,
        {
            "generate": "generate",
            "clarification": "clarification",
        }
    )

    # Both paths end
    workflow.add_edge("generate", END)
    workflow.add_edge("clarification", END)

    # Compile
    app = workflow.compile()

    print("✓ RAG graph compiled")

    return app


def query_with_graph(question: str) -> dict:
    """Query using the LangGraph workflow.

    Args:
        question: User's question

    Returns:
        Final state with answer
    """
    print("=" * 70)
    print("🔍 RAG GRAPH QUERY")
    print("=" * 70)
    print(f"\nQuestion: {question}\n")

    # Create graph
    app = create_rag_graph()

    # Run graph
    initial_state = {
        "question": question,
        "context": "",
        "answer": "",
        "messages": [],
        "retrieved_docs": [],
        "needs_clarification": False,
    }

    result = app.invoke(initial_state)

    print("\n" + "=" * 70)
    print("💡 ANSWER")
    print("=" * 70)
    print(result["answer"])
    print("\n")

    return result
