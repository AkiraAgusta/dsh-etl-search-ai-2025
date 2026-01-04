"""
Semantic search functionality using FAISS vector index.
"""

import sqlite3
import numpy as np
import faiss
import pickle
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from loguru import logger

from .config import EmbeddingConfig


class SemanticSearch:
    """Semantic search using vector embeddings."""
    
    def __init__(self, config: EmbeddingConfig = None):
        """
        Initialize semantic search.
        
        Args:
            config: Configuration object (uses default if None)
        """
        self.config = config or EmbeddingConfig()
        self.model = None
        self.index = None
        self.metadata = None
        self.conn = None
    
    def load_model(self):
        """Load the sentence transformer model."""
        if self.model is None:
            logger.info(f"Loading embedding model: {self.config.MODEL_NAME}")
            self.model = SentenceTransformer(self.config.MODEL_NAME)
        return self.model
    
    def load_index(self):
        """Load FAISS index from disk."""
        if self.index is None:
            if not self.config.FAISS_INDEX_PATH.exists():
                raise FileNotFoundError(
                    f"FAISS index not found at {self.config.FAISS_INDEX_PATH}. "
                    "Please run generate_embeddings.py first."
                )
            
            logger.info(f"Loading FAISS index from: {self.config.FAISS_INDEX_PATH}")
            self.index = faiss.read_index(str(self.config.FAISS_INDEX_PATH))
            logger.info(f"Loaded index with {self.index.ntotal} vectors")
        return self.index
    
    def load_metadata(self):
        """Load dataset metadata from disk."""
        if self.metadata is None:
            if not self.config.METADATA_PATH.exists():
                raise FileNotFoundError(
                    f"Metadata not found at {self.config.METADATA_PATH}. "
                    "Please run generate_embeddings.py first."
                )
            
            logger.info(f"Loading metadata from: {self.config.METADATA_PATH}")
            with open(self.config.METADATA_PATH, 'rb') as f:
                self.metadata = pickle.load(f)
            logger.info(f"Loaded metadata for {len(self.metadata['dataset_ids'])} datasets")
        return self.metadata
    
    def connect_database(self):
        """Connect to SQLite database."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.config.DATABASE_PATH)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def encode_query(self, query: str) -> np.ndarray:
        """
        Encode query text to embedding vector.
        
        Args:
            query: Search query text
            
        Returns:
            Embedding vector as numpy array
        """
        model = self.load_model()
        embedding = model.encode(
            [query],
            normalize_embeddings=self.config.NORMALIZE_EMBEDDINGS,
            show_progress_bar=False
        )[0]
        return embedding.astype('float32')
    
    def search(
        self,
        query: str,
        top_k: int = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar datasets using semantic similarity.
        
        Args:
            query: Search query text
            top_k: Number of results to return (default from config)
            filters: Optional filters (e.g., date range, spatial extent)
            
        Returns:
            List of search results with metadata and scores
        """
        top_k = top_k or self.config.DEFAULT_TOP_K
        
        # Load index and metadata
        index = self.load_index()
        metadata = self.load_metadata()
        
        # Encode query
        query_vector = self.encode_query(query).reshape(1, -1)
        
        # Search FAISS index
        # For normalized vectors with IndexFlatIP, higher scores = more similar
        # For IndexFlatL2, lower distances = more similar
        distances, indices = index.search(query_vector, top_k)
        
        # Prepare results
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0]), 1):
            # Get basic metadata
            dataset_id = metadata['dataset_ids'][idx]
            dataset_metadata = metadata['metadata'][idx]
            
            # Calculate similarity score (0-1, higher = more similar)
            if self.config.NORMALIZE_EMBEDDINGS:
                # For IndexFlatIP with normalized vectors: score is cosine similarity
                similarity = float(distance)
            else:
                # For IndexFlatL2: convert distance to similarity
                similarity = 1 / (1 + float(distance))
            
            result = {
                'rank': i,
                'dataset_id': dataset_id,
                'file_identifier': dataset_metadata['file_identifier'],
                'title': dataset_metadata['title'],
                'abstract': dataset_metadata['abstract'],
                'similarity_score': round(similarity, 4),
                'distance': float(distance)
            }
            
            results.append(result)
        
        # Apply filters if provided
        if filters:
            results = self._apply_filters(results, filters)
        
        return results
    
    def get_full_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full dataset details from database.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            Full dataset dictionary or None
        """
        conn = self.connect_database()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT *
            FROM datasets
            WHERE id = ?
        """, (dataset_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_dataset_keywords(self, dataset_id: str) -> List[str]:
        """
        Get keywords for a dataset.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            List of keyword strings
        """
        conn = self.connect_database()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT keyword
            FROM keywords
            WHERE dataset_id = ?
            ORDER BY keyword
        """, (dataset_id,))
        
        return [row['keyword'] for row in cursor.fetchall()]
    
    def get_dataset_contacts(self, dataset_id: str) -> List[Dict[str, Any]]:
        """
        Get contacts for a dataset.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            List of contact dictionaries
        """
        conn = self.connect_database()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT *
            FROM contacts
            WHERE dataset_id = ?
            ORDER BY role, family_name
        """, (dataset_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def enrich_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich search results with additional dataset details.
        
        Args:
            results: Basic search results
            
        Returns:
            Enriched results with keywords, contacts, etc.
        """
        enriched = []
        
        for result in results:
            dataset_id = result['dataset_id']
            
            # Get full dataset
            dataset = self.get_full_dataset(dataset_id)
            
            if dataset:
                # Add keywords
                result['keywords'] = self.get_dataset_keywords(dataset_id)
                
                # Add spatial/temporal extent
                result['spatial_extent'] = {
                    'west': dataset.get('spatial_west'),
                    'east': dataset.get('spatial_east'),
                    'south': dataset.get('spatial_south'),
                    'north': dataset.get('spatial_north')
                } if dataset.get('spatial_west') else None
                
                result['temporal_extent'] = {
                    'start': dataset.get('temporal_start'),
                    'end': dataset.get('temporal_end')
                } if dataset.get('temporal_start') else None
                
                # Add publication date
                result['publication_date'] = dataset.get('publication_date')
            
            enriched.append(result)
        
        return enriched
    
    def _apply_filters(
        self,
        results: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Apply filters to search results.
        
        Args:
            results: Search results
            filters: Filter criteria
            
        Returns:
            Filtered results
        """
        filtered = results
        
        # Example filters (extend as needed)
        if 'min_year' in filters:
            # Would need to enrich results first
            pass
        
        if 'keywords' in filters:
            # Would need to enrich results first
            pass
        
        return filtered
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


if __name__ == '__main__':
    # Allow direct testing
    search = SemanticSearch()
    
    # Example searches
    queries = [
        "soil carbon content",
        "water quality monitoring",
        "biodiversity surveys"
    ]
    
    for query in queries:
        print(f"\n{'=' * 70}")
        print(f"Query: '{query}'")
        print('=' * 70)
        
        results = search.search(query, top_k=3)
        
        for result in results:
            print(f"\n{result['rank']}. {result['title']}")
            print(f"   ID: {result['file_identifier']}")
            print(f"   Similarity: {result['similarity_score']:.4f}")
            if result['abstract']:
                print(f"   Abstract: {result['abstract'][:150]}...")
    
    search.close()