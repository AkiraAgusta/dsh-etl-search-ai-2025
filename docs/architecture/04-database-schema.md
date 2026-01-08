# Database Schema Documentation

## Overview

The database uses **SQLite** with **SQLAlchemy ORM** for managing environmental dataset metadata from the CEH Catalogue Service. The schema is designed to support:

- **Multiple metadata formats** (XML, JSON, JSON-LD, RDF)
- **Complex relationships** between datasets
- **Semantic search** via embeddings
- **ISO 19115 compliance**

## Entity-Relationship Diagram

```
┌─────────────────┐
│    Datasets     │ ◄─────┐
│  (Core Entity)  │       │
└─────────────────┘       │
        │                 │
        │ 1               │
        │                 │
        ├─────────────────┼─── N ──►  ┌───────────────────┐
        │                 │           │     Contacts      │
        │                 │           └───────────────────┘
        │                 │
        ├─────────────────┼─── N ──►  ┌───────────────────┐
        │                 │           │     Keywords      │
        │                 │           └───────────────────┘
        │                 │
        ├─────────────────┼─── N ──►  ┌───────────────────┐
        │                 │           │   Relationships   │
        │                 │           └───────────────────┘
        │                 │
        ├─────────────────┼─── N ──►  ┌───────────────────┐
        │                 │           │  OnlineResources  │
        │                 │           └───────────────────┘
        │                 │
        ├─────────────────┼─── N ──►  ┌───────────────────┐
        │                 │           │ MetadataDocuments │
        │                 │           └───────────────────┘
        │                 │
        └─────────────────┴─── 1 ──►  ┌───────────────────┐
                                      │    Embeddings     │
                                      └───────────────────┘
```

**Why These Relationships**:
- **One-to-many**: Natural representation of repeating data (multiple contacts, keywords per dataset)
- **One-to-one**: Embedding is unique per dataset, separated for clarity
- **No many-to-many**: Not needed in current schema (keywords are per-dataset, not shared)

## Table Definitions

### 1. datasets (Core Table)

**Purpose**: Store primary dataset metadata

**Key Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID primary key |
| file_identifier | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | CEH dataset identifier |
| title | TEXT | NOT NULL | Dataset title |
| abstract | TEXT | | Dataset description/abstract |
| description | TEXT | | Additional description |
| lineage | TEXT | | Data provenance information |
| publication_date | DATE | | Date of publication |
| metadata_date | DATETIME | | Metadata creation/update date |
| spatial_west/east/south/north | VARCHAR(50) | | Bounding box coordinates |
| temporal_start/end | DATE | | Temporal coverage |
| credit_text | TEXT | | Formatted citation string |
| is_accessible_for_free | BOOLEAN | | Accessibility flag |
| additional_metadata | JSON | | Flexible storage for format-specific data |
| created_at | DATETIME | DEFAULT NOW | Record creation timestamp |
| updated_at | DATETIME | DEFAULT NOW, ON UPDATE | Record update timestamp |

**Design Decisions**:
- **UUID for id**: Ensures global uniqueness, enables distributed systems
- **file_identifier indexed**: Primary lookup field for performance
- **JSON column**: Stores format-specific extras without schema changes
- **Timestamps**: Audit trail for data changes

### 2. contacts (One-to-Many with datasets)

**Purpose**: Store contact information for dataset contributors

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(36) | UUID primary key |
| dataset_id | VARCHAR(36) | FK to datasets.id |
| family_name | VARCHAR(200) | Family/last name |
| given_name | VARCHAR(200) | Given/first name |
| full_name | VARCHAR(500) | Complete name |
| honorific_prefix | VARCHAR(50) | Title (Dr., Prof., etc.) |
| organization_name | VARCHAR(500) | Organization/institution |
| organization_identifier | VARCHAR(500) | RoR ID |
| email | VARCHAR(255) | Email address |
| role | VARCHAR(100) | Role (author, custodian, owner, etc.) - NOT NULL |
| name_identifier | VARCHAR(500) | ORCID or other researcher ID |
| address | JSON | Address information (structured JSON) |

**Design Decisions**:
- **Separate table**: Normalizes repeating contact data
- **CASCADE DELETE**: Removes contacts when dataset is deleted
- **RoR and ORCID support**: Modern research identifiers

### 3. keywords (One-to-Many with datasets)

**Purpose**: Store subject terms, themes, and categories

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(36) | UUID primary key |
| dataset_id | VARCHAR(36) | FK to datasets.id |
| keyword | VARCHAR(500) | Keyword/subject term |
| keyword_type | VARCHAR(50) | Type (theme, place, project, other) |
| uri | VARCHAR(500) | Ontology/vocabulary URI |
| in_defined_term_set | VARCHAR(500) | Vocabulary/controlled term set |

**Design Decisions**:
- **Separate table**: Enables many keywords per dataset
- **keyword_type**: Categorizes keywords for faceted search
- **uri field**: Links to ontologies (from RDF format)

### 4. relationships (One-to-Many with datasets)

**Purpose**: Model connections between datasets (parent-child, related, etc.)

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(36) | UUID primary key |
| source_dataset_id | VARCHAR(36) | FK to datasets.id |
| relation_type | VARCHAR(100) | Type (memberOf, relatedTo, supersedes, etc.) |
| target_dataset_id | VARCHAR(255) | Target dataset file identifier |

**Relationship Types**:
- `memberOf`: Dataset is part of a collection
- `relatedTo`: General relationship
- `supersedes`: Replaces another dataset
- `supersededBy`: Replaced by another dataset

**Design Decision**: Stores file_identifier (not id) for target to handle external references.

