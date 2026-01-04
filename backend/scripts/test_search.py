"""
Test semantic search functionality.

Usage:
    python3 test_search.py
    python3 test_search.py "your custom query"
"""

import sys
from pathlib import Path
from loguru import logger

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from embeddings import SemanticSearch


def test_search(query: str, top_k: int = 5):
    """
    Test semantic search with a query.
    
    Args:
        query: Search query
        top_k: Number of results to return
    """
    logger.info(f"\n{'=' * 70}")
    logger.info(f"Query: '{query}'")
    logger.info('=' * 70)
    
    # Create search instance
    search = SemanticSearch()
    
    try:
        # Perform search
        results = search.search(query, top_k=top_k)
        
        # Display results
        logger.info(f"\nTop {len(results)} results:")
        logger.info("")
        
        for result in results:
            logger.info(f"{result['rank']}. {result['title']}")
            logger.info(f"   File ID:    {result['file_identifier']}")
            logger.info(f"   Similarity: {result['similarity_score']:.4f}")
            if result['abstract']:
                abstract = result['abstract'][:200]
                logger.info(f"   Abstract:   {abstract}...")
            logger.info("")
        
    except FileNotFoundError as e:
        logger.error(f"\n❌ ERROR: {e}")
        logger.error("Please run generate_embeddings.py first!")
        return False
    
    except Exception as e:
        logger.exception(f"\n❌ Unexpected error: {e}")
        return False
    
    finally:
        search.close()
    
    return True


def run_test_suite():
    """Run a suite of test queries."""
    logger.info("=" * 70)
    logger.info("CEH Datasets - Semantic Search Test Suite")
    logger.info("=" * 70)
    
    # Test queries covering different topics
    test_queries = [
        "soil carbon content",
        "water quality monitoring",
        "biodiversity surveys",
        "climate change impact",
        "vegetation mapping",
        "river ecosystems",
        "land use patterns",
        "air pollution data"
    ]
    
    success_count = 0
    
    for query in test_queries:
        if test_search(query, top_k=3):
            success_count += 1
    
    logger.info("=" * 70)
    logger.info(f"Test suite complete: {success_count}/{len(test_queries)} successful")
    logger.info("=" * 70)
    
    return success_count == len(test_queries)


def interactive_mode():
    """Interactive search mode."""
    logger.info("=" * 70)
    logger.info("CEH Datasets - Interactive Semantic Search")
    logger.info("=" * 70)
    logger.info("\nEnter search queries (or 'quit' to exit)")
    logger.info("")
    
    search = SemanticSearch()
    
    try:
        while True:
            try:
                query = input("\nSearch query: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not query:
                    continue
                
                # Perform search
                results = search.search(query, top_k=5)
                
                # Display results
                print(f"\n{'=' * 70}")
                print(f"Top {len(results)} results for: '{query}'")
                print('=' * 70)
                
                for result in results:
                    print(f"\n{result['rank']}. {result['title']}")
                    print(f"   Similarity: {result['similarity_score']:.4f}")
                    print(f"   ID: {result['file_identifier']}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error: {e}")
    
    finally:
        search.close()
        logger.info("\nGoodbye!")


def main():
    """Main entry point."""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<level>{message}</level>"
    )
    
    # Check command line arguments
    if len(sys.argv) > 1:
        # Single query mode
        if sys.argv[1] == '--interactive' or sys.argv[1] == '-i':
            interactive_mode()
        elif sys.argv[1] == '--suite' or sys.argv[1] == '-s':
            success = run_test_suite()
            return 0 if success else 1
        else:
            # Custom query
            query = ' '.join(sys.argv[1:])
            success = test_search(query, top_k=10)
            return 0 if success else 1
    else:
        # Default: run test suite
        success = run_test_suite()
        
        if success:
            logger.info("\n💡 Tip: Try interactive mode with: python3 test_semantic_search.py -i")
            logger.info("   Or search directly: python3 test_semantic_search.py \"your query\"")

        return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())