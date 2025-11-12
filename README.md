# AI Agent for Tenancies

An intelligent assistant for Ontario residential tenancy law, powered by RAG (Retrieval-Augmented Generation) and LangChain. This application helps users understand their rights and responsibilities under the Residential Tenancies Act, 2006, and can analyze rental contracts for compliance.

## Features

- **Question Answering**: Ask questions about Ontario tenancy law and get accurate answers based on the Residential Tenancies Act, 2006
- **Contract Analysis**: Upload rental agreements (PDF or DOCX) for automated compliance analysis
- **RAG System**: Uses vector embeddings and retrieval to provide contextually relevant legal information
- **Interactive Chat Interface**: Chainlit-based web interface for natural conversation
- **REST API**: FastAPI backend for programmatic access

## Requirements

- Python 3.13+
- API Keys:
  - Google Gemini API key (for LLM)
  - Pinecone API key (for vector database)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agent
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
uv pip install -r pyproject.toml
```

Or using uv:
```bash
uv sync
```

## Configuration

1. Create a `.env` file in the root directory:
```env
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here

# Optional Configuration
LLM_MODEL_NAME=gemini-2.5-flash
LLM_TEMPERATURE=0.0
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=*
```

2. Configure Pinecone index name in `config.py` if different from default:
```python
PINECONE_INDEX_NAME = "tenancy-law"
```

## Running the Application

Start the application:
```bash
python main.py
```

The application will be available at:
- FastAPI: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Chainlit Chat Interface: http://localhost:8000/chainlit

## Usage

### Chat Interface

1. Navigate to http://localhost:8000/chainlit
2. Ask questions about Ontario tenancy law, such as:
   - "Can my landlord raise the rent?"
   - "How do I end my lease?"
   - "What are my rights regarding maintenance?"

### Contract Analysis

1. Upload a rental agreement (PDF or DOCX) through the chat interface
2. The system will analyze the contract for compliance with Ontario law
3. Review the analysis report with identified issues and recommendations

### API Endpoints

- `GET /api/health` - Health check
- `GET /api/` - API information
- `POST /api/query` - Query the RAG system programmatically

## Project Structure

```
agent/
├── config.py              # Main configuration
├── main.py                # Application entry point
├── src/
│   ├── core/              # Core RAG functionality
│   │   ├── embeddings.py  # BGE-M3 embeddings
│   │   ├── llm.py         # LLM factory (Gemini)
│   │   ├── qa.py          # Question answering
│   │   ├── retriever.py   # Document retrieval
│   │   └── vectorstore.py # Pinecone integration
│   ├── langchain/         # LangChain/LangGraph workflows
│   │   ├── chains.py      # RAG chains
│   │   ├── contract_graph.py  # Contract analysis workflow
│   │   └── rag_graph.py   # RAG question answering workflow
│   └── web/               # Web interface
│       ├── app.py         # Chainlit app entry point
│       ├── api_routes.py  # FastAPI routes
│       └── chainlit_handlers.py  # Chat and file handlers
├── data/                  # Document parsing
├── scripts/               # Utility scripts
└── docs/                  # Documentation files
```

## Development

### Adding Documents to Vector Store

1. Parse documents using the data parsing pipeline:
```bash
python data/parse_document.py
```

2. Flatten parsed data for RAG:
```bash
python scripts/flatten_for_rag.py
```

3. Upload to Pinecone:
```bash
python scripts/upsert_to_pinecone.py
```

## Technology Stack

- **LLM**: Google Gemini (via langchain-google-genai)
- **Vector Database**: Pinecone
- **Embeddings**: BGE-M3 (sentence-transformers)
- **Framework**: LangChain, LangGraph
- **Web Framework**: FastAPI
- **Chat Interface**: Chainlit
- **Document Processing**: PyPDF2, python-docx, unstructured
# laxkc-ontario-tenancy-assistant
