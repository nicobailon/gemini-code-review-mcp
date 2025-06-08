# Integration Tests

This directory contains integration tests that make real API calls to Google's Gemini API.

## Overview

These tests use `gemini-1.5-flash` for cost-effective validation of core functionality with actual API responses.

## Requirements

- **API Key**: Set `GEMINI_API_KEY` environment variable
- **Optional**: Set `GITHUB_TOKEN` for GitHub integration tests

## Running Tests

```bash
# Set up API key
export GEMINI_API_KEY=your_key_here

# Run all integration tests
pytest -m integration

# Run with verbose output
pytest -v -m integration

# Run specific test class
pytest tests/integration/test_gemini_real.py::TestGeminiRealAPI

# Run with timeout enforcement
pytest -m integration --timeout=60
```

## Test Coverage

### What We Test
- ✅ Basic code review generation
- ✅ Temperature parameter effects
- ✅ Model configuration validation
- ✅ Error handling with invalid inputs
- ✅ Context generation workflows
- ✅ Meta prompt generation

### What We Don't Test
- ❌ Thinking mode (not supported by gemini-1.5-flash)
- ❌ URL context features (not supported by gemini-1.5-flash)
- ❌ Advanced model features requiring 2.0+ models

## Cost Considerations

- Tests use small contexts to minimize API usage
- Each test run costs approximately $0.01-0.05
- Tests are excluded from default test runs
- CI/CD runs only on manual trigger or explicit label

## Writing New Integration Tests

1. Always use the `integration_test_model` fixture (returns `gemini-1.5-flash`)
2. Keep contexts small (use `small_test_context` fixture when possible)
3. Use fuzzy assertions for API responses (content varies between runs)
4. Mark tests with `@pytest.mark.integration`
5. Skip tests requiring features not supported by gemini-1.5-flash

Example:
```python
@pytest.mark.integration
def test_my_feature(integration_test_model, small_test_context):
    result = send_to_gemini_for_review(
        context_content=small_test_context,
        model=integration_test_model,
        temperature=0.5,
        return_text=True,
    )
    assert result is not None
    assert len(result) > 50
```