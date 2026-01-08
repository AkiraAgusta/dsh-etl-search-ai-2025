# Backend

Python backend implementing ETL pipelines, semantic search, and RESTful API for environmental dataset discovery.

## Overview

The backend provides three main subsystems:

1. **ETL Pipeline**: Extracts metadata from CEH Catalogue in 4 formats (XML, JSON, JSON-LD, RDF)
2. **Semantic Search**: Generates embeddings and provides similarity search using FAISS
3. **REST API**: Exposes search and dataset operations via FastAPI

<details>
<summary><b>Technology Stack Details (click to expand)</b></summary>

- **Python**: 3.11+
- **Framework**: FastAPI 0.109
- **ORM**: SQLAlchemy 2.0
- **Database**: SQLite 3
- **Vector Store**: FAISS (CPU)
- **ML Framework**: Sentence Transformers 2.3
- **Logging**: Loguru
- **HTTP Client**: Requests
- **XML/RDF Parsing**: lxml, rdflib, BeautifulSoup4

</details>

## Prerequisites

Before starting, ensure you have:

- **Python 3.11 or higher**
  ```bash
  python --version  # Should show Python 3.11.x or higher
  ```

- **pip** (Python package manager)
  ```bash
  pip --version
  ```

- **Virtual environment support** (recommended)
- **Internet connection** (for downloading datasets and models)

## Installation

### 1. Navigate to Backend Directory

```bash
cd backend
```

### 2. Create Virtual Environment

**Linux/macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs all required packages including FastAPI, SQLAlchemy, FAISS, Sentence Transformers, and more.

**Note**: First-time installation may take 5-10 minutes as it downloads ML models.

### 4. Verify Installation

```bash
python -c "import fastapi, sqlalchemy, faiss, sentence_transformers; print('All dependencies installed successfully')"
```

<details>
<summary><b>Configuration Options (click to expand)</b></summary>

### Environment Variables

The backend uses default configuration, but you can customize via environment variables:

**Database:**
```bash
export DATABASE_URL="sqlite:///./data/ceh_datasets.db"
```

**FAISS Index:**
```bash
export FAISS_INDEX_PATH="./data/faiss_index.bin"
export ID_MAP_PATH="./data/id_map.pkl"
```

**Embedding Model:**
```bash
export EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
```

**API Settings:**
```bash
export API_HOST="0.0.0.0"
export API_PORT="8000"
export DEBUG="true"
```

### Configuration File

Default settings are in `api/config.py`:

```python
class Settings(BaseSettings):
    app_name: str = "CEH Dataset Search API"
    database_url: str = "sqlite:///./data/ceh_datasets.db"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    faiss_index_path: str = "./data/faiss_index.bin"
    # ... more settings
```

</details>

## ETL & Database Pipeline

### Running ETL

```bash
python scripts/run_etl.py
```

<details>
<summary><b>ETL Process Details (click to expand)</b></summary>

### ETL Data Flow

```
CEH Catalogue (HTTPS)
        ↓
Format-Specific Extractors
  ├── XMLExtractor (ISO 19115)
  ├── JSONExtractor (CEH JSON)
  ├── JSONLDExtractor (Schema.org)
  └── RDFExtractor (Turtle)
        ↓
    Merge Logic
        ↓
   Domain Models
        ↓
  Repository Layer
        ↓
  SQLite Database
```

### File Identifier List

The `metadata-file-identifiers.txt` file contains CEH dataset identifiers, one per line:

```
69a6c6e8-afb4-4f6e-b8da-86d28f543a9f
a1b2c3d4-e5f6-7890-1234-567890abcdef
...
```

</details>

### Create Performance Indexes

```bash
python scripts/setup_database.py
```

### Generating Embeddings

```bash
python scripts/generate_embeddings.py
```

### Verify Embeddings

```bash
python scripts/test_search.py
```

## Running the API

### Development Server

```bash
python scripts/start_api.py
```

