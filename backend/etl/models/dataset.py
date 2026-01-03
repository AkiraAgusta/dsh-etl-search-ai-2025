"""
Domain models for CEH metadata.
Updated to support all 4 formats: XML, JSON, JSON-LD, RDF
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import date, datetime


@dataclass
class SpatialExtent:
    """Spatial bounding box."""
    west: float
    east: float
    south: float
    north: float


@dataclass
class TemporalExtent:
    """Temporal coverage."""
    start: Optional[date] = None
    end: Optional[date] = None


@dataclass
class Contact:
    """
    Contact information.
    
    Note: position_name and individual_name are accepted for compatibility
    with extractors but are NOT stored in the database (always NULL in source data).
    """
    role: str
    family_name: Optional[str] = None
    given_name: Optional[str] = None
    full_name: Optional[str] = None
    honorific_prefix: Optional[str] = None
    organization_name: Optional[str] = None
    organization_identifier: Optional[str] = None  # RoR ID
    email: Optional[str] = None
    name_identifier: Optional[str] = None  # ORCID
    address: Optional[Dict[str, Any]] = None
    
    # Backward compatibility - accepted but ignored (not in database schema)
    position_name: Optional[str] = None
    individual_name: Optional[str] = None


@dataclass
class Keyword:
    """Keyword or subject term."""
    keyword: str
    keyword_type: Optional[str] = None  # theme, other, place, project
    uri: Optional[str] = None
    in_defined_term_set: Optional[str] = None  # from JSON-LD
    
    # Backward compatibility - accepted but ignored
    thesaurus: Optional[str] = None


@dataclass
class Relationship:
    """Dataset relationship."""
    relation_type: str  # memberOf, relatedTo, supersedes, uses
    target_dataset_id: str


@dataclass
class OnlineResource:
    """Online resource or download link."""
    url: str
    name: Optional[str] = None
    description: Optional[str] = None
    function: Optional[str] = None  # download, information
    resource_type: Optional[str] = None


@dataclass
class MetadataDocument:
    """Raw metadata document."""
    format: str  # xml, json, jsonld, rdf
    content: str
    file_size: int
    downloaded_at: Optional[datetime] = None


@dataclass
class Dataset:
    """Complete dataset metadata."""
    file_identifier: str
    title: str
    
    # Core metadata
    abstract: Optional[str] = None
    description: Optional[str] = None
    lineage: Optional[str] = None
    
    # Dates
    publication_date: Optional[date] = None
    metadata_date: Optional[datetime] = None
    updated_date: Optional[date] = None
    
    # ISO 19115 fields (from XML/RDF)
    metadata_standard: Optional[str] = None
    metadata_standard_version: Optional[str] = None
    language: Optional[str] = None
    
    # Status and type
    resource_status: Optional[str] = None
    resource_type: Optional[str] = None
    
    # Extents
    spatial_extent: Optional[SpatialExtent] = None
    temporal_extent: Optional[TemporalExtent] = None
    
    # NEW: Citation and accessibility (from JSON-LD/RDF)
    credit_text: Optional[str] = None  # Formatted citation
    is_accessible_for_free: Optional[bool] = None  # Accessibility flag
    
    # Related data
    contacts: List[Contact] = field(default_factory=list)
    keywords: List[Keyword] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    online_resources: List[OnlineResource] = field(default_factory=list)
    metadata_documents: List[MetadataDocument] = field(default_factory=list)
    
    # Additional metadata (flexible JSON storage)
    additional_metadata: Optional[Dict[str, Any]] = None
    
    # Backward compatibility - accepted but ignored
    purpose: Optional[str] = None
    creation_date: Optional[date] = None
    
    # Internal
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def get_search_text(self) -> str:
        """Generate text for semantic search indexing."""
        parts = [
            self.title,
            self.abstract or '',
            self.description or '',
            self.lineage or '',
        ]
        
        # Add keywords
        if self.keywords:
            keywords_text = ' '.join([kw.keyword for kw in self.keywords])
            parts.append(keywords_text)
        
        # Add contact names
        if self.contacts:
            names = []
            for contact in self.contacts:
                if contact.full_name:
                    names.append(contact.full_name)
                if contact.organization_name:
                    names.append(contact.organization_name)
            if names:
                parts.append(' '.join(names))
        
        # Add credit text if available
        if self.credit_text:
            parts.append(self.credit_text)
        
        return ' '.join(filter(None, parts))


# For backward compatibility
DataFile = None
SupportingDocument = None