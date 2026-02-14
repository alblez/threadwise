"""Shared fixtures for threadwise tests."""

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class MockLLMProvider:
    """Mock LLM provider for testing summarization."""

    def __init__(self, response: str = "This thread discusses the Q3 budget approval.") -> None:
        self.response = response
        self.last_prompt: str | None = None
        self.call_count: int = 0

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        self.call_count += 1
        return self.response


@pytest.fixture()
def load_fixture() -> Any:
    """Return a callable that loads a JSON fixture by name."""

    def _load(name: str) -> dict[str, Any]:
        path = FIXTURES_DIR / name
        return json.loads(path.read_text())  # type: ignore[no-any-return]

    return _load
