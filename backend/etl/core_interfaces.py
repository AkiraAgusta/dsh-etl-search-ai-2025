"""
Core interfaces for the ETL subsystem.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class IExtractor(ABC):
    """Abstract interface for data extraction."""
    
    @abstractmethod
    def extract(self, source: str) -> Dict[str, Any]:
        """Extract data from source."""
        pass
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate extracted data."""
        pass
    
    @abstractmethod
    def get_source_type(self) -> str:
        """Get source type identifier."""
        pass


class ExtractionError(Exception):
    """Extraction failed."""
    pass