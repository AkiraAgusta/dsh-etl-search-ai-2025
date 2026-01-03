"""
Repository for dataset persistence.
Handles mapping between domain models and database models.
Filters out backward-compatibility fields that aren't in the database.
"""

from typing import List, Optional
from uuid import uuid4
from sqlalchemy.orm import Session

from ..models.database import (
    DatasetModel, ContactModel, KeywordModel, RelationshipModel,
    OnlineResourceModel, MetadataDocumentModel
)
from ..models.dataset import (
    Dataset, Contact, Keyword, Relationship, OnlineResource,
    MetadataDocument, SpatialExtent, TemporalExtent
)


class DatasetRepository:
    """Repository for dataset CRUD operations."""
    
    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session
    
    def add(self, dataset: Dataset) -> Dataset:
        """
        Add a new dataset to the database.
        
        Args:
            dataset: Dataset domain model
            
        Returns:
            Dataset with generated ID
        """
        # Convert to database model
        db_dataset = self._to_db_model(dataset)
        
        # Add to session
        self.session.add(db_dataset)
        
        # Update domain model with generated ID
        dataset.id = db_dataset.id
        
        return dataset
    
    def get_by_id(self, dataset_id: str) -> Optional[Dataset]:
        """Get dataset by ID."""
        db_dataset = self.session.query(DatasetModel).filter_by(id=dataset_id).first()
        return self._to_domain_model(db_dataset) if db_dataset else None
    
    def get_by_file_identifier(self, file_identifier: str) -> Optional[Dataset]:
        """Get dataset by file identifier."""
        db_dataset = self.session.query(DatasetModel).filter_by(file_identifier=file_identifier).first()
        return self._to_domain_model(db_dataset) if db_dataset else None
    
    def get_all(self) -> List[Dataset]:
        """Get all datasets."""
        db_datasets = self.session.query(DatasetModel).all()
        return [self._to_domain_model(ds) for ds in db_datasets]
    
    def update(self, dataset: Dataset) -> Dataset:
        """Update existing dataset."""
        db_dataset = self.session.query(DatasetModel).filter_by(id=dataset.id).first()
        if not db_dataset:
            raise ValueError(f"Dataset {dataset.id} not found")
        
        # Update fields
        self._update_db_model(db_dataset, dataset)
        
        return dataset
    
    def delete(self, dataset_id: str) -> bool:
        """Delete dataset by ID."""
        db_dataset = self.session.query(DatasetModel).filter_by(id=dataset_id).first()
        if db_dataset:
            self.session.delete(db_dataset)
            return True
        return False
    
    def _to_db_model(self, dataset: Dataset) -> DatasetModel:
        """Convert domain model to database model."""
        # Generate ID if not present
        dataset_id = dataset.id or str(uuid4())
        
        # Create dataset model (filtering out backward-compatibility fields)
        db_dataset = DatasetModel(
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
            # Note: purpose and creation_date are NOT included (removed from schema)
        )
        
        # Add spatial extent
        if dataset.spatial_extent:
            db_dataset.spatial_west = str(dataset.spatial_extent.west)
            db_dataset.spatial_east = str(dataset.spatial_extent.east)
            db_dataset.spatial_south = str(dataset.spatial_extent.south)
            db_dataset.spatial_north = str(dataset.spatial_extent.north)
        
        # Add temporal extent
        if dataset.temporal_extent:
            db_dataset.temporal_start = dataset.temporal_extent.start
            db_dataset.temporal_end = dataset.temporal_extent.end
        
        # Add contacts (filtering out position_name and individual_name)
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
                # Note: position_name and individual_name are NOT included (removed from schema)
            )
            db_dataset.contacts.append(db_contact)
        
        # Add keywords (filtering out thesaurus)
        for keyword in dataset.keywords:
            db_keyword = KeywordModel(
                id=str(uuid4()),
                dataset_id=dataset_id,
                keyword=keyword.keyword,
                keyword_type=keyword.keyword_type,
                uri=keyword.uri,
                in_defined_term_set=keyword.in_defined_term_set,
                # Note: thesaurus is NOT included (removed from schema)
            )
            db_dataset.keywords.append(db_keyword)
        
        # Add relationships
        for relationship in dataset.relationships:
            db_rel = RelationshipModel(
                id=str(uuid4()),
                source_dataset_id=dataset_id,
                relation_type=relationship.relation_type,
                target_dataset_id=relationship.target_dataset_id
            )
            db_dataset.relationships.append(db_rel)
        
        # Add online resources
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
        
        # Add metadata documents
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
        
        return db_dataset
    
    def _to_domain_model(self, db_dataset: DatasetModel) -> Dataset:
        """Convert database model to domain model."""
        # Create spatial extent
        spatial_extent = None
        if db_dataset.spatial_west:
            spatial_extent = SpatialExtent(
                west=float(db_dataset.spatial_west),
                east=float(db_dataset.spatial_east),
                south=float(db_dataset.spatial_south),
                north=float(db_dataset.spatial_north)
            )
        
        # Create temporal extent
        temporal_extent = None
        if db_dataset.temporal_start:
            temporal_extent = TemporalExtent(
                start=db_dataset.temporal_start,
                end=db_dataset.temporal_end
            )
        
        # Convert contacts
        contacts = [
            Contact(
                family_name=c.family_name,
                given_name=c.given_name,
                full_name=c.full_name,
                honorific_prefix=c.honorific_prefix,
                organization_name=c.organization_name,
                organization_identifier=c.organization_identifier,
                email=c.email,
                role=c.role,
                name_identifier=c.name_identifier,
                address=c.address
            )
            for c in db_dataset.contacts
        ]
        
        # Convert keywords
        keywords = [
            Keyword(
                keyword=k.keyword,
                keyword_type=k.keyword_type,
                uri=k.uri,
                in_defined_term_set=k.in_defined_term_set
            )
            for k in db_dataset.keywords
        ]
        
        # Convert relationships
        relationships = [
            Relationship(
                relation_type=r.relation_type,
                target_dataset_id=r.target_dataset_id
            )
            for r in db_dataset.relationships
        ]
        
        # Convert online resources
        online_resources = [
            OnlineResource(
                url=r.url,
                name=r.name,
                description=r.description,
                function=r.function,
                resource_type=r.resource_type
            )
            for r in db_dataset.online_resources
        ]
        
        # Convert metadata documents
        metadata_documents = [
            MetadataDocument(
                format=d.format,
                content=d.content,
                file_size=d.file_size,
                downloaded_at=d.downloaded_at
            )
            for d in db_dataset.metadata_documents
        ]
        
        # Create domain model
        return Dataset(
            id=db_dataset.id,
            file_identifier=db_dataset.file_identifier,
            title=db_dataset.title,
            abstract=db_dataset.abstract,
            description=db_dataset.description,
            lineage=db_dataset.lineage,
            publication_date=db_dataset.publication_date,
            metadata_date=db_dataset.metadata_date,
            updated_date=db_dataset.updated_date,
            metadata_standard=db_dataset.metadata_standard,
            metadata_standard_version=db_dataset.metadata_standard_version,
            language=db_dataset.language,
            resource_status=db_dataset.resource_status,
            resource_type=db_dataset.resource_type,
            spatial_extent=spatial_extent,
            temporal_extent=temporal_extent,
            credit_text=db_dataset.credit_text,
            is_accessible_for_free=db_dataset.is_accessible_for_free,
            contacts=contacts,
            keywords=keywords,
            relationships=relationships,
            online_resources=online_resources,
            metadata_documents=metadata_documents,
            additional_metadata=db_dataset.additional_metadata,
            created_at=db_dataset.created_at,
            updated_at=db_dataset.updated_at
        )
    
    def _update_db_model(self, db_dataset: DatasetModel, dataset: Dataset):
        """Update database model from domain model."""
        # Update fields
        db_dataset.file_identifier = dataset.file_identifier
        db_dataset.title = dataset.title
        db_dataset.abstract = dataset.abstract
        db_dataset.description = dataset.description
        db_dataset.lineage = dataset.lineage
        db_dataset.publication_date = dataset.publication_date
        db_dataset.metadata_date = dataset.metadata_date
        db_dataset.updated_date = dataset.updated_date
        db_dataset.metadata_standard = dataset.metadata_standard
        db_dataset.metadata_standard_version = dataset.metadata_standard_version
        db_dataset.language = dataset.language
        db_dataset.resource_status = dataset.resource_status
        db_dataset.resource_type = dataset.resource_type
        db_dataset.credit_text = dataset.credit_text
        db_dataset.is_accessible_for_free = dataset.is_accessible_for_free
        db_dataset.additional_metadata = dataset.additional_metadata
        
        # Update spatial extent
        if dataset.spatial_extent:
            db_dataset.spatial_west = str(dataset.spatial_extent.west)
            db_dataset.spatial_east = str(dataset.spatial_extent.east)
            db_dataset.spatial_south = str(dataset.spatial_extent.south)
            db_dataset.spatial_north = str(dataset.spatial_extent.north)
        
        # Update temporal extent
        if dataset.temporal_extent:
            db_dataset.temporal_start = dataset.temporal_extent.start
            db_dataset.temporal_end = dataset.temporal_extent.end