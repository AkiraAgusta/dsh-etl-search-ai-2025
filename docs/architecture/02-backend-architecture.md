# Backend Architecture

## Overview

The backend is a Python-based system implementing ETL pipelines, semantic search capabilities, and a RESTful API. It follows **Clean Architecture** principles with clear separation of concerns and dependency inversion.

## Directory Structure

```
backend/
├── api/                         # REST API layer
│   ├── __init__.py
│   ├── app.py                   # FastAPI application
│   ├── config.py                # Configuration management
│   ├── dependencies.py          # Dependency injection
│   ├── schemas.py               # Pydantic models
│   └── routes/
│       ├── datasets.py          # Dataset operations
│       ├── search.py            # Search operations
│       └── utils.py             # Utility endpoints
│
├── etl/                         # ETL subsystem
│   ├── __init__.py
│   ├── core_interfaces.py       # Abstract interfaces
│   ├── pipeline.py              # ETL orchestration
│   ├── batch_processor.py       # Batch processing
│   ├── extractors/
│   │   ├── base_extractor.py    # Base class
│   │   ├── xml_extractor.py     # ISO 19115 XML
│   │   ├── json_extractor.py    # JSON
│   │   ├── jsonld_extractor.py  # Schema.org
│   │   └── rdf_extractor.py     # RDF Turtle
│   ├── models/
│   │   ├── dataset.py           # Domain models
│   │   └── database.py          # SQLAlchemy models
│   ├── repositories/
│   │   └── dataset_repository.py
│   └── utils/
│       └── date_utils.py
│
├── embeddings/                  # Semantic search
│   ├── __init__.py
│   ├── config.py                # Configuration
│   ├── generator.py             # Embedding generation
│   └── search.py                # Search engine
│
├── database/
│   ├── __init__.py
│   └── indexing.py              # Performance indexing
│
└── scripts/                     # Operational scripts
    ├── run_etl.py
    ├── setup_database.py
    ├── generate_embeddings.py
    ├── test_search.py
    └── start_api.py
```

## Architectural Layers

### 1. Domain Layer (Core)

**Purpose**: Business logic and entities independent of external concerns

**Components**:
- `etl/models/dataset.py` - Domain entities (Dataset, Contact, Keyword, etc.)
- `etl/core_interfaces.py` - Core abstractions (IExtractor)

**Principles**:
- No external dependencies
- Pure business logic
- Framework-agnostic

**Example - Dataset Entity**:
```python
@dataclass
class Dataset:
    """Domain model for dataset metadata."""
    id: str
    file_identifier: str
    title: str
    abstract: Optional[str]
    contacts: List[Contact]
    keywords: List[Keyword]
    # ... more fields
```

**Why This Matters**: Domain logic can be tested in isolation and remains stable even if we change frameworks or databases.

### 2. Application Layer (Use Cases)

**Purpose**: Orchestrate domain objects to fulfill use cases

**Components**:
- `etl/pipeline.py` - ETL orchestration
- `etl/batch_processor.py` - Batch operations
- `embeddings/generator.py` - Embedding generation
- `embeddings/search.py` - Search operations

**Responsibilities**:
- Coordinate extractors
- Manage transactions
- Error handling
- Logging

**Example - ETL Pipeline**:
```python
class ETLPipeline:
    """Orchestrates extraction from multiple formats."""
    
    def process_dataset(self, file_identifier: str) -> Optional[Dataset]:
        # Extract from all 4 formats
        xml_data = self._extract_xml(file_identifier)
        json_data = self._extract_json(file_identifier)
        jsonld_data = self._extract_jsonld(file_identifier)
        rdf_data = self._extract_rdf(file_identifier)
        
        # Merge and persist
        dataset = self._merge_all_formats(...)
        self.repository.add(dataset)
        return dataset
```

**Why This Matters**: Business workflows are clearly defined and separated from technical implementation details.

### 3. Infrastructure Layer (External)

**Purpose**: Implementation details for data access and external services

**Components**:
- `etl/extractors/` - HTTP-based data extraction
- `etl/repositories/` - Database operations
- `database/indexing.py` - Database setup
- `etl/models/database.py` - SQLAlchemy mappings

