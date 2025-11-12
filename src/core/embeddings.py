"""Custom BGE-M3 embeddings wrapper for LangChain."""

from typing import List
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

import sys
from pathlib import Path

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    LOCAL_MODEL_NAME,
    LOCAL_MODEL_DEVICE,
    NORMALIZE_EMBEDDINGS,
)


class BGEEmbeddings(Embeddings):
    """LangChain-compatible wrapper for BAAI/bge-m3 embeddings."""

    def __init__(
        self,
        model_name: str = None,
        device: str = None,
        normalize: bool = True,
    ):
        """Initialize BGE-M3 model.

        Args:
            model_name: Model name (default: from config)
            device: Device to use (default: from config)
            normalize: Whether to normalize embeddings (default: True)
        """
        self.model_name = model_name or LOCAL_MODEL_NAME
        self.device = device or LOCAL_MODEL_DEVICE
        self.normalize = normalize

        print(f"🔧 Loading {self.model_name} on {self.device}...")
        self.model = SentenceTransformer(self.model_name, device=self.device)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents.

        Args:
            texts: List of text documents to embed

        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=self.normalize,
            show_progress_bar=False,
            batch_size=32,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text.

        Args:
            text: Query text to embed

        Returns:
            Embedding as list of floats
        """
        embedding = self.model.encode(
            [text],
            normalize_embeddings=self.normalize,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return embedding[0].tolist()
