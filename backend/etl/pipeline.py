"""
ETL Pipeline - Optimized for all 4 metadata formats.
Intelligently merges XML, JSON, JSON-LD, and RDF data.
"""

from typing import Optional
from loguru import logger
from sqlalchemy.orm import Session

from .extractors import XMLExtractor, JSONExtractor, JSONLDExtractor, RDFExtractor
from .repositories import DatasetRepository
from .models.dataset import (
    Dataset, Contact, Keyword, Relationship, OnlineResource,
    MetadataDocument, SpatialExtent, TemporalExtent
)


class ETLPipeline:
    """
    Complete ETL pipeline for CEH metadata.
    Downloads and merges data from all 4 formats.
    """
    
    def __init__(self, session: Session):
        """Initialize pipeline with database session."""
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
        
        Args:
            file_identifier: Dataset identifier
            
        Returns:
            Dataset object if successful, None otherwise
        """
        try:
            logger.info(f"Processing dataset: {file_identifier}")
            
            # Extract from all 4 formats
            xml_data = self._extract_xml(file_identifier)
            json_data = self._extract_json(file_identifier)
            jsonld_data = self._extract_jsonld(file_identifier)
            rdf_data = self._extract_rdf(file_identifier)
            
            # Check if we have at least one format
            if not any([xml_data, json_data, jsonld_data, rdf_data]):
                logger.error(f"No data extracted for {file_identifier}")
                return None
            
            # Merge data from all sources
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
    
    def _extract_xml(self, file_identifier: str) -> Optional[dict]:
        """Extract XML metadata."""
        try:
            url = f"https://catalogue.ceh.ac.uk/documents/{file_identifier}.xml"
            return self.xml_extractor.extract(url)
        except Exception as e:
            logger.warning(f"XML extraction failed: {e}")
            return None
    
    def _extract_json(self, file_identifier: str) -> Optional[dict]:
        """Extract JSON metadata."""
        try:
            url = f"https://catalogue.ceh.ac.uk/documents/{file_identifier}?format=json"
            return self.json_extractor.extract(url)
        except Exception as e:
            logger.warning(f"JSON extraction failed: {e}")
            return None
    
    def _extract_jsonld(self, file_identifier: str) -> Optional[dict]:
        """Extract JSON-LD metadata."""
        try:
            url = f"https://catalogue.ceh.ac.uk/documents/{file_identifier}?format=schema.org"
            return self.jsonld_extractor.extract(url)
        except Exception as e:
            logger.warning(f"JSON-LD extraction failed: {e}")
            return None
    
    def _extract_rdf(self, file_identifier: str) -> Optional[dict]:
        """Extract RDF metadata."""
        try:
            url = f"https://catalogue.ceh.ac.uk/documents/{file_identifier}?format=ttl"
            return self.rdf_extractor.extract(url)
        except Exception as e:
            logger.warning(f"RDF extraction failed: {e}")
            return None
    
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
        
        Priority:
        - Core metadata: JSON (richest)
        - ISO 19115 fields: XML
        - Citation: JSON-LD or RDF
        - Relationships: JSON (most detailed)
        - Contacts: JSON (most detailed)
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
            
            # Core metadata - prefer JSON (richest descriptions)
            title=coalesce(
                json_data.get('title') if json_data else None,
                jsonld_data.get('title') if jsonld_data else None,
                xml_data.get('title') if xml_data else None,
                rdf_data.get('title') if rdf_data else None
            ),
            abstract=coalesce(
                json_data.get('abstract') if json_data else None,
                jsonld_data.get('abstract') if jsonld_data else None,
                xml_data.get('abstract') if xml_data else None,
                rdf_data.get('abstract') if rdf_data else None
            ),
            description=json_data.get('description') if json_data else None,
            lineage=coalesce(
                json_data.get('lineage') if json_data else None,
                xml_data.get('lineage') if xml_data else None
            ),
            
            # Dates
            publication_date=coalesce(
                json_data.get('publication_date') if json_data else None,
                xml_data.get('publication_date') if xml_data else None,
                jsonld_data.get('date_published') if jsonld_data else None
            ),
            metadata_date=coalesce(
                json_data.get('metadata_date') if json_data else None,
                xml_data.get('metadata_date') if xml_data else None
            ),
            updated_date=json_data.get('updated_date') if json_data else None,  # Only in JSON
            
            # ISO 19115 fields - from XML (most complete) or RDF
            metadata_standard=xml_data.get('metadata_standard') if xml_data else None,
            metadata_standard_version=xml_data.get('metadata_standard_version') if xml_data else None,
            language=coalesce(
                xml_data.get('language') if xml_data else None,
                rdf_data.get('language_uri') if rdf_data else None
            ),
            
            # Status and type
            resource_status=json_data.get('resource_status') if json_data else None,
            resource_type=coalesce(
                json_data.get('resource_type') if json_data else None,
                xml_data.get('resource_type') if xml_data else None
            ),
            
            # Citation and accessibility - from JSON-LD/RDF
            credit_text=coalesce(
                jsonld_data.get('credit_text') if jsonld_data else None,
                rdf_data.get('bibliographic_citation') if rdf_data else None
            ),
            is_accessible_for_free=jsonld_data.get('is_accessible_for_free') if jsonld_data else None,
            
            # Additional metadata from JSON
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
            dataset.spatial_extent = SpatialExtent(
                west=spatial.get('west'),
                east=spatial.get('east'),
                south=spatial.get('south'),
                north=spatial.get('north')
            )
        
        # Merge temporal extent (prefer JSON, fallback to others)
        temporal = None
        if json_data and json_data.get('temporal_extent'):
            temporal = json_data['temporal_extent']
        elif xml_data and xml_data.get('temporal_extent'):
            temporal = xml_data['temporal_extent']
        elif jsonld_data and jsonld_data.get('temporal_coverage'):
            temporal = jsonld_data['temporal_coverage']
        
        if temporal:
            dataset.temporal_extent = TemporalExtent(
                start=temporal.get('start'),
                end=temporal.get('end')
            )
        
        # Merge contacts (prefer JSON - most detailed)
        if json_data and json_data.get('contacts'):
            dataset.contacts = [
                Contact(**contact) for contact in json_data['contacts']
            ]
        elif xml_data and xml_data.get('contacts'):
            dataset.contacts = [
                Contact(**contact) for contact in xml_data['contacts']
            ]
        
        # Merge keywords (prefer JSON - typed)
        if json_data and json_data.get('keywords'):
            dataset.keywords = [
                Keyword(**kw) for kw in json_data['keywords']
            ]
        elif xml_data and xml_data.get('keywords'):
            dataset.keywords = [
                Keyword(**kw) for kw in xml_data['keywords']
            ]
        
        # Enhance keywords with JSON-LD term sets
        if jsonld_data and jsonld_data.get('keywords_with_term_sets'):
            # Map by keyword value and add in_defined_term_set
            term_sets = {kw['keyword']: kw.get('in_defined_term_set') 
                        for kw in jsonld_data['keywords_with_term_sets']}
            for kw in dataset.keywords:
                if kw.keyword in term_sets:
                    kw.in_defined_term_set = term_sets[kw.keyword]
        
        # Merge relationships (from JSON - most complete)
        if json_data and json_data.get('relationships'):
            dataset.relationships = [
                Relationship(**rel) for rel in json_data['relationships']
            ]
        
        # Merge online resources (from JSON)
        if json_data and json_data.get('online_resources'):
            dataset.online_resources = [
                OnlineResource(**res) for res in json_data['online_resources']
            ]
        
        # Add raw metadata documents
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
        
        if jsonld_data and jsonld_data.get('raw_jsonld'):
            dataset.metadata_documents.append(
                MetadataDocument(
                    format='jsonld',
                    content=jsonld_data['raw_jsonld'],
                    file_size=jsonld_data.get('raw_jsonld_size', 0)
                )
            )
        
        if rdf_data and rdf_data.get('raw_rdf'):
            dataset.metadata_documents.append(
                MetadataDocument(
                    format='rdf',
                    content=rdf_data['raw_rdf'],
                    file_size=rdf_data.get('raw_rdf_size', 0)
                )
            )
        
        return dataset