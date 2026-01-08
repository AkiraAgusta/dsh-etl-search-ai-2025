# Data Flow & System Integration

## Overview

This document describes how data flows through the DSH ETL Search AI system, from extraction at the CEH Catalogue to presentation in the user interface. It covers all major processes, data transformations, and integration points.

## High-Level Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    CEH Catalogue Service                     │
│  - XML (ISO 19115)                                           │
│  - JSON (CEH Format)                                         │
│  - JSON-LD (Schema.org)                                      │
│  - RDF (Turtle)                                              │
└──────────────────────────────────────────────────────────────┘
                            ↓ HTTP GET
┌──────────────────────────────────────────────────────────────┐
│                      ETL Pipeline                            │
│  1. Extract → 2. Parse → 3. Merge → 4. Validate              │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│                    SQLite Database                           │
│  - Structured metadata (tables)                              │
│  - Raw documents (metadata_documents)                        │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│                  Embedding Generation                        │
│  1. Fetch datasets → 2. Generate embeddings → 3. Build index │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│                     FAISS Vector Index                       │
│  - 384-dimensional embeddings                                │
│  - Fast similarity search                                    │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│                       FastAPI Server                         │
│  - Search endpoints                                          │
│  - Dataset CRUD endpoints                                    │
│  - Statistics endpoints                                      │
└──────────────────────────────────────────────────────────────┘
                            ↓ HTTP REST
┌──────────────────────────────────────────────────────────────┐
│                    SvelteKit Frontend                        │
│  - Search interface                                          │
│  - Results display                                           │
│  - Filter controls                                           │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│                          User                                │
└──────────────────────────────────────────────────────────────┘
```

## Detailed Process Flows

### 1. ETL Process Flow

**Trigger**: Manual execution via `python scripts/run_etl.py`

#### Step 1: Dataset Identification
```
Input: List of file identifiers
Source: metadata-file-identifiers.txt

Process:
1. Read file identifiers from file
2. For each identifier:
   - Construct URLs for all 4 formats
   - Add to processing queue

Output: Queue of (file_identifier, format_urls) tuples
```

#### Step 2: Multi-Format Extraction
```
Input: file_identifier
URLs:
  - XML:     https://catalogue.ceh.ac.uk/documents/{id}.xml
  - JSON:    https://catalogue.ceh.ac.uk/documents/{id}?format=json
  - JSON-LD: https://catalogue.ceh.ac.uk/documents/{id}?format=schema.org
  - RDF:     https://catalogue.ceh.ac.uk/documents/{id}?format=ttl

Process (Parallel):
┌─────────────────────────────────────────────────────┐
│ FOR EACH FORMAT:                                    │
│   1. Fetch raw data (HTTP GET with retries)         │
│   2. Parse using format-specific extractor          │
│   3. Extract key fields                             │
│   4. Validate extracted data                        │
│   5. Return parsed data or None (on failure)        │
└─────────────────────────────────────────────────────┘

Output: Dict with keys {xml_data, json_data, jsonld_data, rdf_data}
```

<details>
<summary><b>Extraction Details by Format (click to expand)</b></summary>

### XML (ISO 19115)
```python
Input: XML bytes
Parser: lxml with XPath
Namespaces: gmd, gco, gml

Extracted Fields:
  - title: //gmd:title/gco:CharacterString
  - abstract: //gmd:abstract/gco:CharacterString
  - contacts: //gmd:CI_ResponsibleParty
  - keywords: //gmd:MD_Keywords/gmd:keyword
  - spatial_extent: //gmd:EX_GeographicBoundingBox
  - temporal_extent: //gmd:EX_TemporalExtent
  - online_resources: //gmd:CI_OnlineResource

Output: Structured dict with extracted fields
```

### JSON (CEH Format)
```python
Input: JSON bytes
Parser: json.loads()

Extracted Fields:
  - title: data['title']
  - description: data['description']
  - contacts: data['individualName'], data['organisationName']
  - keywords: data['keywords']
  - relationships: data['relationships']
  - boundingBox: data['boundingBox']

Output: Dict with CEH-specific structure
```

### JSON-LD (Schema.org)
```python
Input: JSON-LD bytes
Parser: json.loads() with @context awareness

Extracted Fields:
  - name: data['name']
  - description: data['description']
  - creator: data['creator']
  - keywords: data['keywords']
  - creditText: data['creditText']
  - isAccessibleForFree: data['isAccessibleForFree']

