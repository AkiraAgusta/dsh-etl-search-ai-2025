# Code Refactoring and Improvements - AI Conversation

## Identifying Code Smells

### Me:
After implementing the extractors and repository, I want to review the code for potential improvements. Help me identify any code smells or areas where we could apply better software engineering practices.

### Claude:
Excellent! Let's perform a comprehensive code review focusing on SOLID principles, design patterns, and clean code practices.

**Areas to Review:**

1. **Duplication in Extractor Methods**
2. **Date Parsing Logic**
3. **Configuration Management**
4. **Repository Mapping Complexity**

---

## Refactoring 1: Extracting Date Utilities

### Me:
I notice we're parsing dates in multiple places across different extractors. The logic is duplicated, and different formats use different parsing approaches. How can we refactor this?

### Claude:
Great observation! Date parsing is a cross-cutting concern. Let's create a dedicated utility module.

**Problem: Duplication**
```python
# In XMLExtractor
def _parse_date(self, date_str: str) -> date:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None

# In JSONExtractor - SAME CODE
def _parse_date(self, date_str: str) -> date:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None
```

**Solution: Create Utility Module**

```python
# etl/utils/date_utils.py
"""
Date parsing utilities for metadata extraction.
Centralizes all date/time parsing logic.
"""

from datetime import datetime, date
from typing import Optional
from loguru import logger


def parse_date(date_str: str) -> Optional[date]:
    """
    Parse date string to date object.
    
    Supports multiple formats:
    - ISO 8601: 2023-01-15
    - With time: 2023-01-15T10:30:00
    
    Args:
        date_str: Date string to parse
        
    Returns:
        date object if successful, None otherwise
    """
    if not date_str:
        return None
    
    # Try multiple formats
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S%z',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    logger.warning(f"Could not parse date: {date_str}")
    return None


def parse_datetime(datetime_str: str) -> Optional[datetime]:
    """
    Parse datetime string to datetime object.
    
    Handles ISO 8601 format with timezone.
    
    Args:
        datetime_str: Datetime string to parse
        
    Returns:
        datetime object if successful, None otherwise
    """
    if not datetime_str:
        return None
    
    try:
        # Handle ISO 8601 format with Z (UTC)
        if datetime_str.endswith('Z'):
            datetime_str = datetime_str.replace('Z', '+00:00')
        return datetime.fromisoformat(datetime_str)
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse datetime: {datetime_str} - {e}")
        return None


def parse_temporal_extent(extent: dict) -> Optional[dict]:
    """
    Parse temporal extent with start and end dates.
    
    Handles various input formats and validates date order.
    
    Args:
        extent: Dictionary with 'start' and 'end' keys
        
    Returns:
        Dictionary with parsed dates or None
    """
    if not extent:
        return None
    
    start = parse_date(extent.get('start'))
    end = parse_date(extent.get('end'))
    
    # Validate: start should be before end
    if start and end and start > end:
        logger.warning(f"Invalid temporal extent: start {start} after end {end}")
        return None
    
    if start or end:
        return {'start': start, 'end': end}
    
    return None
```

**Benefits:**

1. **DRY**: Date parsing logic in ONE place
2. **Consistency**: All extractors use same parsing
3. **Testability**: Easy to unit test in isolation
4. **Extensibility**: Add new formats in one place
5. **Validation**: Centralized validation logic

**Updated Extractor Usage:**

```python
# In any extractor
from ..utils.date_utils import parse_date, parse_datetime, parse_temporal_extent

class JSONExtractor(BaseExtractor):
    def _parse_data(self, raw_data: bytes) -> Dict[str, Any]:
        data = json.loads(raw_data.decode('utf-8'))
        
        return {
            # Use utility functions
            'publication_date': parse_date(data.get('publicationDate')),
            'metadata_date': parse_datetime(data.get('metadataDate')),
            'updated_date': parse_date(data.get('updatedDate')),
            'temporal_extent': parse_temporal_extent(data.get('temporalExtents', [{}])[0]),
        }
```

---

## Refactoring 2: Configuration Management

### Me:
We have configuration scattered across the codebase (database paths, model names, API URLs). How can we centralize configuration following best practices?

### Claude:
Excellent point! Let's implement proper configuration management using the **Settings Pattern**.

**Problem: Magic Strings Everywhere**

```python
# Scattered in code
DATABASE_PATH = 'data/ceh_metadata.db'
FAISS_INDEX_PATH = 'data/faiss_index.bin'
EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
```

**Solution: Pydantic Settings**

