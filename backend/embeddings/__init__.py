"""
Embeddings module for semantic search.

This module provides functionality for:
- Generating vector embeddings from dataset metadata
- Storing embeddings in a vector database (FAISS)
- Performing semantic similarity search
"""

from .generator import EmbeddingGenerator
from .search import SemanticSearch
from .config import EmbeddingConfig

__all__ = ['EmbeddingGenerator', 'SemanticSearch', 'EmbeddingConfig']