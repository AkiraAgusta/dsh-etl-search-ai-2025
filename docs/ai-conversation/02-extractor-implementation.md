# Extractor Implementation - AI Conversation

## Understanding ISO 19115 Standard

### Me:
Let's implement the extractors. The XML format follows ISO 19115 (Geographic Metadata Standard). Before we start implementing the XML extractor, explain the key concepts of ISO 19115 and the metadata elements we need to extract.

### Claude:
Great question! ISO 19115 is a complex standard, but understanding its structure will help us extract the right data.

**ISO 19115 Key Concepts:**

**1. Metadata Hierarchy:**

```
MD_Metadata (root)
├── fileIdentifier              # Unique ID for the metadata
├── language                    # Metadata language
├── characterSet                # Character encoding
├── hierarchyLevel              # Dataset/service/series
├── contact                     # Metadata point of contact
├── dateStamp                   # Metadata creation date
├── metadataStandardName        # "ISO 19115"
├── metadataStandardVersion     # Version number
├── identificationInfo          # MOST IMPORTANT - dataset description
│   ├── citation
│   │   ├── title              # Dataset title
│   │   ├── date               # Publication/creation date
│   │   └── identifier         # Dataset identifiers
│   ├── abstract               # Dataset description
│   ├── purpose                # Why dataset was created
│   ├── credit                 # Citation text
│   ├── status                 # completed/onGoing/planned
│   ├── pointOfContact         # Dataset contact (author/custodian)
│   ├── descriptiveKeywords    # Thematic keywords
│   ├── resourceConstraints    # Legal/security constraints
│   ├── extent                 # Spatial and temporal coverage
│   │   ├── geographicElement  # Bounding box
│   │   └── temporalElement    # Time period
│   └── lineage                # Data quality/processing history
├── distributionInfo           # How to access data
│   └── transferOptions        # Download links, WMS services
└── dataQualityInfo            # Data quality information
```

**2. Critical Elements to Extract:**

**Core Metadata:**
- `fileIdentifier` → Unique dataset ID
- `title` → Human-readable name
- `abstract` → Full description
- `lineage` → How data was created/processed

**Dates:**
- `dateStamp` → Metadata last modified
- `citation/date` → Publication date (CI_DateTypeCode)
  - Types: creation, publication, revision

**Contacts (Responsible Parties):**
```xml
<CI_ResponsibleParty>
  <individualName>      # Person name
  <organisationName>    # Organization
  <positionName>        # Job title
  <contactInfo>
    <address>
      <electronicMailAddress>  # Email
  <role>               # author/custodian/owner/publisher
```

**Spatial Extent (Bounding Box):**
```xml
<EX_GeographicBoundingBox>
  <westBoundLongitude>  # West edge
  <eastBoundLongitude>  # East edge
  <southBoundLatitude>  # South edge
  <northBoundLatitude>  # North edge
```

**Temporal Extent:**
```xml
<EX_TemporalExtent>
  <extent>
    <TimePeriod>
      <beginPosition>   # Start date
      <endPosition>     # End date (or "now")
```

**Keywords (Descriptive Keywords):**
```xml
<MD_Keywords>
  <keyword>           # Individual keyword
  <type>              # theme/place/temporal/discipline
  <thesaurusName>     # Controlled vocabulary reference
```

**3. Namespace Handling:**

ISO 19115 XML uses multiple namespaces:
```xml
xmlns:gmd="http://www.isotc211.org/2005/gmd"
xmlns:gco="http://www.isotc211.org/2005/gco"
xmlns:srv="http://www.isotc211.org/2005/srv"
xmlns:gml="http://www.opengis.net/gml/3.2"
```

We need to handle these properly:
```python
NAMESPACES = {
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'gco': 'http://www.isotc211.org/2005/gco',
    'gml': 'http://www.opengis.net/gml/3.2',
    'srv': 'http://www.isotc211.org/2005/srv'
}

# Usage:
root.find('.//gmd:fileIdentifier/gco:CharacterString', NAMESPACES)
```

**4. Common Patterns in ISO 19115:**

**a) Character Strings:**
```xml
<gmd:title>
  <gco:CharacterString>Dataset Title</gco:CharacterString>
</gmd:title>
```

**b) Code Lists (enumerations):**
```xml
<gmd:role>
  <gmd:CI_RoleCode codeList="..." codeListValue="author">author</gmd:CI_RoleCode>
</gmd:role>
```

