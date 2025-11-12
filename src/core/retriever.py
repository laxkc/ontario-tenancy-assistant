"""Retriever configuration for RAG."""

from langchain_core.retrievers import BaseRetriever
from .vectorstore import get_vectorstore


def get_retriever(
    k: int = 5,
    filter: dict = None,
    search_kwargs: dict = None,
) -> BaseRetriever:
    """Get configured retriever for tenancy law queries.

    Args:
        k: Number of documents to retrieve (default: 5)
        filter: Metadata filter (default: {"jurisdiction": "Ontario"})
        search_kwargs: Additional search parameters

    Returns:
        Configured retriever
    """
    vectorstore = get_vectorstore()

    # Default filter for Ontario jurisdiction
    if filter is None:
        filter = {"jurisdiction": "Ontario"}

    # Build search kwargs
    if search_kwargs is None:
        search_kwargs = {}

    search_kwargs["k"] = k
    if filter:
        search_kwargs["filter"] = filter

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs,
    )

    print(f"✓ Retriever configured (k={k}, filter={filter})")

    return retriever
