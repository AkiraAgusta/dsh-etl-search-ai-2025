# Backend Architecture - AI Conversation

## Initial Architecture Discussion

### Me:
I need to build an ETL system that extracts metadata from the CEH Catalogue Service. Before we start coding, I want to discuss the overall system architecture. The system needs to:

1. Extract metadata in 4 different formats (XML, JSON, JSON-LD, RDF)
2. Store extracted data in SQLite
3. Support semantic search using vector embeddings
4. Expose a REST API for frontend consumption

What architectural patterns and design principles would you recommend for this system?

### Claude:
For this ETL and semantic search system, I recommend a layered architecture with clear separation of concerns. Here's a comprehensive architectural approach:

**1. Core Architecture Layers:**

- **Presentation Layer**: FastAPI REST API
- **Business Logic Layer**: ETL Pipeline, Search Engine
- **Data Access Layer**: Repository Pattern for database operations
- **Data Storage Layer**: SQLite + FAISS vector store

**2. Design Patterns to Implement:**

**a) Strategy Pattern for Extractors:**
- Create an `IExtractor` interface defining the contract for all extractors
- Implement concrete extractors for each format (XML, JSON, JSON-LD, RDF)
- This allows easy addition of new formats without modifying existing code (Open/Closed Principle)

**b) Template Method Pattern:**
- Create a `BaseExtractor` abstract class that defines the extraction workflow
- Common steps: validate source → fetch data → parse data → validate output
- Subclasses override only the `_parse_data()` method specific to their format

**c) Repository Pattern:**
- Abstract database operations behind a `DatasetRepository` interface
- Separates domain logic from persistence logic
- Makes testing easier with mock repositories
- Allows switching databases without affecting business logic

**d) Factory Pattern (if needed):**
- `ExtractorFactory` to instantiate the correct extractor based on format
- Centralizes object creation logic

**3. Domain-Driven Design:**

Create clear domain models separate from database models:
- Domain models (`Dataset`, `Contact`, `Keyword`) represent business entities
- Database models (`DatasetModel`, `ContactModel`) represent persistence
- Repository handles mapping between the two

**4. SOLID Principles Application:**

- **Single Responsibility**: Each class has one reason to change
  - `XMLExtractor` only handles XML parsing
  - `DatasetRepository` only handles persistence
  - `ETLPipeline` only orchestrates the workflow

- **Open/Closed**: Open for extension, closed for modification
  - Adding new metadata format = create new extractor class
  - No modification to existing extractors

- **Liskov Substitution**: All extractors can be used interchangeably
  - Any `IExtractor` implementation can replace another

- **Interface Segregation**: Small, focused interfaces
  - `IExtractor` has only essential methods
  - No forcing extractors to implement unused methods

- **Dependency Inversion**: Depend on abstractions, not concretions
  - Pipeline depends on `IExtractor`, not `XMLExtractor`
  - Repository pattern abstracts SQLAlchemy details

**5. Suggested Project Structure:**

```
backend/
├── etl/
│   ├── core_interfaces.py      # IExtractor interface
│   ├── extractors/
│   │   ├── base_extractor.py   # Template Method pattern
│   │   ├── xml_extractor.py    # Concrete implementation
│   │   ├── json_extractor.py
│   │   ├── jsonld_extractor.py
│   │   └── rdf_extractor.py
│   ├── models/
│   │   ├── dataset.py          # Domain models
│   │   └── database.py         # SQLAlchemy models
│   ├── repositories/
│   │   └── dataset_repository.py  # Repository pattern
│   ├── pipeline.py             # ETL orchestration
│   └── batch_processor.py      # Batch processing
├── embeddings/
│   ├── generator.py            # Vector embedding generation
│   └── search.py               # Semantic search engine
├── database/
│   └── indexing.py             # Database setup
└── api/
    ├── app.py                  # FastAPI application
    ├── routes/                 # API endpoints
    └── schemas.py              # Pydantic models
```

**6. Data Flow:**

