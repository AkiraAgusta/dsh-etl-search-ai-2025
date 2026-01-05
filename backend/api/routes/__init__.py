"""
API routes package.

Contains all API route handlers organized by domain:
- datasets: Dataset listing and retrieval
- search: Semantic and hybrid search
- utils: Health checks and statistics
"""

from . import datasets, search, utils

__all__ = ['datasets', 'search', 'utils']