**Example - Repository Pattern**:
```python
class DatasetRepository:
    """Data access abstraction."""
    
    def add(self, dataset: Dataset) -> None:
        """Persist dataset to database."""
        
    def get_by_id(self, dataset_id: str) -> Optional[Dataset]:
        """Retrieve dataset by ID."""
        
    def search(self, filters: dict) -> List[Dataset]:
        """Search datasets with filters."""
```

**Why This Matters**: Can swap implementations (e.g., SQLite → PostgreSQL) without changing business logic.

### 4. Presentation Layer (API)

**Purpose**: Expose backend functionality via HTTP

**Components**:
- `api/app.py` - FastAPI application
- `api/routes/` - REST endpoints
- `api/schemas.py` - Request/response models
- `api/dependencies.py` - Dependency injection

**Why This Matters**: API concerns separated from business logic, enabling easy testing and API versioning.

## Design Patterns

### 1. Template Method Pattern

**Location**: `etl/extractors/base_extractor.py`

**Purpose**: Define extraction workflow skeleton, allowing subclasses to customize specific steps

```python
class BaseExtractor(IExtractor):
    def extract(self, source: str) -> Dict[str, Any]:
        """Template method - defines workflow."""
        if not self._validate_source(source):
            raise ExtractionError(f"Invalid source")
        
        raw_data = self._fetch_data(source)
        parsed_data = self._parse_data(raw_data)  # Subclass implements
        
        if not self.validate(parsed_data):
            raise ExtractionError("Validation failed")
        
        return parsed_data
    
    @abstractmethod
    def _parse_data(self, raw_data: bytes) -> Dict[str, Any]:
        """Implemented by subclasses (XML, JSON, RDF, JSON-LD)."""
        pass
```

**Benefits**:
- Code reuse (fetch, validate, error handling)
- Consistent workflow across all extractors
- Easy to add new format extractors

**Why This Pattern**: Extraction follows a common pattern (fetch → parse → validate), but parsing differs by format.

### 2. Strategy Pattern

**Location**: `etl/extractors/` package

**Purpose**: Encapsulate different parsing algorithms (XML, JSON, RDF, JSON-LD)

```python
# Different strategies for different formats
xml_extractor = XMLExtractor()
json_extractor = JSONExtractor()
rdf_extractor = RDFExtractor()

# Same interface, different implementations
xml_data = xml_extractor.extract(xml_url)
json_data = json_extractor.extract(json_url)
```

**Benefits**:
- Interchangeable parsing strategies
- Easy to test each format independently
- Clear separation of parsing logic

**Why This Pattern**: Each metadata format requires different parsing logic, but the interface remains consistent.

### 3. Repository Pattern

**Location**: `etl/repositories/dataset_repository.py`

**Purpose**: Abstract data persistence, decouple business logic from database

```python
class DatasetRepository:
    """Abstracts database operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def add(self, dataset: Dataset) -> None:
        """Add dataset - hides SQLAlchemy details."""
        db_dataset = self._to_model(dataset)
        self.session.add(db_dataset)
    
    def get_by_id(self, dataset_id: str) -> Optional[Dataset]:
        """Retrieve dataset - returns domain model."""
        db_dataset = self.session.query(DatasetModel).filter_by(id=dataset_id).first()
        return self._to_entity(db_dataset) if db_dataset else None
```

**Benefits**:
- Testable without database
- Can swap database implementation
- Domain layer stays clean

**Why This Pattern**: Domain logic should not depend on database details. Repository provides a collection-like interface.

### 4. Dependency Injection

**Location**: `api/dependencies.py`

**Purpose**: Provide dependencies to API routes without tight coupling

```python
# Dependencies
def get_db() -> Generator[Session, None, None]:
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_search_engine() -> SemanticSearchEngine:
    """Search engine dependency."""
    return SemanticSearchEngine(config)

# Usage in routes
@router.get("/datasets/{dataset_id}")
async def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db)  # Injected
):
    repo = DatasetRepository(db)
    return repo.get_by_id(dataset_id)
```

**Benefits**:
- Testable (can inject mocks)
- Centralized dependency management
- Loose coupling

**Why This Pattern**: Routes shouldn't create their own dependencies. DI provides flexibility and testability.

## ETL Subsystem Deep Dive

### Extraction Process

1. **Source Identification**: Construct URLs for each format
   ```python
   xml_url = f"https://catalogue.ceh.ac.uk/documents/{id}.xml"
   json_url = f"https://catalogue.ceh.ac.uk/documents/{id}?format=json"
   jsonld_url = f"https://catalogue.ceh.ac.uk/documents/{id}?format=schema.org"
   rdf_url = f"https://catalogue.ceh.ac.uk/documents/{id}?format=ttl"
   ```