```
CEH API → Extractor (Strategy) → Domain Model → Repository → Database
                                                                ↓
Frontend ← REST API ← Search Engine ← FAISS Index ← Embedding Generator
```

**7. Error Handling Strategy:**

- Custom exceptions (`ExtractionError`, `ValidationError`)
- Graceful degradation (if XML fails, try JSON)
- Comprehensive logging with `loguru`
- Transaction management for database operations

**8. Testing Strategy:**

- Unit tests for each extractor (mock HTTP responses)
- Integration tests for pipeline (test database)
- Repository tests with in-memory SQLite
- API tests with TestClient

Would you like me to start implementing these patterns, beginning with the core interfaces and base extractor?

---

## Discussing Interface Design

### Me:
Yes, let's start with the core interfaces. I want to make sure we define the right abstractions. What methods should the IExtractor interface define, and what responsibilities should it have?

### Claude:
Great question! The interface should be minimal but sufficient. Let's think about what ALL extractors need to do, regardless of format:

**Core Responsibilities:**
1. Extract data from a source (URL or file)
2. Validate the extracted data
3. Identify its source type (for logging/debugging)

**Proposed Interface:**

```python
from abc import ABC, abstractmethod
from typing import Any, Dict

class IExtractor(ABC):
    """Abstract interface for data extraction."""
    
    @abstractmethod
    def extract(self, source: str) -> Dict[str, Any]:
        """
        Extract data from source.
        
        Args:
            source: URL or file path to extract from
            
        Returns:
            Dictionary containing extracted metadata
            
        Raises:
            ExtractionError: If extraction fails
        """
        pass
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate extracted data.
        
        Args:
            data: Extracted data dictionary
            
        Returns:
            True if data is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_source_type(self) -> str:
        """
        Get source type identifier.
        
        Returns:
            String identifier (e.g., 'xml', 'json', 'jsonld', 'rdf')
        """
        pass
```

**Key Design Decisions:**

1. **Return Type**: `Dict[str, Any]` provides flexibility
   - Allows different extractors to return slightly different structures
   - Can be mapped to domain models later

2. **Validation Separation**: `validate()` is separate from `extract()`
   - Allows for different validation strategies per format
   - Can be overridden in subclasses
   - Supports the Single Responsibility Principle

3. **Type Identification**: `get_source_type()` helps with:
   - Logging which extractor is being used
   - Factory pattern implementation
   - Debugging and error messages

4. **Error Handling**: Define custom exception:

```python
class ExtractionError(Exception):
    """Raised when extraction fails."""
    pass
```

**What the Interface Does NOT Include:**

- HTTP fetching logic (belongs in base class)
- Parsing implementation (format-specific)
- Database operations (belongs in repository)
- Business logic (belongs in pipeline)

This keeps the interface clean and focused. Each extractor can implement its own parsing logic while sharing common functionality through the base class.

Should we implement the `BaseExtractor` class next, using the Template Method pattern?

---

## Implementing Template Method Pattern

### Me:
Now let's implement the BaseExtractor class using the Template Method pattern. I want to ensure we handle common concerns like HTTP requests, retries, and error handling in one place. How should we structure this?

### Claude:
Excellent! The Template Method pattern is perfect here. The base class defines the algorithm skeleton, and subclasses fill in specific steps.

**Key Template Method Concepts:**

1. **Define the algorithm structure** in a template method
2. **Abstract methods** for format-specific steps
3. **Hook methods** (optional overrides) for customization
4. **Common functionality** shared across all extractors

**Implementation Strategy:**