```python
# embeddings/config.py
"""
Configuration for embedding generation.
Uses Pydantic for validation and environment variable support.
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class EmbeddingConfig(BaseSettings):
    """
    Configuration for embedding generation and vector search.
    
    Can be configured via:
    1. Environment variables (e.g., EMBEDDING_MODEL_NAME)
    2. .env file
    3. Direct instantiation
    """
    
    # Model Configuration
    MODEL_NAME: str = Field(
        default='sentence-transformers/all-MiniLM-L6-v2',
        description="Sentence transformer model name"
    )
    
    # Processing Configuration
    BATCH_SIZE: int = Field(
        default=32,
        description="Batch size for embedding generation",
        ge=1,
        le=512
    )
    
    NORMALIZE_EMBEDDINGS: bool = Field(
        default=True,
        description="Normalize embeddings for cosine similarity"
    )
    
    # Content Configuration
    INCLUDE_TITLE: bool = Field(default=True, description="Include title in embeddings")
    INCLUDE_ABSTRACT: bool = Field(default=True, description="Include abstract in embeddings")
    INCLUDE_LINEAGE: bool = Field(default=True, description="Include lineage in embeddings")
    
    # Paths
    DATABASE_PATH: Path = Field(
        default=Path('data/ceh_metadata.db'),
        description="Path to SQLite database"
    )
    
    FAISS_INDEX_PATH: Path = Field(
        default=Path('data/faiss_index.bin'),
        description="Path to FAISS index file"
    )
    
    METADATA_PATH: Path = Field(
        default=Path('data/metadata.pkl'),
        description="Path to metadata pickle file"
    )
    
    DATA_DIR: Path = Field(
        default=Path('data'),
        description="Base data directory"
    )
    
    class Config:
        """Pydantic configuration."""
        env_prefix = 'EMBEDDING_'  # Environment variables start with EMBEDDING_
        env_file = '.env'
        env_file_encoding = 'utf-8'
    
    def ensure_data_dir(self) -> None:
        """Ensure data directory exists."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)


# API Configuration
# api/config.py
"""
FastAPI application configuration.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Application Info
    app_name: str = Field(default="CEH Dataset Discovery API", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    app_description: str = Field(
        default="Semantic search API for CEH datasets",
        description="Application description"
    )
    
    # API Configuration
    api_prefix: str = Field(default="/api/v1", description="API route prefix")
    debug: bool = Field(default=False, description="Debug mode")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",  # Alternative frontend port
        ],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///data/ceh_metadata.db",
        description="Database connection URL"
    )
    
    # Embedding Configuration
    faiss_index_path: str = Field(default="data/faiss_index.bin", description="FAISS index path")
    metadata_path: str = Field(default="data/metadata.pkl", description="Metadata pickle path")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model name"
    )
    
    class Config:
        """Pydantic configuration."""
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using @lru_cache ensures settings are loaded once and reused.
    """
    return Settings()
```

**Benefits:**

1. **Centralized**: All configuration in one place
2. **Validated**: Pydantic validates types and constraints
3. **Environment-aware**: Can override via environment variables
4. **Type-safe**: IDE autocomplete and type checking
5. **Testable**: Easy to inject test configurations
6. **Cached**: Singleton pattern via `@lru_cache`

**Usage:**

```python
# In any module
from embeddings.config import EmbeddingConfig

config = EmbeddingConfig()
model = SentenceTransformer(config.MODEL_NAME)
```

```python
# Override via environment
import os
os.environ['EMBEDDING_MODEL_NAME'] = 'custom-model'
config = EmbeddingConfig()  # Uses custom model
```

---

## Refactoring 3: Repository Mapping Complexity

### Me:
The repository's _to_db_model() method is over 100 lines and handles many concerns. How can we refactor this to be more maintainable?

### Claude:
Great observation! This violates the Single Responsibility Principle. Let's refactor using **private helper methods**.

**Problem: God Method**

```python
def _to_db_model(self, dataset: Dataset) -> DatasetModel:
    """Convert domain model to database model."""
    # Generate ID
    # Create dataset model
    # Handle spatial extent
    # Handle temporal extent
    # Convert contacts
    # Convert keywords
    # Convert relationships
    # Convert online resources
    # Convert metadata documents
    # ... 190+ lines!
```

**Solution: Extract Methods**

