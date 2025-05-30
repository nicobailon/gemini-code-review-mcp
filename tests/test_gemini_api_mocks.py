"""
Mock Gemini API responses for deterministic testing.
Following TDD Protocol: Creating comprehensive mock responses for all Gemini interactions.
"""

import json
import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List, Optional


class MockGeminiResponse:
    """Mock response object that mimics Gemini API response structure."""
    
    def __init__(self, text: str, usage_metadata: Optional[Dict] = None):
        self.text = text
        self.usage_metadata = usage_metadata or {
            "prompt_token_count": 150,
            "candidates_token_count": 75,
            "total_token_count": 225
        }


class GeminiAPIMockFactory:
    """Factory for creating deterministic Gemini API mock responses."""
    
    @staticmethod
    def create_successful_prompt_generation_response() -> MockGeminiResponse:
        """Mock response for successful auto-prompt generation."""
        prompt_text = """Focus on the following critical areas in your code review:

1. **Security Vulnerabilities**: Look for authentication bypasses, input validation issues, and SQL injection risks
2. **Performance Bottlenecks**: Identify inefficient database queries, memory leaks, and algorithmic complexity issues  
3. **Code Quality**: Check for proper error handling, code duplication, and adherence to established patterns
4. **Testing Coverage**: Ensure adequate unit tests and integration tests for new functionality
5. **Documentation**: Verify that complex logic is properly documented and API changes are reflected

Pay special attention to the recent changes in the authentication system and the new user profile management features."""
        
        return MockGeminiResponse(
            text=prompt_text,
            usage_metadata={
                "prompt_token_count": 1250,
                "candidates_token_count": 180,
                "total_token_count": 1430
            }
        )
    
    @staticmethod
    def create_context_analysis_response() -> MockGeminiResponse:
        """Mock response for code context analysis."""
        analysis_text = """Based on the provided code context, I can see this is a Python web application with the following key components:

**Architecture**: FastAPI-based REST API with SQLAlchemy ORM
**Key Areas of Focus**:
- User authentication and session management (priority: HIGH)
- Database query optimization in user profile endpoints (priority: MEDIUM)  
- Error handling in API routes (priority: HIGH)
- Input validation for user data (priority: CRITICAL)

**Recommended Review Focus**: Security vulnerabilities in authentication, performance issues in database operations, and proper error handling throughout the API."""
        
        return MockGeminiResponse(
            text=analysis_text,
            usage_metadata={
                "prompt_token_count": 2100,
                "candidates_token_count": 250,
                "total_token_count": 2350
            }
        )
    
    @staticmethod
    def create_large_project_prompt_response() -> MockGeminiResponse:
        """Mock response for large project auto-prompt generation."""
        large_prompt = """For this comprehensive codebase review, focus on these architectural and implementation concerns:

**System Architecture Review**:
1. **Microservices Communication**: Verify proper error handling between services
2. **Data Consistency**: Check for race conditions in distributed transactions
3. **Scalability Patterns**: Review caching strategies and database connection pooling
4. **Security Architecture**: Audit authentication flows and authorization boundaries

**Code Quality Priorities**:
1. **Performance Critical Paths**: Focus on API endpoints with high traffic
2. **Error Resilience**: Ensure graceful degradation and proper retry mechanisms
3. **Monitoring & Observability**: Verify adequate logging and metrics collection
4. **Testing Strategy**: Check integration test coverage for cross-service interactions

**Specific Focus Areas**:
- Payment processing workflow (CRITICAL)
- User data synchronization between services (HIGH)
- Background job processing reliability (MEDIUM)
- API rate limiting and abuse prevention (HIGH)

Review with emphasis on production readiness and operational concerns."""
        
        return MockGeminiResponse(
            text=large_prompt,
            usage_metadata={
                "prompt_token_count": 4500,
                "candidates_token_count": 420,
                "total_token_count": 4920
            }
        )
    
    @staticmethod
    def create_error_response() -> Exception:
        """Mock Gemini API error for testing error handling."""
        return Exception("Gemini API rate limit exceeded. Please try again later.")
    
    @staticmethod
    def create_timeout_response() -> Exception:
        """Mock timeout error for testing timeout handling."""
        return TimeoutError("Request to Gemini API timed out after 30 seconds.")
    
    @staticmethod
    def create_invalid_response() -> MockGeminiResponse:
        """Mock invalid/empty response for testing edge cases."""
        return MockGeminiResponse(
            text="",
            usage_metadata={
                "prompt_token_count": 100,
                "candidates_token_count": 0,
                "total_token_count": 100
            }
        )
    
    @staticmethod
    def create_minimal_context_response() -> MockGeminiResponse:
        """Mock response for minimal code context."""
        minimal_prompt = """Focus on basic code quality in this small module:

1. **Function Design**: Check for single responsibility and clear interfaces
2. **Error Handling**: Ensure proper exception handling and validation
3. **Code Style**: Verify adherence to Python PEP 8 standards
4. **Testing**: Confirm adequate unit test coverage

This appears to be a utility module, so prioritize clarity and reliability."""
        
        return MockGeminiResponse(
            text=minimal_prompt,
            usage_metadata={
                "prompt_token_count": 450,
                "candidates_token_count": 95,
                "total_token_count": 545
            }
        )
    
    @staticmethod
    def create_scope_specific_response(scope: str) -> MockGeminiResponse:
        """Create scope-specific mock responses."""
        scope_prompts = {
            "full_project": "Review the entire codebase with focus on architectural patterns, security, and performance across all modules.",
            "recent_phase": "Focus on the most recent development phase, emphasizing integration points and new feature stability.",
            "specific_phase": "Deep dive into the specified phase implementation, checking for completion criteria and quality standards.",
            "specific_task": "Targeted review of the specific task implementation, focusing on requirements fulfillment and edge cases."
        }
        
        prompt_text = scope_prompts.get(scope, "General code review focusing on quality, security, and maintainability.")
        
        return MockGeminiResponse(
            text=prompt_text,
            usage_metadata={
                "prompt_token_count": 800,
                "candidates_token_count": 120,
                "total_token_count": 920
            }
        )