```python
import requests
from abc import abstractmethod
from typing import Dict, Any
from loguru import logger

class BaseExtractor(IExtractor):
    """
    Base class for all extractors using Template Method pattern.
    
    The extract() method defines the extraction workflow:
    1. Validate source
    2. Fetch data
    3. Parse data (format-specific)
    4. Validate result
    """
    
    def __init__(self, timeout: int = 30, retry_count: int = 3):
        """
        Initialize extractor with common settings.
        
        Args:
            timeout: Request timeout in seconds
            retry_count: Number of retry attempts
        """
        self.timeout = timeout
        self.retry_count = retry_count
        self.session = requests.Session()  # Reuse connections
    
    # TEMPLATE METHOD - defines the algorithm
    def extract(self, source: str) -> Dict[str, Any]:
        """
        Template method defining extraction workflow.
        
        This method orchestrates the extraction process but delegates
        format-specific parsing to subclasses.
        """
        try:
            logger.info(f"[{self.get_source_type().upper()}] Extracting from: {source}")
            
            # Step 1: Validate source (common)
            if not self._validate_source(source):
                raise ExtractionError(f"Invalid source: {source}")
            
            # Step 2: Fetch data (common)
            raw_data = self._fetch_data(source)
            
            # Step 3: Parse data (format-specific - implemented by subclasses)
            parsed_data = self._parse_data(raw_data)
            
            # Step 4: Validate result (can be overridden by subclasses)
            if not self.validate(parsed_data):
                raise ExtractionError("Data validation failed")
            
            logger.info(f"[{self.get_source_type().upper()}] Successfully extracted")
            return parsed_data
            
        except Exception as e:
            logger.error(f"[{self.get_source_type().upper()}] Extraction failed: {e}")
            raise ExtractionError(f"Failed to extract from {source}: {e}")
    
    # CONCRETE METHOD - common implementation
    def _validate_source(self, source: str) -> bool:
        """Validate that source is a valid URL or file path."""
        if not source or not isinstance(source, str):
            return False
        # For this project, we expect URLs
        return source.startswith(('http://', 'https://'))
    
    # CONCRETE METHOD - common implementation with retry logic
    def _fetch_data(self, source: str) -> bytes:
        """
        Fetch data from source with retry logic.
        
        Implements exponential backoff for transient failures.
        """
        for attempt in range(self.retry_count):
            try:
                response = self.session.get(source, timeout=self.timeout)
                response.raise_for_status()
                return response.content
                
            except requests.RequestException as e:
                if attempt == self.retry_count - 1:
                    # Final attempt failed
                    raise ExtractionError(
                        f"Failed after {self.retry_count} attempts: {e}"
                    )
                logger.warning(
                    f"[{self.get_source_type().upper()}] "
                    f"Attempt {attempt + 1} failed, retrying..."
                )
        
        # Should never reach here, but for type safety
        raise ExtractionError(f"Failed to fetch data from {source}")
    
    # ABSTRACT METHOD - must be implemented by subclasses
    @abstractmethod
    def _parse_data(self, raw_data: bytes) -> Dict[str, Any]:
        """
        Parse raw data into structured format.
        
        This is the format-specific step that each extractor must implement.
        
        Args:
            raw_data: Raw bytes from HTTP response
            
        Returns:
            Dictionary with parsed metadata
        """
        pass
    
    # ABSTRACT METHOD - interface requirement
    @abstractmethod
    def get_source_type(self) -> str:
        """Return the source type identifier."""
        pass
    
    # HOOK METHOD - default implementation, can be overridden
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Default validation - checks data is not empty.
        
        Subclasses can override for format-specific validation.
        """
        return data is not None and len(data) > 0
```

**Why This Design Works:**

1. **Separation of Concerns:**
   - HTTP logic is in `BaseExtractor`
   - Format parsing is in subclasses
   - Clear responsibility boundaries

