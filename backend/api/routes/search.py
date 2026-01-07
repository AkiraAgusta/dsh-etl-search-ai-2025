"""
Search routes for the API.

Endpoints for semantic search and hybrid search with filters.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from embeddings import SemanticSearch
from etl.models.database import DatasetModel, KeywordModel, ContactModel
from api.schemas import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SearchResult,
    HybridSearchRequest,
    SpatialExtent,
    TemporalExtent,
)
from api.dependencies import get_db, verify_embeddings_exist
from api.date_utils import parse_date_string


router = APIRouter(prefix="/search", tags=["search"])


@router.post("/semantic", response_model=SemanticSearchResponse)
def semantic_search(
    request: SemanticSearchRequest,
    search: SemanticSearch = Depends(verify_embeddings_exist)
):
    """
    Perform semantic search on dataset metadata.
    
    Searches dataset titles and abstracts using vector similarity.
    Returns ranked results based on semantic similarity.
    
    Args:
        request: Search request with query and top_k
        
    Returns:
        Ranked search results with similarity scores
    """
    start_time = time.time()
    
    # Perform search
    try:
        results = search.search(request.query, top_k=request.top_k)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
    
    # Calculate processing time
    processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    # Format results
    search_results = [
        SearchResult(
            rank=r['rank'],
            dataset_id=r['dataset_id'],
            file_identifier=r['file_identifier'],
            title=r['title'],
            abstract=r.get('abstract'),
            similarity_score=r['similarity_score'],
            distance=r.get('distance')
        )
        for r in results
    ]
    
    return SemanticSearchResponse(
        query=request.query,
        total_results=len(search_results),
        results=search_results,
        processing_time_ms=round(processing_time, 2)
    )


@router.post("/semantic/enriched", response_model=SemanticSearchResponse)
def semantic_search_enriched(
    request: SemanticSearchRequest,
    search: SemanticSearch = Depends(verify_embeddings_exist),
    db: Session = Depends(get_db)
):
    """
    Perform semantic search with enriched results.
    
    Same as semantic search but includes additional metadata like keywords,
    spatial/temporal extents, and publication dates.
    
    Args:
        request: Search request with query and top_k
        
    Returns:
        Enriched search results
    """
    start_time = time.time()
    
    # Perform search
    try:
        results = search.search(request.query, top_k=request.top_k)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
    
    # Enrich results
    enriched_results = []
    for r in results:
        dataset_id = r['dataset_id']
        
        # Get dataset from database
        dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
        
        if dataset:
            # Get keywords
            keywords = db.query(KeywordModel.keyword).filter(
                KeywordModel.dataset_id == dataset_id
            ).all()
            keyword_list = [k[0] for k in keywords] if keywords else None
            
            # Build spatial extent
            spatial_extent = None
            if any([dataset.spatial_west, dataset.spatial_east, 
                   dataset.spatial_south, dataset.spatial_north]):
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
            
            # Create enriched result
            enriched_results.append(
                SearchResult(
                    rank=r['rank'],
                    dataset_id=r['dataset_id'],
                    file_identifier=r['file_identifier'],
                    title=r['title'],
                    abstract=r.get('abstract'),
                    similarity_score=r['similarity_score'],
                    distance=r.get('distance'),
                    keywords=keyword_list,
                    spatial_extent=spatial_extent,
                    temporal_extent=temporal_extent,
                    publication_date=str(dataset.publication_date) if dataset.publication_date else None
                )
            )
        else:
            # Dataset not found in DB, use basic result
            enriched_results.append(
                SearchResult(
                    rank=r['rank'],
                    dataset_id=r['dataset_id'],
                    file_identifier=r['file_identifier'],
                    title=r['title'],
                    abstract=r.get('abstract'),
                    similarity_score=r['similarity_score'],
                    distance=r.get('distance')
                )
            )
    
    processing_time = (time.time() - start_time) * 1000
    
    return SemanticSearchResponse(
        query=request.query,
        total_results=len(enriched_results),
        results=enriched_results,
        processing_time_ms=round(processing_time, 2)
    )


@router.post("/hybrid", response_model=SemanticSearchResponse)
def hybrid_search(
    request: HybridSearchRequest,
    search: SemanticSearch = Depends(verify_embeddings_exist),
    db: Session = Depends(get_db)
):
    """
    Perform hybrid search combining semantic search with metadata filters.
    
    Supports multiple authors, organizations, and keywords.
    
    Steps:
    1. If query provided: semantic search to get initial candidates
    2. Apply filters: authors (array), organizations (array), keywords (array), dates, spatial bbox
    3. Return filtered and ranked results
    
    Args:
        request: Hybrid search request with query and filters
        
    Returns:
        Filtered search results
    """
    start_time = time.time()
    
    # Step 1: Semantic search (if query provided)
    if request.query and request.query.strip():
        try:
            # Get more results than needed for filtering
            semantic_results = search.search(request.query, top_k=request.top_k * 3)
            candidate_ids = [r['dataset_id'] for r in semantic_results]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Semantic search failed: {str(e)}"
            )
    else:
        # No query: get all dataset IDs
        candidate_ids = [d[0] for d in db.query(DatasetModel.id).all()]
    
    # Step 2: Build filter query
    query = db.query(DatasetModel).filter(DatasetModel.id.in_(candidate_ids))
    
    # Apply authors filter (supports multiple authors)
    if request.authors and len(request.authors) > 0:
        # Build OR conditions for each author
        author_conditions = []
        for author in request.authors:
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
            # No matching authors, return empty results
            return SemanticSearchResponse(
                query=request.query or "filter-only",
                total_results=0,
                results=[],
                processing_time_ms=round((time.time() - start_time) * 1000, 2)
            )
    
    # Apply organizations filter (supports multiple organizations)
    if request.organizations and len(request.organizations) > 0:
        # Build OR conditions for each organization
        org_conditions = []
        for org in request.organizations:
            org_conditions.append(ContactModel.organization_name.like(f"%{org}%"))
        
        org_ids = db.query(ContactModel.dataset_id).filter(
            or_(*org_conditions)
        ).distinct().all()
        org_dataset_ids = [o[0] for o in org_ids]
        
        if org_dataset_ids:
            query = query.filter(DatasetModel.id.in_(org_dataset_ids))
        else:
            # No matching organizations, return empty results
            return SemanticSearchResponse(
                query=request.query or "filter-only",
                total_results=0,
                results=[],
                processing_time_ms=round((time.time() - start_time) * 1000, 2)
            )
    
    # Apply keyword filter (supports multiple keywords)
    if request.keywords and len(request.keywords) > 0:
        # Get datasets that have ALL specified keywords (intersection)
        keyword_dataset_ids = None
        for keyword in request.keywords:
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
            # No datasets with all specified keywords, return empty results
            return SemanticSearchResponse(
                query=request.query or "filter-only",
                total_results=0,
                results=[],
                processing_time_ms=round((time.time() - start_time) * 1000, 2)
            )
    
    # Apply date filter using shared utility function
    if request.date_from:
        try:
            date_from_obj = parse_date_string(request.date_from)
            query = query.filter(DatasetModel.publication_date >= date_from_obj)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date_from format: {str(e)}"
            )
    
    if request.date_to:
        try:
            date_to_obj = parse_date_string(request.date_to)
            query = query.filter(DatasetModel.publication_date <= date_to_obj)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date_to format: {str(e)}"
            )
    
    # Apply spatial filter
    if request.spatial_bbox:
        bbox = request.spatial_bbox
        if all(k in bbox for k in ['west', 'east', 'south', 'north']):
            query = query.filter(
                and_(
                    DatasetModel.spatial_west >= str(bbox['west']),
                    DatasetModel.spatial_east <= str(bbox['east']),
                    DatasetModel.spatial_south >= str(bbox['south']),
                    DatasetModel.spatial_north <= str(bbox['north'])
                )
            )
    
    # Execute query
    filtered_datasets = query.all()
    
    # Step 3: Rank results
    if request.query and request.query.strip():
        # Use semantic search ranking
        rank_map = {r['dataset_id']: (r['rank'], r['similarity_score']) 
                   for r in semantic_results}
        
        # Sort by semantic rank
        filtered_datasets.sort(
            key=lambda d: rank_map.get(d.id, (999, 0.0))[0]
        )
        
        # Build results with scores
        results = []
        for i, dataset in enumerate(filtered_datasets[:request.top_k], 1):
            rank, score = rank_map.get(dataset.id, (i, 0.0))
            results.append(
                SearchResult(
                    rank=i,
                    dataset_id=dataset.id,
                    file_identifier=dataset.file_identifier,
                    title=dataset.title,
                    abstract=dataset.abstract,
                    similarity_score=score,
                    publication_date=str(dataset.publication_date) if dataset.publication_date else None
                )
            )
    else:
        # No semantic ranking, just return filtered results
        results = [
            SearchResult(
                rank=i,
                dataset_id=d.id,
                file_identifier=d.file_identifier,
                title=d.title,
                abstract=d.abstract,
                similarity_score=0.0,
                publication_date=str(d.publication_date) if d.publication_date else None
            )
            for i, d in enumerate(filtered_datasets[:request.top_k], 1)
        ]
    
    processing_time = (time.time() - start_time) * 1000
    
    return SemanticSearchResponse(
        query=request.query or "filter-only",
        total_results=len(results),
        results=results,
        processing_time_ms=round(processing_time, 2)
    )