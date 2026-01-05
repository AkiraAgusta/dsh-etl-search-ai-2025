"""
Dataset routes for the API.

Endpoints for listing, retrieving, and filtering datasets.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from etl.models.database import (
    DatasetModel, KeywordModel, ContactModel, 
    OnlineResourceModel, MetadataDocumentModel
)
from api.schemas import (
    DatasetSummary,
    DatasetDetail,
    DatasetListResponse,
    SpatialExtent,
    TemporalExtent,
)
from api.dependencies import get_db, get_pagination_params


router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/", response_model=DatasetListResponse)
def list_datasets(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("title", description="Sort field"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db)
):
    """
    List all datasets with pagination.
    
    Returns paginated list of datasets with basic information.
    """
    # Validate parameters
    _, page_size, offset = get_pagination_params(page, page_size)
    
    # Validate sort order
    if sort_order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Sort order must be 'asc' or 'desc'")
    
    # Get total count
    total = db.query(func.count(DatasetModel.id)).scalar()
    
    # Build query
    query = db.query(DatasetModel)
    
    # Apply sorting
    if hasattr(DatasetModel, sort_by):
        sort_column = getattr(DatasetModel, sort_by)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    else:
        # Default to title
        query = query.order_by(DatasetModel.title.asc())
    
    # Apply pagination
    datasets = query.offset(offset).limit(page_size).all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    return DatasetListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        datasets=[DatasetSummary.model_validate(d) for d in datasets]
    )


@router.get("/{dataset_id}", response_model=DatasetDetail)
def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific dataset.
    
    Args:
        dataset_id: Dataset ID
        
    Returns:
        Complete dataset information including keywords, contacts, resources
    """
    # Query dataset
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
    
    # Build spatial extent
    spatial_extent = None
    if any([dataset.spatial_west, dataset.spatial_east, dataset.spatial_south, dataset.spatial_north]):
        spatial_extent = SpatialExtent(
            west=float(dataset.spatial_west) if dataset.spatial_west else None,
            east=float(dataset.spatial_east) if dataset.spatial_east else None,
            south=float(dataset.spatial_south) if dataset.spatial_south else None,
            north=float(dataset.spatial_north) if dataset.spatial_north else None
        )
    
    # Build temporal extent
    temporal_extent = None
    if dataset.temporal_start or dataset.temporal_end:
        temporal_extent = TemporalExtent(
            start=str(dataset.temporal_start) if dataset.temporal_start else None,
            end=str(dataset.temporal_end) if dataset.temporal_end else None
        )
    
    # Build response using model_validate
    response_data = DatasetDetail.model_validate(dataset)
    response_data.spatial_extent = spatial_extent
    response_data.temporal_extent = temporal_extent
    
    return response_data


@router.get("/{dataset_id}/keywords")
def get_dataset_keywords(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """
    Get keywords for a specific dataset.
    
    Args:
        dataset_id: Dataset ID
        
    Returns:
        List of keywords
    """
    # Verify dataset exists
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
    
    # Get keywords
    keywords = db.query(KeywordModel).filter(KeywordModel.dataset_id == dataset_id).all()
    
    return {
        "dataset_id": dataset_id,
        "total": len(keywords),
        "keywords": [
            {
                "keyword": k.keyword,
                "type": k.keyword_type,
                "uri": k.uri
            }
            for k in keywords
        ]
    }


@router.get("/{dataset_id}/contacts")
def get_dataset_contacts(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """
    Get contacts/authors for a specific dataset.
    
    Args:
        dataset_id: Dataset ID
        
    Returns:
        List of contacts
    """
    # Verify dataset exists
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
    
    # Get contacts
    contacts = db.query(ContactModel).filter(ContactModel.dataset_id == dataset_id).all()
    
    return {
        "dataset_id": dataset_id,
        "total": len(contacts),
        "contacts": [
            {
                "role": c.role,
                "name": f"{c.given_name} {c.family_name}".strip() if c.given_name or c.family_name else c.full_name,
                "organization": c.organization_name,
                "email": c.email,
                "orcid": c.name_identifier
            }
            for c in contacts
        ]
    }


@router.get("/{dataset_id}/resources")
def get_dataset_resources(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """
    Get online resources/download links for a specific dataset.
    
    Args:
        dataset_id: Dataset ID
        
    Returns:
        List of online resources
    """
    # Verify dataset exists
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
    
    # Get resources
    resources = db.query(OnlineResourceModel).filter(OnlineResourceModel.dataset_id == dataset_id).all()
    
    return {
        "dataset_id": dataset_id,
        "total": len(resources),
        "resources": [
            {
                "url": r.url,
                "function": r.function,
                "description": r.description,
                "protocol": r.resource_type
            }
            for r in resources
        ]
    }


@router.get("/{dataset_id}/metadata")
def get_dataset_metadata(
    dataset_id: str,
    format: Optional[str] = Query(None, description="Metadata format: xml, json, jsonld, rdf"),
    db: Session = Depends(get_db)
):
    """
    Get metadata documents for a specific dataset.
    
    Args:
        dataset_id: Dataset ID
        format: Optional format filter (xml, json, jsonld, rdf)
        
    Returns:
        Metadata documents in requested format(s)
    """
    # Verify dataset exists
    dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
    
    # Build query
    query = db.query(MetadataDocumentModel).filter(MetadataDocumentModel.dataset_id == dataset_id)
    
    # Filter by format if specified
    if format:
        format_lower = format.lower()
        if format_lower not in ["xml", "json", "jsonld", "rdf"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format: {format}. Must be one of: xml, json, jsonld, rdf"
            )
        query = query.filter(MetadataDocumentModel.format == format_lower)
    
    # Get documents
    documents = query.all()
    
    if not documents:
        if format:
            raise HTTPException(
                status_code=404,
                detail=f"No {format} metadata found for dataset"
            )
        else:
            return {
                "dataset_id": dataset_id,
                "total": 0,
                "documents": []
            }
    
    return {
        "dataset_id": dataset_id,
        "total": len(documents),
        "documents": [
            {
                "format": d.format,
                "content": d.content
            }
            for d in documents
        ]
    }