**c) Dates:**
```xml
<gmd:date>
  <gmd:CI_Date>
    <gmd:date>
      <gco:Date>2023-01-15</gco:Date>
    </gmd:date>
    <gmd:dateType>
      <gmd:CI_DateTypeCode codeListValue="publication">publication</gmd:CI_DateTypeCode>
    </gmd:dateType>
  </gmd:CI_Date>
</gmd:date>
```

**5. Extraction Strategy:**

```python
def _parse_data(self, raw_data: bytes) -> Dict[str, Any]:
    """Parse ISO 19115 XML metadata."""
    root = ET.fromstring(raw_data)
    
    return {
        # Core metadata
        'file_identifier': self._get_text(root, './/gmd:fileIdentifier/gco:CharacterString'),
        'title': self._get_text(root, './/gmd:identificationInfo//gmd:title/gco:CharacterString'),
        'abstract': self._get_text(root, './/gmd:identificationInfo//gmd:abstract/gco:CharacterString'),
        'lineage': self._get_text(root, './/gmd:lineage//gco:CharacterString'),
        
        # Dates
        'metadata_date': self._extract_date_stamp(root),
        'publication_date': self._extract_publication_date(root),
        
        # Complex elements
        'contacts': self._extract_contacts(root),
        'keywords': self._extract_keywords(root),
        'spatial_extent': self._extract_bounding_box(root),
        'temporal_extent': self._extract_temporal_extent(root),
        
        # Raw XML (for reference)
        'raw_xml': raw_data.decode('utf-8'),
        'raw_xml_size': len(raw_data)
    }
```

**6. Helper Methods Pattern:**

Each complex element gets its own extraction method:
```python
def _extract_contacts(self, root: ET.Element) -> List[Dict]:
    """Extract all responsible parties."""
    contacts = []
    
    # Search all CI_ResponsibleParty elements
    for party in root.findall('.//gmd:CI_ResponsibleParty', NAMESPACES):
        contact = {
            'individual_name': self._get_text(party, './/gmd:individualName/gco:CharacterString'),
            'organization_name': self._get_text(party, './/gmd:organisationName/gco:CharacterString'),
            'position_name': self._get_text(party, './/gmd:positionName/gco:CharacterString'),
            'email': self._get_text(party, './/gmd:electronicMailAddress/gco:CharacterString'),
            'role': self._get_code_list_value(party, './/gmd:role/gmd:CI_RoleCode')
        }
        
        # Only add if role is present (required field)
        if contact['role']:
            contacts.append(contact)
    
    return contacts
```

This approach ensures we extract all critical ISO 19115 elements while maintaining clean, testable code.

---

## JSON Extractor Implementation

### Me:
The CEH catalogue also provides JSON metadata. This is not ISO 19115 (which is XML-based) but a JSON representation with similar information. How should we structure the JSON extractor, and what are the key differences from the XML format?

### Claude:
Excellent question! The JSON format is much simpler than ISO 19115 XML, but it contains richer relational data. Here's how to approach it:

**Key Differences Between XML and JSON Formats:**

| Aspect | ISO 19115 XML | CEH JSON |
|--------|---------------|----------|
| Structure | Deeply nested | Flatter, arrays |
| Namespaces | Yes (gmd:, gco:) | No |
| Field names | ISO standard names | Simplified names |
| Contacts | CI_ResponsibleParty | responsibleParties array |
| Keywords | MD_Keywords structure | keywordsTheme/keywordsPlace arrays |
| Relationships | Limited | Rich (relationships array) |
| Online Resources | distributionInfo | onlineResources array |

**JSON Structure Overview:**

```json
{
  "id": "abc123",
  "title": "Dataset Title",
  "description": "Abstract/description",
  "lineage": "Processing information",
  "publicationDate": "2023-01-15",
  "metadataDate": "2023-12-01T10:30:00",
  "updatedDate": "2023-12-15",
  
  "resourceStatus": "completed",
  "type": "dataset",
  
  "boundingBoxes": [{
    "westBoundLongitude": -10.0,
    "eastBoundLongitude": 2.0,
    "southBoundLatitude": 50.0,
    "northBoundLatitude": 60.0
  }],
  
  "temporalExtents": [{
    "begin": "1990-01-01",
    "end": "2020-12-31"
  }],
  
  "responsibleParties": [{
    "individualName": "John Doe",
    "organisationName": "UKCEH",
    "role": "author",
    "email": "john.doe@example.com",
    "organisationIdentifier": "https://ror.org/00pggkr55"  # ROR ID
  }],
  
  "keywordsTheme": [{
    "value": "soil science",
    "uri": "http://vocab.nerc.ac.uk/..."
  }],
  
  "keywordsPlace": [
    "Great Britain",
    "United Kingdom"
  ],
  
  "relationships": [{
    "relation": "http://purl.org/dc/terms/isPartOf",
    "target": "parent-dataset-id"
  }],
  
  "onlineResources": [{
    "url": "https://...",
    "name": "Download dataset",
    "function": "download",
    "type": "application/zip"
  }]
}
```

