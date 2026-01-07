"""
Dataset routes for the API.

Endpoints for listing, retrieving, and filtering datasets.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
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
from api.date_utils import parse_date_string


router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/", response_model=DatasetListResponse)
def list_datasets(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("title", description="Sort field"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    # Filter parameters
    authors: Optional[List[str]] = Query(None, description="Filter by author names"),
    organizations: Optional[List[str]] = Query(None, description="Filter by organizations"),
    keywords: Optional[List[str]] = Query(None, description="Filter by keywords"),
    date_from: Optional[str] = Query(None, description="Filter by publication date from (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by publication date to (YYYY-MM-DD)"),
    formats: Optional[List[str]] = Query(None, description="Filter by metadata formats (xml, json, jsonld, rdf)"),
    db: Session = Depends(get_db)
):
    """
    List all datasets with pagination and optional filters.
    
    Returns paginated list of datasets with basic information.
    Supports filtering by authors, organizations, keywords, publication date range, and metadata formats.
    """
    # Validate parameters
    _, page_size, offset = get_pagination_params(page, page_size)
    
    # Validate sort order
    if sort_order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Sort order must be 'asc' or 'desc'")
    
    # Build base query
    query = db.query(DatasetModel)
    
    # Apply author filter
    if authors:
        # Get dataset IDs that match any of the specified authors
        author_conditions = []
        for author in authors:
            author_conditions.append(ContactModel.full_name.like(f"%{author}%"))
            author_conditions.append(ContactModel.given_name.like(f"%{author}%"))
            author_conditions.append(ContactModel.family_name.like(f"%{author}%"))
        
        contact_ids = db.query(ContactModel.dataset_id).filter(
            or_(*author_conditions)
        ).distinct().all()
        author_dataset_ids = [c[0] for c in contact_ids]
        
        if author_dataset_ids:
            query = query.filter(DatasetModel.id.in_(author_dataset_ids))
        else:
            # No matching authors found
            return DatasetListResponse(
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0,
                datasets=[]
            )
    
    # Apply organization filter
    if organizations:
        # Get dataset IDs that match any of the specified organizations
        org_conditions = []
        for org in organizations:
            org_conditions.append(ContactModel.organization_name.like(f"%{org}%"))
        
        org_ids = db.query(ContactModel.dataset_id).filter(
            or_(*org_conditions)
        ).distinct().all()
        org_dataset_ids = [o[0] for o in org_ids]
        
        if org_dataset_ids:
            query = query.filter(DatasetModel.id.in_(org_dataset_ids))
        else:
            # No matching organizations found
            return DatasetListResponse(
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0,
                datasets=[]
            )
    
    # Apply keyword filter
    if keywords:
        # Get dataset IDs that have ALL of the specified keywords
        keyword_dataset_ids = None
        for keyword in keywords:
            kw_ids = db.query(KeywordModel.dataset_id).filter(
                KeywordModel.keyword == keyword
            ).distinct().all()
            kw_dataset_ids = set([k[0] for k in kw_ids])
            
            if keyword_dataset_ids is None:
                keyword_dataset_ids = kw_dataset_ids
            else:
                # Intersection - dataset must have all keywords
                keyword_dataset_ids &= kw_dataset_ids
        
        if keyword_dataset_ids:
            query = query.filter(DatasetModel.id.in_(list(keyword_dataset_ids)))
        else:
            # No datasets with all specified keywords
            return DatasetListResponse(
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0,
                datasets=[]
            )
    
    # Apply date range filter using shared utility function
    if date_from:
        try:
            date_from_obj = parse_date_string(date_from)
            query = query.filter(DatasetModel.publication_date >= date_from_obj)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date_from: {str(e)}"
            )
    
    if date_to:
        try:
            date_to_obj = parse_date_string(date_to)
            query = query.filter(DatasetModel.publication_date <= date_to_obj)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date_to: {str(e)}"
            )
    
    # Apply metadata format filter
    if formats:
        # Validate format values
        valid_formats = ['xml', 'json', 'jsonld', 'rdf']
        for fmt in formats:
            if fmt.lower() not in valid_formats:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid format: {fmt}. Must be one of: {', '.join(valid_formats)}"
                )
        
        # Get dataset IDs that have metadata in ANY of the specified formats
        format_conditions = []
        for fmt in formats:
            format_conditions.append(MetadataDocumentModel.format == fmt.lower())
        
        format_ids = db.query(MetadataDocumentModel.dataset_id).filter(
            or_(*format_conditions)
        ).distinct().all()
        format_dataset_ids = [f[0] for f in format_ids]
        
        if format_dataset_ids:
            query = query.filter(DatasetModel.id.in_(format_dataset_ids))
        else:
            # No datasets with the specified formats
            return DatasetListResponse(
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0,
                datasets=[]
            )
    
    # Get total count after filters
    total = query.count()
    
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
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    
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