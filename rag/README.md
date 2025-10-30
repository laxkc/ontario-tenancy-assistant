# 🤖 RAG Ingestion Pipeline

Complete pipeline for ingesting legal documents into a vector database (Pinecone) for RAG (Retrieval-Augmented Generation).

---

## 🚀 Quick Start

```bash
# 1. Set API keys
export COHERE_API_KEY="your-cohere-key"
export PINECONE_API_KEY="your-pinecone-key"

# 2. Flatten JSON to RAG format
python scripts/flatten_for_rag.py

# 3. Generate embeddings & upload to Pinecone
python scripts/upsert_to_pinecone.py

# 4. Query your RAG system
python scripts/query_example.py
```

---

## 📁 Structure

```
rag/
├── config.py                      # Configuration
├── scripts/
│   ├── flatten_for_rag.py        # Step 1: JSON → RAG chunks
│   ├── upsert_to_pinecone.py     # Step 2: Generate embeddings & upsert
│   └── query_example.py          # Step 3: Query examples
│
└── output/
    ├── rag_ready.json            # Flattened chunks
    └── embeddings.npy            # (Optional) Cached embeddings
```

---

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Embedding provider
EMBEDDING_PROVIDER = "cohere"  # or "openai"
COHERE_MODEL = "embed-english-v3.0"
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# Pinecone settings
PINECONE_INDEX_NAME = "tenancy-law"
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# Chunking strategy
CHUNK_LEVEL = "subsection"  # Each subsection = 1 chunk
MAX_TOKENS_PER_CHUNK = 800
```

---

## 📊 Data Model

### Input (from parser)
Nested JSON: Act → Parts → Sections → Subsections → Paragraphs

### Output (RAG-ready)
Flat list where each **subsection** (or section if no subsections) = **1 chunk**

### Chunk Format

```json
{
  "id": "ONT_RTA_2006_I_2_3",
  "text": "For the purposes of this Act, a tenant has not abandoned...",
  "metadata": {
    "act_name": "Residential Tenancies Act, 2006",
    "jurisdiction": "Ontario",
    "citation": "S.O. 2006, c. 17",
    "part_number": "I",
    "part_title": "INTRODUCTION",
    "section_id": "I.2",
    "section_number": "2",
    "section_title": "(1) In this Act,",
    "subsection_number": "(3)",
    "source_url": "https://www.ontario.ca/laws/statute/06r17",
    "tokens": 34,
    "chunk_type": "subsection",
    "amendment_info": {
      "year": "2006",
      "chapter": "17",
      "citation": "2006, c. 17, s. 2"
    }
  }
}
```

---

## 🔧 Step-by-Step

### Step 1: Flatten JSON

```bash
python scripts/flatten_for_rag.py
```

**What it does:**
- Loads `data/output/parsed_output_final.json`
- Converts nested structure → flat chunks
- Each subsection = 1 retrievable document
- Generates unique IDs: `ONT_RTA_2006_I_2_3`
- Saves to `output/rag_ready.json`

**Output:**
```
📊 Chunking Statistics:
   Total chunks: 638
   - Subsection chunks: 638
   - Section chunks: 0

   Total estimated tokens: 24,937
   Average tokens per chunk: 39
```

---

### Step 2: Generate Embeddings & Upsert

```bash
python scripts/upsert_to_pinecone.py
```

**What it does:**
- Loads `output/rag_ready.json`
- Generates embeddings using Cohere/OpenAI
- Creates Pinecone index (if doesn't exist)
- Upserts vectors in batches
- Includes metadata for filtering

**Output:**
```
🔧 Generating embeddings...
  Batch 1/7
  Batch 2/7
  ...

✓ Generated 638 embeddings
  Embedding dimension: 1024

🔧 Upserting 638 vectors to Pinecone...
  Batch 1/7 upserted (100 vectors)
  ...

✅ Upsert complete!
```

---

### Step 3: Query

```bash
python scripts/query_example.py
```

**Or use programmatically:**

```python
from pinecone import Pinecone
import cohere

# Initialize
pc = Pinecone(api_key="your-key")
index = pc.Index("tenancy-law")
cohere_client = cohere.Client("your-key")

# Query
question = "What are the tenant's rights when evicted?"

query_embedding = cohere_client.embed(
    texts=[question],
    model="embed-english-v3.0",
    input_type="search_query"  # Important!
).embeddings[0]

results = index.query(
    vector=query_embedding,
    top_k=5,
    include_metadata=True,
    filter={"jurisdiction": "Ontario"}
)

for match in results.matches:
    print(f"Score: {match.score}")
    print(f"Section: {match.metadata['section_number']}")
    print(f"Text: {match.metadata['text'][:200]}")
    print()
```

---

## 🔍 Metadata Filtering

Filter by any metadata field:

```python
# By jurisdiction
filter={"jurisdiction": "Ontario"}

# By part
filter={"part_number": "V"}

# By section
filter={"section_number": "47"}

# Multiple filters
filter={
    "jurisdiction": "Ontario",
    "part_number": "V",
    "chunk_type": "subsection"
}
```

---

## 📦 Dependencies

```bash
pip install pinecone-client cohere openai
```

Or add to requirements.txt:
```
pinecone-client>=3.0.0
cohere>=4.0.0
openai>=1.0.0
```

---

## 💡 Best Practices

### Chunking Strategy
- **Subsection level**: Best for precise legal retrieval
- **Section level**: Better for broader context
- **Hybrid**: Mix both based on content length

### Embedding Model
- **Cohere embed-english-v3.0**: Optimized for retrieval (1024 dim)
- **OpenAI text-embedding-3-large**: Higher quality (3072 dim)

### Metadata
- Include all relevant context (part, section, subsection)
- Add amendment info for version tracking
- Include source URLs for citations

### Filtering
- Pre-filter by jurisdiction/act before vector search
- Use metadata for post-retrieval ranking
- Combine with lexical search for better results

---

## 📊 Statistics

**Ontario Residential Tenancies Act, 2006:**
- **Total chunks**: 638
- **Average tokens/chunk**: 39
- **Embedding dimension**: 1024 (Cohere)
- **Index size**: ~2.5 MB (vectors only)

---

## 🎯 Use Cases

1. **Legal Q&A Chatbot**
   - Query RAG → Get relevant sections
   - Pass to LLM for answer generation

2. **Citation Lookup**
   - Search by section number
   - Return exact legal text

3. **Semantic Legal Search**
   - Natural language queries
   - Find relevant laws without keywords

4. **Compliance Checking**
   - Check if action complies with law
   - Retrieve applicable sections

---

## 🐛 Troubleshooting

**Pinecone index already exists?**
```python
# Delete and recreate
pc.delete_index("tenancy-law")
```

**Embedding rate limits?**
- Cohere: 10,000 embeds/minute
- Adjust `EMBEDDING_BATCH_SIZE` in config

**Out of memory?**
- Process in smaller batches
- Use streaming for large documents

**Wrong results?**
- Check `input_type` for Cohere (use "search_query" for queries)
- Try different `top_k` values
- Adjust metadata filters

---

## 🔐 Security

```bash
# Never commit API keys!
# Use environment variables
export COHERE_API_KEY="sk-..."
export PINECONE_API_KEY="..."

# Or use .env file
echo "COHERE_API_KEY=sk-..." >> .env
echo "PINECONE_API_KEY=..." >> .env
```

---

Generated with ❤️ by Claude Code
