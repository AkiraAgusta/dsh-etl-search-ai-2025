"""
Embedding generator for dataset metadata.
"""

import sqlite3
import numpy as np
import faiss
import pickle
from uuid import uuid4
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from loguru import logger

from .config import EmbeddingConfig


class EmbeddingGenerator:
    """Generate and store vector embeddings for datasets."""
    
    def __init__(self, config: EmbeddingConfig = None):
        """
        Initialize embedding generator.
        
        Args:
            config: Configuration object (uses default if None)
        """
        self.config = config or EmbeddingConfig()
        self.model = None
        
    def load_model(self):
        """Load the sentence transformer model."""
        if self.model is None:
            logger.info(f"Loading embedding model: {self.config.MODEL_NAME}")
            self.model = SentenceTransformer(self.config.MODEL_NAME)
            logger.info(f"Model loaded. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        return self.model
    
    def get_dataset_text(self, dataset: Dict[str, Any]) -> str:
        """
        Combine dataset fields into text for embedding.
        
        Args:
            dataset: Dataset dictionary with metadata
            
        Returns:
            Combined text string
        """
        text_parts = []
        
        if self.config.INCLUDE_TITLE and dataset.get('title'):
            text_parts.append(dataset['title'])
        
        if self.config.INCLUDE_ABSTRACT and dataset.get('abstract'):
            text_parts.append(dataset['abstract'])
        
        if self.config.INCLUDE_LINEAGE and dataset.get('lineage'):
            text_parts.append(dataset['lineage'])
        
        # Combine with periods for better sentence boundaries
        return '. '.join(filter(None, text_parts))
    
    def fetch_datasets(self) -> List[Dict[str, Any]]:
        """
        Fetch all datasets from database.
        
        Returns:
            List of dataset dictionaries
        """
        logger.info(f"Connecting to database: {self.config.DATABASE_PATH}")
        conn = sqlite3.connect(self.config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, file_identifier, title, abstract, lineage
            FROM datasets
            ORDER BY file_identifier
        """)
        
        datasets = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        logger.info(f"Fetched {len(datasets)} datasets from database")
        return datasets
    
    def generate_embeddings(self, datasets: List[Dict[str, Any]]) -> np.ndarray:
        """
        Generate embeddings for all datasets.
        
        Args:
            datasets: List of dataset dictionaries
            
        Returns:
            Numpy array of embeddings
        """
        # Load model
        model = self.load_model()
        
        # Prepare texts
        logger.info("Preparing texts for embedding...")
        texts = [self.get_dataset_text(d) for d in datasets]
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} datasets...")
        embeddings = model.encode(
            texts,
            batch_size=self.config.BATCH_SIZE,
            show_progress_bar=True,
            normalize_embeddings=self.config.NORMALIZE_EMBEDDINGS
        )
        
        logger.info(f"Generated embeddings with shape: {embeddings.shape}")
        return embeddings
    
    def create_faiss_index(self, embeddings: np.ndarray) -> faiss.Index:
        """
        Create FAISS index from embeddings.
        
        Args:
            embeddings: Numpy array of embeddings
            
        Returns:
            FAISS index
        """
        logger.info("Creating FAISS index...")
        
        # Convert to float32 (FAISS requirement)
        embeddings_f32 = embeddings.astype('float32')
        
        # Get dimension
        dimension = embeddings_f32.shape[1]
        
        # Create index
        # For small datasets (< 10k), use IndexFlatL2 or IndexFlatIP
        # For normalized vectors, use IndexFlatIP (inner product = cosine similarity)
        if self.config.NORMALIZE_EMBEDDINGS:
            index = faiss.IndexFlatIP(dimension)  # Inner product (cosine for normalized)
        else:
            index = faiss.IndexFlatL2(dimension)  # L2 distance
        
        # Add vectors
        index.add(embeddings_f32)
        
        logger.info(f"Created FAISS index with {index.ntotal} vectors")
        return index
    
    def save_index(self, index: faiss.Index):
        """
        Save FAISS index to disk.
        
        Args:
            index: FAISS index to save
        """
        logger.info(f"Saving FAISS index to: {self.config.FAISS_INDEX_PATH}")
        faiss.write_index(index, str(self.config.FAISS_INDEX_PATH))
        logger.info("FAISS index saved successfully")
    
    def save_metadata(self, datasets: List[Dict[str, Any]]):
        """
        Save dataset metadata for search results.
        
        Args:
            datasets: List of dataset dictionaries
        """
        logger.info(f"Saving metadata to: {self.config.METADATA_PATH}")
        
        metadata = {
            'dataset_ids': [d['id'] for d in datasets],
            'file_identifiers': [d['file_identifier'] for d in datasets],
            'metadata': [
                {
                    'id': d['id'],
                    'file_identifier': d['file_identifier'],
                    'title': d['title'],
                    'abstract': d['abstract'][:300] if d['abstract'] else None
                }
                for d in datasets
            ],
            'model_name': self.config.MODEL_NAME,
            'total_datasets': len(datasets)
        }
        
        with open(self.config.METADATA_PATH, 'wb') as f:
            pickle.dump(metadata, f)
        
        logger.info("Metadata saved successfully")
    
    def update_database(self, datasets: List[Dict[str, Any]], embeddings: np.ndarray):
        """
        Update database with embedding metadata.
        
        Args:
            datasets: List of dataset dictionaries
            embeddings: Numpy array of embeddings
        """
        logger.info("Updating database with embedding metadata...")
        
        conn = sqlite3.connect(self.config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Clear existing embeddings
        cursor.execute("DELETE FROM embeddings")
        
        # Insert new embeddings metadata
        for dataset, embedding in zip(datasets, embeddings):
            cursor.execute("""
                INSERT INTO embeddings (id, dataset_id, embedding_model, embedding_dimension)
                VALUES (?, ?, ?, ?)
            """, (
                str(uuid4()),
                dataset['id'],
                self.config.MODEL_NAME,
                len(embedding)
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Updated database with {len(datasets)} embedding records")
    
    def generate_all(self) -> Dict[str, Any]:
        """
        Complete pipeline: generate embeddings, create index, save everything.
        
        Returns:
            Dictionary with generation statistics
        """
        # Ensure data directory exists
        self.config.ensure_data_dir()
        
        # Fetch datasets
        datasets = self.fetch_datasets()
        
        if not datasets:
            logger.error("No datasets found in database!")
            return {'success': False, 'error': 'No datasets found'}
        
        # Generate embeddings
        embeddings = self.generate_embeddings(datasets)
        
        # Create FAISS index
        index = self.create_faiss_index(embeddings)
        
        # Save index
        self.save_index(index)
        
        # Save metadata
        self.save_metadata(datasets)
        
        # Update database
        self.update_database(datasets, embeddings)
        
        logger.info("=" * 70)
        logger.info("✅ Embedding generation complete!")
        logger.info(f"   Total datasets: {len(datasets)}")
        logger.info(f"   Embedding dimension: {embeddings.shape[1]}")
        logger.info(f"   Model: {self.config.MODEL_NAME}")
        logger.info(f"   Index: {self.config.FAISS_INDEX_PATH}")
        logger.info(f"   Metadata: {self.config.METADATA_PATH}")
        logger.info("=" * 70)
        
        return {
            'success': True,
            'total_datasets': len(datasets),
            'embedding_dimension': embeddings.shape[1],
            'model_name': self.config.MODEL_NAME,
            'index_path': str(self.config.FAISS_INDEX_PATH),
            'metadata_path': str(self.config.METADATA_PATH)
        }


if __name__ == '__main__':
    # Allow direct execution for testing
    generator = EmbeddingGenerator()
    result = generator.generate_all()
    
    if result['success']:
        print("\n✅ Success!")
        print(f"Generated embeddings for {result['total_datasets']} datasets")
    else:
        print(f"\n❌ Error: {result.get('error', 'Unknown error')}")