Output: Dict with Schema.org properties
```

### RDF (Turtle)
```python
Input: Turtle bytes
Parser: rdflib.Graph

Extracted Fields (SPARQL Queries):
  - title: SELECT ?title WHERE { ?dataset dct:title ?title }
  - description: SELECT ?desc WHERE { ?dataset dct:description ?desc }
  - keywords: SELECT ?kw WHERE { ?dataset dcat:keyword ?kw }
  - spatial: SELECT ?spatial WHERE { ?dataset dct:spatial ?spatial }

Output: Dict with RDF triple-extracted data
```

</details>

#### Step 3: Data Merging Strategy
```python
Input: {xml_data, json_data, jsonld_data, rdf_data}

Merging Rules (Priority Order):
1. Title: JSON → JSON-LD → XML → RDF (first non-empty)
2. Abstract: JSON → JSON-LD → XML → RDF
3. Contacts: MERGE all formats (deduplicate by email/name)
4. Keywords: MERGE all formats (deduplicate, keep URIs from RDF)
5. Spatial Extent: JSON → XML → JSON-LD (JSON most complete in practice)
6. Temporal Extent: JSON → XML
7. Relationships: JSON (most detailed)
8. Citation: JSON-LD (creditText) → RDF → construct from contacts
9. Online Resources: XML → JSON

Merge Algorithm:
def coalesce(*values):
    """Return first non-None value."""
    return next((v for v in values if v is not None), None)

def merge_all_formats(xml, json, jsonld, rdf, file_identifier):
    dataset = Dataset()
    
    # Core fields (with fallback chain) - JSON preferred
    dataset.title = coalesce(
        json.get('title') if json else None,
        jsonld.get('title') if jsonld else None,
        xml.get('title') if xml else None,
        rdf.get('title') if rdf else None
    )
    
    dataset.abstract = coalesce(
        json.get('abstract') if json else None,
        jsonld.get('abstract') if jsonld else None,
        xml.get('abstract') if xml else None,
        rdf.get('abstract') if rdf else None
    )
    
    # Contacts (merge from all sources)
    contacts = []
    if xml: contacts.extend(xml.get('contacts', []))
    if json: contacts.extend(json.get('contacts', []))
    if jsonld: contacts.extend(jsonld.get('creator', []))
    dataset.contacts = deduplicate_contacts(contacts)
    
    # Keywords (merge and enrich with URIs from RDF)
    keywords = merge_keywords(
        xml.get('keywords', []) if xml else [],
        json.get('keywords', []) if json else [],
        rdf.get('keywords', []) if rdf else []  # RDF has ontology URIs
    )
    dataset.keywords = keywords
    
    # Citation from JSON-LD or RDF
    dataset.credit_text = coalesce(
        jsonld.get('credit_text') if jsonld else None,
        rdf.get('bibliographic_citation') if rdf else None
    )
    
    return dataset

Output: Single Dataset object with merged data
```

**Rationale**: Maximizes data completeness by leveraging strengths of each format.

#### Step 4: Persistence
```
Input: Dataset object

Process:
1. Convert domain model to SQLAlchemy model
2. Begin database transaction
3. Insert main dataset record
4. Insert related records (contacts, keywords, etc.)
5. Store raw documents in metadata_documents table
6. Commit transaction

On Error:
  - Rollback transaction
  - Log error with file_identifier
  - Continue to next dataset (graceful degradation)

Output: Persisted dataset in database
```

**Rationale**: Atomic transactions ensure data consistency, error handling enables continuation despite individual failures.

#### Step 5: Batch Processing
```
Input: List of file identifiers

Process:
FOR EACH file_identifier IN batch:
    result = pipeline.process_dataset(file_identifier)
    
    IF result:
        success_count += 1
        LOG: "Success: {file_identifier}"
    ELSE:
        failure_count += 1
        LOG: "Failed: {file_identifier}"
    
    LOG: "Progress: {success_count}/{total}"

Output: 
  - success_count: Number successfully processed
  - failure_count: Number of failures
  - error_log: List of failed file identifiers
```

### 2. Embedding Generation Flow

**Trigger**: After ETL completes, run `python scripts/generate_embeddings.py`

#### Step 1: Data Preparation
```
Input: SQLite database with datasets

