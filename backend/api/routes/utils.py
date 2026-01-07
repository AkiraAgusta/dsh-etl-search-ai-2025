"""
Utility routes for health checks, statistics, and system information.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text, desc, and_
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from etl.models.database import (
    DatasetModel, KeywordModel, ContactModel, OnlineResourceModel, MetadataDocumentModel
)
from api.schemas import HealthCheckResponse, DatabaseStats
from api.dependencies import get_db
from api.config import get_settings


router = APIRouter(tags=["utilities"])


@router.get("/health", response_model=HealthCheckResponse)
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    
    Checks if the API and its dependencies are working correctly.
    
    Returns:
        Health status of API components
    """
    errors = []
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        database_healthy = True
    except Exception as e:
        database_healthy = False
        errors.append(f"Database error: {str(e)}")
    
    # Check embeddings table
    try:
        # Try to query embeddings table directly
        result = db.execute(text("SELECT COUNT(*) FROM embeddings")).scalar()
        embeddings_healthy = result > 0 if result is not None else False
        if not embeddings_healthy:
            errors.append("No embeddings found in database")
    except Exception as e:
        embeddings_healthy = False
        errors.append(f"Embeddings check error: {str(e)}")
    
    # Check FAISS index
    settings = get_settings()
    faiss_index_path = Path(settings.faiss_index_path)
    faiss_healthy = faiss_index_path.exists()
    if not faiss_healthy:
        errors.append(f"FAISS index not found at {faiss_index_path}")
    
    # Determine overall status
    status = "healthy" if all([
        database_healthy,
        embeddings_healthy,
        faiss_healthy
    ]) else "unhealthy"
    
    return HealthCheckResponse(
        status=status,
        timestamp=datetime.utcnow(),
        database=database_healthy,
        embeddings=embeddings_healthy,
        faiss_index=faiss_healthy,
        version="1.0.0",
        errors=errors if errors else None
    )


