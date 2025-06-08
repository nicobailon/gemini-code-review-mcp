"""
Configuration for integration tests that use real Gemini API.

These tests make actual API calls to gemini-1.5-flash for cost-effective testing.
Run with: pytest -m integration
"""

import os
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.fixture(scope="session", autouse=True)
def validate_api_key():
    """Validate that GEMINI_API_KEY is available for integration tests."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip(
            "Integration tests require GEMINI_API_KEY environment variable. "
            "Set it to run real API tests: export GEMINI_API_KEY=your_key_here"
        )


@pytest.fixture
def integration_test_model():
    """Return the model to use for integration tests."""
    # Use gemini-1.5-flash for cost-effective testing
    return "gemini-1.5-flash"


@pytest.fixture
def small_test_context():
    """Provide a small context for testing to minimize API costs."""
    return """# Code Review Context

## Project Overview
This is a test project for integration testing.

## Recent Changes
- Added new function `calculate_sum(a, b)` that returns a + b
- Fixed bug in error handling

## Code Sample
```python
def calculate_sum(a: int, b: int) -> int:
    \"\"\"Add two numbers together.\"\"\"
    return a + b
```

Please review this code for best practices and potential improvements.
"""


@pytest.fixture
def minimal_project_dir(tmp_path):
    """Create a minimal project structure for testing."""
    # Create basic structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text("")
    (tmp_path / "src" / "main.py").write_text("""
def hello_world():
    \"\"\"Simple hello world function.\"\"\"
    print("Hello, World!")

def add_numbers(a, b):
    \"\"\"Add two numbers.\"\"\"
    return a + b
""")
    
    # Create a simple task list
    (tmp_path / "tasks").mkdir()
    (tmp_path / "tasks" / "tasks-test.md").write_text("""
## Tasks

- [x] 1.0 Create basic functions
  - [x] 1.1 Implement hello_world
  - [x] 1.2 Implement add_numbers
- [ ] 2.0 Add tests
  - [ ] 2.1 Test hello_world
  - [ ] 2.2 Test add_numbers
""")
    
    return tmp_path


@pytest.fixture
def integration_timeout():
    """Timeout for integration tests (in seconds)."""
    return 30  # 30 seconds should be enough for gemini-1.5-flash


# Mark all tests in this directory as integration tests
pytest_plugins = []


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test that uses real APIs"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark all tests in integration directory."""
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)