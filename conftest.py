import pytest
import sys
from pathlib import Path

# Add src to path for all tests
sys.path.insert(0, str(Path(__file__).parent / "src"))

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test that uses real APIs"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )

def pytest_collection_modifyitems(config, items):
    """Automatically mark tests in the integration directory."""
    for item in items:
        # Check if the test path contains the 'integration' directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration) 