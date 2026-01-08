# DSH ETL Search AI 2025

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg)](https://fastapi.tiangolo.com/)
[![Svelte](https://img.shields.io/badge/Svelte-4.2-FF3E00.svg)](https://svelte.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57.svg)](https://www.sqlite.org/)

A full-stack semantic search and discovery system for environmental datasets from the CEH (Centre for Ecology & Hydrology) Catalogue Service.

## Project Overview

This project demonstrates professional software engineering practices by implementing a complete data pipeline and search system that:

- **Extracts** metadata from multiple standardized formats (ISO 19115 XML, JSON, JSON-LD, RDF)
- **Transforms** and intelligently merges data from diverse sources
- **Loads** structured data into a relational database
- **Generates** semantic embeddings for AI-powered search
- **Provides** a modern web interface for dataset discovery

## Key Features

### ETL Pipeline
- Multi-format metadata extraction (XML, JSON, JSON-LD, RDF Turtle)
- Intelligent data merging with format-specific extractors
- Robust error handling with graceful degradation
- Clean architecture with Repository and Strategy patterns

### Semantic Search
- AI-powered semantic search using Sentence Transformers
- FAISS vector index for fast similarity search
- Hybrid search combining semantic and keyword filtering
- 384-dimensional embeddings for precise matching

### REST API
- FastAPI backend with auto-generated OpenAPI documentation
- Semantic and combined search endpoints
- Dataset CRUD operations
- Statistics and health check endpoints

### Web Interface
- Modern SvelteKit frontend with TailwindCSS
- Responsive search interface
- Advanced filtering (keywords, date range, spatial bounds)
- Dataset detail views with rich metadata

## Architecture

### System Design
```
┌─────────────────────────────────────────────────────────┐
│                  Presentation Layer                     │
│              (SvelteKit + TailwindCSS)                  │
└─────────────────────────────────────────────────────────┘
                        ↓ HTTP/REST
┌─────────────────────────────────────────────────────────┐
│                 Application Layer                       │
│                 (FastAPI + Python)                      │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                   Data Layer                            │
│           SQLite + FAISS Vector Store                   │
└─────────────────────────────────────────────────────────┘
```

<details>
<summary><b>Detailed Technology Stack (click to expand)</b></summary>

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI 0.109
- **Database**: SQLite with SQLAlchemy ORM
- **Vector Store**: FAISS (CPU)
- **ML Models**: Sentence Transformers (all-MiniLM-L6-v2)
- **Logging**: Loguru

### Frontend
- **Framework**: SvelteKit 2.0
- **Styling**: TailwindCSS 3.4
- **HTTP Client**: Axios
- **Build Tool**: Vite 5.0

### Data Processing
- **XML Parsing**: lxml with XPath
- **JSON/JSON-LD**: Native JSON parsing
- **RDF Processing**: rdflib with SPARQL
- **Web Scraping**: Requests, BeautifulSoup

</details>

## Quick Start

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18 or higher
- **Git**: For cloning the repository

### 1. Clone Repository

```bash
git clone https://github.com/AkiraAgusta/dsh-etl-search-ai-2025.git
cd dsh-etl-search-ai-2025
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run ETL pipeline (creates database & tables automatically)
python scripts/run_etl.py

# Create performance indexes
python scripts/setup_database.py

# Generate embeddings
python scripts/generate_embeddings.py

# Start API server
python scripts/start_api.py
```

Backend API will be available at: **http://localhost:8000**  
API Documentation: **http://localhost:8000/docs**

### 3. Frontend Setup

```bash
# Navigate to frontend directory (from root)
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: **http://localhost:3000**

### 4. Access the Application

1. Open browser to **http://localhost:3000**
2. Use the search bar to find datasets
3. Apply filters for refined results
4. View dataset details by clicking on results

<details>
<summary><b>Project Structure (click to expand)</b></summary>

```
dsh-etl-search-ai-2025/
├── backend/                    # Python backend
│   ├── api/                    # FastAPI application
│   ├── etl/                    # ETL pipeline
│   │   ├── extractors/         # Format-specific extractors
│   │   ├── models/             # Domain and database models
│   │   └── repositories/       # Data access layer
│   ├── embeddings/             # Semantic search engine
│   ├── database/               # Database initialization
│   ├── scripts/                # Utility scripts
│   └── requirements.txt        # Python dependencies
│
├── frontend/                   # SvelteKit frontend
│   ├── src/
│   │   ├── lib/                # Reusable components
│   │   │   ├── components/     # UI components
│   │   │   ├── stores/         # State management
│   │   │   ├── api/            # Backend API client
│   │   │   └── utils/          # Utility functions
│   │   └── routes/             # SvelteKit pages
│   └── package.json            # Node dependencies
│
└── docs/                       # Documentation
    ├── architecture/           # System architecture docs
    └── ai-conversation/        # LLM interaction logs
```

</details>

## Documentation

### Comprehensive Documentation

- **[Backend Documentation](./backend/README.md)** - Backend setup, API reference, ETL usage
- **[Frontend Documentation](./frontend/README.md)** - Frontend setup, development guide

### Architecture Documents

1. **[System Overview](./docs/architecture/01-system-overview.md)** - High-level architecture
2. **[Backend Architecture](./docs/architecture/02-backend-architecture.md)** - Backend design patterns
3. **[Frontend Architecture](./docs/architecture/03-frontend-architecture.md)** - Frontend component design
4. **[Database Schema](./docs/architecture/04-database-schema.md)** - Complete data model
5. **[Data Flow](./docs/architecture/05-data-flow.md)** - System integration and flows

## Design Patterns Demonstrated

This project demonstrates professional software engineering through:

### Clean Architecture
- **Domain Layer**: Business logic independent of frameworks
- **Application Layer**: Use case orchestration
- **Infrastructure Layer**: External services and persistence
- **Presentation Layer**: API and UI

### Design Patterns
- **Template Method**: Common extraction workflow with format-specific implementations
- **Strategy Pattern**: Interchangeable parsing strategies for different metadata formats
- **Repository Pattern**: Data access abstraction separating domain from persistence
- **Dependency Injection**: Loose coupling via FastAPI dependencies

### SOLID Principles
- **Single Responsibility**: Each class has one clear purpose
- **Open/Closed**: Extensible without modification (e.g., adding new format extractors)
- **Liskov Substitution**: Extractors are interchangeable
- **Interface Segregation**: Clean interfaces (IExtractor)
- **Dependency Inversion**: Depend on abstractions, not concretions

## Key Technical Achievements

### Multi-Format ETL
- Extracts from 4 different metadata standards
- Intelligent merging prioritizes richest data sources
- Graceful degradation when formats fail
- Stores both structured data and raw documents

### Semantic Search
- Sentence Transformers for query encoding
- FAISS for efficient similarity search
- Hybrid search combining semantic and keyword filters
- Sub-100ms search latency

<details>
<summary><b>Database Schema Overview (click to expand)</b></summary>

The system uses SQLite with the following key tables:

- **datasets** - Core dataset metadata
- **contacts** - Author and organization information
- **keywords** - Subject terms and themes
- **relationships** - Dataset relationships (memberOf, relatedTo)
- **online_resources** - Download links and documentation
- **metadata_documents** - Raw metadata in original formats
- **embeddings** - Vector embedding metadata

See [Database Schema Documentation](./docs/architecture/04-database-schema.md) for complete details.

</details>

<details>
<summary><b>API Endpoints Overview (click to expand)</b></summary>

### Search Endpoints
- `POST /api/search/semantic` - Semantic search with natural language
- `POST /api/search/semantic/enriched` - Semantic search with full database metadata
- `POST /api/search/hybrid` - Hybrid search with filters

### Dataset Endpoints
- `GET /api/datasets` - List datasets with pagination
- `GET /api/datasets/{dataset_id}` - Get dataset details
- `GET /api/datasets/{dataset_id}/keywords` - Get dataset keywords
- `GET /api/datasets/{dataset_id}/contacts` - Get dataset contacts
- `GET /api/datasets/{dataset_id}/resources` - Get online resources
- `GET /api/datasets/{dataset_id}/metadata` - Get raw metadata documents

### Utility Endpoints
- `GET /api/stats` - System statistics
- `GET /api/health` - Health check

Full API documentation: **http://localhost:8000/docs** (when backend is running)

</details>

## Evaluation Criteria Addressed

This project demonstrates competency in:

### Software Architecture
- Three-tier architecture (Presentation, Application, Data)
- Clean architecture with clear separation of concerns
- Modular design for maintainability and extensibility

### Software Engineering
- Design patterns (Template Method, Strategy, Repository, DI)
- SOLID principles
- Error handling and logging
- Configuration management

### Good Coding Practices
- Type hints throughout Python code
- Comprehensive docstrings
- Consistent naming conventions
- Code organization and modularity

### Object-Oriented Design
- Inheritance hierarchies (BaseExtractor → Format-specific extractors)
- Polymorphism (interchangeable extractors)
- Encapsulation (private methods, clear interfaces)
- Abstraction (IExtractor interface)

### Clean Architecture
- Domain logic independent of frameworks
- Dependency inversion
- Testable components
- Clear layer boundaries

## AI-Assisted Development

This project was developed using LLM assistance (Claude) to demonstrate:

- Effective prompting for architecture decisions
- Guiding AI to generate clean, maintainable code
- Iterative refinement based on software engineering principles
- Code review and refactoring with AI assistance

**LLM Conversation Logs**: See `/docs/ai-conversation/` for complete interaction history.

## Author

- **Candidate**: Akira Agusta
- **Email**: <akiraagusta@gmail.com>
- **GitHub**: <https://github.com/AkiraAgusta>

## Acknowledgments

- **CEH Catalogue Service** for providing the metadata
- **Centre for Ecology & Hydrology** for dataset documentation
- **Anthropic** for AI assistance during development
- **DSH Team** for the evaluation opportunity