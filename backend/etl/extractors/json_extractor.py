"""
JSON extractor for CEH metadata.
"""

import json
from typing import Dict, Any, List
from .base_extractor import BaseExtractor
from ..core_interfaces import ExtractionError
from ..utils.date_utils import parse_date, parse_datetime, parse_temporal_extent


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
                
                # Dates
                'publication_date': parse_date(self._extract_publication_date(data)),
                'metadata_date': parse_datetime(data.get('metadataDate')),
                'updated_date': parse_date(data.get('updatedDate')),
                
                # Status and type
                'resource_status': data.get('resourceStatus'),
                'resource_type': data.get('type'),
                
                # Spatial extent
                'spatial_extent': self._extract_spatial_extent(data),
                
                # Temporal extent
                'temporal_extent': self._extract_temporal_extent(data),
                
                # Collections
                'contacts': self._extract_contacts(data),
                'keywords': self._extract_keywords(data),
                'relationships': self._extract_relationships(data),
                'online_resources': self._extract_online_resources(data),
                
                # Additional metadata (unexpected fields)
                'additional_metadata': self._extract_additional_metadata(data),
                
                # Raw content
                'raw_json': raw_data.decode('utf-8'),
                'raw_json_size': len(raw_data)
            }
        except json.JSONDecodeError as e:
            raise ExtractionError(f"JSON parsing failed: {e}")
    
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
    
    def _extract_temporal_extent(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract temporal coverage."""
        if 'temporalExtents' in data and data['temporalExtents']:
            extent = data['temporalExtents'][0]
            return parse_temporal_extent({
                'start': extent.get('begin'),
                'end': extent.get('end')
            })
        return None
    
    def _extract_contacts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all responsible parties (contacts), filtering out those without roles."""
        contacts = []
        
        # responsibleParties includes all roles
        for party in data.get('responsibleParties', []):
            # Skip contacts without a role (required field)
            role = party.get('role')
            if not role:
                continue
            
            contact = {
                'family_name': party.get('familyName'),
                'given_name': party.get('givenName'),
                'full_name': party.get('fullName'),
                'honorific_prefix': party.get('honorificPrefix'),
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
    
    def _extract_keywords(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract keywords from all categories, filtering out empty values."""
        keywords = []
        
        # Theme keywords
        for kw in data.get('keywordsTheme', []):
            keyword_value = kw.get('value')
            if keyword_value:  # Skip if None or empty
                keywords.append({
                    'keyword': keyword_value,
                    'keyword_type': 'theme',
                    'uri': kw.get('uri'),
                    'thesaurus': None
                })
        
        # Other keywords
        for kw in data.get('keywordsOther', []):
            keyword_value = kw.get('value') if isinstance(kw, dict) else kw
            if keyword_value:  # Skip if None or empty
                keywords.append({
                    'keyword': keyword_value,
                    'keyword_type': 'other',
                    'uri': kw.get('uri') if isinstance(kw, dict) else None,
                    'thesaurus': None
                })
        
        # Project keywords
        for kw in data.get('keywordsProject', []):
            keyword_value = kw.get('value') if isinstance(kw, dict) else kw
            if keyword_value:  # Skip if None or empty
                keywords.append({
                    'keyword': keyword_value,
                    'keyword_type': 'project',
                    'uri': None,
                    'thesaurus': None
                })
        
        # Place keywords
        for kw in data.get('keywordsPlace', []):
            keyword_value = kw.get('value') if isinstance(kw, dict) else kw
            if keyword_value:  # Skip if None or empty
                keywords.append({
                    'keyword': keyword_value,
                    'keyword_type': 'place',
                    'uri': kw.get('uri') if isinstance(kw, dict) else None,
                    'thesaurus': None
                })
        
        return keywords
    
    def _extract_relationships(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract relationships to other datasets."""
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
    
    def _extract_online_resources(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract online resources (downloads, WMS, etc.)."""
        resources = []
        
        for resource in data.get('onlineResources', []):
            resources.append({
                'url': resource.get('url'),
                'name': resource.get('name'),
                'description': resource.get('description'),
                'function': resource.get('function'),
                'resource_type': resource.get('type')
            })
        
        # Also check infoLinks
        for link in data.get('infoLinks', []):
            resources.append({
                'url': link.get('url'),
                'name': link.get('name'),
                'description': link.get('description'),
                'function': link.get('function'),
                'resource_type': link.get('type')
            })
        
        return resources
    
    def _extract_additional_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract fields that don't fit in core schema."""
        additional = {}
        
        # WMS service info
        if 'service' in data:
            additional['service'] = data['service']
        
        # Spatial resolutions
        if 'spatialResolutions' in data:
            additional['spatial_resolutions'] = data['spatialResolutions']
        
        # Distribution formats
        if 'distributionFormats' in data:
            additional['distribution_formats'] = data['distributionFormats']
        
        # Funding information
        if 'funding' in data:
            additional['funding'] = data['funding']
        
        # INSPIRE themes
        if 'inspireThemes' in data:
            additional['inspire_themes'] = data['inspireThemes']
        
        # Spatial reference systems
        if 'spatialReferenceSystems' in data:
            additional['spatial_reference_systems'] = data['spatialReferenceSystems']
        
        # Use constraints / licenses
        if 'useConstraints' in data:
            additional['use_constraints'] = data['useConstraints']
        
        if 'licences' in data:
            additional['licences'] = data['licences']
        
        # Topic categories
        if 'topicCategories' in data:
            additional['topic_categories'] = data['topicCategories']
        
        return additional if additional else None
    
    def _extract_publication_date(self, data: Dict[str, Any]) -> str:
        """Extract publication date string from various possible locations."""
        # Direct field
        if 'publicationDate' in data:
            return data['publicationDate']
        
        # datasetReferenceDate
        if 'datasetReferenceDate' in data:
            ref_date = data['datasetReferenceDate']
            if 'publicationDate' in ref_date:
                return ref_date['publicationDate']
        
        return None
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate extracted data."""
        return bool(data.get('file_identifier')) and bool(data.get('title'))