**JSON Extractor Implementation:**

```python
import json
from typing import Dict, Any, List

class JSONExtractor(BaseExtractor):
    """Extractor for CEH JSON metadata."""
    
    def get_source_type(self) -> str:
        return 'json'
    
    def _parse_data(self, raw_data: bytes) -> Dict[str, Any]:
        """Parse CEH JSON metadata with complete field extraction."""
        try:
            data = json.loads(raw_data.decode('utf-8'))
            
            return {
                # Core metadata
                'file_identifier': data.get('id'),
                'title': data.get('title'),
                'abstract': data.get('description'),  # JSON uses 'description'
                'description': data.get('description'),
                'lineage': data.get('lineage'),
                
                # Dates (different formats!)
                'publication_date': self._parse_date(data.get('publicationDate')),
                'metadata_date': self._parse_datetime(data.get('metadataDate')),
                'updated_date': self._parse_date(data.get('updatedDate')),
                
                # Status and type
                'resource_status': data.get('resourceStatus'),
                'resource_type': data.get('type'),
                
                # Spatial extent
                'spatial_extent': self._extract_spatial_extent(data),
                
                # Temporal extent
                'temporal_extent': self._extract_temporal_extent(data),
                
                # Collections (much cleaner than XML!)
                'contacts': self._extract_contacts(data),
                'keywords': self._extract_keywords(data),
                'relationships': self._extract_relationships(data),
                'online_resources': self._extract_online_resources(data),
                
                # Additional metadata
                'additional_metadata': self._extract_additional_metadata(data),
                
                # Raw content
                'raw_json': raw_data.decode('utf-8'),
                'raw_json_size': len(raw_data)
            }
        except json.JSONDecodeError as e:
            raise ExtractionError(f"JSON parsing failed: {e}")
```

**Key Implementation Details:**

**1. Spatial Extent Extraction:**

```python
def _extract_spatial_extent(self, data: Dict[str, Any]) -> Dict[str, float]:
    """Extract geographic bounding box."""
    if 'boundingBoxes' in data and data['boundingBoxes']:
        bbox = data['boundingBoxes'][0]  # Take first bounding box
        return {
            'west': bbox.get('westBoundLongitude'),
            'east': bbox.get('eastBoundLongitude'),
            'south': bbox.get('southBoundLatitude'),
            'north': bbox.get('northBoundLatitude')
        }
    return None
```

**2. Temporal Extent Extraction:**

```python
def _extract_temporal_extent(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract temporal coverage."""
    if 'temporalExtents' in data and data['temporalExtents']:
        extent = data['temporalExtents'][0]
        return {
            'start': self._parse_date(extent.get('begin')),
            'end': self._parse_date(extent.get('end'))
        }
    return None
```

**3. Contacts with Filtering:**

```python
def _extract_contacts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract all responsible parties (contacts).
    Filter out entries without roles (required field).
    """
    contacts = []
    
    for party in data.get('responsibleParties', []):
        # Skip contacts without a role (data quality issue)
        role = party.get('role')
        if not role:
            continue
        
        contact = {
            'family_name': party.get('familyName'),
            'given_name': party.get('givenName'),
            'full_name': party.get('individualName'),  # Compatibility
            'organization_name': party.get('organisationName'),
            'organization_identifier': party.get('organisationIdentifier'),
            'position_name': party.get('positionName'),
            'role': role,
            'email': party.get('email'),
            'name_identifier': party.get('nameIdentifier'),  # ORCID
        }
        
        # Address (if present)
        if 'address' in party:
            contact['address'] = party['address']
        
        contacts.append(contact)
    
    return contacts
```

**4. Keywords by Type:**

