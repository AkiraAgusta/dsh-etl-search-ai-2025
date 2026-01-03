"""
Base extractor with Template Method pattern.
"""

import requests
from abc import abstractmethod
from typing import Dict, Any
from loguru import logger
from ..core_interfaces import IExtractor, ExtractionError


class BaseExtractor(IExtractor):
    """Base class for all extractors."""
    
    def __init__(self, timeout: int = 30, retry_count: int = 3):
        self.timeout = timeout
        self.retry_count = retry_count
        self.session = requests.Session()
    
    def extract(self, source: str) -> Dict[str, Any]:
        """Template method for extraction workflow."""
        try:
            logger.info(f"Extracting from: {source}")
            
            if not self._validate_source(source):
                raise ExtractionError(f"Invalid source: {source}")
            
            raw_data = self._fetch_data(source)
            parsed_data = self._parse_data(raw_data)
            
            if not self.validate(parsed_data):
                raise ExtractionError("Data validation failed")
            
            logger.info(f"Successfully extracted from: {source}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise ExtractionError(f"Failed: {e}")
    
    def _validate_source(self, source: str) -> bool:
        """Validate source is accessible."""
        if not source or not isinstance(source, str):
            return False
        return source.startswith(('http://', 'https://'))
    
    def _fetch_data(self, source: str) -> bytes:
        """Fetch data with retry logic."""
        for attempt in range(self.retry_count):
            try:
                response = self.session.get(source, timeout=self.timeout)
                response.raise_for_status()
                return response.content
            except requests.RequestException as e:
                if attempt == self.retry_count - 1:
                    raise ExtractionError(f"Failed after {self.retry_count} attempts: {e}")
                logger.warning(f"Attempt {attempt + 1} failed, retrying...")
        raise ExtractionError(f"Failed to fetch: {source}")
    
    @abstractmethod
    def _parse_data(self, raw_data: bytes) -> Dict[str, Any]:
        """Parse raw data - implemented by subclasses."""
        pass
    
    @abstractmethod
    def get_source_type(self) -> str:
        """Return source type."""
        pass
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Default validation."""
        return data is not None and len(data) > 0