"""
Setup and optimize database with performance indexes.
"""

import sys
from pathlib import Path
from loguru import logger

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import DatabaseIndexer


def main():
    """Main entry point for database setup."""
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # Get database path from args or use default
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'data/datasets.db'
    
    try:
        # Initialize indexer
        indexer = DatabaseIndexer(db_path)
        
        # Create indexes
        stats = indexer.create_indexes()
        
        # Verify indexes
        indexer.verify_indexes()
        
        # Print summary
        if stats['failed_count'] == 0:
            print("\n✅ All indexes created successfully!")
            print("   Your database queries should now be much faster.")
            sys.exit(0)
        else:
            print(f"\n⚠️  {stats['failed_count']} indexes failed to create.")
            print("   Check the logs above for details.")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()