```python
def _extract_keywords(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Extract keywords from all categories.
    JSON provides typed keywords: theme, place, project, other.
    """
    keywords = []
    
    # Theme keywords (controlled vocabularies)
    for kw in data.get('keywordsTheme', []):
        keywords.append({
            'keyword': kw.get('value'),
            'keyword_type': 'theme',
            'uri': kw.get('uri'),
            'thesaurus': None
        })
    
    # Place keywords (geographic locations)
    for kw in data.get('keywordsPlace', []):
        keyword_value = kw.get('value') if isinstance(kw, dict) else kw
        if keyword_value:
            keywords.append({
                'keyword': keyword_value,
                'keyword_type': 'place',
                'uri': kw.get('uri') if isinstance(kw, dict) else None,
                'thesaurus': None
            })
    
    # Project keywords
    for kw in data.get('keywordsProject', []):
        keyword_value = kw.get('value') if isinstance(kw, dict) else kw
        if keyword_value:
            keywords.append({
                'keyword': keyword_value,
                'keyword_type': 'project',
                'uri': None,
                'thesaurus': None
            })
    
    # Other keywords
    for kw in data.get('keywordsOther', []):
        keyword_value = kw.get('value') if isinstance(kw, dict) else kw
        if keyword_value:
            keywords.append({
                'keyword': keyword_value,
                'keyword_type': 'other',
                'uri': kw.get('uri') if isinstance(kw, dict) else None,
                'thesaurus': None
            })
    
    return keywords
```

**5. Relationships (JSON-specific feature):**

```python
def _extract_relationships(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Extract relationships to other datasets.
    
    JSON format provides rich relational metadata:
    - isPartOf (collection membership)
    - hasPart (collection contents)
    - supersedes (version replacement)
    """
    relationships = []
    
    for rel in data.get('relationships', []):
        # Extract relation type from URI
        relation = rel.get('relation', '')
        relation_type = relation.split('#')[-1] if '#' in relation else relation
        
        relationships.append({
            'relation_type': relation_type,
            'target_dataset_id': rel.get('target')
        })
    
    return relationships
```

**6. Additional Metadata:**

```python
def _extract_additional_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract fields that don't fit in core schema.
    Stored as JSON for flexibility.
    """
    additional = {}
    
    # Funding information (grant details)
    if 'funding' in data:
        additional['funding'] = data['funding']
    
    # INSPIRE themes (European directive)
    if 'inspireThemes' in data:
        additional['inspire_themes'] = data['inspireThemes']
    
    # Spatial reference systems (coordinate systems)
    if 'spatialReferenceSystems' in data:
        additional['spatial_reference_systems'] = data['spatialReferenceSystems']
    
    # Use constraints / licenses
    if 'useConstraints' in data:
        additional['use_constraints'] = data['useConstraints']
    
    if 'licences' in data:
        additional['licences'] = data['licences']
    
    # Topic categories (ISO 19115 categories)
    if 'topicCategories' in data:
        additional['topic_categories'] = data['topicCategories']
    
    return additional if additional else None
```

**7. Date Parsing Utilities:**

```python
from datetime import datetime, date

def _parse_date(self, date_str: str) -> date:
    """Parse date string to date object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        logger.warning(f"Could not parse date: {date_str}")
        return None

def _parse_datetime(self, datetime_str: str) -> datetime:
    """Parse datetime string to datetime object."""
    if not datetime_str:
        return None
    try:
        # Handle ISO 8601 format
        return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    except ValueError:
        logger.warning(f"Could not parse datetime: {datetime_str}")
        return None
```

**Key Advantages of JSON Format:**

1. **Simpler parsing** - No XML namespaces
2. **Richer relationships** - Explicit dataset relationships
3. **Better typed data** - Keywords categorized by type
4. **More metadata** - Additional fields like `updatedDate`
5. **Cleaner structure** - Arrays instead of nested XML

**Validation:**

```python
def validate(self, data: Dict[str, Any]) -> bool:
    """
    Validate extracted JSON data.
    Must have file_identifier and title.
    """
    return bool(data.get('file_identifier')) and bool(data.get('title'))
```

This JSON extractor complements the XML extractor, and we can use BOTH in our pipeline to get the richest metadata possible!

---

## Handling Multiple Formats in Pipeline

### Me:
We now have extractors for XML (ISO 19115) and JSON. How should the ETL pipeline orchestrate these extractors? Should we extract from all formats for each dataset and merge the data? What's the best strategy?

### Claude:
Excellent question! This is where the pipeline's intelligence matters. Let's design a smart merging strategy.