2. **DRY (Don't Repeat Yourself):**
   - Retry logic written once
   - Validation pattern written once
   - Logging structure consistent

3. **Open for Extension:**
   - Add new format = implement `_parse_data()`
   - No need to duplicate HTTP/retry logic
   - Can override `validate()` for custom rules

4. **Closed for Modification:**
   - Base class rarely needs changes
   - Adding JSON-LD extractor doesn't affect XML extractor

5. **Error Handling:**
   - Consistent exception hierarchy
   - Detailed logging at each step
   - Graceful degradation possible

**Usage Example:**

```python
class XMLExtractor(BaseExtractor):
    def get_source_type(self) -> str:
        return 'xml'
    
    def _parse_data(self, raw_data: bytes) -> Dict[str, Any]:
        # Only implement XML-specific parsing
        root = ET.fromstring(raw_data)
        return {
            'file_identifier': root.find('.//fileIdentifier').text,
            'title': root.find('.//title').text,
            # ... more XML parsing
        }
```

This pattern makes it trivial to add new extractors while maintaining consistency across all implementations. Should we implement the concrete extractors next?

---

## Repository Pattern Discussion

### Me:
Before we implement the extractors, I want to design the repository pattern properly. The repository should handle the mapping between domain models and database models. What's the best approach for this, especially considering we have complex relationships (contacts, keywords, relationships, etc.)?

### Claude:
Excellent thinking! The Repository pattern is crucial for maintaining clean separation between domain logic and persistence. Let's design this carefully.

**Repository Pattern Goals:**

1. **Abstraction**: Hide SQLAlchemy details from business logic
2. **Testability**: Easy to mock for unit tests
3. **Flexibility**: Could swap out SQLite for PostgreSQL later
4. **Clarity**: Clear API for CRUD operations

**Design Approach:**

**1. Two-Model System:**

```
Domain Model (dataset.py)     ←→     Database Model (database.py)
    ↓                                      ↓
Business Logic                       SQLAlchemy ORM
Clean, simple dataclasses           Database constraints
No DB awareness                     Relationships defined
```

**2. Repository Responsibilities:**

```python
class DatasetRepository:
    """
    Repository for dataset persistence operations.
    
    Handles the mapping between domain models (Dataset) and 
    database models (DatasetModel).
    """
    
    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
    
    # CREATE
    def add(self, dataset: Dataset) -> Dataset:
        """Add a new dataset and all its related entities."""
        pass
    
    # READ
    def get_by_id(self, dataset_id: str) -> Optional[Dataset]:
        """Retrieve dataset by ID."""
        pass
    
    def get_by_file_identifier(self, file_identifier: str) -> Optional[Dataset]:
        """Retrieve dataset by file identifier."""
        pass
    
    def get_all(self) -> List[Dataset]:
        """Retrieve all datasets."""
        pass
    
    # UPDATE
    def update(self, dataset: Dataset) -> Dataset:
        """Update existing dataset."""
        pass
    
    # DELETE
    def delete(self, dataset_id: str) -> bool:
        """Delete dataset by ID."""
        pass
    
    # PRIVATE MAPPERS
    def _to_db_model(self, dataset: Dataset) -> DatasetModel:
        """Convert domain model to database model."""
        pass
    
    def _to_domain_model(self, db_dataset: DatasetModel) -> Dataset:
        """Convert database model to domain model."""
        pass
```

**3. Handling Complex Relationships:**

The key challenge is managing one-to-many relationships (contacts, keywords, etc.). Here's the strategy:

```python
def _to_db_model(self, dataset: Dataset) -> DatasetModel:
    """
    Convert domain model to database model with all relationships.
    
    This method:
    1. Creates the main DatasetModel
    2. Converts and attaches all related entities
    3. Lets SQLAlchemy handle the cascade
    """
    from uuid import uuid4
    
    # Generate ID if not present
    dataset_id = dataset.id or str(uuid4())
    
    # Create main dataset model
    db_dataset = DatasetModel(
        id=dataset_id,
        file_identifier=dataset.file_identifier,
        title=dataset.title,
        abstract=dataset.abstract,
        # ... more fields
    )
    
    # Handle spatial extent (flattened into dataset table)
    if dataset.spatial_extent:
        db_dataset.spatial_west = str(dataset.spatial_extent.west)
        db_dataset.spatial_east = str(dataset.spatial_extent.east)
        db_dataset.spatial_south = str(dataset.spatial_extent.south)
        db_dataset.spatial_north = str(dataset.spatial_extent.north)
    
    # Handle temporal extent (flattened into dataset table)
    if dataset.temporal_extent:
        db_dataset.temporal_start = dataset.temporal_extent.start
        db_dataset.temporal_end = dataset.temporal_extent.end
    
    # Convert contacts (one-to-many)
    for contact in dataset.contacts:
        db_contact = ContactModel(
            id=str(uuid4()),
            dataset_id=dataset_id,
            family_name=contact.family_name,
            given_name=contact.given_name,
            # ... more fields
        )
        db_dataset.contacts.append(db_contact)
    
    # Convert keywords (one-to-many)
    for keyword in dataset.keywords:
        db_keyword = KeywordModel(
            id=str(uuid4()),
            dataset_id=dataset_id,
            keyword=keyword.keyword,
            keyword_type=keyword.keyword_type,
            # ... more fields
        )
        db_dataset.keywords.append(db_keyword)
    
    # Similar for relationships, online_resources, metadata_documents
    
    return db_dataset
```

**4. Key Design Decisions:**

**a) Domain Model Purity:**
- Domain models are Python dataclasses
- No SQLAlchemy imports in domain models
- Business logic works with domain models only

