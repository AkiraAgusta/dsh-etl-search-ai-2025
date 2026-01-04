"""
Run ETL batch processing for all CEH datasets.

This script processes all datasets listed in metadata-file-identifiers.txt
and extracts metadata in all 4 formats (XML, JSON, JSON-LD, RDF).
"""

import sys
from pathlib import Path
from loguru import logger

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.batch_processor import BatchProcessor


def main():
    """Main entry point for batch processing."""
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add("logs/batch_process.log", level="DEBUG", rotation="10 MB")
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    try:
        # Initialize processor
        processor = BatchProcessor(
            database_url="sqlite:///data/datasets.db",
            log_level="INFO"
        )
        
        # Run batch processing
        stats = processor.process()
        
        # Close database connection
        processor.close()
        
        # Exit with appropriate code
        if stats['fail_count'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()