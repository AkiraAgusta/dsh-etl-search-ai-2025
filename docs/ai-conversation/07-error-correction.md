# Error Correction and Debugging - AI Conversation

## Database Schema Issues

### Me:
I'm getting an error when running the ETL pipeline: IntegrityError: NOT NULL constraint failed: contacts.position_name. But I thought position_name should be optional. What's wrong with my database schema?

### Claude:
This is a schema mismatch issue! Let's debug it systematically.

**Problem Analysis:**

The error indicates that the database expects `position_name` to be NOT NULL, but your code is trying to insert NULL values. This could happen in two scenarios:

1. **Schema Definition Issue**: Column defined as NOT NULL in database
2. **Data Migration Issue**: Old schema still in use

**Let's Check the Database Model:**

```python
# In etl/models/database.py
class ContactModel(Base):
    __tablename__ = 'contacts'
    
    position_name = Column(String(200))  # No nullable=False
```

This looks correct (nullable by default). The issue must be in the database itself, not the model definition.

**Root Cause:**

You likely created the database with an old schema where `position_name` was required, then updated your model but didn't recreate the database.

**Solution 1: Recreate Database**

```python
# scripts/setup_database.py
"""
Drop and recreate database with correct schema.
"""

from pathlib import Path
from sqlalchemy import create_engine
from etl.models.database import Base

# Database path
DATABASE_PATH = Path('data/ceh_metadata.db')

# Delete existing database
if DATABASE_PATH.exists():
    print(f"Deleting existing database: {DATABASE_PATH}")
    DATABASE_PATH.unlink()

# Create engine
engine = create_engine(f'sqlite:///{DATABASE_PATH}')

# Create all tables
print("Creating database schema...")
Base.metadata.create_all(engine)
print("✓ Database created successfully")
```

**Solution 2: Migration Script (If You Have Data)**

```python
"""
Migrate database to new schema.
"""

import sqlite3

# Connect to database
conn = sqlite3.connect('data/ceh_metadata.db')
cursor = conn.cursor()

# Check current schema
cursor.execute("PRAGMA table_info(contacts)")
columns = cursor.fetchall()

for col in columns:
    print(f"Column: {col[1]}, Type: {col[2]}, NotNull: {col[3]}")

# Drop NOT NULL constraint (SQLite doesn't support ALTER COLUMN)
# Must recreate table

# Step 1: Create new table with correct schema
cursor.execute("""
    CREATE TABLE contacts_new (
        id TEXT PRIMARY KEY,
        dataset_id TEXT NOT NULL,
        family_name TEXT,
        given_name TEXT,
        full_name TEXT,
        honorific_prefix TEXT,
        organization_name TEXT,
        organization_identifier TEXT,
        position_name TEXT,  -- Now nullable
        email TEXT,
        role TEXT NOT NULL,
        name_identifier TEXT,
        address TEXT,
        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
    )
""")

# Step 2: Copy data
cursor.execute("""
    INSERT INTO contacts_new
    SELECT * FROM contacts
""")

# Step 3: Drop old table
cursor.execute("DROP TABLE contacts")

# Step 4: Rename new table
cursor.execute("ALTER TABLE contacts_new RENAME TO contacts")

conn.commit()
conn.close()

print("✓ Migration complete")
```

**Prevention Strategy:**

1. **Use Alembic** for database migrations
2. **Version your schema** in git
3. **Test schema changes** before running ETL
4. **Document breaking changes**

**Quick Fix for Your Case:**

Since you're in development, just delete and recreate:

```bash
rm data/ceh_metadata.db
python scripts/setup_database.py
python scripts/run_etl.py
```

This ensures your database matches your model definitions!

---

## Date Parsing Issues

### Me:
The ETL is failing with ValueError: time data '2023-01-15T10:30:00Z' does not match format '%Y-%m-%d'. My date parsing isn't handling all the different date formats from the metadata. How can I fix this?

### Claude:
This is a common issue! The CEH metadata uses multiple date formats. Let's create robust date parsing.

**Problem:**

Different metadata formats use different date representations:
- XML: `2023-01-15` (date only)
- JSON: `2023-01-15T10:30:00Z` (ISO 8601 with timezone)
- RDF: `2023-01-15T10:30:00+00:00` (ISO 8601 with offset)

**Solution: Robust Date Parser**

We already created `date_utils.py`, but let's ensure it handles all cases:

