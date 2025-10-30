"""Generate embeddings with BAAI/bge-m3 and upsert to Pinecone."""

import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))
import config


def main():
    print("=" * 70)
    print("🚀 UPSERT TO PINECONE")
    print("=" * 70)

    # Check Pinecone API key
    if not config.PINECONE_API_KEY:
        print("\n❌ PINECONE_API_KEY not set")
        print("Set it: export PINECONE_API_KEY='your-key'")
        return 1

    # Check input file
    if not config.RAG_READY_JSON.exists():
        print(f"\n❌ File not found: {config.RAG_READY_JSON}")
        print("Run: python scripts/flatten_for_rag.py")
        return 1

    print(f"\n📄 Input: {config.RAG_READY_JSON}")
    print(f"🔹 Model: {config.LOCAL_MODEL_NAME}")
    print(f"🔹 Device: {config.LOCAL_MODEL_DEVICE}")
    print(f"🔹 Index: {config.PINECONE_INDEX_NAME}\n")

    # Load chunks
    print("🔧 Loading chunks...")
    with open(config.RAG_READY_JSON, "r", encoding="utf-8") as f:
        rag_data = json.load(f)
    chunks = rag_data["chunks"]
    print(f"✓ Loaded {len(chunks)} chunks")

    # Load BGE-M3 model
    print(f"\n🔧 Loading {config.LOCAL_MODEL_NAME}...")
    print("  (First run downloads ~2GB model)")

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(config.LOCAL_MODEL_NAME, device=config.LOCAL_MODEL_DEVICE)
    print(f"✓ Model loaded")

    # Generate embeddings
    print(f"\n🔧 Generating {len(chunks)} embeddings...")
    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(
        texts,
        normalize_embeddings=config.NORMALIZE_EMBEDDINGS,
        show_progress_bar=True,
        batch_size=32
    )
    embeddings = embeddings.tolist()
    print(f"✓ Generated embeddings (dimension: {len(embeddings[0])})")

    # Connect to Pinecone
    print(f"\n🔧 Connecting to Pinecone...")
    from pinecone import Pinecone, ServerlessSpec

    pc = Pinecone(api_key=config.PINECONE_API_KEY)

    # Create index if needed
    if config.PINECONE_INDEX_NAME not in pc.list_indexes().names():
        print(f"  Creating index: {config.PINECONE_INDEX_NAME}")
        pc.create_index(
            name=config.PINECONE_INDEX_NAME,
            dimension=len(embeddings[0]),
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        time.sleep(5)
    else:
        print(f"  Using existing index")

    index = pc.Index(config.PINECONE_INDEX_NAME)

    # Upsert vectors
    print(f"\n🔧 Upserting {len(chunks)} vectors...")
    for i in range(0, len(chunks), config.UPSERT_BATCH_SIZE):
        batch_chunks = chunks[i:i + config.UPSERT_BATCH_SIZE]
        batch_embeddings = embeddings[i:i + config.UPSERT_BATCH_SIZE]

        vectors = []
        for chunk, embedding in zip(batch_chunks, batch_embeddings):
            # Flatten metadata for Pinecone (no nested objects)
            metadata = {
                "text": chunk["text"],
                **{k: v for k, v in chunk["metadata"].items() if k != "amendment_info"}
            }

            # Convert amendment_info to string if present
            if "amendment_info" in chunk["metadata"]:
                metadata["amendment_citation"] = chunk["metadata"]["amendment_info"].get("citation", "")

            vectors.append({
                "id": chunk["id"],
                "values": embedding,
                "metadata": metadata
            })

        index.upsert(vectors=vectors)
        print(f"  Batch {i//config.UPSERT_BATCH_SIZE + 1} done")

    # Stats
    stats = index.describe_index_stats()
    print(f"\n📊 Pinecone Stats:")
    print(f"  Vectors: {stats.total_vector_count}")
    print(f"  Dimension: {stats.dimension}")

    print(f"\n✅ Complete! Run: python scripts/query_example.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