2. **Parallel Extraction**: All formats extracted independently
   ```python
   xml_data = xml_extractor.extract(xml_url)           # ISO 19115
   json_data = json_extractor.extract(json_url)        # JSON
   jsonld_data = jsonld_extractor.extract(jsonld_url)  # Schema.org
   rdf_data = rdf_extractor.extract(rdf_url)           # Turtle
   ```

3. **Data Merging**: Intelligent merge favoring richest source
   ```python
   dataset = Dataset(
       title=xml_data.get('title') or json_data.get('title'),
       abstract=xml_data.get('abstract') or json_data.get('abstract'),
       # JSON-LD has additional relationship data
       relationships=jsonld_data.get('relationships', []),
       # RDF has structured keywords
       keywords=rdf_data.get('keywords') or xml_data.get('keywords')
   )
   ```

4. **Persistence**: Store both structured data and raw documents
   ```python
   # Store structured data
   repository.add(dataset)
   
   # Store raw documents for reference
   metadata_doc = MetadataDocument(
       format='xml',
       content=raw_xml_content,
       dataset_id=dataset.id
   )
   repository.add_metadata_document(metadata_doc)
   ```

### Format-Specific Extractors

<details>
<summary><b>XMLExtractor (ISO 19115) - Click to expand</b></summary>

- **Parsing**: lxml with XPath queries
- **Namespaces**: Handles GMD, GCO, GML namespaces
- **Strengths**: Comprehensive metadata, standardized structure
- **Challenges**: Verbose, complex namespace handling

```python
class XMLExtractor(BaseExtractor):
    def _parse_data(self, raw_data: bytes) -> Dict[str, Any]:
        tree = etree.fromstring(raw_data)
        return {
            'title': self._extract_xpath(tree, './/gmd:title/gco:CharacterString'),
            'abstract': self._extract_xpath(tree, './/gmd:abstract/gco:CharacterString'),
            # ... more XPath extractions
        }
```

</details>

<details>
<summary><b>JSONExtractor (CEH Format) - Click to expand</b></summary>

- **Parsing**: Native JSON parsing
- **Strengths**: Easy to parse, rich relationship data
- **Structure**: Nested objects for contacts, keywords, relationships

```python
class JSONExtractor(BaseExtractor):
    def _parse_data(self, raw_data: bytes) -> Dict[str, Any]:
        data = json.loads(raw_data)
        return {
            'title': data.get('title'),
            'abstract': data.get('description'),
            'relationships': [
                {'type': r['rel'], 'target': r['href']}
                for r in data.get('relationships', [])
            ]
        }
```

</details>

<details>
<summary><b>JSONLDExtractor (Schema.org) - Click to expand</b></summary>

- **Parsing**: JSON-LD with RDF context
- **Strengths**: Web-friendly, structured data for SEO
- **Special Fields**: Citation text, accessibility flags

```python
class JSONLDExtractor(BaseExtractor):
    def _parse_data(self, raw_data: bytes) -> Dict[str, Any]:
        data = json.loads(raw_data)
        return {
            'title': data.get('name'),
            'description': data.get('description'),
            'credit_text': data.get('creditText'),
            'is_accessible_for_free': data.get('isAccessibleForFree')
        }
```

</details>

<details>
<summary><b>RDFExtractor (Turtle) - Click to expand</b></summary>

- **Parsing**: rdflib with SPARQL queries
- **Strengths**: Semantic relationships, ontology URIs
- **Graph Traversal**: Follow RDF triples

```python
class RDFExtractor(BaseExtractor):
    def _parse_data(self, raw_data: bytes) -> Dict[str, Any]:
        g = Graph()
        g.parse(data=raw_data, format='turtle')
        
        # SPARQL query example
        title = g.value(subject=dataset_uri, predicate=DCT.title)
        keywords = list(g.objects(subject=dataset_uri, predicate=DCAT.keyword))
        
        return {
            'title': str(title),
            'keywords': [str(k) for k in keywords]
        }
```

</details>

### Error Handling Strategy

**Graceful Degradation**: If one format fails, continue with others

