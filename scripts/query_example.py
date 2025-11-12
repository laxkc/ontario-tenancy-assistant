"""Query the RAG system."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    LOCAL_MODEL_NAME,
    LOCAL_MODEL_DEVICE,
    NORMALIZE_EMBEDDINGS,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
)


def query_rag(question: str, top_k: int = 5):
    """Query RAG and print results."""

    print("=" * 70)
    print("🔍 RAG QUERY")
    print("=" * 70)
    print(f"\nQuestion: {question}\n")

    # Load model
    print(f"🔧 Loading {LOCAL_MODEL_NAME}...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(LOCAL_MODEL_NAME, device=LOCAL_MODEL_DEVICE)

    # Generate query embedding
    query_embedding = model.encode(
        question,
        normalize_embeddings=NORMALIZE_EMBEDDINGS
    ).tolist()

    # Connect to Pinecone
    from pinecone import Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)

    # Search
    print("🔧 Searching...")
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        filter={"jurisdiction": "Ontario"}
    )

    # Display results
    print(f"\n📊 Found {len(results.matches)} results:\n")
    print("=" * 70)

    for i, match in enumerate(results.matches, 1):
        m = match.metadata
        print(f"\n🔹 Result {i} (Score: {match.score:.4f})")
        print(f"   Section: {m.get('section_number')} - {m.get('section_title', '')[:50]}")
        if m.get('subsection_number'):
            print(f"   Subsection: {m['subsection_number']}")
        print(f"\n   {m.get('text', '')[:250]}...")
        print("-" * 70)


def main():
    """Main with example queries."""

    examples = [
        "What are the tenant's rights when evicted?",
        "Can a landlord increase rent without notice?",
        "What is the notice period for termination?",
        "Are pets allowed in rental units?",
    ]

    print("🎯 Example Questions:\n")
    for i, q in enumerate(examples, 1):
        print(f"{i}. {q}")

    print(f"\nEnter number (1-{len(examples)}) or type your question:")
    user_input = input("> ").strip()

    if user_input.isdigit() and 1 <= int(user_input) <= len(examples):
        question = examples[int(user_input) - 1]
    else:
        question = user_input

    if question:
        query_rag(question)


if __name__ == "__main__":
    main()
