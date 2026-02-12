"""Shared fixtures for threadwise tests."""

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def load_fixture() -> Any:
    """Return a callable that loads a JSON fixture by name."""

    def _load(name: str) -> dict[str, Any]:
        path = FIXTURES_DIR / name
        return json.loads(path.read_text())  # type: ignore[no-any-return]

    return _load