```python
def process_dataset(self, file_identifier: str) -> Optional[Dataset]:
    xml_data = self._safe_extract(self.xml_extractor, xml_url)
    json_data = self._safe_extract(self.json_extractor, json_url)
    jsonld_data = self._safe_extract(self.jsonld_extractor, jsonld_url)
    rdf_data = self._safe_extract(self.rdf_extractor, rdf_url)
    
    # Require at least one successful extraction
    if not any([xml_data, json_data, jsonld_data, rdf_data]):
        logger.error(f"No data extracted for {file_identifier}")
        return None
    
    # Proceed with available data
    return self._merge_all_formats(...)

def _safe_extract(self, extractor, url):
    try:
        return extractor.extract(url)
    except Exception as e:
        logger.warning(f"Extraction failed: {e}")
        return None
```

**Why This Approach**: Maximizes data extraction even when some sources are unavailable.

## Database Schema

### Core Tables

**datasets** (primary entity)
- id (PK), file_identifier (unique)
- title, abstract, description, lineage
- publication_date, metadata_date
- spatial extent, temporal extent
- additional_metadata (JSON for flexibility)

**Relationships**:
```
Dataset (1) ──── (N) Contact
Dataset (1) ──── (N) Keyword
Dataset (1) ──── (N) Relationship
Dataset (1) ──── (N) OnlineResource
Dataset (1) ──── (N) MetadataDocument
Dataset (1) ──── (1) Embedding
```

**Design Decision**: Normalized schema for data integrity, with JSON field for format-specific extras.

## Semantic Search Engine

### Embedding Generation

**Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimension**: 384
- **Language**: English
- **Speed**: ~100 sentences/sec on CPU
- **Quality**: Good balance of speed and accuracy

**Why This Model**: Lightweight enough to run on CPU, quality sufficient for prototype, open source (no API costs).

**Text Preparation**:
```python
def get_dataset_text(self, dataset: Dict[str, Any]) -> str:
    text_parts = []
    
    if dataset.get('title'):
        text_parts.append(dataset['title'])
    
    if dataset.get('abstract'):
        text_parts.append(dataset['abstract'])
    
    if dataset.get('lineage'):
        text_parts.append(dataset['lineage'])
    
    return '. '.join(filter(None, text_parts))
```

**Embedding Storage**:
- **Vector Store**: FAISS IndexFlatL2
- **Index Type**: Flat (exact search, no compression)
- **Metadata**: Stored separately in SQLite, linked by dataset ID

**Why FAISS IndexFlatL2**: Exact search with L2 distance, no loss of accuracy, sufficient performance for ~200 datasets.

### Search Process

1. **Query Embedding**: Convert user query to vector
2. **Similarity Search**: Find nearest neighbors in FAISS
3. **Result Enrichment**: Fetch full metadata from SQLite
4. **Ranking**: Order by cosine similarity

### Hybrid Search

Combines semantic search with keyword filtering:

```python
def combined_search(
    query: str,
    keywords: List[str] = None,
    date_range: tuple = None,
    spatial_bounds: dict = None
) -> List[Dataset]:
    # Step 1: Semantic search (broad)
    semantic_results = semantic_search(query, k=100)
    
    # Step 2: Filter by keywords
    if keywords:
        semantic_results = [
            r for r in semantic_results
            if any(k.lower() in r.title.lower() for k in keywords)
        ]
    
    # Step 3: Filter by date/spatial (if provided)
    # ...
    
    return semantic_results[:20]  # Top 20
```

**Why This Approach**: Semantic search finds relevant results, filters refine for precision.

## API Design

### REST Principles

1. **Resource-based URLs**: `/api/datasets/{id}`
2. **HTTP Methods**: GET, POST
3. **Status Codes**: 200 OK, 400 Bad Request, 404 Not Found, 500 Server Error
4. **Content Type**: application/json

### Request Validation (Pydantic)

```python
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(10, ge=1, le=100)
    filters: Optional[SearchFilters] = None

class SearchFilters(BaseModel):
    keywords: Optional[List[str]] = None
    date_range: Optional[tuple[date, date]] = None
    spatial_bounds: Optional[dict] = None
```

**Why Pydantic**: Automatic validation, clear error messages, type safety.

### Middleware Pipeline

```
Request
  ↓
CORS Middleware
  ↓
Request Logging
  ↓
Route Handler
  ↓
Response Logging
  ↓
Error Handler (if exception)
  ↓
Response
```