Process:
1. Query all datasets with title, abstract, lineage
   SQL: SELECT id, file_identifier, title, abstract, lineage FROM datasets
2. For each dataset, combine text fields:
   text = f"{title}. {abstract}"
   NOTE: Lineage is available but NOT included by default (configurable)
3. Clean text (handled by sentence transformer)

Output: List of (dataset_id, combined_text) tuples
```

**Rationale**: Combining title and abstract provides rich context for semantic search. Lineage can be verbose and is disabled by default (but configurable via INCLUDE_LINEAGE setting).

#### Step 2: Embedding Generation
```
Input: List of (dataset_id, text) tuples

Process:
1. Load sentence transformer model
   Model: sentence-transformers/all-MiniLM-L6-v2
   Dimension: 384
   
2. Batch encode texts with built-in normalization
   embeddings = model.encode(
       texts, 
       batch_size=32,
       show_progress_bar=True,
       normalize_embeddings=True  # L2 normalization for cosine similarity
   )

Output: 
  - embeddings: numpy array (N, 384) - already normalized
  - dataset_ids: list mapping index → dataset_id
```

**Rationale**: Batch encoding improves performance. Built-in normalization by sentence-transformers library enables cosine similarity via inner product.

#### Step 3: FAISS Index Creation
```
Input: embeddings array, dataset_ids list

Process:
1. Create FAISS index (type depends on normalization)
   if normalize_embeddings:
       index = faiss.IndexFlatIP(dimension=384)  # Inner product (cosine for normalized)
   else:
       index = faiss.IndexFlatL2(dimension=384)  # L2 distance
   
   # Since NORMALIZE_EMBEDDINGS = True by default, we use IndexFlatIP
   
2. Add vectors to index
   index.add(embeddings.astype('float32'))
   
3. Save index to disk
   faiss.write_index(index, "data/faiss_index.bin")
   
4. Save metadata mapping
   metadata = {
       'dataset_ids': dataset_ids,
       'file_identifiers': file_identifiers,
       'metadata': [{'id': ..., 'title': ..., 'abstract': ...}],
       'model_name': 'all-MiniLM-L6-v2',
       'total_datasets': len(datasets)
   }
   with open("data/dataset_mapping.pkl", "wb") as f:
       pickle.dump(metadata, f)

Output: 
  - faiss_index.bin: Binary FAISS index file (IndexFlatIP)
  - dataset_mapping.pkl: Dataset metadata and ID mappings
```

**Rationale**: IndexFlatIP with normalized vectors enables fast cosine similarity search via inner product. Exact search (no approximation) is sufficient for ~200 datasets.

### 3. Search Request Flow

**Trigger**: User submits search query in frontend

#### Frontend Search Initiation
```
User Action: Types query + clicks "Search"

Process (Frontend):
1. User types query: "climate change impacts UK"
2. Click search button
3. Set loading state: isSearching = true
4. Clear previous results: searchResults = []
5. Call API:
   POST /api/search/semantic
   Body: { query: "climate change impacts UK", top_k: 10 }

Request Flow:
  Browser → API Client (axios) → Backend API
```

#### Backend Search Processing
```
Input: POST /api/search/semantic
Body: { query: string, top_k: int }

Process:
1. Validate request (Pydantic)
   - query must be 1-500 chars
   - top_k must be 1-100
   
2. Load search engine dependencies
   - Load FAISS index from disk (if not cached)
   - Load sentence transformer model
   - Load ID mapping
   
3. Generate query embedding
   query_vector = model.encode([query])[0]
   query_vector = normalize(query_vector)
   
4. Search FAISS index
   distances, indices = index.search(
       query_vector.reshape(1, -1),
       k=top_k
   )
   
5. Map indices to dataset IDs
   dataset_ids = [id_map[idx] for idx in indices[0]]
   
6. Fetch full metadata from database
   datasets = [repository.get_by_id(id) for id in dataset_ids]
   
7. Calculate relevance scores
   scores = [1 / (1 + distance) for distance in distances[0]]
   
8. Format response
   results = [
       {
           'dataset': serialize(dataset),
           'score': score,
           'rank': i + 1
       }
       for i, (dataset, score) in enumerate(zip(datasets, scores))
   ]

