"""Smoke tests validating Docker PostgreSQL + pgvector environment."""

import psycopg
import pytest

pytest_plugins = ["tests.conftest_db"]

pytestmark = pytest.mark.db


def test_pgvector_extension_loaded(db_connection: psycopg.Connection) -> None:  # type: ignore[type-arg]
    """Verify the vector extension is installed."""
    row = db_connection.execute(
        "SELECT extname FROM pg_extension WHERE extname = 'vector'"
    ).fetchone()
    assert row is not None
    assert row[0] == "vector"


def test_vector_insert_and_query(
    db_connection: psycopg.Connection, db_clean_tables: None  # type: ignore[type-arg]
) -> None:
    """Verify vector insert and retrieval roundtrip."""
    db_connection.execute(
        "INSERT INTO _test_vectors (content, embedding) VALUES (%s, %s)",
        ("hello", "[1,2,3]"),
    )
    row = db_connection.execute(
        "SELECT content, embedding FROM _test_vectors WHERE content = 'hello'"
    ).fetchone()
    assert row is not None
    assert row[0] == "hello"
    assert row[1] == "[1,2,3]"


def test_cosine_distance_operator(
    db_connection: psycopg.Connection, db_clean_tables: None  # type: ignore[type-arg]
) -> None:
    """Verify cosine distance operator computes a valid distance."""
    db_connection.execute(
        "INSERT INTO _test_vectors (content, embedding) VALUES (%s, %s)",
        ("a", "[1,0,0]"),
    )
    db_connection.execute(
        "INSERT INTO _test_vectors (content, embedding) VALUES (%s, %s)",
        ("b", "[0,1,0]"),
    )
    row = db_connection.execute(
        "SELECT embedding <=> '[1,0,0]' AS distance "
        "FROM _test_vectors WHERE content = 'b'"
    ).fetchone()
    assert row is not None
    assert row[0] is not None
    assert row[0] > 0


def test_vector_dimension_enforcement(
    db_connection: psycopg.Connection, db_clean_tables: None  # type: ignore[type-arg]
) -> None:
    """Verify inserting a vector with wrong dimensions raises an error."""
    with pytest.raises(psycopg.errors.DataError):
        db_connection.execute(
            "INSERT INTO _test_vectors (content, embedding) VALUES (%s, %s)",
            ("bad", "[1,2,3,4]"),
        )
