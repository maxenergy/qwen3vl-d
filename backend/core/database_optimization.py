"""Database optimization utilities.

This module provides tools for optimizing database performance including
index creation, query optimization, and performance monitoring.
"""

import logging
from typing import List, Dict, Any
from sqlalchemy import text, inspect, Index
from sqlalchemy.orm import Session

from backend.core.database import engine, SessionLocal
from backend.models import (
    Project, Label, GenerationTask, Image,
    AnnotationTask, Annotation, Dataset, TrainingJob
)

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Database optimization manager."""

    def __init__(self):
        """Initialize database optimizer."""
        self.engine = engine

    def create_indexes(self, session: Session) -> List[str]:
        """Create optimized indexes for better query performance.

        Args:
            session: Database session

        Returns:
            List of created indexes
        """
        created_indexes = []

        try:
            # Project indexes
            indexes = [
                # Projects - search and filtering
                Index('idx_project_name', Project.name),
                Index('idx_project_created_at', Project.created_at),
                Index('idx_project_status', Project.status),

                # Labels - lookup
                Index('idx_label_project_id', Label.project_id),
                Index('idx_label_name', Label.name),

                # Generation Tasks - status tracking
                Index('idx_generation_status', GenerationTask.status),
                Index('idx_generation_project_id', GenerationTask.project_id),
                Index('idx_generation_created_at', GenerationTask.created_at),

                # Images - filtering and lookup
                Index('idx_image_project_id', Image.project_id),
                Index('idx_image_status', Image.status),
                Index('idx_image_review_status', Image.review_status),
                Index('idx_image_generation_task', Image.generation_task_id),
                Index('idx_image_created_at', Image.created_at),

                # Annotation Tasks - tracking
                Index('idx_annotation_task_status', AnnotationTask.status),
                Index('idx_annotation_task_project', AnnotationTask.project_id),
                Index('idx_annotation_task_created', AnnotationTask.created_at),

                # Annotations - lookups and filtering
                Index('idx_annotation_image_id', Annotation.image_id),
                Index('idx_annotation_label_id', Annotation.label_id),
                Index('idx_annotation_task_id', Annotation.task_id),
                Index('idx_annotation_source', Annotation.source),
                Index('idx_annotation_verified', Annotation.is_verified),

                # Datasets - filtering
                Index('idx_dataset_project_id', Dataset.project_id),
                Index('idx_dataset_split', Dataset.split),
                Index('idx_dataset_created_at', Dataset.created_at),

                # Training Jobs - monitoring
                Index('idx_training_status', TrainingJob.status),
                Index('idx_training_dataset_id', TrainingJob.dataset_id),
                Index('idx_training_created_at', TrainingJob.created_at),
            ]

            # Create indexes
            for index in indexes:
                try:
                    # Check if index already exists
                    if not self._index_exists(session, index.name):
                        index.create(self.engine)
                        created_indexes.append(index.name)
                        logger.info(f"Created index: {index.name}")
                except Exception as e:
                    logger.warning(f"Failed to create index {index.name}: {e}")

            logger.info(f"Created {len(created_indexes)} new indexes")
            return created_indexes

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            return created_indexes

    def _index_exists(self, session: Session, index_name: str) -> bool:
        """Check if index exists.

        Args:
            session: Database session
            index_name: Name of index

        Returns:
            True if exists, False otherwise
        """
        try:
            inspector = inspect(self.engine)
            for table_name in inspector.get_table_names():
                indexes = inspector.get_indexes(table_name)
                if any(idx['name'] == index_name for idx in indexes):
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking index existence: {e}")
            return False

    def analyze_tables(self, session: Session) -> Dict[str, Any]:
        """Analyze tables for optimization opportunities.

        Args:
            session: Database session

        Returns:
            Dictionary with analysis results
        """
        analysis = {}

        try:
            # PostgreSQL ANALYZE command
            if self.engine.dialect.name == 'postgresql':
                tables = [
                    'projects', 'labels', 'generation_tasks', 'images',
                    'annotation_tasks', 'annotations', 'datasets', 'training_jobs'
                ]

                for table in tables:
                    session.execute(text(f"ANALYZE {table}"))
                    logger.info(f"Analyzed table: {table}")

                analysis['analyzed_tables'] = tables
                analysis['status'] = 'success'

            session.commit()
            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze tables: {e}")
            session.rollback()
            return {'status': 'error', 'error': str(e)}

    def vacuum_database(self, session: Session, full: bool = False) -> bool:
        """Vacuum database to reclaim space and update statistics.

        Args:
            session: Database session
            full: Whether to do VACUUM FULL (requires more locks)

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.engine.dialect.name == 'postgresql':
                # Close current transaction
                session.commit()

                # VACUUM cannot run inside transaction
                connection = self.engine.raw_connection()
                connection.set_isolation_level(0)  # AUTOCOMMIT
                cursor = connection.cursor()

                if full:
                    cursor.execute("VACUUM FULL ANALYZE")
                    logger.info("Performed VACUUM FULL ANALYZE")
                else:
                    cursor.execute("VACUUM ANALYZE")
                    logger.info("Performed VACUUM ANALYZE")

                cursor.close()
                connection.close()

                return True

        except Exception as e:
            logger.error(f"Failed to vacuum database: {e}")
            return False

    def get_slow_queries(self, session: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slow queries from PostgreSQL pg_stat_statements.

        Args:
            session: Database session
            limit: Number of queries to return

        Returns:
            List of slow query statistics
        """
        slow_queries = []

        try:
            if self.engine.dialect.name == 'postgresql':
                # Check if pg_stat_statements extension is available
                result = session.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
                    )
                """))

                if not result.scalar():
                    logger.warning("pg_stat_statements extension not available")
                    return []

                # Get slow queries
                result = session.execute(text(f"""
                    SELECT
                        query,
                        calls,
                        total_exec_time,
                        mean_exec_time,
                        max_exec_time,
                        rows
                    FROM pg_stat_statements
                    ORDER BY mean_exec_time DESC
                    LIMIT {limit}
                """))

                for row in result:
                    slow_queries.append({
                        'query': row[0],
                        'calls': row[1],
                        'total_time': row[2],
                        'mean_time': row[3],
                        'max_time': row[4],
                        'rows': row[5]
                    })

            return slow_queries

        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            return []

    def get_table_stats(self, session: Session) -> Dict[str, Any]:
        """Get table statistics.

        Args:
            session: Database session

        Returns:
            Dictionary with table statistics
        """
        stats = {}

        try:
            inspector = inspect(self.engine)

            for table_name in inspector.get_table_names():
                # Get row count
                result = session.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                )
                row_count = result.scalar()

                # Get table size (PostgreSQL)
                if self.engine.dialect.name == 'postgresql':
                    result = session.execute(
                        text(f"SELECT pg_total_relation_size('{table_name}')")
                    )
                    size_bytes = result.scalar()
                else:
                    size_bytes = 0

                stats[table_name] = {
                    'row_count': row_count,
                    'size_bytes': size_bytes,
                    'size_mb': size_bytes / (1024 * 1024) if size_bytes else 0
                }

            return stats

        except Exception as e:
            logger.error(f"Failed to get table stats: {e}")
            return {}

    def optimize_all(self) -> Dict[str, Any]:
        """Run all optimization tasks.

        Returns:
            Dictionary with optimization results
        """
        results = {}

        with SessionLocal() as session:
            # Create indexes
            results['indexes_created'] = self.create_indexes(session)

            # Analyze tables
            results['analyze'] = self.analyze_tables(session)

            # Get table stats
            results['table_stats'] = self.get_table_stats(session)

        return results


# Global optimizer instance
_optimizer = None


def get_optimizer() -> DatabaseOptimizer:
    """Get global database optimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = DatabaseOptimizer()
    return _optimizer


# CLI command for optimization
def optimize_database(full_vacuum: bool = False):
    """Optimize database (can be called from CLI).

    Args:
        full_vacuum: Whether to perform VACUUM FULL
    """
    logger.info("Starting database optimization...")

    optimizer = get_optimizer()
    results = optimizer.optimize_all()

    logger.info(f"Created {len(results['indexes_created'])} indexes")
    logger.info(f"Analyzed {len(results['analyze'].get('analyzed_tables', []))} tables")

    # Print table stats
    logger.info("\nTable Statistics:")
    for table, stats in results['table_stats'].items():
        logger.info(
            f"  {table}: {stats['row_count']} rows, "
            f"{stats['size_mb']:.2f} MB"
        )

    # Vacuum if requested
    if full_vacuum:
        with SessionLocal() as session:
            optimizer.vacuum_database(session, full=True)

    logger.info("Database optimization complete!")
