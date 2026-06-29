"""
Database Connection Module
--------------------------
Uses SQLAlchemy connection pooling for production-grade reliability.
Falls back gracefully so the UI can still demo without a live DB.
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Optional SQLAlchemy / pymysql ───────────────────────────────────────────
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import QueuePool
    _SQLALCHEMY_AVAILABLE = True
except ImportError:
    _SQLALCHEMY_AVAILABLE = False
    logger.warning("SQLAlchemy not installed — DB features disabled")

_engine = None


def _build_engine():
    """Build a pooled SQLAlchemy engine from env vars."""
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", 3306))
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "12345")
    database = os.getenv("DB_NAME", "gene_expression_db")

    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(
        url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,          # Auto-reconnect on stale connections
        pool_recycle=1800,           # Recycle every 30 min
        poolclass=QueuePool,
    )
    logger.info("Database engine created: %s@%s/%s", user, host, database)
    return engine


def get_db_engine():
    """Singleton engine accessor."""
    global _engine
    if _engine is None and _SQLALCHEMY_AVAILABLE:
        try:
            _engine = _build_engine()
        except Exception as e:
            logger.error("Failed to create DB engine: %s", e)
    return _engine


@contextmanager
def get_db_connection():
    """
    Context manager that yields a live connection.
    Rolls back on error and always closes.

    Usage:
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT ..."))
    """
    engine = get_db_engine()
    if engine is None:
        raise RuntimeError("Database engine unavailable. Check DB_* environment variables.")

    conn = engine.connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