@router.get("/stats", response_model=DatabaseStats)
def get_statistics(db: Session = Depends(get_db)):
    """
    Get database statistics.
    
    Returns counts of datasets, keywords, contacts, and other metadata.
    Useful for understanding the size and coverage of the database.
    
    Returns:
        Database statistics including all authors, organizations, and keywords
    """
    # Count datasets
    total_datasets = db.query(func.count(DatasetModel.id)).scalar()
    
    # Count keywords
    total_keywords = db.query(func.count(KeywordModel.id)).scalar()
    
    # Count contacts
    total_contacts = db.query(func.count(ContactModel.id)).scalar()
    
    # Count metadata documents
    total_metadata_docs = db.query(func.count(MetadataDocumentModel.id)).scalar()
    
    # Count online resources
    total_resources = db.query(func.count(OnlineResourceModel.id)).scalar()
    
    # Metadata format breakdown
    format_counts = db.query(
        MetadataDocumentModel.format,
        func.count(MetadataDocumentModel.id)
    ).group_by(MetadataDocumentModel.format).all()
    
    metadata_formats = {format_name: count for format_name, count in format_counts}
    
    # Embeddings info - query directly from embeddings table
    embeddings_count = 0
    embedding_model_name = None
    embedding_dimension = None
    
    try:
        # Try to get embeddings info
        embeddings_count_result = db.execute(text("SELECT COUNT(*) FROM embeddings")).scalar()
        embeddings_count = embeddings_count_result if embeddings_count_result is not None else 0
        
        if embeddings_count > 0:
            # Get first embedding's metadata
            embedding_info = db.execute(
                text("SELECT embedding_model, embedding_dimension FROM embeddings LIMIT 1")
            ).first()
            
            if embedding_info:
                embedding_model_name = embedding_info[0]
                embedding_dimension = embedding_info[1]
    except Exception as e:
        # Embeddings table might not exist or be empty
        pass
    
    embeddings_generated = embeddings_count > 0
    
    # Top Authors - NO LIMIT, with explicit null/empty filtering
    # Get authors with their full names and organizations, counting dataset appearances
    top_authors_query = db.query(
        # Use full_name if available, otherwise combine given and family names
        func.coalesce(
            ContactModel.full_name,
            func.concat(
                func.coalesce(ContactModel.given_name, ''),
                ' ',
                func.coalesce(ContactModel.family_name, '')
            )
        ).label('name'),
        ContactModel.organization_name.label('organization'),
        func.count(func.distinct(ContactModel.dataset_id)).label('count')
    ).filter(
        # Explicitly filter out null and empty names
        and_(
            # Ensure we have either full_name OR (given_name OR family_name)
            func.coalesce(
                ContactModel.full_name,
                func.concat(
                    func.coalesce(ContactModel.given_name, ''),
                    ' ',
                    func.coalesce(ContactModel.family_name, '')
                )
            ).isnot(None),
            # Ensure the name is not just whitespace
            func.trim(
                func.coalesce(
                    ContactModel.full_name,
                    func.concat(
                        func.coalesce(ContactModel.given_name, ''),
                        ' ',
                        func.coalesce(ContactModel.family_name, '')
                    )
                )
            ) != ''
        )
    ).group_by(
        'name', ContactModel.organization_name
    ).order_by(
        desc('count')
    ).all()
    
    top_authors = [
        {
            'name': author.name.strip(),
            'organization': author.organization,
            'count': author.count
        }
        for author in top_authors_query
        if author.name and author.name.strip()  # Additional safety check
    ]
    
    # Top Organizations - NO LIMIT, with explicit null/empty filtering
    top_organizations_query = db.query(
        ContactModel.organization_name.label('name'),
        func.count(func.distinct(ContactModel.dataset_id)).label('count')
    ).filter(
        # Explicitly filter out null and empty organizations
        and_(
            ContactModel.organization_name.isnot(None),
            func.trim(ContactModel.organization_name) != ''
        )
    ).group_by(
        ContactModel.organization_name
    ).order_by(
        desc('count')
    ).all()
    
    top_organizations = [
        {
            'name': org.name,
            'count': org.count
        }
        for org in top_organizations_query
        if org.name and org.name.strip()  # Additional safety check
    ]
    
    # Top Keywords - NO LIMIT, with explicit null/empty filtering
    top_keywords_query = db.query(
        KeywordModel.keyword,
        func.count(func.distinct(KeywordModel.dataset_id)).label('count')
    ).filter(
        # Explicitly filter out null and empty keywords
        and_(
            KeywordModel.keyword.isnot(None),
            func.trim(KeywordModel.keyword) != ''
        )
    ).group_by(
        KeywordModel.keyword
    ).order_by(
        desc('count')
    ).all()
    
    top_keywords = [
        {
            'keyword': keyword.keyword,
            'count': keyword.count
        }
        for keyword in top_keywords_query
        if keyword.keyword and keyword.keyword.strip()  # Additional safety check
    ]
    
    return DatabaseStats(
        total_datasets=total_datasets,
        total_keywords=total_keywords,
        total_contacts=total_contacts,
        total_metadata_documents=total_metadata_docs,
        total_online_resources=total_resources,
        metadata_formats=metadata_formats,
        embeddings_generated=embeddings_generated,
        embedding_model_name=embedding_model_name,
        embedding_dimension=embedding_dimension,
        top_authors=top_authors,
        top_organizations=top_organizations,
        top_keywords=top_keywords
    )


@router.get("/")
def root():
    """
    Root endpoint with API information.
    
    Returns:
        API welcome message and useful links
    """
    return {
        "message": "CEH Datasets API",
        "version": "1.0.0",
        "description": "Semantic search and discovery API for CEH environmental datasets",
        "documentation": "/docs",
        "health": "/api/health",
        "statistics": "/api/stats",
        "endpoints": {
            "datasets": "/api/datasets",
            "search": "/api/search",
            "semantic_search": "/api/search/semantic",
            "hybrid_search": "/api/search/hybrid"
        }
    }