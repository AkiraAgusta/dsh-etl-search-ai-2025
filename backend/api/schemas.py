"""
API request and response schemas using Pydantic.

These models define the structure of data sent to and received from the API,
providing automatic validation and serialization.
"""

from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from typing import List, Optional, Dict, Union
from datetime import datetime, date


# ==================== Dataset Schemas ====================

class DatasetBase(BaseModel):
    """Base dataset information."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    id: str
    file_identifier: str
    title: str
    abstract: Optional[str] = None


class DatasetSummary(DatasetBase):
    """Dataset summary for list views."""
    publication_date: Optional[Union[str, date]] = None
    
    @field_serializer('publication_date')
    def serialize_date(self, dt: Optional[Union[str, date]], _info):
        if dt is None:
            return None
        if isinstance(dt, date):
            return dt.isoformat()
        return dt


class SpatialExtent(BaseModel):
    """Spatial bounding box."""
    west: Optional[float] = None
    east: Optional[float] = None
    south: Optional[float] = None
    north: Optional[float] = None


class TemporalExtent(BaseModel):
    """Temporal extent."""
    start: Optional[str] = None
    end: Optional[str] = None


class Contact(BaseModel):
    """Dataset contact/author."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    role: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    organization_name: Optional[str] = None
    email: Optional[str] = None
    name_identifier: Optional[str] = None  # ORCID


class Keyword(BaseModel):
    """Dataset keyword."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    keyword: str
    keyword_type: Optional[str] = None
    uri: Optional[str] = None


class OnlineResource(BaseModel):
    """Online resource/download link."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    url: str
    function: Optional[str] = None
    description: Optional[str] = None
    protocol: Optional[str] = None


class MetadataDocument(BaseModel):
    """Metadata document in various formats."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    format: str  # xml, json, jsonld, rdf
    content: Optional[str] = None


class DatasetDetail(DatasetBase):
    """Complete dataset information."""
    lineage: Optional[str] = None
    publication_date: Optional[Union[str, date]] = None
    
    # Extents
    spatial_extent: Optional[SpatialExtent] = None
    temporal_extent: Optional[TemporalExtent] = None
    
    # Related data
    keywords: List[Keyword] = []
    contacts: List[Contact] = []
    online_resources: List[OnlineResource] = []
    metadata_documents: List[MetadataDocument] = []
    
    @field_serializer('publication_date')
    def serialize_date(self, dt: Optional[Union[str, date]], _info):
        if dt is None:
            return None
        if isinstance(dt, date):
            return dt.isoformat()
        return dt


# ==================== Search Schemas ====================

class SemanticSearchRequest(BaseModel):
    """Semantic search request."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    top_k: int = Field(10, ge=1, le=100, description="Number of results to return")
    
    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()


class SearchResult(BaseModel):
    """Single search result."""
    rank: int
    dataset_id: str
    file_identifier: str
    title: str
    abstract: Optional[str] = None
    similarity_score: float
    distance: Optional[float] = None
    
    # Optional enriched data
    keywords: Optional[List[str]] = None
    spatial_extent: Optional[SpatialExtent] = None
    temporal_extent: Optional[TemporalExtent] = None
    publication_date: Optional[str] = None


class SemanticSearchResponse(BaseModel):
    """Semantic search response."""
    query: str
    total_results: int
    results: List[SearchResult]
    processing_time_ms: float


class HybridSearchRequest(BaseModel):
    """Hybrid search request with filters."""
    query: Optional[str] = Field(None, max_length=500, description="Semantic search query")
    
    # Arrays to support multiple selections
    authors: Optional[List[str]] = Field(None, description="Author names to filter by")
    organizations: Optional[List[str]] = Field(None, description="Organizations to filter by")
    keywords: Optional[List[str]] = Field(None, description="Keywords to filter by")
    date_from: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    
    # Spatial filter
    spatial_bbox: Optional[Dict[str, float]] = Field(
        None,
        description="Bounding box {west, east, south, north}"
    )
    
    top_k: int = Field(10, ge=1, le=100, description="Number of results")


# ==================== Dataset List Schemas ====================

class DatasetListRequest(BaseModel):
    """Request for listing datasets."""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Results per page")
    sort_by: Optional[str] = Field("title", description="Field to sort by")
    sort_order: Optional[str] = Field("asc", description="Sort order: asc or desc")


class DatasetListResponse(BaseModel):
    """Response for dataset listing."""
    total: int
    page: int
    page_size: int
    total_pages: int
    datasets: List[DatasetSummary]


# ==================== Statistics Schemas ====================

class AuthorStat(BaseModel):
    """Author statistics entry."""
    name: str
    organization: Optional[str] = None
    count: int


class OrganizationStat(BaseModel):
    """Organization statistics entry."""
    name: str
    count: int


class KeywordStat(BaseModel):
    """Keyword statistics entry."""
    keyword: str
    count: int


class DatabaseStats(BaseModel):
    """Database statistics."""
    model_config = ConfigDict(protected_namespaces=())
    
    total_datasets: int
    total_keywords: int
    total_contacts: int
    total_metadata_documents: int
    total_online_resources: int
    
    # Metadata format breakdown
    metadata_formats: Dict[str, int]
    
    # Embeddings info
    embeddings_generated: bool
    embedding_model_name: Optional[str] = None
    embedding_dimension: Optional[int] = None
    
    # Top aggregations for filter dropdowns (includes ALL values)
    top_authors: List[AuthorStat] = []
    top_organizations: List[OrganizationStat] = []
    top_keywords: List[KeywordStat] = []


# ==================== Health Check Schemas ====================

class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str  # "healthy" or "unhealthy"
    timestamp: datetime
    
    # Component health
    database: bool
    embeddings: bool
    faiss_index: bool
    
    # Version info
    version: str = "1.0.0"
    
    # Optional error details
    errors: Optional[List[str]] = None


# ==================== Error Schemas ====================

class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    status_code: int


# ==================== Embedding Schemas ====================

class GenerateEmbeddingsRequest(BaseModel):
    """Request to generate embeddings."""
    force_regenerate: bool = Field(
        False,
        description="Force regeneration even if embeddings exist"
    )


class GenerateEmbeddingsResponse(BaseModel):
    """Response from embedding generation."""
    model_config = ConfigDict(protected_namespaces=())
    
    success: bool
    total_datasets: int
    embedding_dimension: int
    model_name: str
    processing_time_seconds: float
    message: str