**Merging Strategy:**

**1. Multi-Format Extraction:**

```python
class ETLPipeline:
    """
    Complete ETL pipeline for CEH metadata.
    Downloads and merges data from all 4 formats.
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.repository = DatasetRepository(session)
        
        # Initialize all extractors
        self.xml_extractor = XMLExtractor()
        self.json_extractor = JSONExtractor()
        self.jsonld_extractor = JSONLDExtractor()
        self.rdf_extractor = RDFExtractor()
    
    def process_dataset(self, file_identifier: str) -> Optional[Dataset]:
        """
        Process a single dataset - extract from all 4 formats.
        
        Strategy:
        1. Try to extract from all formats
        2. Gracefully handle failures (format may not exist)
        3. Merge data intelligently
        4. Save merged result
        """
        try:
            logger.info(f"Processing dataset: {file_identifier}")
            
            # Extract from all 4 formats (failures are OK)
            xml_data = self._extract_xml(file_identifier)
            json_data = self._extract_json(file_identifier)
            jsonld_data = self._extract_jsonld(file_identifier)
            rdf_data = self._extract_rdf(file_identifier)
            
            # Check if we have at least one format
            if not any([xml_data, json_data, jsonld_data, rdf_data]):
                logger.error(f"No data extracted for {file_identifier}")
                return None
            
            # Intelligently merge data from all sources
            dataset = self._merge_all_formats(
                xml_data, json_data, jsonld_data, rdf_data, file_identifier
            )
            
            # Save to database
            self.repository.add(dataset)
            self.session.commit()
            
            logger.info(f"✅ Successfully processed: {file_identifier}")
            return dataset
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Pipeline failed for {file_identifier}: {e}")
            return None
```

**2. Graceful Format Extraction:**

```python
def _extract_xml(self, file_identifier: str) -> Optional[dict]:
    """Extract XML metadata - don't fail pipeline if missing."""
    try:
        url = f"https://catalogue.ceh.ac.uk/documents/{file_identifier}.xml"
        return self.xml_extractor.extract(url)
    except Exception as e:
        logger.warning(f"XML extraction failed: {e}")
        return None

def _extract_json(self, file_identifier: str) -> Optional[dict]:
    """Extract JSON metadata - don't fail pipeline if missing."""
    try:
        url = f"https://catalogue.ceh.ac.uk/documents/{file_identifier}?format=json"
        return self.json_extractor.extract(url)
    except Exception as e:
        logger.warning(f"JSON extraction failed: {e}")
        return None
```

**3. Intelligent Merging Logic:**

