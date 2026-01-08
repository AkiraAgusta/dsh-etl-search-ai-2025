# API Design and Integration - AI Conversation

## FastAPI Application Architecture

### Me:
We have the ETL system, embeddings, and search engine working. Now I need to expose this functionality through a REST API using FastAPI. What's the best way to structure the API application following clean architecture principles?

### Claude:
Excellent! Let's design a professional FastAPI application with proper separation of concerns.

**API Architecture Layers:**

```
┌──────────────────────────────────────────────┐
│           API Layer (FastAPI)                │
│  - Route definitions                         │
│  - Request/response models (Pydantic)        │
│  - Dependency injection                      │
│  - Middleware                                │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│         Business Logic Layer                 │
│  - Search engine                             │
│  - Database operations                       │
│  - Data transformation                       │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│         Data Access Layer                    │
│  - SQLAlchemy sessions                       │
│  - FAISS index                               │
│  - File system                               │
└──────────────────────────────────────────────┘
```

**Project Structure:**

```
api/
├── app.py                    # Main FastAPI application
├── config.py                 # Configuration
├── dependencies.py           # Dependency injection
├── schemas.py                # Pydantic models
├── date_utils.py             # Date handling utilities
└── routes/
    ├── __init__.py
    ├── datasets.py           # Dataset CRUD endpoints
    ├── search.py             # Search endpoints
    └── utils.py              # Utility endpoints (health, stats)
```

---

## Application Configuration

### Me:
Let's start with the application configuration and setup. How should we structure the main FastAPI app with proper middleware and error handling?

### Claude:
Great! Let's create a production-ready FastAPI application.

**Main Application (app.py):**

```python
"""
Main FastAPI application.

This module creates and configures the FastAPI application with all routes,
middleware, and error handlers.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import time
import logging

from api.config import get_settings
from api.routes import datasets, search, utils


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# ==================== Middleware ====================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing information."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Add timing header
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
    
    # Log response
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time*1000:.2f}ms"
    )
    
    return response


# ==================== Error Handlers ====================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "status_code": 422
        }
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors."""
    logger.error(f"Database error on {request.url.path}: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database Error",
            "detail": "An error occurred while accessing the database",
            "status_code": 500
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(f"Unexpected error on {request.url.path}: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
            "status_code": 500
        }
    )


# ==================== Events ====================

@app.on_event("startup")
async def startup_event():
    """Execute on application startup."""
    logger.info("=" * 70)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info("=" * 70)
    logger.info(f"Database: {settings.database_url}")
    logger.info(f"FAISS Index: {settings.faiss_index_path}")
    logger.info(f"Embedding Model: {settings.embedding_model}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info(f"API Prefix: {settings.api_prefix}")
    logger.info("=" * 70)
    logger.info("API is ready to accept requests")
    logger.info("Documentation available at: /docs")
    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Execute on application shutdown."""
    logger.info("Shutting down API...")


# ==================== Routes ====================

# Include routers
app.include_router(utils.router, prefix=settings.api_prefix)
app.include_router(datasets.router, prefix=settings.api_prefix)
app.include_router(search.router, prefix=settings.api_prefix)


# Root endpoint (no prefix)
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "api": settings.api_prefix
    }


# ==================== Main ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
```

**Key Features:**

1. **CORS Configuration**: Allows frontend to communicate
2. **Request Logging**: Tracks all requests with timing
3. **Error Handling**: Graceful error responses
4. **Startup Events**: Validates configuration on startup
5. **Documentation**: Auto-generated Swagger docs at /docs

---

## Dependency Injection

### Me:
I notice we need database sessions and the search engine in our routes. How should we handle dependencies in FastAPI to maintain clean code?

### Claude:
Excellent question! FastAPI's dependency injection system is powerful. Let's use it properly.

**Dependency Injection (dependencies.py):**

```python
"""
Dependency injection for FastAPI routes.
Provides database sessions, search engines, and other dependencies.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from functools import lru_cache

from api.config import get_settings
from embeddings.search import SemanticSearchEngine
from embeddings.config import EmbeddingConfig


# ==================== Database ====================

@lru_cache()
def get_engine():
    """
    Get SQLAlchemy engine.
    Cached to reuse connection pool.
    """
    settings = get_settings()
    return create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False}  # For SQLite
    )


def get_session_maker():
    """Get session maker."""
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.
    
    Yields:
        Database session
        
    This is a generator that:
    1. Creates a session
    2. Yields it to the route
    3. Closes it after the request
    """
    SessionLocal = get_session_maker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== Search Engine ====================

@lru_cache()
def get_search_engine() -> SemanticSearchEngine:
    """
    Get semantic search engine.
    
    Cached to reuse loaded FAISS index and model.
    
    Returns:
        Initialized search engine
    """
    config = EmbeddingConfig()
    engine = SemanticSearchEngine(config)
    
    # Pre-load index and model on first access
    engine.load_index()
    engine.load_model()
    engine.load_metadata()
    
    return engine


# ==================== Configuration ====================

def get_embedding_config() -> EmbeddingConfig:
    """Get embedding configuration."""
    return EmbeddingConfig()
```