**b) Mapping Strategy:**
- Repository handles ALL mapping
- Bidirectional conversion (domain ↔ database)
- Preserves data integrity during conversion

**c) Transaction Management:**
- Repository doesn't commit
- Caller (Pipeline) manages transactions
- Allows atomic multi-dataset operations

**d) Relationship Handling:**
- Use SQLAlchemy's cascade operations
- When adding dataset, related entities auto-save
- When deleting dataset, related entities auto-delete

**5. Why This Matters:**

```python
# BUSINESS LOGIC (Pipeline) - works with domain models
dataset = Dataset(
    file_identifier="abc123",
    title="Sample Dataset",
    contacts=[
        Contact(full_name="John Doe", role="author")
    ]
)

# PERSISTENCE - repository handles complexity
repository.add(dataset)
session.commit()

# RETRIEVAL - get back domain model
retrieved = repository.get_by_file_identifier("abc123")
# retrieved is a Dataset object, not DatasetModel
# Business logic never sees SQLAlchemy details
```

**6. Testing Benefits:**

```python
# Mock repository for unit tests
class MockDatasetRepository:
    def __init__(self):
        self.datasets = []
    
    def add(self, dataset: Dataset) -> Dataset:
        self.datasets.append(dataset)
        return dataset
    
    def get_by_id(self, dataset_id: str) -> Optional[Dataset]:
        return next((d for d in self.datasets if d.id == dataset_id), None)

# Business logic works with either real or mock repository!
```

**7. Database vs Domain Model Differences:**

| Aspect | Domain Model | Database Model |
|--------|--------------|----------------|
| Purpose | Business logic | Persistence |
| Framework | Pure Python / dataclass | SQLAlchemy |
| Relationships | Python lists | SQLAlchemy relationships |
| Spatial Extent | `SpatialExtent` object | 4 separate columns |
| IDs | Optional | Required (UUID) |

This separation ensures:
- Business logic stays clean
- Database changes don't break business logic
- Easy testing with mocks
- Clear architectural boundaries

Should we implement the domain models next, then the database models, then wire them together in the repository?

---

## Summary and Next Steps

### Me:
Let me summarize what we've designed:

1. **Layered Architecture** with clear separation of concerns
2. **Strategy Pattern** for different metadata extractors (IExtractor interface)
3. **Template Method Pattern** for common extraction workflow (BaseExtractor)
4. **Repository Pattern** for clean data access layer
5. **Domain-Driven Design** with separate domain and database models
6. **SOLID Principles** applied throughout

Can you confirm this architecture will support:
- Easy addition of new metadata formats?
- Switching databases if needed?
- Comprehensive testing?
- Clean separation between ETL, storage, and API layers?

### Claude:
Absolutely! Let me confirm how this architecture supports each requirement:

