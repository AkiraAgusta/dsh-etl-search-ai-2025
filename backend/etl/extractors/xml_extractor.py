"""
XML extractor for ISO 19115 metadata.
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from .base_extractor import BaseExtractor
from ..core_interfaces import ExtractionError
from ..utils.date_utils import parse_date, parse_datetime, parse_temporal_extent


class XMLExtractor(BaseExtractor):
    """Extractor for ISO 19115 XML."""
    
    NAMESPACES = {
        'gmd': 'http://www.isotc211.org/2005/gmd',
        'gco': 'http://www.isotc211.org/2005/gco',
        'gml': 'http://www.opengis.net/gml/3.2',
        'gmx': 'http://www.isotc211.org/2005/gmx',
    }
    
    def get_source_type(self) -> str:
        return 'xml'
    
    def _parse_data(self, raw_data: bytes) -> Dict[str, Any]:
        """Parse ISO 19115 XML."""
        try:
            root = ET.fromstring(raw_data)
            
            return {
                'file_identifier': self._extract_file_identifier(root),
                'title': self._extract_title(root),
                'abstract': self._extract_abstract(root),
                'purpose': self._extract_purpose(root),
                'lineage': self._extract_lineage(root),
                
                'contacts': self._extract_contacts(root),
                'keywords': self._extract_keywords(root),
                'online_resources': self._extract_online_resources(root),
                
                'temporal_extent': parse_temporal_extent(self._extract_temporal_extent(root)),
                'spatial_extent': self._extract_spatial_extent(root),
                
                'creation_date': parse_date(self._extract_date(root, 'creation')),
                'publication_date': parse_date(self._extract_date(root, 'publication')),
                'metadata_date': parse_datetime(self._extract_metadata_date_string(root)),
                
                'metadata_standard': self._extract_metadata_standard(root),
                'metadata_standard_version': self._extract_metadata_standard_version(root),
                'language': self._extract_language(root),
                
                'raw_xml': raw_data.decode('utf-8'),
                'raw_xml_size': len(raw_data)
            }
        except ET.ParseError as e:
            raise ExtractionError(f"XML parsing failed: {e}")
    
    def _extract_file_identifier(self, root: ET.Element) -> Optional[str]:
        elem = root.find('.//gmd:fileIdentifier/gco:CharacterString', self.NAMESPACES)
        return elem.text if elem is not None else None
    
    def _extract_title(self, root: ET.Element) -> Optional[str]:
        elem = root.find('.//gmd:identificationInfo//gmd:citation//gmd:title/gco:CharacterString', self.NAMESPACES)
        return elem.text if elem is not None else None
    
    def _extract_abstract(self, root: ET.Element) -> Optional[str]:
        elem = root.find('.//gmd:identificationInfo//gmd:abstract/gco:CharacterString', self.NAMESPACES)
        return elem.text if elem is not None else None
    
    def _extract_purpose(self, root: ET.Element) -> Optional[str]:
        elem = root.find('.//gmd:identificationInfo//gmd:purpose/gco:CharacterString', self.NAMESPACES)
        return elem.text if elem is not None else None
    
    def _extract_lineage(self, root: ET.Element) -> Optional[str]:
        elem = root.find('.//gmd:lineage//gmd:statement/gco:CharacterString', self.NAMESPACES)
        return elem.text if elem is not None else None
    
    def _extract_contacts(self, root: ET.Element) -> List[Dict]:
        """Extract contacts - handle both CharacterString and Anchor."""
        contacts = []
        contact_elems = root.findall('.//gmd:contact//gmd:CI_ResponsibleParty', self.NAMESPACES)
        contact_elems += root.findall('.//gmd:identificationInfo//gmd:pointOfContact//gmd:CI_ResponsibleParty', self.NAMESPACES)
        
        for elem in contact_elems:
            contact = {}
            
            # Individual name - try both CharacterString and Anchor
            ind = elem.find('.//gmd:individualName/gco:CharacterString', self.NAMESPACES)
            if ind is None:
                ind = elem.find('.//gmd:individualName/gmx:Anchor', self.NAMESPACES)
            if ind is not None:
                contact['individual_name'] = ind.text
                
                # Check for ORCID in Anchor
                if ind.tag.endswith('Anchor') and 'href' in ind.attrib:
                    href = ind.attrib['{http://www.w3.org/1999/xlink}href']
                    if 'orcid.org' in href:
                        contact['name_identifier'] = href
            
            # Organization name
            org = elem.find('.//gmd:organisationName/gco:CharacterString', self.NAMESPACES)
            if org is None:
                org = elem.find('.//gmd:organisationName/gmx:Anchor', self.NAMESPACES)
            if org is not None:
                contact['organization_name'] = org.text
                
                # Check for RoR ID
                if org.tag.endswith('Anchor') and 'href' in org.attrib:
                    href = org.attrib['{http://www.w3.org/1999/xlink}href']
                    if 'ror.org' in href:
                        contact['organization_identifier'] = href
            
            # Email
            email = elem.find('.//gmd:electronicMailAddress/gco:CharacterString', self.NAMESPACES)
            if email is not None:
                contact['email'] = email.text.strip()
            
            # Role (required field)
            role = elem.find('.//gmd:role//gmd:CI_RoleCode', self.NAMESPACES)
            if role is not None and 'codeListValue' in role.attrib:
                contact['role'] = role.attrib['codeListValue']
            
            # Only add contact if it has a role (required field)
            if contact and 'role' in contact:
                contacts.append(contact)
        
        return contacts
    
    def _extract_keywords(self, root: ET.Element) -> List[Dict]:
        keywords = []
        kw_elems = root.findall('.//gmd:descriptiveKeywords//gmd:MD_Keywords', self.NAMESPACES)
        
        for elem in kw_elems:
            kw_list = elem.findall('.//gmd:keyword/gco:CharacterString', self.NAMESPACES)
            for kw in kw_list:
                if kw.text:
                    keywords.append({
                        'keyword': kw.text,
                        'keyword_type': 'theme',  # Default to theme for XML
                        'thesaurus': None
                    })
        
        return keywords
    
    def _extract_online_resources(self, root: ET.Element) -> List[Dict]:
        """Extract online resources (download URLs, WMS, etc.)."""
        resources = []
        
        # Distribution info - data downloads and supporting docs
        resource_elems = root.findall('.//gmd:distributionInfo//gmd:transferOptions//gmd:onLine//gmd:CI_OnlineResource', self.NAMESPACES)
        
        for elem in resource_elems:
            url_elem = elem.find('.//gmd:URL', self.NAMESPACES)
            if url_elem is None or not url_elem.text:
                continue
            
            name_elem = elem.find('.//gmd:name/gco:CharacterString', self.NAMESPACES)
            desc_elem = elem.find('.//gmd:description/gco:CharacterString', self.NAMESPACES)
            func_elem = elem.find('.//gmd:function//gmd:CI_OnLineFunctionCode', self.NAMESPACES)
            
            function = func_elem.attrib.get('codeListValue') if func_elem is not None else None
            
            resources.append({
                'url': url_elem.text,
                'name': name_elem.text if name_elem is not None else None,
                'description': desc_elem.text if desc_elem is not None else None,
                'function': function,
                'resource_type': 'OTHER'
            })
        
        return resources
    
    def _extract_temporal_extent(self, root: ET.Element) -> Optional[Dict]:
        start = root.find('.//gmd:temporalElement//gml:TimePeriod//gml:beginPosition', self.NAMESPACES)
        end = root.find('.//gmd:temporalElement//gml:TimePeriod//gml:endPosition', self.NAMESPACES)
        
        if start is not None or end is not None:
            return {
                'start': start.text if start is not None else None,
                'end': end.text if end is not None else None
            }
        return None
    
    def _extract_spatial_extent(self, root: ET.Element) -> Optional[Dict]:
        west = root.find('.//gmd:westBoundLongitude/gco:Decimal', self.NAMESPACES)
        east = root.find('.//gmd:eastBoundLongitude/gco:Decimal', self.NAMESPACES)
        south = root.find('.//gmd:southBoundLatitude/gco:Decimal', self.NAMESPACES)
        north = root.find('.//gmd:northBoundLatitude/gco:Decimal', self.NAMESPACES)
        
        if all([west, east, south, north]):
            return {
                'west': float(west.text),
                'east': float(east.text),
                'south': float(south.text),
                'north': float(north.text)
            }
        return None
    
    def _extract_date(self, root: ET.Element, date_type: str) -> Optional[str]:
        """Extract date by type (creation, publication, etc.)."""
        date_elem = root.find(
            f'.//gmd:identificationInfo//gmd:citation//gmd:date//gmd:dateType//gmd:CI_DateTypeCode[@codeListValue="{date_type}"]/../../../gmd:date/gco:Date',
            self.NAMESPACES
        )
        return date_elem.text if date_elem is not None else None
    
    def _extract_metadata_date_string(self, root: ET.Element) -> Optional[str]:
        """Extract metadata date stamp as string."""
        date_elem = root.find('.//gmd:dateStamp/gco:DateTime', self.NAMESPACES)
        if date_elem is None:
            date_elem = root.find('.//gmd:dateStamp/gco:Date', self.NAMESPACES)
        
        return date_elem.text if date_elem is not None else None
    
    def _extract_metadata_standard(self, root: ET.Element) -> Optional[str]:
        elem = root.find('.//gmd:metadataStandardName/gco:CharacterString', self.NAMESPACES)
        if elem is None:
            elem = root.find('.//gmd:metadataStandardName/gmx:Anchor', self.NAMESPACES)
        return elem.text if elem is not None else None
    
    def _extract_metadata_standard_version(self, root: ET.Element) -> Optional[str]:
        elem = root.find('.//gmd:metadataStandardVersion/gco:CharacterString', self.NAMESPACES)
        return elem.text if elem is not None else None
    
    def _extract_language(self, root: ET.Element) -> Optional[str]:
        elem = root.find('.//gmd:language/gco:CharacterString', self.NAMESPACES)
        if elem is None:
            elem = root.find('.//gmd:language//gmd:LanguageCode', self.NAMESPACES)
            if elem is not None and 'codeListValue' in elem.attrib:
                return elem.attrib['codeListValue']
        return elem.text if elem is not None else None
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate required fields."""
        return bool(data.get('file_identifier')) and bool(data.get('title'))