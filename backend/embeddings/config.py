"""
Configuration for embeddings generation and search.
"""

from pathlib import Path


class EmbeddingConfig:
    """Configuration for embedding generation and storage."""
    
    # Model configuration
    MODEL_NAME = 'all-MiniLM-L6-v2'  # Fast, good quality, 384 dimensions
    # Alternative models:
    # 'all-mpnet-base-v2'  # Best quality, slower, 768 dimensions
    # 'paraphrase-MiniLM-L3-v2'  # Fastest, 384 dimensions
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / 'data'
    
    DATABASE_PATH = DATA_DIR / 'datasets.db'
    FAISS_INDEX_PATH = DATA_DIR / 'faiss_index.bin'
    METADATA_PATH = DATA_DIR / 'dataset_mapping.pkl'
    
    # Embedding parameters
    BATCH_SIZE = 32  # Process this many datasets at once
    NORMALIZE_EMBEDDINGS = True  # L2 normalization for cosine similarity
    
    # Search parameters
    DEFAULT_TOP_K = 10  # Return top 10 results by default
    
    # Text combination strategy
    INCLUDE_TITLE = True
    INCLUDE_ABSTRACT = True
    INCLUDE_LINEAGE = False  # Can be verbose, disable for now
    INCLUDE_KEYWORDS = False  # Already captured in abstract usually
    
    @classmethod
    def ensure_data_dir(cls):
        """Ensure data directory exists."""
        cls.DATA_DIR.mkdir(exist_ok=True)
        return cls.DATA_DIR