```python
class DatasetRepository:
    """Repository with clean, focused methods."""
    
    def _to_db_model(self, dataset: Dataset) -> DatasetModel:
        """
        Convert domain model to database model.
        
        Orchestrates conversion by delegating to specialized methods.
        """
        dataset_id = dataset.id or str(uuid4())
        
        # Create main dataset model
        db_dataset = self._create_dataset_model(dataset, dataset_id)
        
        # Map embedded objects (spatial/temporal)
        self._map_spatial_extent(dataset, db_dataset)
        self._map_temporal_extent(dataset, db_dataset)
        
        # Map one-to-many relationships
        self._map_contacts(dataset, db_dataset, dataset_id)
        self._map_keywords(dataset, db_dataset, dataset_id)
        self._map_relationships(dataset, db_dataset, dataset_id)
        self._map_online_resources(dataset, db_dataset, dataset_id)
        self._map_metadata_documents(dataset, db_dataset, dataset_id)
        
        return db_dataset
    
    def _create_dataset_model(self, dataset: Dataset, dataset_id: str) -> DatasetModel:
        """
        Create core DatasetModel with scalar fields.
        
        Handles simple field mapping only.
        """
        return DatasetModel(
            id=dataset_id,
            file_identifier=dataset.file_identifier,
            title=dataset.title,
            abstract=dataset.abstract,
            description=dataset.description,
            lineage=dataset.lineage,
            publication_date=dataset.publication_date,
            metadata_date=dataset.metadata_date,
            updated_date=dataset.updated_date,
            metadata_standard=dataset.metadata_standard,
            metadata_standard_version=dataset.metadata_standard_version,
            language=dataset.language,
            resource_status=dataset.resource_status,
            resource_type=dataset.resource_type,
            credit_text=dataset.credit_text,
            is_accessible_for_free=dataset.is_accessible_for_free,
            additional_metadata=dataset.additional_metadata,
        )
    
    def _map_spatial_extent(self, dataset: Dataset, db_dataset: DatasetModel) -> None:
        """Map spatial extent to flattened database columns."""
        if dataset.spatial_extent:
            db_dataset.spatial_west = str(dataset.spatial_extent.west)
            db_dataset.spatial_east = str(dataset.spatial_extent.east)
            db_dataset.spatial_south = str(dataset.spatial_extent.south)
            db_dataset.spatial_north = str(dataset.spatial_extent.north)
    
    def _map_temporal_extent(self, dataset: Dataset, db_dataset: DatasetModel) -> None:
        """Map temporal extent to database columns."""
        if dataset.temporal_extent:
            db_dataset.temporal_start = dataset.temporal_extent.start
            db_dataset.temporal_end = dataset.temporal_extent.end
    
    def _map_contacts(self, dataset: Dataset, db_dataset: DatasetModel, dataset_id: str) -> None:
        """Map contacts (one-to-many relationship)."""
        for contact in dataset.contacts:
            db_contact = ContactModel(
                id=str(uuid4()),
                dataset_id=dataset_id,
                family_name=contact.family_name,
                given_name=contact.given_name,
                full_name=contact.full_name,
                honorific_prefix=contact.honorific_prefix,
                organization_name=contact.organization_name,
                organization_identifier=contact.organization_identifier,
                email=contact.email,
                role=contact.role,
                name_identifier=contact.name_identifier,
                address=contact.address,
            )
            db_dataset.contacts.append(db_contact)
    
    def _map_keywords(self, dataset: Dataset, db_dataset: DatasetModel, dataset_id: str) -> None:
        """Map keywords (one-to-many relationship)."""
        for keyword in dataset.keywords:
            db_keyword = KeywordModel(
                id=str(uuid4()),
                dataset_id=dataset_id,
                keyword=keyword.keyword,
                keyword_type=keyword.keyword_type,
                uri=keyword.uri,
                in_defined_term_set=keyword.in_defined_term_set,
            )
            db_dataset.keywords.append(db_keyword)
    
    def _map_relationships(self, dataset: Dataset, db_dataset: DatasetModel, dataset_id: str) -> None:
        """Map dataset relationships (one-to-many)."""
        for relationship in dataset.relationships:
            db_rel = RelationshipModel(
                id=str(uuid4()),
                source_dataset_id=dataset_id,
                relation_type=relationship.relation_type,
                target_dataset_id=relationship.target_dataset_id
            )
            db_dataset.relationships.append(db_rel)
    
    def _map_online_resources(self, dataset: Dataset, db_dataset: DatasetModel, dataset_id: str) -> None:
        """Map online resources (one-to-many)."""
        for resource in dataset.online_resources:
            db_resource = OnlineResourceModel(
                id=str(uuid4()),
                dataset_id=dataset_id,
                url=resource.url,
                name=resource.name,
                description=resource.description,
                function=resource.function,
                resource_type=resource.resource_type
            )
            db_dataset.online_resources.append(db_resource)
    
    def _map_metadata_documents(self, dataset: Dataset, db_dataset: DatasetModel, dataset_id: str) -> None:
        """Map metadata documents (one-to-many)."""
        for doc in dataset.metadata_documents:
            db_doc = MetadataDocumentModel(
                id=str(uuid4()),
                dataset_id=dataset_id,
                format=doc.format,
                content=doc.content,
                file_size=doc.file_size,
                downloaded_at=doc.downloaded_at
            )
            db_dataset.metadata_documents.append(db_doc)
```

**Benefits:**

1. **Single Responsibility**: Each method has ONE job
2. **Readability**: Easy to understand what each method does
3. **Testability**: Can test each mapping method independently
4. **Maintainability**: Changes to contact mapping don't affect keywords
5. **Reusability**: Helper methods can be called from update operations
6. **Documentation**: Method names self-document purpose

**Testing Becomes Easier:**

```python
def test_map_contacts():
    """Test contact mapping in isolation."""
    repo = DatasetRepository(session)
    dataset = Dataset(contacts=[Contact(full_name="John Doe", role="author")])
    db_dataset = DatasetModel(id="test-id")
    
    repo._map_contacts(dataset, db_dataset, "test-id")
    
    assert len(db_dataset.contacts) == 1
    assert db_dataset.contacts[0].full_name == "John Doe"
```