class MockGeminiClient:
    """Mock Gemini client for testing."""
    
    def __init__(self, mock_responses: Optional[List[MockGeminiResponse]] = None):
        self.mock_responses = mock_responses or []
        self.call_count = 0
        self.last_request = None
    
    def generate_content(self, prompt: str, **kwargs) -> MockGeminiResponse:
        """Mock generate_content method."""
        self.last_request = {
            "prompt": prompt,
            "kwargs": kwargs,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        self.call_count += 1
        
        if self.mock_responses:
            # Cycle through provided responses
            response_index = (self.call_count - 1) % len(self.mock_responses)
            return self.mock_responses[response_index]
        
        # Default response
        return GeminiAPIMockFactory.create_successful_prompt_generation_response()


@pytest.fixture
def mock_gemini_factory():
    """Pytest fixture providing the GeminiAPIMockFactory."""
    return GeminiAPIMockFactory


@pytest.fixture
def mock_gemini_client():
    """Pytest fixture providing a basic mock Gemini client."""
    return MockGeminiClient()


@pytest.fixture
def mock_gemini_client_with_responses():
    """Pytest fixture providing a mock client with predefined responses."""
    responses = [
        GeminiAPIMockFactory.create_successful_prompt_generation_response(),
        GeminiAPIMockFactory.create_context_analysis_response(),
        GeminiAPIMockFactory.create_large_project_prompt_response()
    ]
    return MockGeminiClient(mock_responses=responses)


@pytest.fixture
def mock_gemini_error_client():
    """Pytest fixture providing a mock client that simulates errors."""
    client = MockGeminiClient()
    
    def generate_content_with_error(prompt: str, **kwargs):
        client.call_count += 1
        if client.call_count == 1:
            raise GeminiAPIMockFactory.create_error_response()
        elif client.call_count == 2:
            raise GeminiAPIMockFactory.create_timeout_response()
        else:
            return GeminiAPIMockFactory.create_successful_prompt_generation_response()
    
    client.generate_content = generate_content_with_error
    return client


class TestGeminiAPIMocks:
    """Test the mock responses themselves for consistency."""
    
    def test_successful_prompt_generation_mock(self, mock_gemini_factory):
        """Test that successful prompt generation mock is properly structured."""
        response = mock_gemini_factory.create_successful_prompt_generation_response()
        
        assert isinstance(response.text, str)
        assert len(response.text) > 100  # Should be substantial prompt
        assert "security" in response.text.lower() or "performance" in response.text.lower()
        assert response.usage_metadata["total_token_count"] > 0
        assert response.usage_metadata["prompt_token_count"] > 0
        assert response.usage_metadata["candidates_token_count"] > 0
    
    def test_context_analysis_mock(self, mock_gemini_factory):
        """Test that context analysis mock provides meaningful analysis."""
        response = mock_gemini_factory.create_context_analysis_response()
        
        assert isinstance(response.text, str)
        assert "priority" in response.text.lower()
        assert "focus" in response.text.lower()
        assert response.usage_metadata["total_token_count"] > 1000  # Analysis should be detailed
    
    def test_large_project_mock(self, mock_gemini_factory):
        """Test that large project mock handles complexity appropriately."""
        response = mock_gemini_factory.create_large_project_prompt_response()
        
        assert isinstance(response.text, str)
        assert len(response.text) > 500  # Should be comprehensive
        assert "architecture" in response.text.lower()
        assert "microservices" in response.text.lower() or "scalability" in response.text.lower()
        assert response.usage_metadata["total_token_count"] > 3000  # Large context
    
    def test_scope_specific_mocks(self, mock_gemini_factory):
        """Test that scope-specific mocks return appropriate content."""
        scopes = ["full_project", "recent_phase", "specific_phase", "specific_task"]
        
        for scope in scopes:
            response = mock_gemini_factory.create_scope_specific_response(scope)
            assert isinstance(response.text, str)
            assert len(response.text) > 50
            assert response.usage_metadata["total_token_count"] > 0
    
    def test_error_mocks(self, mock_gemini_factory):
        """Test that error mocks raise appropriate exceptions."""
        error = mock_gemini_factory.create_error_response()
        assert isinstance(error, Exception)
        assert "rate limit" in str(error).lower()
        
        timeout_error = mock_gemini_factory.create_timeout_response()
        assert isinstance(timeout_error, TimeoutError)
        assert "timeout" in str(timeout_error).lower()
    
    def test_invalid_response_mock(self, mock_gemini_factory):
        """Test that invalid response mock simulates edge cases."""
        response = mock_gemini_factory.create_invalid_response()
        
        assert response.text == ""
        assert response.usage_metadata["candidates_token_count"] == 0
        assert response.usage_metadata["total_token_count"] > 0  # Still used tokens for prompt
    
    def test_mock_client_basic_functionality(self, mock_gemini_client):
        """Test that mock client tracks calls and requests properly."""
        prompt = "Test prompt for code review"
        
        response = mock_gemini_client.generate_content(prompt)
        
        assert mock_gemini_client.call_count == 1
        assert mock_gemini_client.last_request["prompt"] == prompt
        assert isinstance(response, MockGeminiResponse)
        assert len(response.text) > 0
    
    def test_mock_client_with_predefined_responses(self, mock_gemini_client_with_responses):
        """Test that mock client cycles through predefined responses."""
        client = mock_gemini_client_with_responses
        
        # First call should get first response
        response1 = client.generate_content("Test prompt 1")
        assert "Security Vulnerabilities" in response1.text
        
        # Second call should get second response  
        response2 = client.generate_content("Test prompt 2")
        assert "FastAPI-based" in response2.text
        
        # Third call should get third response
        response3 = client.generate_content("Test prompt 3")
        assert "Microservices Communication" in response3.text
        
        # Fourth call should cycle back to first response
        response4 = client.generate_content("Test prompt 4")
        assert "Security Vulnerabilities" in response4.text
    
    def test_mock_error_client_behavior(self, mock_gemini_error_client):
        """Test that error client simulates various error conditions."""
        client = mock_gemini_error_client
        
        # First call should raise API error
        with pytest.raises(Exception, match="rate limit"):
            client.generate_content("Test prompt 1")
        
        # Second call should raise timeout error
        with pytest.raises(TimeoutError, match="timeout"):
            client.generate_content("Test prompt 2")
        
        # Third call should succeed
        response = client.generate_content("Test prompt 3")
        assert isinstance(response, MockGeminiResponse)
        assert len(response.text) > 0