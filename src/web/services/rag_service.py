"""RAG service for handling tenancy law queries."""
from typing import Dict, Any, Optional
from rag.langchain import create_rag_graph


class RAGService:
    """Service for RAG-based query answering."""

    def __init__(self):
        """Initialize the RAG service."""
        self.graph = None

    def initialize(self) -> None:
        """Initialize the RAG graph."""
        if self.graph is None:
            print("🔧 Initializing RAG graph...")
            self.graph = create_rag_graph()
            print("✓ RAG graph initialized")

    def query(self, question: str) -> Dict[str, Any]:
        """Query the RAG system.

        Args:
            question: User's question

        Returns:
            Dictionary containing answer and metadata
        """
        if self.graph is None:
            raise RuntimeError("RAG service not initialized. Call initialize() first.")

        # Prepare initial state
        initial_state = {
            "question": question,
            "context": "",
            "answer": "",
            "messages": [],
            "retrieved_docs": [],
            "needs_clarification": False,
        }

        # Run the graph
        result = self.graph.invoke(initial_state)

        # Format response
        return {
            "answer": result["answer"],
            "sources": self._format_sources(result.get("retrieved_docs", [])),
            "needs_clarification": result.get("needs_clarification", False),
            "num_sources": len(result.get("retrieved_docs", [])),
        }

    def _format_sources(self, docs: list) -> list:
        """Format source documents.

        Args:
            docs: Retrieved documents

        Returns:
            List of formatted source dictionaries
        """
        sources = []
        for doc in docs[:5]:  # Top 5 sources
            metadata = doc.metadata
            section_info = f"Section {metadata.get('section_number', 'N/A')}"
            if metadata.get('subsection_number'):
                section_info += f" - Subsection {metadata.get('subsection_number')}"

            sources.append({
                "section": section_info,
                "title": metadata.get('section_title', ''),
                "content_preview": doc.page_content[:200] + "...",
                "full_content": doc.page_content,
            })

        return sources


# Singleton instance
_rag_service_instance: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the RAG service singleton.

    Returns:
        RAGService instance
    """
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = RAGService()
    return _rag_service_instance
