"""
Batch process all CEH datasets with all 4 metadata formats.
XML + JSON + JSON-LD + RDF
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from etl.pipeline import ETLPipeline
from etl.models.database import Base
from loguru import logger
import sys
from time import sleep
from datetime import datetime

logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/batch_process.log", level="DEBUG", rotation="10 MB")


def batch_process():
    """Process all datasets with all 4 metadata formats."""
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Load dataset IDs
    possible_paths = [
        Path(__file__).parent.parent / "metadata-file-identifiers.txt",
        Path(__file__).parent / "metadata-file-identifiers.txt",
        Path("../metadata-file-identifiers.txt"),
        Path("metadata-file-identifiers.txt"),
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
        return
    
    with open(ids_file) as f:
        dataset_ids = [line.strip() for line in f if line.strip()]
    
    logger.info(f"\n{'='*70}")
    logger.info(f"📦 BATCH PROCESSING - ALL 4 FORMATS")
    logger.info(f"{'='*70}")
    logger.info(f"Total datasets: {len(dataset_ids)}")
    logger.info(f"Formats per dataset: XML + JSON + JSON-LD + RDF")
    logger.info(f"Expected metadata docs: {len(dataset_ids) * 4}")
    logger.info(f"Start time: {datetime.now()}")
    logger.info(f"{'='*70}\n")
    
    # Setup database
    engine = create_engine("sqlite:///data/datasets.db", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    pipeline = ETLPipeline(session)
    
    # Track progress
    success_count = 0
    fail_count = 0
    failed_ids = []
    
    format_stats = {
        'xml': 0,
        'json': 0,
        'jsonld': 0,
        'rdf': 0
    }
    
    # Process all datasets
    for i, file_id in enumerate(dataset_ids, 1):
        logger.info(f"\n[{i}/{len(dataset_ids)}] Processing: {file_id}")
        
        try:
            dataset = pipeline.process_dataset(file_id)
            
            if dataset:
                success_count += 1
                
                # Count which formats were extracted
                for doc in dataset.metadata_documents:
                    format_stats[doc.format] = format_stats.get(doc.format, 0) + 1
                
                logger.info(f"  ✅ {dataset.title[:60]}...")
                logger.info(f"     Formats: {len(dataset.metadata_documents)}/4")
            else:
                fail_count += 1
                failed_ids.append(file_id)
                logger.error(f"  ❌ Failed: {file_id}")
                
        except Exception as e:
            fail_count += 1
            failed_ids.append(file_id)
            logger.error(f"  ❌ Error: {str(e)[:200]}")
        
        # Progress update every 10
        if i % 10 == 0:
            logger.info(f"\n{'='*70}")
            logger.info(f"📊 Progress Update:")
            logger.info(f"   Processed: {i}/{len(dataset_ids)}")
            logger.info(f"   ✅ Success: {success_count}")
            logger.info(f"   ❌ Failed: {fail_count}")
            logger.info(f"   Format counts: {format_stats}")
            logger.info(f"{'='*70}\n")
            sleep(0.5)  # Be nice to CEH server
    
    session.close()
    
    # Final summary
    logger.info(f"\n{'='*70}")
    logger.info(f"🏁 BATCH PROCESSING COMPLETE!")
    logger.info(f"{'='*70}")
    logger.info(f"End time: {datetime.now()}")
    logger.info(f"\n📊 Results:")
    logger.info(f"   Total datasets: {len(dataset_ids)}")
    logger.info(f"   ✅ Successful: {success_count} ({success_count/len(dataset_ids)*100:.1f}%)")
    logger.info(f"   ❌ Failed: {fail_count}")
    
    logger.info(f"\n📄 Metadata Documents Extracted:")
    for format_type, count in sorted(format_stats.items()):
        expected = success_count  # Should have one of each format per success
        percentage = (count / expected * 100) if expected > 0 else 0
        logger.info(f"   {format_type.upper():.<10} {count}/{expected} ({percentage:.1f}%)")
    
    total_docs = sum(format_stats.values())
    logger.info(f"   TOTAL: {total_docs}")
    
    if failed_ids:
        logger.info(f"\n❌ Failed Dataset IDs ({len(failed_ids)}):")
        for fid in failed_ids[:10]:
            logger.info(f"   - {fid}")
        if len(failed_ids) > 10:
            logger.info(f"   ... and {len(failed_ids)-10} more")
    
    logger.info(f"\n{'='*70}")
    logger.info("✅ Batch processing complete!")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    batch_process()