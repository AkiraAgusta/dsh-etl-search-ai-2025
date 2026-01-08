# System Architecture Overview

## Executive Summary

This document provides a high-level architectural overview of the DSH ETL Search AI system - a full-stack application designed for semantic search and discovery of environmental datasets from the CEH (Centre for Ecology & Hydrology) Catalogue Service.

## System Purpose

The system enables users to:
- **Discover datasets** through intelligent semantic search
- **Explore metadata** across multiple standardized formats
- **Access resources** including data files and supporting documents
- **Navigate relationships** between related datasets

## Architectural Style

The system follows a **modern three-tier architecture**:

```
┌─────────────────────────────────────────────────────────┐
│                  Presentation Layer                     │
│              (SvelteKit + TailwindCSS)                  │
│  - Responsive web interface                             │
│  - Component-based architecture                         │
│  - Client-side state management                         │
└─────────────────────────────────────────────────────────┘
                           ↓ HTTP/REST
┌─────────────────────────────────────────────────────────┐
│                  Application Layer                      │
│                  (FastAPI + Python)                     │
│  - RESTful API endpoints                                │
│  - Business logic orchestration                         │
│  - Request validation & error handling                  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                     Data Layer                          │
│      SQLite (Structured) + FAISS (Vector Store)         │
│  - Dataset metadata storage                             │
│  - Relational data modeling                             │
│  - Vector embeddings for semantic search                │
└─────────────────────────────────────────────────────────┘
```

## Core Subsystems

### 1. ETL Subsystem (Backend)

**Purpose**: Extract, Transform, Load metadata from CEH Catalogue

**Key Components**:
- **Extractors**: Specialized parsers for XML (ISO 19115), JSON, JSON-LD (Schema.org), RDF (Turtle)
- **Pipeline**: Orchestrates multi-format extraction and merging
- **Repository**: Data access abstraction using Repository pattern
- **Models**: Domain entities representing datasets, contacts, keywords, etc.

**Design Patterns**:
- **Strategy Pattern**: Different extractors for different formats
- **Template Method**: Common extraction workflow in base class
- **Repository Pattern**: Abstraction of data persistence

### 2. Semantic Search Subsystem (Backend)

**Purpose**: Enable natural language dataset discovery

**Key Components**:
- **Embedding Generator**: Creates vector representations using Sentence Transformers
- **FAISS Index**: High-performance similarity search
- **Search Engine**: Combines keyword and semantic search

**Technologies**:
- Sentence Transformers (all-MiniLM-L6-v2)
- FAISS (Facebook AI Similarity Search)
- NumPy for vector operations

### 3. REST API Subsystem (Backend)

**Purpose**: Expose backend functionality to frontend

**Key Components**:
- **Routes**: Modular endpoint organization (datasets, search, utils)
- **Middleware**: CORS, logging, request timing
- **Error Handlers**: Consistent error responses
- **Schemas**: Pydantic models for request/response validation

**Endpoints**:
- `POST /api/search/semantic` - Semantic search with natural language
- `POST /api/search/semantic/enriched` - Semantic search with full database metadata
- `POST /api/search/hybrid` - Hybrid search with filters
- `GET /api/datasets` - List datasets with pagination
- `GET /api/datasets/{dataset_id}` - Get dataset details
- `GET /api/datasets/{dataset_id}/keywords` - Get dataset keywords
- `GET /api/datasets/{dataset_id}/contacts` - Get dataset contacts
- `GET /api/datasets/{dataset_id}/resources` - Get online resources
- `GET /api/datasets/{dataset_id}/metadata` - Get raw metadata documents
- `GET /api/stats` - System statistics
- `GET /api/health` - Health check

### 4. Web Frontend (Presentation)

**Purpose**: User interface for dataset discovery

**Key Components**:
- **Pages**: Search, Browse, Dashboard, About
- **Components**: Reusable UI elements (common, layout, search, filters)
- **Stores**: Client-side state management
- **API Client**: Axios-based backend communication

