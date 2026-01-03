"""
JSON-LD extractor for Schema.org metadata.
"""

import json
from typing import Dict, Any
from .base_extractor import BaseExtractor
from ..core_interfaces import ExtractionError
from ..utils.date_utils import parse_date, parse_temporal_extent


class JSONLDExtractor(BaseExtractor):
    """Extractor for JSON-LD (Schema.org) metadata."""
    
    def get_source_type(self) -> str:
        return 'jsonld'
    
    def _parse_data(self, raw_data: bytes) -> Dict[str, Any]:
        """Parse Schema.org JSON-LD metadata."""
        try:
            data = json.loads(raw_data.decode('utf-8'))
            
            # JSON-LD has @graph array containing the dataset
            graph = data.get('@graph', [])
            dataset = None
            
            # Find the main dataset object
            for item in graph:
                if item.get('@type') == 'Dataset':
                    dataset = item
                    break
            
            if not dataset:
                raise ExtractionError("No Dataset found in JSON-LD")
            
            return {
                'file_identifier': dataset.get('@id', '').split('/')[-1],
                'title': dataset.get('name'),
                'abstract': dataset.get('description'),
                
                # Unique to JSON-LD
                'credit_text': dataset.get('creditText'),  # Formatted citation
                'is_accessible_for_free': dataset.get('isAccessibleForFree'),
                'date_published': parse_date(dataset.get('datePublished')),
                
                # Extract creators as ORCID URIs
                'creator_orcids': [
                    creator.get('@id') 
                    for creator in dataset.get('creator', [])
                    if isinstance(creator, dict) and '@id' in creator
                ],
                
                # Spatial coverage
                'spatial_coverage': self._extract_spatial(dataset, graph),
                
                # Temporal coverage
                'temporal_coverage': parse_temporal_extent(self._extract_temporal(dataset)),
                
                # License
                'license': dataset.get('license'),
                
                # Publisher
                'publisher_uri': dataset.get('publisher', {}).get('@id') if isinstance(dataset.get('publisher'), dict) else None,
                
                # Raw content
                'raw_jsonld': raw_data.decode('utf-8'),
                'raw_jsonld_size': len(raw_data)
            }
        except json.JSONDecodeError as e:
            raise ExtractionError(f"JSON-LD parsing failed: {e}")
    
    def _extract_spatial(self, dataset: dict, graph: list) -> Dict[str, Any]:
        """Extract spatial coverage from linked objects."""
        spatial_ref = dataset.get('spatialCoverage', [])
        if not spatial_ref:
            return None
        
        # Find the GeoShape in graph
        spatial_id = spatial_ref[0].get('@id') if spatial_ref else None
        if not spatial_id:
            return None
        
        for item in graph:
            if item.get('@id') == spatial_id:
                geo_ref = item.get('geo', {}).get('@id')
                # Find the GeoShape
                for geo_item in graph:
                    if geo_item.get('@id') == geo_ref:
                        box = geo_item.get('box', '')
                        if box:
                            # Parse "west south, east north"
                            try:
                                parts = box.split(',')
                                west_south = parts[0].strip().split()
                                east_north = parts[1].strip().split()
                                return {
                                    'west': float(west_south[0]),
                                    'south': float(west_south[1]),
                                    'east': float(east_north[0]),
                                    'north': float(east_north[1])
                                }
                            except:
                                pass
        return None
    
    def _extract_temporal(self, dataset: dict) -> Dict[str, str]:
        """Extract temporal coverage."""
        temporal = dataset.get('temporalCoverage', [])
        if not temporal:
            return None
        
        # Format: "2017-01-01/2017-12-31"
        temporal_str = temporal[0] if temporal else ''
        if '/' in temporal_str:
            parts = temporal_str.split('/')
            return {
                'start': parts[0],
                'end': parts[1] if len(parts) > 1 else None
            }
        return None
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate extracted data."""
        return bool(data.get('file_identifier')) and bool(data.get('title'))