**Expected output:**
```
======================================================================
Starting CEH Dataset Search API v1.0.0
======================================================================
Database: sqlite:///./data/ceh_datasets.db
FAISS Index: ./data/faiss_index.bin
API is ready to accept requests
Documentation available at: /docs
======================================================================

INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Access the API

- **API Base URL**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## API Documentation

### Quick Reference

**Search Operations:**
- `POST /api/search/semantic` - Semantic search with natural language
- `POST /api/search/semantic/enriched` - Semantic search with full database metadata
- `POST /api/search/hybrid` - Hybrid search with filters

**Dataset Operations:**
- `GET /api/datasets` - List datasets with pagination
- `GET /api/datasets/{dataset_id}` - Get dataset details
- `GET /api/datasets/{dataset_id}/keywords` - Get dataset keywords
- `GET /api/datasets/{dataset_id}/contacts` - Get dataset contacts
- `GET /api/datasets/{dataset_id}/resources` - Get online resources
- `GET /api/datasets/{dataset_id}/metadata` - Get raw metadata documents

**Health & Utility:**
- `GET /api/stats` - System statistics
- `GET /api/health` - Health check

<details>
<summary><b>Detailed API Examples (click to expand)</b></summary>

### GET /api/datasets

Query Parameters:
- `limit` (int): Max results (default: 20)
- `offset` (int): Skip results (default: 0)
- `keywords` (str): Filter by keywords (comma-separated)
- `date_from` (date): Publication date from
- `date_to` (date): Publication date to

**Example:**
```bash
curl "http://localhost:8000/api/datasets?limit=10&keywords=climate,hydrology"
```

**Response:**
```json
{
  "datasets": [
    {
      "id": "uuid",
      "file_identifier": "...",
      "title": "Dataset Title",
      "abstract": "Description...",
      "publication_date": "2015-09-30",
      "keywords": [...],
      "contacts": [...]
    }
  ],
  "total": 195,
  "page": 1,
  "limit": 10
}
```

### POST /api/search/semantic

**Request:**
```json
{
  "query": "climate change impacts on UK hydrology",
  "top_k": 10
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/search/semantic" \
  -H "Content-Type: application/json" \
  -d '{"query": "climate change hydrology", "top_k": 10}'
```

**Response:**
```json
{
  "results": [
    {
      "dataset": {...},
      "score": 0.89,
      "rank": 1
    }
  ],
  "query": "climate change hydrology",
  "total": 10,
  "search_time_ms": 45.2
}
```

### Using the API from Python

```python
import requests

# Semantic search
response = requests.post(
    "http://localhost:8000/api/search/semantic",
    json={"query": "climate data UK", "top_k": 5}
)
results = response.json()

# Get dataset details
dataset_id = results['results'][0]['dataset']['id']
response = requests.get(f"http://localhost:8000/api/datasets/{dataset_id}")
dataset = response.json()
```

</details>

## 📂 Project Structure

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

## Architecture

### Design Patterns

The backend demonstrates several key design patterns:

**Template Method** - `BaseExtractor` defines extraction workflow
```python
class BaseExtractor:
    def extract(self, source: str):     # Template method
        raw = self._fetch_data(source)
        parsed = self._parse_data(raw)  # Implemented by subclasses
        return self.validate(parsed)
```

**Strategy Pattern** - Format-specific extractors
```python
xml_extractor = XMLExtractor()
json_extractor = JSONExtractor()
# Both implement IExtractor interface
```

**Repository Pattern** - Data access abstraction
```python
repository = DatasetRepository(session)
dataset = repository.get_by_id(id)
repository.add(dataset)
```

**Dependency Injection** - FastAPI dependencies
```python
@router.get("/datasets")
def list_datasets(db: Session = Depends(get_db)):
    # db is injected automatically
```

### Clean Architecture Layers

1. **Domain**: `etl/models/dataset.py` (business logic)
2. **Application**: `etl/pipeline.py` (use cases)
3. **Infrastructure**: `etl/extractors/`, `etl/repositories/` (external services)
4. **Presentation**: `api/routes/` (HTTP interface)

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [FAISS Wiki](https://github.com/facebookresearch/faiss/wiki)
- [Sentence Transformers](https://www.sbert.net/)
- [CEH Catalogue API](https://catalogue.ceh.ac.uk/eidc/documents)