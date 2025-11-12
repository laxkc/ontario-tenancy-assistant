"""Pinecone vector store integration with LangChain."""

from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

import sys
from pathlib import Path

# Add root directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import PINECONE_API_KEY, PINECONE_INDEX_NAME
from .embeddings import BGEEmbeddings


def get_vectorstore(
    index_name: str = None,
    embeddings: BGEEmbeddings = None,
    namespace: str = "",
) -> PineconeVectorStore:
    """Get LangChain Pinecone vector store.

    Args:
        index_name: Pinecone index name (default: from config)
        embeddings: Embeddings model (default: BGEEmbeddings)
        namespace: Pinecone namespace (default: "")

    Returns:
        PineconeVectorStore instance
    """
    index_name = index_name or PINECONE_INDEX_NAME

    if embeddings is None:
        embeddings = BGEEmbeddings()

    print(f"🔧 Connecting to Pinecone index: {index_name}")

    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(index_name)

    # Create vector store
    vectorstore = PineconeVectorStore(
        index=index,
        embedding=embeddings,
        text_key="text",
        namespace=namespace,
    )

    return vectorstore