Output: JSON response
{
  "results": [...],
  "query": "climate change impacts UK",
  "total": 10,
  "search_time_ms": 45.2
}
```

**Rationale**: Two-stage process (vector search → database lookup) optimizes both speed and completeness.

#### Frontend Result Display
```
Input: API response with results

Process:
1. Update state
   searchResults.set(response.results)
   isSearching.set(false)
   
2. Render results
   FOR EACH result IN results:
       Render <ResultCard
         dataset={result.dataset}
         score={result.score}
         rank={result.rank}
       />
   
3. Update UI
   - Display result count
   - Show search time
   - Enable filters

Output: Rendered search results page
```

### 4. Filtered Search Flow

**Trigger**: User applies filters after initial search

<details>
<summary><b>Filter Application Details (click to expand)</b></summary>

#### Filter Application
```
User Action: Selects keywords, date range

Process (Frontend):
1. User selects filters:
   - Keywords: ["climate", "hydrology"]
   - Date range: [2010-01-01, 2020-12-31]
   - Spatial bounds: {west: -10, east: 2, south: 50, north: 60}
   
2. Update filter state:
   activeFilters.update({
       keywords: ["climate", "hydrology"],
       dateRange: [2010, 2020],
       spatialBounds: {...}
   })
   
3. Call combined search API:
   POST /api/search/combined
   Body: {
       query: "original query",
       filters: {
           keywords: ["climate", "hydrology"],
           date_range: ["2010-01-01", "2020-12-31"],
           spatial_bounds: {...}
       }
   }
```

#### Backend Filtered Search
```
Input: Query + Filters

Process:
1. Perform semantic search (broad, k=100)
   initial_results = semantic_search(query, top_k=100)
   
2. Apply keyword filter
   IF filters.keywords:
       filtered = [
           r for r in initial_results
           if any(keyword.lower() in r.title.lower() 
                  for keyword in filters.keywords)
       ]
   
3. Apply date range filter
   IF filters.date_range:
       start, end = filters.date_range
       filtered = [
           r for r in filtered
           if start <= r.publication_date <= end
       ]
   
4. Apply spatial filter
   IF filters.spatial_bounds:
       filtered = [
           r for r in filtered
           if intersects(r.spatial_extent, filters.spatial_bounds)
       ]
   
5. Re-rank and limit
   results = filtered[:20]  # Top 20 after filtering

Output: Filtered and ranked results
```

**Rationale**: Broad semantic search followed by precise filtering provides both relevance and precision.

</details>

## Data Transformation Diagrams

### ETL Data Transformation

```
┌─────────────────────────────────────────────────────────────┐
│                  Source Data (Multiple Formats)             │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌─────────────┬──────────┬──────────┐
        ↓             ↓          ↓          ↓
    ┌──────┐     ┌──────┐   ┌────────┐  ┌──────┐
    │ XML  │     │ JSON │   │JSON-LD │  │ RDF  │
    │Parse │     │Parse │   │ Parse  │  │Parse │
    └──────┘     └──────┘   └────────┘  └──────┘
        ↓             ↓          ↓          ↓
    ┌────────────────────────────────────────────────┐
    │          Intermediate Parsed Data              │
    │  {xml_data, json_data, jsonld_data, rdf_data}  │
    └────────────────────────────────────────────────┘
                            ↓
                ┌──────────────────────┐
                │      Merge Logic     │
                │    (Priority Rules)  │
                └──────────────────────┘
                            ↓
                ┌──────────────────────┐
                │     Domain Model     │
                │   (Dataset object)   │
                └──────────────────────┘
                            ↓
                ┌──────────────────────┐
                │    Database Model    │
                │   (SQLAlchemy ORM)   │
                └──────────────────────┘
                            ↓
                ┌──────────────────────┐
                │    SQLite Storage    │
                └──────────────────────┘
