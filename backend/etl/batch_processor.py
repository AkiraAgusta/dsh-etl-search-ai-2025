"""
Batch processor for CEH datasets.

This module provides batch processing capabilities for extracting
and processing multiple datasets with all metadata formats.
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .pipeline import ETLPipeline
from .models.database import Base
from loguru import logger
from time import sleep
from datetime import datetime
from typing import List, Dict


class BatchProcessor:
    """Batch process multiple CEH datasets with all metadata formats."""
    
    def __init__(
        self,
        database_url: str = "sqlite:///data/datasets.db",
        dataset_ids_file: str = None,
        log_level: str = "INFO"
    ):
        """
        Initialize batch processor.
        
        Args:
            database_url: Database connection URL
            dataset_ids_file: Path to file containing dataset IDs
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.database_url = database_url
        self.dataset_ids_file = dataset_ids_file
        self.log_level = log_level
        self.session: Session = None
        self.pipeline: ETLPipeline = None
        
    def setup_database(self) -> Session:
        """
        Setup database connection and create tables.
        
        Returns:
            SQLAlchemy session
        """
        logger.info(f"Setting up database: {self.database_url}")
        engine = create_engine(self.database_url, echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        self.session = SessionLocal()
        return self.session
    
    def load_dataset_ids(self) -> List[str]:
        """
        Load dataset IDs from file.
        
        Returns:
            List of dataset file identifiers
            
        Raises:
            FileNotFoundError: If dataset IDs file not found
        """
        if self.dataset_ids_file:
            ids_file = Path(self.dataset_ids_file)
            if not ids_file.exists():
                raise FileNotFoundError(f"Dataset IDs file not found: {ids_file}")
        else:
            # Search for file in common locations
            possible_paths = [
                Path("metadata-file-identifiers.txt"),
                Path("../metadata-file-identifiers.txt"),
                Path(__file__).parent.parent / "metadata-file-identifiers.txt",
            ]
            
            ids_file = None
            for path in possible_paths:
                if path.exists():
                    ids_file = path
                    logger.info(f"Found dataset IDs file: {ids_file}")
                    break
            
            if not ids_file:
                logger.error("❌ metadata-file-identifiers.txt not found!")
                logger.error("Searched in:")
                for path in possible_paths:
                    logger.error(f"  - {path}")
                raise FileNotFoundError("metadata-file-identifiers.txt not found")
        
        with open(ids_file) as f:
            dataset_ids = [line.strip() for line in f if line.strip()]
        
        logger.info(f"Loaded {len(dataset_ids)} dataset IDs")
        return dataset_ids
    
    def process(self, dataset_ids: List[str] = None) -> Dict[str, any]:
        """
        Batch process datasets with all metadata formats.
        
        Args:
            dataset_ids: List of dataset IDs to process (loads from file if None)
            
        Returns:
            Dictionary with processing statistics
        """
        # Load dataset IDs if not provided
        if dataset_ids is None:
            dataset_ids = self.load_dataset_ids()
        
        logger.info(f"\n{'='*70}")
        logger.info(f"📦 BATCH PROCESSING - ALL 4 FORMATS")
        logger.info(f"{'='*70}")
        logger.info(f"Total datasets: {len(dataset_ids)}")
        logger.info(f"Formats per dataset: XML + JSON + JSON-LD + RDF")
        logger.info(f"Expected metadata docs: {len(dataset_ids) * 4}")
        logger.info(f"Start time: {datetime.now()}")
        logger.info(f"{'='*70}\n")
        
        # Setup database and pipeline
        if not self.session:
            self.setup_database()
        
        self.pipeline = ETLPipeline(self.session)
        
        # Track progress
        stats = {
            'success_count': 0,
            'fail_count': 0,
            'failed_ids': [],
            'format_stats': {
                'xml': 0,
                'json': 0,
                'jsonld': 0,
                'rdf': 0
            },
            'start_time': datetime.now(),
            'end_time': None
        }
        
        # Process all datasets
        for i, file_id in enumerate(dataset_ids, 1):
            logger.info(f"\n[{i}/{len(dataset_ids)}] Processing: {file_id}")
            
            try:
                dataset = self.pipeline.process_dataset(file_id)
                
                if dataset:
                    stats['success_count'] += 1
                    
                    # Count which formats were extracted
                    for doc in dataset.metadata_documents:
                        stats['format_stats'][doc.format] = stats['format_stats'].get(doc.format, 0) + 1
                    
                    logger.info(f"  ✅ {dataset.title[:60]}...")
                    logger.info(f"     Formats: {len(dataset.metadata_documents)}/4")
                else:
                    stats['fail_count'] += 1
                    stats['failed_ids'].append(file_id)
                    logger.error(f"  ❌ Failed: {file_id}")
                    
            except Exception as e:
                stats['fail_count'] += 1
                stats['failed_ids'].append(file_id)
                logger.error(f"  ❌ Error: {str(e)[:200]}")
            
            # Progress update every 10
            if i % 10 == 0:
                self._log_progress(i, len(dataset_ids), stats)
                sleep(0.5)  # Be nice to CEH server
        
        stats['end_time'] = datetime.now()
        
        # Final summary
        self._log_summary(dataset_ids, stats)
        
        return stats
    
    def _log_progress(self, current: int, total: int, stats: Dict):
        """Log progress update."""
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 Progress Update:")
        logger.info(f"   Processed: {current}/{total}")
        logger.info(f"   ✅ Success: {stats['success_count']}")
        logger.info(f"   ❌ Failed: {stats['fail_count']}")
        logger.info(f"   Format counts: {stats['format_stats']}")
        logger.info(f"{'='*70}\n")
    
    def _log_summary(self, dataset_ids: List[str], stats: Dict):
        """Log final summary."""
        logger.info(f"\n{'='*70}")
        logger.info(f"🏁 BATCH PROCESSING COMPLETE!")
        logger.info(f"{'='*70}")
        logger.info(f"Start time: {stats['start_time']}")
        logger.info(f"End time: {stats['end_time']}")
        logger.info(f"Duration: {stats['end_time'] - stats['start_time']}")
        
        logger.info(f"\n📊 Results:")
        logger.info(f"   Total datasets: {len(dataset_ids)}")
        
        success_pct = (stats['success_count'] / len(dataset_ids) * 100) if dataset_ids else 0
        logger.info(f"   ✅ Successful: {stats['success_count']} ({success_pct:.1f}%)")
        logger.info(f"   ❌ Failed: {stats['fail_count']}")
        
        logger.info(f"\n📄 Metadata Documents Extracted:")
        for format_type, count in sorted(stats['format_stats'].items()):
            expected = stats['success_count']
            percentage = (count / expected * 100) if expected > 0 else 0
            logger.info(f"   {format_type.upper():.<10} {count}/{expected} ({percentage:.1f}%)")
        
        total_docs = sum(stats['format_stats'].values())
        logger.info(f"   TOTAL: {total_docs}")
        
        if stats['failed_ids']:
            logger.info(f"\n❌ Failed Dataset IDs ({len(stats['failed_ids'])}):")
            for fid in stats['failed_ids'][:10]:
                logger.info(f"   - {fid}")
            if len(stats['failed_ids']) > 10:
                logger.info(f"   ... and {len(stats['failed_ids'])-10} more")
        
        logger.info(f"\n{'='*70}")
        logger.info("✅ Batch processing complete!")
        logger.info(f"{'='*70}")
    
    def close(self):
        """Close database session."""
        if self.session:
            self.session.close()