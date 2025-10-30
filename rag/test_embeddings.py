"""Quick test of local embeddings."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import config

print("Testing local embeddings with BAAI/bge-m3...")
print(f"Model: {config.LOCAL_MODEL_NAME}")
print(f"Device: {config.LOCAL_MODEL_DEVICE}\n")

try:
    from sentence_transformers import SentenceTransformer
    
    print("Loading model (first run will download)...")
    model = SentenceTransformer(config.LOCAL_MODEL_NAME, device=config.LOCAL_MODEL_DEVICE)
    print("✓ Model loaded\n")
    
    # Test embedding
    test_texts = [
        "What are the tenant's rights?",
        "Can a landlord increase rent?"
    ]
    
    print(f"Generating embeddings for {len(test_texts)} texts...")
    embeddings = model.encode(
        test_texts,
        normalize_embeddings=config.NORMALIZE_EMBEDDINGS,
        show_progress_bar=False
    )
    
    print(f"✓ Generated embeddings")
    print(f"  Shape: {embeddings.shape}")
    print(f"  Dimension: {embeddings.shape[1]}")
    print(f"  Normalized: {config.NORMALIZE_EMBEDDINGS}")
    print(f"\n✅ Test passed! Ready to use for RAG.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"\nMake sure you have installed:")
    print(f"  uv add torch sentence-transformers")