**Usage in Routes:**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_search_engine
from embeddings.search import SemanticSearchEngine


router = APIRouter()


@router.get("/datasets/{dataset_id}")
async def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db)  # Inject database session
):
    """Get dataset by ID."""
    # db session automatically created and closed
    dataset = db.query(DatasetModel).filter_by(id=dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.post("/search/semantic")
async def semantic_search(
    query: str,
    top_k: int = 10,
    search_engine: SemanticSearchEngine = Depends(get_search_engine)  # Inject search engine
):
    """Perform semantic search."""
    # search_engine automatically loaded and reused
    results = search_engine.search(query, top_k)
    return {"results": results, "total": len(results)}
```

**Benefits:**

1. **Automatic Cleanup**: Database sessions closed automatically
2. **Caching**: Search engine loaded once, reused for all requests
3. **Testability**: Easy to override dependencies in tests
4. **Type Safety**: Full type hints
5. **Separation**: Business logic separate from dependency management

---

## Pydantic Schemas

### Me:
We need proper request/response models for type safety and validation. How should we define Pydantic schemas for our API?

### Claude:
Great! Pydantic schemas provide validation, documentation, and type safety.

**Schema Design (schemas.py):**

```python
"""
Pydantic models for API request/response validation.
Provides type safety and automatic documentation.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import date, datetime


# ==================== Base Schemas ====================

class ResponseBase(BaseModel):
    """Base response model with success indicator."""
    success: bool = True
    message: Optional[str] = None


# ==================== Search Schemas ====================

class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    
    @validator('query')
    def query_not_empty(cls, v):
        """Validate query is not just whitespace."""
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()


class HybridSearchRequest(BaseModel):
    """Request model for hybrid search with filters."""
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(default=20, ge=1, le=100)
    
    # Filters
    authors: List[str] = Field(default_factory=list, description="Filter by authors")
    organizations: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    formats: List[str] = Field(default_factory=list)
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        """Validate date format."""
        if v is None:
            return v
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')


class SearchResultItem(BaseModel):
    """Single search result."""
    rank: int
    dataset_id: str
    file_identifier: str
    similarity_score: float
    title: Optional[str] = None
    abstract: Optional[str] = None
    publication_date: Optional[str] = None
    keywords: Optional[List[str]] = None
    
    class Config:
        from_attributes = True  # Allows creation from ORM models


class SearchResponse(BaseModel):
    """Search response with results and metadata."""
    results: List[SearchResultItem]
    total: int
    query: str
    top_k: int
    processing_time_ms: Optional[float] = None


# ==================== Dataset Schemas ====================

class SpatialExtent(BaseModel):
    """Spatial extent (bounding box)."""
    west: float = Field(..., ge=-180, le=180)
    east: float = Field(..., ge=-180, le=180)
    south: float = Field(..., ge=-90, le=90)
    north: float = Field(..., ge=-90, le=90)


class TemporalExtent(BaseModel):
    """Temporal extent (time period)."""
    start: Optional[date] = None
    end: Optional[date] = None


class Contact(BaseModel):
    """Contact information."""
    full_name: Optional[str] = None
    organization_name: Optional[str] = None
    role: str
    email: Optional[str] = None


class Keyword(BaseModel):
    """Keyword."""
    keyword: str
    keyword_type: Optional[str] = None


class DatasetSummary(BaseModel):
    """Summary dataset information."""
    id: str
    file_identifier: str
    title: str
    abstract: Optional[str] = None
    publication_date: Optional[date] = None
    resource_type: Optional[str] = None
    
    class Config:
        from_attributes = True


class DatasetDetail(BaseModel):
    """Detailed dataset information."""
    id: str
    file_identifier: str
    title: str
    abstract: Optional[str] = None
    lineage: Optional[str] = None
    publication_date: Optional[date] = None
    metadata_date: Optional[datetime] = None
    resource_type: Optional[str] = None
    resource_status: Optional[str] = None
    spatial_extent: Optional[SpatialExtent] = None
    temporal_extent: Optional[TemporalExtent] = None
    contacts: List[Contact] = []
    keywords: List[Keyword] = []
    
    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    """Response for dataset list."""
    datasets: List[DatasetSummary]
    total: int
    page: int
    page_size: int


# ==================== Stats Schemas ====================

class DatabaseStats(BaseModel):
    """Database statistics."""
    total_datasets: int
    total_contacts: int
    total_keywords: int
    total_relationships: int
    total_metadata_documents: int
    embedding_model: Optional[str] = None
    indexed_datasets: int


class APIInfo(BaseModel):
    """API information."""
    name: str
    version: str
    description: str


# ==================== Error Schemas ====================

class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: str
    status_code: int
```

**Benefits:**

1. **Validation**: Automatic input validation
2. **Documentation**: Auto-generated in Swagger docs
3. **Type Safety**: IDE autocomplete and type checking
4. **Serialization**: Automatic JSON conversion
5. **ORM Integration**: `from_attributes = True` allows ORM model conversion

---

## Route Implementation

### Me:
Let's implement the search routes with proper error handling, validation, and performance optimization.

### Claude:
Perfect! Let's create production-ready search endpoints.

**Search Routes (routes/search.py):**

```python
"""
Search API routes.
Provides semantic and hybrid search endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import time
from typing import List

from api.dependencies import get_db, get_search_engine
from api.schemas import (
    SemanticSearchRequest,
    HybridSearchRequest,
    SearchResponse,
    SearchResultItem
)
from api.date_utils import parse_date_string
from embeddings.search import SemanticSearchEngine
from etl.models.database import DatasetModel, ContactModel, KeywordModel


router = APIRouter(prefix="/search", tags=["search"])


@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    search_engine: SemanticSearchEngine = Depends(get_search_engine),
    db: Session = Depends(get_db)
):
    """
    Perform semantic search using vector embeddings.
    
    Uses FAISS index for fast similarity search.
    """
    start_time = time.time()
    
    try:
        # Perform search
        results = search_engine.search(request.query, request.top_k)
        
        # Enrich with basic metadata
        enriched_results = []
        for result in results:
            # Get dataset from database
            dataset = db.query(DatasetModel).filter_by(id=result['dataset_id']).first()
            
            if dataset:
                enriched_results.append(SearchResultItem(
                    rank=result['rank'],
                    dataset_id=result['dataset_id'],
                    file_identifier=result['file_identifier'],
                    similarity_score=result['similarity_score'],
                    title=dataset.title,
                    abstract=dataset.abstract[:300] if dataset.abstract else None,
                    publication_date=str(dataset.publication_date) if dataset.publication_date else None,
                    keywords=[k.keyword for k in dataset.keywords[:5]]  # First 5 keywords
                ))
        
        processing_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            results=enriched_results,
            total=len(enriched_results),
            query=request.query,
            top_k=request.top_k,
            processing_time_ms=round(processing_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/hybrid", response_model=SearchResponse)
async def hybrid_search(
    request: HybridSearchRequest,
    search_engine: SemanticSearchEngine = Depends(get_search_engine),
    db: Session = Depends(get_db)
):
    """
    Perform hybrid search combining semantic search with filters.
    
    1. Semantic search using FAISS
    2. Filter results using SQL
    """
    start_time = time.time()
    
    try:
        # Step 1: Semantic search (get more results than needed for filtering)
        initial_k = request.top_k * 3  # Get 3x results for filtering
        results = search_engine.search(request.query, initial_k)
        
        # Extract dataset IDs
        dataset_ids = [r['dataset_id'] for r in results]
        
        # Step 2: Build filters
        filters = [DatasetModel.id.in_(dataset_ids)]
        
        if request.authors:
            # Filter by authors
            filters.append(
                DatasetModel.id.in_(
                    db.query(ContactModel.dataset_id)
                    .filter(
                        or_(*[
                            ContactModel.full_name.contains(author)
                            for author in request.authors
                        ])
                    )
                )
            )
        
        if request.keywords:
            # Filter by keywords
            filters.append(
                DatasetModel.id.in_(
                    db.query(KeywordModel.dataset_id)
                    .filter(
                        or_(*[
                            KeywordModel.keyword.contains(kw)
                            for kw in request.keywords
                        ])
                    )
                )
            )
        
        if request.start_date:
            # Filter by publication date >= start_date
            start_dt = parse_date_string(request.start_date)
            if start_dt:
                filters.append(DatasetModel.publication_date >= start_dt)
        
        if request.end_date:
            # Filter by publication date <= end_date
            end_dt = parse_date_string(request.end_date)
            if end_dt:
                filters.append(DatasetModel.publication_date <= end_dt)
        
        # Step 3: Query database with filters
        query = db.query(DatasetModel).filter(and_(*filters))
        filtered_datasets = {d.id: d for d in query.all()}
        
        # Step 4: Re-rank results based on filters
        enriched_results = []
        rank = 1
        for result in results:
            dataset = filtered_datasets.get(result['dataset_id'])
            if dataset:
                enriched_results.append(SearchResultItem(
                    rank=rank,
                    dataset_id=result['dataset_id'],
                    file_identifier=result['file_identifier'],
                    similarity_score=result['similarity_score'],
                    title=dataset.title,
                    abstract=dataset.abstract[:300] if dataset.abstract else None,
                    publication_date=str(dataset.publication_date) if dataset.publication_date else None,
                    keywords=[k.keyword for k in dataset.keywords[:5]]
                ))
                rank += 1
                
                if rank > request.top_k:
                    break
        
        processing_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            results=enriched_results,
            total=len(enriched_results),
            query=request.query,
            top_k=request.top_k,
            processing_time_ms=round(processing_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")
```

**Key Features:**

1. **Performance Tracking**: Measure processing time
2. **Error Handling**: Proper HTTP exceptions
3. **Filtering**: SQL filters after semantic search
4. **Ranking Preservation**: Maintains semantic similarity order
5. **Enrichment**: Adds metadata from database

This API provides professional, production-ready search functionality!