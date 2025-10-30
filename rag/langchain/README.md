# LangChain RAG Components

Modular, clean LangChain-based RAG system for Ontario Tenancy Law queries.

## Architecture

```
langchain/
├── embeddings.py      # BGE-M3 wrapper for LangChain
├── vectorstore.py     # Pinecone vector store integration
├── retriever.py       # Configured retriever with filters
├── chains.py          # LCEL chains for Q&A
├── graph.py           # LangGraph workflow
└── __init__.py        # Public API
```

## Components

### 1. Embeddings (`embeddings.py`)

LangChain-compatible wrapper for BAAI/bge-m3 local embeddings.

```python
from rag.langchain import BGEEmbeddings

embeddings = BGEEmbeddings()
vectors = embeddings.embed_documents(["text1", "text2"])
query_vector = embeddings.embed_query("my question")
```

**Features:**
- 1024-dimensional embeddings
- CPU-based (no GPU required)
- Normalized vectors for cosine similarity
- Batch processing support

### 2. Vector Store (`vectorstore.py`)

Pinecone integration with LangChain.

```python
from rag.langchain import get_vectorstore

vectorstore = get_vectorstore()
results = vectorstore.similarity_search("tenant rights", k=5)
```

**Features:**
- Automatic Pinecone connection
- BGE-M3 embeddings by default
- Namespace support
- Metadata filtering

### 3. Retriever (`retriever.py`)

Configured retriever for tenancy law queries.

```python
from rag.langchain import get_retriever

# Default: Ontario jurisdiction, k=5
retriever = get_retriever()

# Custom filters
retriever = get_retriever(
    k=10,
    filter={"part_number": "I"}
)

docs = retriever.invoke("rent increase rules")
```

**Features:**
- Default Ontario jurisdiction filter
- Configurable number of results
- Metadata filtering support
- Similarity-based search

### 4. Chains (`chains.py`)

LCEL (LangChain Expression Language) chains for Q&A.

```python
from rag.langchain import get_qa_chain

# Full RAG chain with OpenAI
chain = get_qa_chain(model_name="gpt-4o-mini", k=5)
answer = chain.invoke("Can landlords increase rent?")

# Simple retrieval (no LLM)
from rag.langchain.chains import get_simple_retrieval_chain
chain = get_simple_retrieval_chain(k=5)
formatted_docs = chain.invoke("eviction rules")
```

**QA Chain Features:**
- OpenAI GPT-4o-mini for answers
- Temperature=0 for factual responses
- Automatic context formatting
- Section citation in answers

**Prompt Template:**
- Expert legal assistant persona
- Ontario RTA specialization
- Clear section citations
- Acknowledgment of limitations

### 5. LangGraph Workflow (`graph.py`)

Advanced multi-step RAG workflow with routing.

```python
from rag.langchain import create_rag_graph
from rag.langchain.graph import query_with_graph

# Simple usage
result = query_with_graph("What are tenant rights?")
print(result["answer"])

# Advanced usage
app = create_rag_graph()
state = {
    "question": "eviction process",
    "context": "",
    "answer": "",
    "messages": [],
    "retrieved_docs": [],
    "needs_clarification": False,
}
final_state = app.invoke(state)
```

**Workflow Steps:**
1. **Retrieve** - Get relevant documents from Pinecone
2. **Check Relevance** - Assess if documents are relevant
3. **Route** - Either generate answer or request clarification
4. **Generate/Clarify** - Produce final response

**State Schema:**
```python
{
    "question": str,           # User's question
    "context": str,            # Formatted retrieved docs
    "answer": str,             # Final answer
    "messages": List[Message], # Chat history
    "retrieved_docs": List,    # Raw documents
    "needs_clarification": bool # Routing flag
}
```

## Usage Examples

### Simple Retrieval (No LLM)

```python
from rag.langchain import get_retriever

retriever = get_retriever(k=3)
docs = retriever.invoke("rent increase notice period")

for doc in docs:
    print(f"Section {doc.metadata['section_number']}")
    print(doc.page_content)
```

### Q&A with GPT-4o-mini

```python
from rag.langchain import get_qa_chain

chain = get_qa_chain(
    model_name="gpt-4o-mini",
    temperature=0.0,
    k=5
)

answer = chain.invoke("What are the rules about pets in rental units?")
print(answer)
```

### LangGraph Workflow

```python
from rag.langchain.graph import query_with_graph

result = query_with_graph("Can a landlord evict without notice?")

print(f"Answer: {result['answer']}")
print(f"Retrieved: {len(result['retrieved_docs'])} documents")
print(f"Clarification needed: {result['needs_clarification']}")
```

### Interactive CLI

```bash
python langchain_query.py --interactive
```

## Configuration

All settings in `rag/config.py`:

```python
# API Keys (loaded from .env)
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Embeddings
LOCAL_MODEL_NAME = "BAAI/bge-m3"
LOCAL_MODEL_DEVICE = "cpu"
EMBEDDING_DIMENSION = 1024
NORMALIZE_EMBEDDINGS = True

# Pinecone
PINECONE_INDEX_NAME = "tenancy-law"
```

## Dependencies

```bash
uv add langchain langchain-core langchain-community
uv add langchain-pinecone langgraph langchain-openai
uv add sentence-transformers pinecone python-dotenv
```

## Benefits of This Architecture

### Modularity
- Each component has single responsibility
- Easy to swap implementations
- Clean imports and dependencies

### Flexibility
- Choose retrieval-only or full RAG
- Multiple LLM options (OpenAI, local, etc.)
- Custom filtering and routing

### Scalability
- LangGraph for complex workflows
- Stateful conversation support
- Easy to add new nodes/steps

### Cost Efficiency
- Local BGE-M3 embeddings (free)
- OpenAI only for generation
- Batch processing support

### Developer Experience
- Type hints throughout
- Clear documentation
- Simple public API
- LCEL for composability

## Extension Ideas

1. **Conversation Memory**: Add chat history tracking
2. **Multi-Query**: Generate multiple search queries
3. **Re-ranking**: Add cross-encoder for better results
4. **Streaming**: Stream LLM responses
5. **Caching**: Cache common queries
6. **Analytics**: Track query patterns
7. **Multi-Agent**: Route to specialized agents
8. **Guardrails**: Add safety checks
