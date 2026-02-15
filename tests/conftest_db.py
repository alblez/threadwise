"""Database fixtures for threadwise tests requiring PostgreSQL + pgvector.

This module is NOT auto-discovered by pytest (it's not named conftest.py).
Tests that need database access import fixtures from here via pytest plugins
or by using them as a conftest plugin in their own conftest.

Usage in test files:
    pytest_plugins = ["tests.conftest_db"]
"""

import psycopg
import pytest

DSN = "postgresql://threadwise:threadwise@localhost:5433/threadwise"


@pytest.fixture(scope="session")
def db_connection_string() -> str:
    """Return the database DSN, skipping the session if the database is unreachable."""
    try:
        conn = psycopg.connect(DSN, connect_timeout=3)
        conn.close()
    except psycopg.OperationalError:
        pytest.skip("PostgreSQL not available. Run: docker compose up -d")
    return DSN


@pytest.fixture()
def db_connection(db_connection_string: str) -> psycopg.Connection:  # type: ignore[type-arg]
    """Yield a database connection with transaction rollback on teardown."""
    conn = psycopg.connect(db_connection_string, autocommit=False)
    try:
        yield conn  # type: ignore[misc]
    finally:
        conn.rollback()
        conn.close()


@pytest.fixture(scope="session")
def db_setup_tables(db_connection_string: str) -> None:  # type: ignore[misc]
    """Create minimal test tables for pgvector validation."""
    conn = psycopg.connect(db_connection_string, autocommit=True)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _test_vectors (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            embedding vector(3)
        );
    """)
    conn.close()
    yield None  # type: ignore[misc]
    # Teardown: drop test tables
    conn = psycopg.connect(db_connection_string, autocommit=True)
    conn.execute("DROP TABLE IF EXISTS _test_vectors CASCADE;")
    conn.close()


@pytest.fixture()
def db_clean_tables(db_setup_tables: None, db_connection_string: str) -> None:
    """Truncate all test tables before each test."""
    conn = psycopg.connect(db_connection_string, autocommit=True)
    conn.execute("TRUNCATE _test_vectors RESTART IDENTITY;")
    conn.close()