**Technologies**:
- SvelteKit (framework)
- TailwindCSS (styling)
- Axios (HTTP client)

## Data Flow

### ETL Flow

```
CEH Catalogue Service
    ↓
Extractors (XML, JSON, JSON-LD, RDF)
    ↓
Pipeline (merge all formats)
    ↓
Repository (validation & persistence)
    ↓
SQLite Database
    ↓
Embedding Generator
    ↓
FAISS Vector Index
```

### Search Flow

```
User Query
    ↓
Frontend (SearchBar component)
    ↓
API Client (POST /api/search/semantic)
    ↓
Search Endpoint (FastAPI)
    ↓
Search Engine (FAISS + SQLite)
    ↓
Results (ranked by relevance)
    ↓
Frontend (ResultCard components)
    ↓
User Views Results
```

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: SQLite
- **Vector Store**: FAISS
- **ML Models**: Sentence Transformers
- **Web Scraping**: Requests, BeautifulSoup, lxml
- **RDF Parsing**: rdflib
- **Logging**: Loguru

### Frontend
- **Language**: JavaScript/TypeScript
- **Framework**: SvelteKit
- **Styling**: TailwindCSS
- **HTTP Client**: Axios
- **Build Tool**: Vite

## Key Design Decisions

### Why SQLite?
**Decision**: Use SQLite over PostgreSQL  
**Rationale**:
- **Simplicity**: No separate database server required
- **Portability**: Single file database, easy to distribute
- **Performance**: Sufficient for prototype scale (200 datasets)
- **Ease of Setup**: Zero configuration needed

**Trade-off**: Limited concurrent writes, but acceptable for read-heavy workload

### Why FAISS?
**Decision**: Use FAISS over managed vector DB (Pinecone, Weaviate)  
**Rationale**:
- **Performance**: Highly optimized for vector similarity
- **No Dependencies**: Runs locally, no external services
- **Cost**: Free and open source
- **Control**: Full control over indexing strategy

**Trade-off**: Manual index management, but provides flexibility for prototype

### Why Svelte/SvelteKit?
**Decision**: Use SvelteKit over React or Vue  
**Rationale**:
- **Performance**: Compiles to vanilla JavaScript (no virtual DOM overhead)
- **Simplicity**: Less boilerplate than React
- **Modern**: Built-in routing, SSR support
- **Developer Experience**: Intuitive syntax, fast development

**Trade-off**: Smaller ecosystem than React, but sufficient for project needs

### Why FastAPI?
**Decision**: Use FastAPI over Flask or Django  
**Rationale**:
- **Modern**: Async support out of the box
- **Fast**: High performance with Pydantic validation
- **Documentation**: Auto-generated OpenAPI docs
- **Type Safety**: Python type hints throughout

**Trade-off**: Newer framework, but excellent for API-focused applications

### Multi-Format Extraction Strategy
**Decision**: Extract all 4 metadata formats and merge  
**Rationale**:
- **Completeness**: Each format contains unique information
- **Redundancy**: Fallback if one format fails
- **Quality**: Can choose best data from each source
- **Flexibility**: Easy to prioritize certain formats

**Trade-off**: More complex ETL, but results in richer metadata

## Documentation Standards

All code follows these documentation principles:
1. **Module docstrings**: Purpose and overview
2. **Class docstrings**: Responsibility and usage
3. **Method docstrings**: Parameters, returns, raises
4. **Inline comments**: Complex logic explanation
5. **Type hints**: All function signatures

## References

- [CEH Catalogue Service](https://catalogue.ceh.ac.uk/eidc/documents)
- [ISO 19115 Standard](https://www.iso.org/standard/53798.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SvelteKit Documentation](https://kit.svelte.dev/)
- [FAISS Wiki](https://github.com/facebookresearch/faiss/wiki)