```python
def _merge_all_formats(
    self,
    xml_data: Optional[dict],
    json_data: Optional[dict],
    jsonld_data: Optional[dict],
    rdf_data: Optional[dict],
    file_identifier: str
) -> Dataset:
    """
    Intelligently merge data from all 4 formats.
    
    Priority Rules:
    1. Core metadata (title, abstract): JSON (richest descriptions)
    2. ISO 19115 fields: XML (most complete)
    3. Citation: JSON-LD or RDF (formatted citation)
    4. Relationships: JSON (most detailed)
    5. Contacts: JSON (includes ORCID, ROR IDs)
    6. Keywords: JSON (typed by category)
    
    Use coalesce pattern: take first non-None value.
    """
    
    # Helper function to get first non-None value
    def coalesce(*values):
        return next((v for v in values if v is not None), None)
    
    # Create dataset with merged core metadata
    dataset = Dataset(
        file_identifier=coalesce(
            json_data.get('file_identifier') if json_data else None,
            xml_data.get('file_identifier') if xml_data else None,
            file_identifier
        ),
        
        # Title: Prefer JSON (often more complete)
        title=coalesce(
            json_data.get('title') if json_data else None,
            jsonld_data.get('title') if jsonld_data else None,
            xml_data.get('title') if xml_data else None,
            rdf_data.get('title') if rdf_data else None
        ),
        
        # Abstract: Prefer JSON
        abstract=coalesce(
            json_data.get('abstract') if json_data else None,
            jsonld_data.get('abstract') if jsonld_data else None,
            xml_data.get('abstract') if xml_data else None,
            rdf_data.get('abstract') if rdf_data else None
        ),
        
        # Lineage: JSON or XML
        lineage=coalesce(
            json_data.get('lineage') if json_data else None,
            xml_data.get('lineage') if xml_data else None
        ),
        
        # Dates (different sources for different dates)
        publication_date=coalesce(
            json_data.get('publication_date') if json_data else None,
            xml_data.get('publication_date') if xml_data else None,
            jsonld_data.get('date_published') if jsonld_data else None
        ),
        metadata_date=coalesce(
            json_data.get('metadata_date') if json_data else None,
            xml_data.get('metadata_date') if xml_data else None
        ),
        updated_date=json_data.get('updated_date') if json_data else None,
        
        # ISO 19115 fields: From XML (most authoritative)
        metadata_standard=xml_data.get('metadata_standard') if xml_data else None,
        metadata_standard_version=xml_data.get('metadata_standard_version') if xml_data else None,
        language=coalesce(
            xml_data.get('language') if xml_data else None,
            rdf_data.get('language_uri') if rdf_data else None
        ),
        
        # Citation: From JSON-LD/RDF (formatted)
        credit_text=coalesce(
            jsonld_data.get('credit_text') if jsonld_data else None,
            rdf_data.get('bibliographic_citation') if rdf_data else None
        ),
        
        # Additional metadata from JSON (richest)
        additional_metadata=json_data.get('additional_metadata') if json_data else None
    )
    
    # Merge spatial extent (prefer JSON, fallback to others)
    spatial = None
    if json_data and json_data.get('spatial_extent'):
        spatial = json_data['spatial_extent']
    elif xml_data and xml_data.get('spatial_extent'):
        spatial = xml_data['spatial_extent']
    elif jsonld_data and jsonld_data.get('spatial_coverage'):
        spatial = jsonld_data['spatial_coverage']
    
    if spatial:
        dataset.spatial_extent = SpatialExtent(**spatial)
    
    # Merge contacts (prefer JSON - has ORCID/ROR IDs)
    if json_data and json_data.get('contacts'):
        dataset.contacts = [Contact(**contact) for contact in json_data['contacts']]
    elif xml_data and xml_data.get('contacts'):
        dataset.contacts = [Contact(**contact) for contact in xml_data['contacts']]
    
    # Merge keywords (prefer JSON - typed)
    if json_data and json_data.get('keywords'):
        dataset.keywords = [Keyword(**kw) for kw in json_data['keywords']]
    elif xml_data and xml_data.get('keywords'):
        dataset.keywords = [Keyword(**kw) for kw in xml_data['keywords']]
    
    # Enhance keywords with JSON-LD term sets (add semantic URIs)
    if jsonld_data and jsonld_data.get('keywords_with_term_sets'):
        term_sets = {kw['keyword']: kw.get('in_defined_term_set') 
                    for kw in jsonld_data['keywords_with_term_sets']}
        for kw in dataset.keywords:
            if kw.keyword in term_sets:
                kw.in_defined_term_set = term_sets[kw.keyword]
    
    # Relationships (only in JSON)
    if json_data and json_data.get('relationships'):
        dataset.relationships = [Relationship(**rel) for rel in json_data['relationships']]
    
    # Online resources (only in JSON)
    if json_data and json_data.get('online_resources'):
        dataset.online_resources = [OnlineResource(**res) for res in json_data['online_resources']]
    
    # Store ALL raw metadata documents
    if xml_data and xml_data.get('raw_xml'):
        dataset.metadata_documents.append(
            MetadataDocument(
                format='xml',
                content=xml_data['raw_xml'],
                file_size=xml_data.get('raw_xml_size', 0)
            )
        )
    
    if json_data and json_data.get('raw_json'):
        dataset.metadata_documents.append(
            MetadataDocument(
                format='json',
                content=json_data['raw_json'],
                file_size=json_data.get('raw_json_size', 0)
            )
        )
    
    return dataset
```

**Why This Strategy Works:**

1. **Resilience**: If one format fails, we still have others
2. **Richness**: Get best data from each format
3. **Completeness**: Store all raw formats for reference
4. **Intelligence**: Prioritize based on format strengths
5. **Traceability**: Can always go back to raw metadata

**Format Strengths:**

| Data Type | Best Format | Why |
|-----------|-------------|-----|
| Core metadata | JSON | Cleaner, more complete |
| ISO fields | XML | Official ISO 19115 standard |
| Citations | JSON-LD/RDF | Structured, formatted |
| Relationships | JSON | Explicit relationship modeling |
| Contacts | JSON | Modern IDs (ORCID, ROR) |
| Keywords | JSON | Typed by category |

This multi-format approach gives us the **best of all worlds**!