```

### Search Data Transformation

```
┌──────────────────────────────────────────────────────────┐
│              User Query (Natural Language)               │
│           "climate change hydrology UK"                  │
└──────────────────────────────────────────────────────────┘
                        ↓
            ┌──────────────────────────┐
            │  Sentence Transformer    │
            │  (Embedding Generation)  │
            └──────────────────────────┘
                        ↓
        ┌──────────────────────────────────────┐
        │    Query Embedding (384-dim vector)  │
        │  [0.123, -0.456, 0.789, ...]         │
        └──────────────────────────────────────┘
                        ↓
            ┌──────────────────────────┐
            │    FAISS Index Search    │
            │  (Cosine Similarity)     │
            └──────────────────────────┘
                        ↓
        ┌──────────────────────────────────────┐
        │  Top K Nearest Neighbors             │
        │  [(idx_1, dist_1), (idx_2, dist_2)]  │
        └──────────────────────────────────────┘
                        ↓
        ┌──────────────────────────────────────┐
        │   Map to Dataset IDs                 │
        │   [id_a1b2, id_c3d4, ...]            │
        └──────────────────────────────────────┘
                        ↓
            ┌──────────────────────────┐
            │  Database Lookup         │
            │  (Fetch full metadata)   │
            └──────────────────────────┘
                        ↓
        ┌──────────────────────────────────────┐
        │   Enriched Results                   │
        │   [{dataset, score, rank}, ...]      │
        └──────────────────────────────────────┘
                        ↓
            ┌──────────────────────────┐
            │   JSON Serialization     │
            └──────────────────────────┘
                        ↓
        ┌──────────────────────────────────────┐
        │        HTTP Response                 │
        └──────────────────────────────────────┘
                        ↓
            ┌──────────────────────────┐
            │   Frontend Rendering     │
            └──────────────────────────┘
```

## Integration Points

### 1. External Service Integration (CEH Catalogue)

**Protocol**: HTTP/HTTPS  
**Authentication**: None (public API)  
**Rate Limiting**: Respectful delays between requests (1s)  
**Error Handling**: Retry with exponential backoff

**URL Patterns**:
```
XML:     https://catalogue.ceh.ac.uk/documents/{file_id}.xml
JSON:    https://catalogue.ceh.ac.uk/documents/{file_id}?format=json
JSON-LD: https://catalogue.ceh.ac.uk/documents/{file_id}?format=schema.org
RDF:     https://catalogue.ceh.ac.uk/documents/{file_id}?format=ttl
```

**Request Headers**:
```python
headers = {
    'User-Agent': 'DSH-ETL-Search-AI/1.0',
    'Accept': 'application/xml'  # or application/json, etc.
}
```

### 2. Database Integration (SQLAlchemy → SQLite)

**Connection**:
```python
engine = create_engine('sqlite:///data/ceh_datasets.db')
SessionLocal = sessionmaker(bind=engine)
```

**Transaction Management**: Explicit commits/rollbacks  
**Error Handling**: Catch SQLAlchemy exceptions, rollback on error

### 3. Vector Store Integration (FAISS)

**Index Loading**:
```python
import faiss
import pickle

# Load index
index = faiss.read_index("data/faiss_index.bin")

# Load ID mapping
with open("data/id_map.pkl", "rb") as f:
    id_map = pickle.load(f)
```

**Search Operation**:
```python
distances, indices = index.search(query_vector, k=10)
```

### 4. ML Model Integration (Sentence Transformers)

**Model Loading**:
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
```

**Encoding**:
```python
# Single text
embedding = model.encode("sample text")

# Batch encoding
embeddings = model.encode(["text1", "text2"], batch_size=32)
```

**Device**: CPU (no GPU required)

### 5. Frontend-Backend Integration (REST API)

**API Client Configuration**:
```javascript
import axios from 'axios';

const client = axios.create({
  baseURL: process.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});
```

**Request/Response Format**: JSON  
**Error Handling**: Axios interceptors for global error handling  
**CORS**: Configured in FastAPI middleware

## Error Handling & Recovery

### ETL Errors
- **Network failures**: Retry with exponential backoff (3 attempts)
- **Parse errors**: Log and continue to next dataset
- **Database errors**: Rollback transaction, log error

### Search Errors
- **FAISS not loaded**: Return 500 with helpful message
- **Invalid query**: Return 400 with validation errors
- **Database timeout**: Return 503 (service unavailable)

### Frontend Errors
- **API failures**: Show toast notification, optionally retry
- **Network errors**: Offline indicator
- **Rendering errors**: Error boundary with fallback UI

## Data Consistency

### Transaction Management
- ETL → Database: Atomic transactions (commit or rollback)
- Database → FAISS: Eventual consistency (rebuild required)

### Data Validation
- **At extraction**: Format-specific validation
- **At merge**: Cross-format consistency checks
- **At persistence**: Database constraints
- **At API**: Pydantic schema validation