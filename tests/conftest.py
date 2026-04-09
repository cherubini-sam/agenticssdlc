"""Pytest configuration and fixtures."""

import sys
from unittest.mock import MagicMock

# Mock Google Cloud and LangChain dependencies for testing
sys.modules["google.cloud.storage"] = MagicMock()
sys.modules["langchain_google_vertexai"] = MagicMock()
sys.modules["vertexai"] = MagicMock()
sys.modules["vertexai.tuning"] = MagicMock()
sys.modules["vertexai.tuning.sft"] = MagicMock()


def pytest_configure(config):
    """Configure pytest."""

    config.addinivalue_line(
        "markers", "asyncio: mark test as async (deselect with '-m \"not asyncio\"')"
    )
