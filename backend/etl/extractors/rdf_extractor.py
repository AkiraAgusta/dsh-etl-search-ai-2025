"""
RDF/Turtle extractor for linked data.
"""

from typing import Dict, Any
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import DCTERMS, DCAT, RDF
from .base_extractor import BaseExtractor
from ..core_interfaces import ExtractionError
from ..utils.date_utils import parse_date, parse_temporal_extent


class RDFExtractor(BaseExtractor):
    """Extractor for RDF/Turtle metadata."""
    
    def get_source_type(self) -> str:
        return 'rdf'
    
    def _parse_data(self, raw_data: bytes) -> Dict[str, Any]:
        """Parse RDF/Turtle metadata."""
        try:
            # Parse RDF graph
            g = Graph()
            g.parse(data=raw_data.decode('utf-8'), format='turtle')
            
            # Find the main dataset subject
            dataset_uri = None
            for s in g.subjects(RDF.type, DCAT.Dataset):
                dataset_uri = s
                break
            
            if not dataset_uri:
                raise ExtractionError("No Dataset found in RDF")
            
            return {
                'file_identifier': str(dataset_uri).split('/')[-1],
                'title': self._get_value(g, dataset_uri, DCTERMS.title),
                'abstract': self._get_value(g, dataset_uri, DCTERMS.description),
                
                # Unique to RDF
                'language_uri': self._get_uri(g, dataset_uri, DCTERMS.language),
                'bibliographic_citation': self._get_value(g, dataset_uri, DCTERMS.bibliographicCitation),
                'provenance': self._get_provenance(g, dataset_uri),
                
                # Dates
                'date_available': parse_date(self._get_value(g, dataset_uri, DCTERMS.available)),
                
                # Relationships (isPartOf)
                'is_part_of': self._get_uris(g, dataset_uri, DCTERMS.isPartOf),
                
                # License
                'license_uri': self._get_uri(g, dataset_uri, DCTERMS.license),
                
                # Access rights
                'access_rights_uri': self._get_uri(g, dataset_uri, DCTERMS.accessRights),
                
                # Creators (ORCID URIs)
                'creator_uris': self._get_uris(g, dataset_uri, DCTERMS.creator),
                
                # Spatial (WKT format)
                'spatial_wkt': self._get_spatial_wkt(g, dataset_uri),
                
                # Temporal
                'temporal_period': parse_temporal_extent(self._get_temporal(g, dataset_uri)),
                
                # Landing pages
                'landing_pages': self._get_uris(g, dataset_uri, DCAT.landingPage),
                
                # Raw content
                'raw_rdf': raw_data.decode('utf-8'),
                'raw_rdf_size': len(raw_data)
            }
        except Exception as e:
            raise ExtractionError(f"RDF parsing failed: {e}")
    
    def _get_value(self, g: Graph, subject: URIRef, predicate: URIRef) -> str:
        """Get literal value from RDF graph."""
        for obj in g.objects(subject, predicate):
            return str(obj)
        return None
    
    def _get_uri(self, g: Graph, subject: URIRef, predicate: URIRef) -> str:
        """Get URI value from RDF graph."""
        for obj in g.objects(subject, predicate):
            if isinstance(obj, URIRef):
                return str(obj)
        return None
    
    def _get_uris(self, g: Graph, subject: URIRef, predicate: URIRef) -> list:
        """Get all URI values from RDF graph."""
        return [str(obj) for obj in g.objects(subject, predicate) if isinstance(obj, URIRef)]
    
    def _get_provenance(self, g: Graph, subject: URIRef) -> str:
        """Extract provenance statement."""
        PROV = Namespace("http://www.w3.org/ns/prov#")
        for prov_node in g.objects(subject, DCTERMS.provenance):
            for label in g.objects(prov_node, URIRef("http://www.w3.org/2000/01/rdf-schema#label")):
                return str(label)
        return None
    
    def _get_spatial_wkt(self, g: Graph, subject: URIRef) -> str:
        """Extract spatial coverage as WKT."""
        for spatial_node in g.objects(subject, DCTERMS.spatial):
            bbox_pred = URIRef("http://www.w3.org/ns/dcat#bbox")
            for bbox in g.objects(spatial_node, bbox_pred):
                return str(bbox)
        return None
    
    def _get_temporal(self, g: Graph, subject: URIRef) -> Dict[str, str]:
        """Extract temporal period."""
        for temporal_node in g.objects(subject, DCTERMS.temporal):
            start_pred = URIRef("http://www.w3.org/ns/dcat#startDate")
            end_pred = URIRef("http://www.w3.org/ns/dcat#endDate")
            
            start = None
            end = None
            
            for s in g.objects(temporal_node, start_pred):
                start = str(s)
            for e in g.objects(temporal_node, end_pred):
                end = str(e)
            
            if start or end:
                return {'start': start, 'end': end}
        return None
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate extracted data."""
        return bool(data.get('file_identifier')) and bool(data.get('title'))