### 5. online_resources (One-to-Many with datasets)

**Purpose**: Store URLs for downloads, documentation, and related resources

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(36) | UUID primary key |
| dataset_id | VARCHAR(36) | FK to datasets.id |
| url | TEXT | Resource URL |
| name | VARCHAR(500) | Resource name/title |
| description | TEXT | Resource description |
| function | VARCHAR(100) | Function (download, information, etc.) |
| resource_type | VARCHAR(100) | Type (data, documentation, etc.) |

**Function Types**:
- `download`: Direct data download
- `information`: Additional information/documentation
- `fileAccess`: Web-accessible folder

### 6. metadata_documents (One-to-Many with datasets)

**Purpose**: Store raw metadata in original formats for reference

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(36) | UUID primary key |
| dataset_id | VARCHAR(36) | FK to datasets.id |
| format | VARCHAR(20) | Format (xml, json, jsonld, rdf) |
| content | TEXT | Raw document content |
| file_size | INTEGER | Content size in bytes |
| downloaded_at | DATETIME | Download timestamp |

**Format Values**:
- `xml`: ISO 19115 XML
- `json`: CEH JSON format
- `jsonld`: Schema.org JSON-LD
- `rdf`: RDF Turtle format

**Design Decision**: Preserves raw formats for reference, debugging, and potential re-processing.

### 7. embeddings (One-to-One with datasets)

**Purpose**: Store vector embeddings metadata for semantic search

**Key Columns**:

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(36) | UUID primary key |
| dataset_id | VARCHAR(36) | FK to datasets.id |
| embedding_model | VARCHAR(100) | Model name (e.g., "all-MiniLM-L6-v2") |
| embedding_dimension | INTEGER | Vector dimension (e.g., 384) |
| created_at | DATETIME | Creation timestamp |

**Note**: Actual embedding vectors stored in FAISS index file, not database.

**Design Decision**: Metadata in database for tracking, vectors in FAISS for performance.

## Indexes & Performance

### Primary Indexes
- All tables have UUID primary keys
- Foreign keys automatically indexed by SQLAlchemy

### Query Optimization Indexes
- `datasets.file_identifier`: Unique index for fast lookups
- All foreign key columns: Indexed for join performance

**Rationale**: These indexes cover primary query patterns (lookup by file_identifier, joins on dataset_id).

## Query Patterns

### 1. Get Dataset with All Related Data

```python
# Using SQLAlchemy with eager loading
dataset = session.query(DatasetModel).options(
    joinedload(DatasetModel.contacts),
    joinedload(DatasetModel.keywords),
    joinedload(DatasetModel.relationships),
    joinedload(DatasetModel.online_resources)
).filter_by(file_identifier=file_id).first()
```

**Why Eager Loading**: Avoids N+1 query problem, fetches all data in one round trip.

### 2. Search by Keywords

```python
# Find datasets with specific keyword
datasets = session.query(DatasetModel).join(KeywordModel).filter(
    KeywordModel.keyword.ilike('%climate%')
).all()
```

### 3. Filter by Date Range

```python
# Datasets published in a date range
datasets = session.query(DatasetModel).filter(
    DatasetModel.publication_date >= start_date,
    DatasetModel.publication_date <= end_date
).all()
```

## Data Integrity Constraints

### Referential Integrity
- All foreign keys use `CASCADE DELETE` to maintain consistency
- When a dataset is deleted, all related records are automatically removed

### Business Rules (Enforced in Application Layer)
1. `file_identifier` must be unique across all datasets
2. `title` cannot be empty
3. `role` in contacts must be from valid set
4. At least one metadata format must be present per dataset

### Data Validation

```python
class DatasetRepository:
    def add(self, dataset: Dataset) -> None:
        # Validate before insert
        if not dataset.title or not dataset.title.strip():
            raise ValueError("Dataset title is required")
        
        if not dataset.file_identifier:
            raise ValueError("File identifier is required")
        
        # Check uniqueness
        existing = self.get_by_file_identifier(dataset.file_identifier)
        if existing:
            raise ValueError(f"Dataset {dataset.file_identifier} already exists")
        
        # Proceed with insert
        db_dataset = self._to_model(dataset)
        self.session.add(db_dataset)
```

**Rationale**: Application-level validation provides clear error messages and business rule enforcement.

## Schema Design Rationale

### Normalization Level: 3NF

The schema follows **Third Normal Form (3NF)**:
- **1NF**: All attributes are atomic (no multi-valued attributes)
- **2NF**: No partial dependencies (all non-key attributes depend on entire primary key)
- **3NF**: No transitive dependencies (non-key attributes don't depend on other non-key attributes)

**Why 3NF**: Balances data integrity with query performance. Avoids update anomalies while maintaining reasonable join complexity.

### Denormalization Choices

**additional_metadata (JSON column)**:
- Stores format-specific fields that don't warrant separate columns
- Flexibility without schema migrations
- Trade-off: Not indexed, but acceptable for infrequently queried data

**spatial extent as separate columns**:
- Could be JSON, but separate columns enable direct filtering
- Performance over flexibility for commonly queried spatial bounds

**Rationale**: Strategic denormalization for query performance on frequently accessed fields.

### Why SQLite?

**Chosen for**:
- Zero configuration
- Single file portability
- Sufficient for 200 datasets
- Simple deployment

**Trade-offs**:
- Limited concurrent writes (acceptable for read-heavy workload)
- No built-in full-text search (using FAISS instead for semantic search)
- Size limits (not a concern for this scale)

**Rationale**: Simplicity and ease of evaluation outweigh limitations for prototype.