**1. Easy Addition of New Metadata Formats:** ✅

```python
# To add a new format (e.g., CSV), just:
class CSVExtractor(BaseExtractor):
    def get_source_type(self) -> str:
        return 'csv'
    
    def _parse_data(self, raw_data: bytes) -> Dict[str, Any]:
        # CSV-specific parsing
        pass
```

- No changes to existing extractors
- No changes to base class
- No changes to pipeline (works with IExtractor)
- **Open/Closed Principle in action**

**2. Switching Databases:** ✅

The Repository pattern makes this trivial:

```python
# Current: SQLite with SQLAlchemy
class SQLiteDatasetRepository:
    def add(self, dataset: Dataset) -> Dataset:
        # SQLAlchemy implementation
        pass

# Future: PostgreSQL, MongoDB, or even REST API
class PostgreSQLDatasetRepository:
    def add(self, dataset: Dataset) -> Dataset:
        # Different implementation, same interface
        pass

# Pipeline doesn't care:
pipeline = ETLPipeline(repository=repository)  # Works with any repository
```

- Business logic depends on repository interface
- Swap implementation without touching pipeline
- **Dependency Inversion Principle**

**3. Comprehensive Testing:** ✅

Each layer can be tested independently:

```python
# Test extractors in isolation
def test_json_extractor():
    extractor = JSONExtractor()
    mock_response = '{"id": "123", "title": "Test"}'
    # Mock HTTP, test parsing logic
    
# Test repository with in-memory database
def test_repository():
    engine = create_engine('sqlite:///:memory:')
    session = Session(engine)
    repo = DatasetRepository(session)
    # Test CRUD operations

# Test pipeline with mock dependencies
def test_pipeline():
    mock_repo = MockDatasetRepository()
    mock_extractor = MockExtractor()
    pipeline = ETLPipeline(repository=mock_repo)
    # Test orchestration logic
```

**4. Clean Layer Separation:** ✅

```
┌─────────────────────────────────────────┐
│         API Layer (FastAPI)             │  ← Presentation
│  - REST endpoints                       │
│  - Pydantic schemas                     │
│  - Request/Response handling            │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│     Business Logic Layer                │  ← Domain
│  - ETL Pipeline orchestration           │
│  - Domain models (Dataset, Contact)     │
│  - Extraction interfaces (IExtractor)   │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│      Data Access Layer                  │  ← Infrastructure
│  - Repository pattern (DatasetRepo)     │
│  - Database models (SQLAlchemy)         │
│  - FAISS vector operations              │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│        Storage Layer                    │  ← Persistence
│  - SQLite database                      │
│  - FAISS index files                    │
│  - File system                          │
└─────────────────────────────────────────┘
```

**Each layer:**
- Has a single responsibility
- Depends only on layers below (unidirectional dependency)
- Can be tested independently
- Can be changed without affecting other layers

**Additional Benefits:**

1. **Maintainability**: Clear structure makes code easy to understand
2. **Scalability**: Can scale components independently
3. **Error Isolation**: Errors in one layer don't cascade
4. **Documentation**: Architecture is self-documenting
5. **Onboarding**: New developers can understand structure quickly

**Potential Enhancements:**

1. **Service Layer** (if business logic grows):
   ```python
   class DatasetService:
       def process_batch(self, identifiers: List[str]):
           # Orchestrate complex business operations
           pass
   ```

2. **Specification Pattern** (for complex queries):
   ```python
   class DatasetSpecification:
       def is_satisfied_by(self, dataset: Dataset) -> bool:
           pass
   ```

3. **Unit of Work Pattern** (for complex transactions):
   ```python
   class UnitOfWork:
       def __init__(self):
           self.datasets = DatasetRepository(session)
           self.contacts = ContactRepository(session)
   ```

**The architecture is ready to implement!** Should we start with:
1. Core interfaces and base extractor?
2. Domain models?
3. Database models?

Which would you like to tackle first?