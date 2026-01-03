"""
Database indexing utilities for performance optimization.

This module provides utilities for creating and managing database indexes
to improve query performance.
"""

import sqlite3
from pathlib import Path
from loguru import logger
from typing import List, Tuple, Dict


class DatabaseIndexer:
    """Manage database indexes for query performance optimization."""
    
    # Index definitions: (name, SQL, description)
    INDEXES = [
        # Dataset indexes - for fast dataset lookups
        ("idx_datasets_title", 
         "CREATE INDEX IF NOT EXISTS idx_datasets_title ON datasets(title)",
         "Fast title search"),
        
        ("idx_datasets_file_id", 
         "CREATE INDEX IF NOT EXISTS idx_datasets_file_id ON datasets(file_identifier)",
         "Fast file identifier lookup"),
        
        ("idx_datasets_pub_date",
         "CREATE INDEX IF NOT EXISTS idx_datasets_pub_date ON datasets(publication_date)",
         "Date range queries"),
        
        # Keyword indexes - for keyword filtering
        ("idx_keywords_keyword", 
         "CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword)",
         "Fast keyword lookup"),
        
        ("idx_keywords_type", 
         "CREATE INDEX IF NOT EXISTS idx_keywords_type ON keywords(keyword_type)",
         "Filter by keyword type"),
        
        ("idx_keywords_uri", 
         "CREATE INDEX IF NOT EXISTS idx_keywords_uri ON keywords(uri)",
         "Ontology URI lookups"),
        
        ("idx_keywords_dataset", 
         "CREATE INDEX IF NOT EXISTS idx_keywords_dataset ON keywords(dataset_id)",
         "Get keywords for dataset"),
        
        # Contact indexes - for author/organization search
        ("idx_contacts_dataset", 
         "CREATE INDEX IF NOT EXISTS idx_contacts_dataset ON contacts(dataset_id)",
         "Get contacts for dataset"),
        
        ("idx_contacts_role", 
         "CREATE INDEX IF NOT EXISTS idx_contacts_role ON contacts(role)",
         "Filter by contact role"),
        
        ("idx_contacts_family", 
         "CREATE INDEX IF NOT EXISTS idx_contacts_family ON contacts(family_name)",
         "Search by author name"),
        
        ("idx_contacts_org", 
         "CREATE INDEX IF NOT EXISTS idx_contacts_org ON contacts(organization_name)",
         "Search by organization"),
        
        ("idx_contacts_orcid", 
         "CREATE INDEX IF NOT EXISTS idx_contacts_orcid ON contacts(name_identifier)",
         "ORCID lookups"),
        
        # Relationship indexes - for graph traversal
        ("idx_rels_source", 
         "CREATE INDEX IF NOT EXISTS idx_rels_source ON relationships(source_dataset_id)",
         "Find related datasets"),
        
        ("idx_rels_target",
         "CREATE INDEX IF NOT EXISTS idx_rels_target ON relationships(target_dataset_id)",
         "Reverse relationship lookup"),
        
        ("idx_rels_type", 
         "CREATE INDEX IF NOT EXISTS idx_rels_type ON relationships(relation_type)",
         "Filter by relationship type"),
        
        # Online resources indexes - for download links
        ("idx_resources_dataset", 
         "CREATE INDEX IF NOT EXISTS idx_resources_dataset ON online_resources(dataset_id)",
         "Get resources for dataset"),
        
        ("idx_resources_function", 
         "CREATE INDEX IF NOT EXISTS idx_resources_function ON online_resources(function)",
         "Filter by resource type"),
        
        # Metadata documents indexes - for format retrieval
        ("idx_docs_dataset", 
         "CREATE INDEX IF NOT EXISTS idx_docs_dataset ON metadata_documents(dataset_id)",
         "Get metadata docs for dataset"),
        
        ("idx_docs_format", 
         "CREATE INDEX IF NOT EXISTS idx_docs_format ON metadata_documents(format)",
         "Filter by metadata format"),
        
        # Embeddings indexes - for vector search
        ("idx_embeddings_dataset", 
         "CREATE INDEX IF NOT EXISTS idx_embeddings_dataset ON embeddings(dataset_id)",
         "Link embeddings to datasets"),
    ]
    
    def __init__(self, database_path: str = 'data/datasets.db'):
        """
        Initialize database indexer.
        
        Args:
            database_path: Path to SQLite database
        """
        self.database_path = Path(database_path)
    
    def create_indexes(self) -> Dict[str, any]:
        """
        Create all performance indexes.
        
        Returns:
            Dictionary with creation statistics
            
        Raises:
            FileNotFoundError: If database doesn't exist
        """
        if not self.database_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.database_path}\n"
                "Please run the ETL process first to create the database."
            )
        
        logger.info(f"Adding indexes to database: {self.database_path}")
        logger.info("=" * 70)
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        success_count = 0
        failed_count = 0
        failed_indexes = []
        
        # Create indexes
        for name, sql, description in self.INDEXES:
            try:
                cursor.execute(sql)
                logger.info(f"✅ Created: {name:.<40} ({description})")
                success_count += 1
            except Exception as e:
                logger.error(f"❌ Failed: {name:.<40} - {e}")
                failed_count += 1
                failed_indexes.append((name, str(e)))
        
        conn.commit()
        conn.close()
        
        # Summary
        logger.info("=" * 70)
        logger.info(f"Index creation complete!")
        logger.info(f"   ✅ Success: {success_count}")
        if failed_count > 0:
            logger.info(f"   ❌ Failed: {failed_count}")
        logger.info("=" * 70)
        
        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'failed_indexes': failed_indexes,
            'total_indexes': len(self.INDEXES)
        }
    
    def verify_indexes(self) -> List[Tuple[str, str]]:
        """
        Verify which indexes exist in the database.
        
        Returns:
            List of (index_name, table_name) tuples
        """
        logger.info("\nVerifying indexes...")
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, tbl_name
            FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_%'
            ORDER BY name
        """)
        
        all_indexes = cursor.fetchall()
        
        logger.info(f"\nTotal indexes in database: {len(all_indexes)}")
        for idx_name, table_name in all_indexes:
            logger.info(f"   {idx_name:.<45} ({table_name})")
        
        conn.close()
        
        return all_indexes
    
    def drop_indexes(self) -> int:
        """
        Drop all indexes (useful for rebuilding).
        
        Returns:
            Number of indexes dropped
        """
        logger.info(f"Dropping indexes from database: {self.database_path}")
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Get all index names
        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_%'
        """)
        
        index_names = [row[0] for row in cursor.fetchall()]
        
        dropped_count = 0
        for name in index_names:
            try:
                cursor.execute(f"DROP INDEX IF EXISTS {name}")
                logger.info(f"✅ Dropped: {name}")
                dropped_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to drop {name}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"\n✅ Dropped {dropped_count} indexes")
        return dropped_count