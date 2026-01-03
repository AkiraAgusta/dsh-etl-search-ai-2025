"""
Optimized database models for CEH metadata.
Supports all 4 formats: XML, JSON, JSON-LD, RDF
Removed unused fields, added new fields from all formats.
"""

from sqlalchemy import Column, String, Text, Date, DateTime, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class DatasetModel(Base):
    """Dataset metadata - core information."""
    __tablename__ = 'datasets'
    
    # Primary keys
    id = Column(String(36), primary_key=True)
    file_identifier = Column(String(255), unique=True, nullable=False, index=True)
    
    # Core metadata (all formats)
    title = Column(Text, nullable=False)
    abstract = Column(Text)
    description = Column(Text)
    lineage = Column(Text)
    
    # Dates
    publication_date = Column(Date)
    metadata_date = Column(DateTime)
    updated_date = Column(Date)
    
    # ISO 19115 fields (from XML/RDF)
    metadata_standard = Column(String(100))
    metadata_standard_version = Column(String(50))
    language = Column(String(10))
    
    # Status and type
    resource_status = Column(String(50))
    resource_type = Column(String(50))
    
    # Spatial extent
    spatial_west = Column(String(50))
    spatial_east = Column(String(50))
    spatial_south = Column(String(50))
    spatial_north = Column(String(50))
    
    # Temporal extent
    temporal_start = Column(Date)
    temporal_end = Column(Date)
    
    # NEW: Citation and accessibility (from JSON-LD/RDF)
    credit_text = Column(Text)  # Formatted citation string
    is_accessible_for_free = Column(Boolean)  # Accessibility flag
    
    # Additional metadata (JSON column for flexibility)
    additional_metadata = Column(JSON)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contacts = relationship("ContactModel", back_populates="dataset", cascade="all, delete-orphan")
    keywords = relationship("KeywordModel", back_populates="dataset", cascade="all, delete-orphan")
    relationships = relationship("RelationshipModel", back_populates="source_dataset", 
                                foreign_keys="RelationshipModel.source_dataset_id",
                                cascade="all, delete-orphan")
    online_resources = relationship("OnlineResourceModel", back_populates="dataset", cascade="all, delete-orphan")
    metadata_documents = relationship("MetadataDocumentModel", back_populates="dataset", cascade="all, delete-orphan")
    embeddings = relationship("EmbeddingModel", back_populates="dataset", cascade="all, delete-orphan")


class ContactModel(Base):
    """Contact information for datasets."""
    __tablename__ = 'contacts'
    
    id = Column(String(36), primary_key=True)
    dataset_id = Column(String(36), ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Name components
    family_name = Column(String(200))
    given_name = Column(String(200))
    full_name = Column(String(500))
    honorific_prefix = Column(String(50))
    
    # Organization
    organization_name = Column(String(500))
    organization_identifier = Column(String(500))  # RoR ID
    
    # Contact details
    email = Column(String(255))
    role = Column(String(100), nullable=False)
    name_identifier = Column(String(500))  # ORCID
    
    # Address (JSON for flexibility)
    address = Column(JSON)
    
    # Relationship
    dataset = relationship("DatasetModel", back_populates="contacts")


class KeywordModel(Base):
    """Keywords and subject terms."""
    __tablename__ = 'keywords'
    
    id = Column(String(36), primary_key=True)
    dataset_id = Column(String(36), ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False, index=True)
    
    keyword = Column(String(500), nullable=False)
    keyword_type = Column(String(50))  # theme, other, place, project
    uri = Column(String(500))  # Ontology URI
    in_defined_term_set = Column(String(500))  # from JSON-LD
    
    # Relationship
    dataset = relationship("DatasetModel", back_populates="keywords")


class RelationshipModel(Base):
    """Dataset relationships (memberOf, relatedTo, etc.)."""
    __tablename__ = 'relationships'
    
    id = Column(String(36), primary_key=True)
    source_dataset_id = Column(String(36), ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False, index=True)
    relation_type = Column(String(100), nullable=False)
    target_dataset_id = Column(String(255), nullable=False)
    
    # Relationship
    source_dataset = relationship("DatasetModel", back_populates="relationships",
                                 foreign_keys=[source_dataset_id])


class OnlineResourceModel(Base):
    """Online resources and download links."""
    __tablename__ = 'online_resources'
    
    id = Column(String(36), primary_key=True)
    dataset_id = Column(String(36), ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False, index=True)
    
    url = Column(Text, nullable=False)
    name = Column(String(500))
    description = Column(Text)
    function = Column(String(100))  # download, information, etc.
    resource_type = Column(String(100))
    
    # Relationship
    dataset = relationship("DatasetModel", back_populates="online_resources")


class MetadataDocumentModel(Base):
    """Raw metadata documents in multiple formats."""
    __tablename__ = 'metadata_documents'
    
    id = Column(String(36), primary_key=True)
    dataset_id = Column(String(36), ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False, index=True)
    
    format = Column(String(20), nullable=False)  # xml, json, jsonld, rdf
    content = Column(Text, nullable=False)
    file_size = Column(Integer)
    downloaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    dataset = relationship("DatasetModel", back_populates="metadata_documents")


class EmbeddingModel(Base):
    """Vector embeddings for semantic search."""
    __tablename__ = 'embeddings'
    
    id = Column(String(36), primary_key=True)
    dataset_id = Column(String(36), ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False, index=True)
    
    embedding_model = Column(String(100))
    embedding_dimension = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    dataset = relationship("DatasetModel", back_populates="embeddings")