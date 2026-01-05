"""
API configuration settings.

This module defines all configuration settings for the API including
database connections, CORS settings, and other environment-specific configurations.
"""

from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    # API Info
    app_name: str = "CEH Datasets API"
    app_version: str = "1.0.0"
    app_description: str = "Semantic search and discovery API for CEH environmental datasets"
    
    # Database
    database_url: str = "sqlite:///data/datasets.db"
    
    # Embeddings
    faiss_index_path: str = "data/faiss_index.bin"
    metadata_path: str = "data/dataset_mapping.pkl"
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # API Settings
    api_prefix: str = "/api"
    debug: bool = False
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",      # Svelte dev server
        "http://localhost:5173",      # Vite dev server
        "http://localhost:8080",      # Alternative dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Search
    default_top_k: int = 10
    max_top_k: int = 100
    
    # Rate limiting (future)
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using lru_cache ensures settings are loaded only once.
    """
    return Settings()