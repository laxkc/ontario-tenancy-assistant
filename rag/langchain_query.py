#!/usr/bin/env python3
"""
LangChain-based RAG Query Interface

This script demonstrates different ways to query the Ontario Residential Tenancies Act
using LangChain components:

1. Simple Retrieval - Get relevant sections without LLM generation
2. QA Chain - Get LLM-generated answers with context
3. LangGraph Workflow - Advanced multi-step processing with routing

Usage:
    python langchain_query.py
"""

from langchain.chains import get_qa_chain
from langchain.retriever import get_retriever
from langchain.graph import query_with_graph


def simple_retrieval_demo():
    """Demo: Simple document retrieval without LLM."""
    print("\n" + "=" * 70)
    print("1️⃣  SIMPLE RETRIEVAL (No LLM)")
    print("=" * 70)

    question = "What are the rules about rent increases?"

    print(f"\n🔍 Searching for: {question}\n")

    # Get retriever
    retriever = get_retriever(k=3)

    # Retrieve documents
    docs = retriever.invoke(question)

    print(f"📊 Found {len(docs)} relevant sections:\n")

    for i, doc in enumerate(docs, 1):
        metadata = doc.metadata
        section_info = f"Section {metadata.get('section_number', 'N/A')}"
        if metadata.get('subsection_number'):
            section_info += f" - Subsection {metadata.get('subsection_number')}"

        print(f"[{i}] {section_info}")
        print(f"    {metadata.get('section_title', '')}")
        print(f"    {doc.page_content[:200]}...")
        print()


def qa_chain_demo():
    """Demo: Question-answering with LLM generation."""
    print("\n" + "=" * 70)
    print("2️⃣  QA CHAIN (Retrieval + LLM)")
    print("=" * 70)

    question = "Can a landlord increase rent without giving notice?"

    print(f"\n❓ Question: {question}\n")

    # Get QA chain
    chain = get_qa_chain(model_name="gpt-4o-mini", k=5)

    # Generate answer
    print("💬 Generating answer...\n")
    answer = chain.invoke(question)

    print("=" * 70)
    print("💡 ANSWER")
    print("=" * 70)
    print(answer)
    print()


def langgraph_demo():
    """Demo: LangGraph workflow with advanced routing."""
    print("\n" + "=" * 70)
    print("3️⃣  LANGGRAPH WORKFLOW (Advanced)")
    print("=" * 70)

    question = "What happens if a tenant doesn't pay rent?"

    # Use LangGraph workflow
    result = query_with_graph(question)

    # Show additional info
    print(f"📊 Retrieved Documents: {len(result['retrieved_docs'])}")
    print(f"🔧 Needed Clarification: {result['needs_clarification']}")


def interactive_mode():
    """Interactive query mode."""
    print("\n" + "=" * 70)
    print("🎯 INTERACTIVE MODE")
    print("=" * 70)
    print("\nChoose query method:")
    print("  1. Simple Retrieval (no LLM)")
    print("  2. QA Chain (with GPT-4o-mini)")
    print("  3. LangGraph Workflow")
    print("  4. Exit")

    while True:
        print("\n" + "-" * 70)
        choice = input("\nSelect mode (1-4): ").strip()

        if choice == "4":
            print("👋 Goodbye!")
            break

        question = input("Your question: ").strip()

        if not question:
            print("❌ Please enter a question")
            continue

        try:
            if choice == "1":
                # Simple retrieval
                retriever = get_retriever(k=5)
                docs = retriever.invoke(question)

                print(f"\n📊 Found {len(docs)} results:\n")
                for i, doc in enumerate(docs, 1):
                    meta = doc.metadata
                    section = f"Section {meta.get('section_number', 'N/A')}"
                    if meta.get('subsection_number'):
                        section += f" - Subsection {meta.get('subsection_number')}"

                    print(f"[{i}] {section}")
                    print(f"    {doc.page_content[:300]}...")
                    print()

            elif choice == "2":
                # QA Chain
                chain = get_qa_chain(model_name="gpt-4o-mini", k=5)
                answer = chain.invoke(question)

                print("\n💡 ANSWER")
                print("=" * 70)
                print(answer)

            elif choice == "3":
                # LangGraph
                result = query_with_graph(question)
                print(f"\n📊 Retrieved: {len(result['retrieved_docs'])} docs")

            else:
                print("❌ Invalid choice. Please select 1-4.")

        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("🏠 ONTARIO TENANCY LAW - RAG QUERY SYSTEM")
    print("=" * 70)
    print("\nPowered by:")
    print("  • LangChain - Modular RAG components")
    print("  • LangGraph - Advanced workflows")
    print("  • BGE-M3 - Local embeddings (1024-dim)")
    print("  • OpenAI GPT-4o-mini - Answer generation")
    print("  • Pinecone - Vector database")
    print("\nData: Ontario Residential Tenancies Act, 2006")

    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        # Run all demos
        print("\n📚 Running demonstrations...\n")

        simple_retrieval_demo()
        input("\nPress Enter to continue to QA Chain demo...")

        qa_chain_demo()
        input("\nPress Enter to continue to LangGraph demo...")

        langgraph_demo()

        print("\n" + "=" * 70)
        print("✅ DEMOS COMPLETE")
        print("=" * 70)
        print("\nTo run interactive mode:")
        print("  python langchain_query.py --interactive")
        print()


if __name__ == "__main__":
    main()