```python
# etl/utils/date_utils.py
"""
Robust date parsing utilities.
"""

from datetime import datetime, date
from typing import Optional
from loguru import logger


def parse_date(date_str: str) -> Optional[date]:
    """
    Parse date string to date object.
    
    Tries multiple formats to handle various metadata sources.
    
    Args:
        date_str: Date string to parse
        
    Returns:
        date object if successful, None otherwise
    """
    if not date_str:
        return None
    
    # Remove whitespace
    date_str = date_str.strip()
    
    # Try multiple formats in order of likelihood
    formats = [
        '%Y-%m-%d',                    # 2023-01-15
        '%Y-%m-%dT%H:%M:%S',          # 2023-01-15T10:30:00
        '%Y-%m-%dT%H:%M:%SZ',         # 2023-01-15T10:30:00Z
        '%Y-%m-%dT%H:%M:%S%z',        # 2023-01-15T10:30:00+00:00
        '%Y-%m-%dT%H:%M:%S.%f',       # 2023-01-15T10:30:00.123456
        '%Y-%m-%dT%H:%M:%S.%fZ',      # 2023-01-15T10:30:00.123456Z
        '%Y/%m/%d',                    # 2023/01/15
        '%d-%m-%Y',                    # 15-01-2023
        '%d/%m/%Y',                    # 15/01/2023
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    # Try ISO format parsing (more flexible)
    try:
        # Handle Z timezone
        if date_str.endswith('Z'):
            date_str = date_str[:-1] + '+00:00'
        return datetime.fromisoformat(date_str).date()
    except (ValueError, TypeError):
        pass
    
    logger.warning(f"Could not parse date: '{date_str}'")
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
    
    datetime_str = datetime_str.strip()
    
    try:
        # Handle Z timezone (UTC)
        if datetime_str.endswith('Z'):
            datetime_str = datetime_str[:-1] + '+00:00'
        return datetime.fromisoformat(datetime_str)
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse datetime: '{datetime_str}' - {e}")
        return None


def parse_temporal_extent(extent: dict) -> Optional[dict]:
    """
    Parse temporal extent with validation.
    
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
        # Don't fail, just log and return what we have
    
    if start or end:
        return {'start': start, 'end': end}
    
    return None
```

**Update Extractors:**

```python
# In extractors
from ..utils.date_utils import parse_date, parse_datetime, parse_temporal_extent

class JSONExtractor(BaseExtractor):
    def _parse_data(self, raw_data: bytes) -> Dict[str, Any]:
        data = json.loads(raw_data.decode('utf-8'))
        
        return {
            # Use robust parsers
            'publication_date': parse_date(data.get('publicationDate')),
            'metadata_date': parse_datetime(data.get('metadataDate')),
            'updated_date': parse_date(data.get('updatedDate')),
            'temporal_extent': parse_temporal_extent(
                data.get('temporalExtents', [{}])[0]
            ),
        }
```

**Testing:**

```python
# Test all formats
test_dates = [
    '2023-01-15',
    '2023-01-15T10:30:00',
    '2023-01-15T10:30:00Z',
    '2023-01-15T10:30:00+00:00',
    '2023-01-15T10:30:00.123456Z',
]

for date_str in test_dates:
    result = parse_date(date_str)
    print(f"{date_str:35} -> {result}")
```

Now your ETL handles all date formats gracefully!

---

## FAISS Index Loading Issues

### Me:
My search endpoint is very slow on the first request (10+ seconds), then fast on subsequent requests. What's causing this?

### Claude:
This is a classic lazy loading issue! Let's optimize the startup behavior.

**Problem Analysis:**

The search engine loads the FAISS index and model on first use:

```python
@lru_cache()
def get_search_engine() -> SemanticSearchEngine:
    """Get search engine."""
    engine = SemanticSearchEngine(config)
    # Index and model NOT loaded yet!
    return engine
```

On first request:
1. Create engine (fast)
2. First search call triggers:
   - Load FAISS index (~1-2 seconds)
   - Load embedding model (~3-5 seconds)
   - Load metadata (~0.1 seconds)
3. Return results (fast)

**Solution: Eager Loading**

**Option 1: Pre-load in Dependency (Recommended)**

```python
# api/dependencies.py

@lru_cache()
def get_search_engine() -> SemanticSearchEngine:
    """
    Get semantic search engine with pre-loaded resources.
    
    Loads index and model on first access, then caches.
    """
    logger.info("Initializing search engine...")
    config = EmbeddingConfig()
    engine = SemanticSearchEngine(config)
    
    # Pre-load all resources
    logger.info("Loading FAISS index...")
    engine.load_index()
    
    logger.info("Loading embedding model...")
    engine.load_model()
    
    logger.info("Loading metadata...")
    engine.load_metadata()
    
    logger.info("Search engine ready!")
    return engine
```

**Option 2: Startup Event (Best for Production)**

```python
# api/app.py

# Global search engine
_search_engine: Optional[SemanticSearchEngine] = None


@app.on_event("startup")
async def startup_event():
    """Load search engine on startup."""
    global _search_engine
    
    logger.info("=" * 70)
    logger.info("Loading search engine...")
    logger.info("=" * 70)
    
    config = EmbeddingConfig()
    _search_engine = SemanticSearchEngine(config)
    
    # Pre-load all resources
    _search_engine.load_index()
    _search_engine.load_model()
    _search_engine.load_metadata()
    
    logger.info("✓ Search engine ready")
    logger.info("=" * 70)


def get_search_engine() -> SemanticSearchEngine:
    """Get pre-loaded search engine."""
    if _search_engine is None:
        raise RuntimeError("Search engine not initialized")
    return _search_engine
```

**Benefits:**

1. **Predictable Performance**: First request is fast
2. **Fail Fast**: Startup errors caught immediately
3. **Resource Reuse**: Index and model loaded once
4. **Production Ready**: No surprises in production

**Measuring Impact:**

```python
import time

@app.on_event("startup")
async def startup_event():
    start = time.time()
    
    # Load search engine
    global _search_engine
    config = EmbeddingConfig()
    _search_engine = SemanticSearchEngine(config)
    _search_engine.load_index()
    _search_engine.load_model()
    _search_engine.load_metadata()
    
    duration = time.time() - start
    logger.info(f"Search engine loaded in {duration:.2f}s")
```

Now your API is fast from the very first request!