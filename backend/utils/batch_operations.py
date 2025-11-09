"""Batch operation optimization utilities.

This module provides optimized batch operations for database
and API operations to improve performance.
"""

import logging
from typing import List, Dict, Any, Callable, TypeVar
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

T = TypeVar('T')


def batch_insert(
    session: Session,
    model_class: type,
    data: List[Dict[str, Any]],
    batch_size: int = 1000,
    return_objects: bool = False
) -> List[Any]:
    """Batch insert records with optimal performance.

    Args:
        session: Database session
        model_class: SQLAlchemy model class
        data: List of dictionaries with record data
        batch_size: Size of each batch
        return_objects: Whether to return created objects

    Returns:
        List of created objects (if return_objects=True)
    """
    created = []

    try:
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]

            if return_objects:
                objects = [model_class(**item) for item in batch]
                session.bulk_save_objects(objects, return_defaults=True)
                created.extend(objects)
            else:
                session.bulk_insert_mappings(model_class, batch)

            session.commit()
            logger.info(f"Inserted batch {i//batch_size + 1}: {len(batch)} records")

        return created

    except Exception as e:
        session.rollback()
        logger.error(f"Batch insert failed: {e}")
        raise


def batch_update(
    session: Session,
    model_class: type,
    data: List[Dict[str, Any]],
    batch_size: int = 1000
) -> int:
    """Batch update records with optimal performance.

    Args:
        session: Database session
        model_class: SQLAlchemy model class
        data: List of dictionaries with record data (must include 'id')
        batch_size: Size of each batch

    Returns:
        Number of updated records
    """
    updated = 0

    try:
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            session.bulk_update_mappings(model_class, batch)
            session.commit()
            updated += len(batch)
            logger.info(f"Updated batch {i//batch_size + 1}: {len(batch)} records")

        return updated

    except Exception as e:
        session.rollback()
        logger.error(f"Batch update failed: {e}")
        raise


def batch_delete(
    session: Session,
    model_class: type,
    ids: List[int],
    batch_size: int = 1000
) -> int:
    """Batch delete records with optimal performance.

    Args:
        session: Database session
        model_class: SQLAlchemy model class
        ids: List of IDs to delete
        batch_size: Size of each batch

    Returns:
        Number of deleted records
    """
    deleted = 0

    try:
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            count = session.query(model_class).filter(
                model_class.id.in_(batch_ids)
            ).delete(synchronize_session=False)
            session.commit()
            deleted += count
            logger.info(f"Deleted batch {i//batch_size + 1}: {count} records")

        return deleted

    except Exception as e:
        session.rollback()
        logger.error(f"Batch delete failed: {e}")
        raise


def batch_process(
    items: List[T],
    processor: Callable[[T], Any],
    batch_size: int = 100,
    parallel: bool = False
) -> List[Any]:
    """Process items in batches.

    Args:
        items: List of items to process
        processor: Function to process each item
        batch_size: Size of each batch
        parallel: Whether to process batches in parallel

    Returns:
        List of processing results
    """
    results = []

    if parallel:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                for item in batch:
                    future = executor.submit(processor, item)
                    futures.append(future)

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Batch processing error: {e}")

    else:
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            for item in batch:
                try:
                    result = processor(item)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Processing error: {e}")

            logger.info(f"Processed batch {i//batch_size + 1}: {len(batch)} items")

    return results
