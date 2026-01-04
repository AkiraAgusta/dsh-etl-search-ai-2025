"""
Generate vector embeddings for semantic search.

This script:
1. Loads all datasets from the database
2. Generates vector embeddings using sentence transformers
3. Creates a FAISS index for fast similarity search
4. Saves the index and metadata to disk
"""

import sys
from pathlib import Path
from loguru import logger

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from embeddings import EmbeddingGenerator


def main():
    """Main entry point."""
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
    
    logger.info("=" * 70)
    logger.info("CEH Datasets - Embedding Generation")
    logger.info("=" * 70)
    
    try:
        # Create generator
        generator = EmbeddingGenerator()
        
        # Generate embeddings
        result = generator.generate_all()
        
        if result['success']:
            logger.info("\n" + "=" * 70)
            logger.info("✅ SUCCESS! Embeddings generated successfully")
            logger.info("=" * 70)
            logger.info(f"\nStatistics:")
            logger.info(f"  Total datasets:      {result['total_datasets']}")
            logger.info(f"  Embedding dimension: {result['embedding_dimension']}")
            logger.info(f"  Model:              {result['model_name']}")
            logger.info(f"\nFiles created:")
            logger.info(f"  FAISS index:        {result['index_path']}")
            logger.info(f"  Metadata:           {result['metadata_path']}")
            logger.info("=" * 70)
            
            return 0
        else:
            logger.error(f"\n❌ ERROR: {result.get('error', 'Unknown error')}")
            return 1
    
    except FileNotFoundError as e:
        logger.error(f"\n❌ ERROR: {e}")
        logger.error("Make sure you've run the ETL process and created the database first.")
        return 1
    
    except Exception as e:
        logger.exception(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())