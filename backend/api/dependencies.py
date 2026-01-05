"""
API dependencies for dependency injection.

This module provides dependency injection functions for database sessions,
search instances, and other shared resources.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends, HTTPException
from typing import Generator
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from embeddings import SemanticSearch
from api.config import get_settings, Settings


# ==================== Database ====================

def get_engine():
    """Get database engine."""
    settings = get_settings()
    return create_engine(settings.database_url, echo=False)


def get_session_maker():
    """Get session maker."""
    engine = get_engine()
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    
    Yields:
        Database session
        
    Usage:
        @app.get("/datasets")
        def get_datasets(db: Session = Depends(get_db)):
            # Use db session
            pass
    """
    SessionLocal = get_session_maker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== Semantic Search ====================

_semantic_search_instance = None


def get_semantic_search() -> SemanticSearch:
    """
    Dependency to get semantic search instance.
    
    Uses a singleton pattern to avoid loading the model multiple times.
    
    Returns:
        SemanticSearch instance
        
    Raises:
        HTTPException: If embeddings not generated or FAISS index missing
        
    Usage:
        @app.post("/search")
        def search(search: SemanticSearch = Depends(get_semantic_search)):
            results = search.search("query")
            return results
    """
    global _semantic_search_instance
    
    if _semantic_search_instance is None:
        try:
            _semantic_search_instance = SemanticSearch()
            # Verify index loads successfully
            _semantic_search_instance.load_index()
            _semantic_search_instance.load_metadata()
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Embeddings not generated. "
                    "Please run 'python scripts/generate_embeddings.py' first. "
                    f"Error: {str(e)}"
                )
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize semantic search: {str(e)}"
            )
    
    return _semantic_search_instance


# ==================== Settings ====================

def get_api_settings() -> Settings:
    """
    Dependency to get API settings.
    
    Returns:
        Settings instance
    """
    return get_settings()


# ==================== Utility Dependencies ====================

async def verify_embeddings_exist(
    search: SemanticSearch = Depends(get_semantic_search)
) -> SemanticSearch:
    """
    Verify embeddings are generated before allowing search operations.
    
    Args:
        search: SemanticSearch instance
        
    Returns:
        SemanticSearch instance if embeddings exist
        
    Raises:
        HTTPException: If embeddings don't exist
    """
    # If we got here, embeddings exist (would have failed in get_semantic_search)
    return search


def get_pagination_params(
    page: int = 1,
    page_size: int = 20
):
    """
    Validate and get pagination parameters.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        Tuple of (page, page_size, offset)
        
    Raises:
        HTTPException: If parameters are invalid
    """
    # Get settings
    settings = get_settings()
    
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
    
    if page_size < 1:
        raise HTTPException(status_code=400, detail="Page size must be >= 1")
    
    if page_size > settings.max_page_size:
        raise HTTPException(
            status_code=400,
            detail=f"Page size cannot exceed {settings.max_page_size}"
        )
    
    offset = (page - 1) * page_size
    
    return page, page_size, offset