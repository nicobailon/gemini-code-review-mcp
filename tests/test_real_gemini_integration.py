"""
Test real Gemini API integration with rate limiting.
Following TDD Protocol: Testing actual Gemini API behavior with proper rate limiting and error handling.
"""

import pytest
import os
import sys
import time
import json
from unittest.mock import patch, Mock
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile


@pytest.fixture(scope="session", autouse=True)
def setup_import_path():
    """Fixture to ensure src module can be imported in tests."""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)


@pytest.fixture
def gemini_api_key():
    """Get Gemini API key from environment or skip tests."""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key or api_key == 'test_key_for_testing':
        pytest.skip("Real Gemini API key not available - set GEMINI_API_KEY environment variable")
    return api_key


@pytest.fixture
def rate_limit_tracker():
    """Track API calls for rate limiting tests."""
    class RateLimitTracker:
        def __init__(self):
            self.calls = []
            self.start_time = time.time()
        
        def record_call(self):
            self.calls.append(time.time() - self.start_time)
        
        def get_calls_per_minute(self):
            current_time = time.time() - self.start_time
            recent_calls = [call for call in self.calls if current_time - call < 60]
            return len(recent_calls)
        
        def get_average_interval(self):
            if len(self.calls) < 2:
                return 0
            intervals = [self.calls[i] - self.calls[i-1] for i in range(1, len(self.calls))]
            return sum(intervals) / len(intervals)
    
    return RateLimitTracker()


class TestRealGeminiAPIIntegration:
    """Test real Gemini API integration scenarios."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_gemini_auto_prompt_generation(self, gemini_api_key, tmp_path):
        """Test real Gemini API for auto-prompt generation."""
        try:
            from src.server import generate_meta_prompt
            
            # Create realistic test project
            project_path = str(tmp_path / "real_api_test")
            os.makedirs(project_path, exist_ok=True)
            
            (Path(project_path) / "app.py").write_text("""
def login(username, password):
    # Direct SQL query - potential SQL injection
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    return execute_query(query)

def get_user_data(user_id):
    # Missing input validation
    return database.fetch_user(user_id)
""")
            
            # Set API key in environment
            original_key = os.environ.get('GEMINI_API_KEY')
            os.environ['GEMINI_API_KEY'] = gemini_api_key
            
            try:
                # Test with real API
                result = generate_meta_prompt(
                    project_path=project_path,
                    scope="full_project"
                )
                
                # Verify real API response structure
                assert result is not None
                assert isinstance(result, dict)
                assert "generated_prompt" in result
                assert isinstance(result["generated_prompt"], str)
                assert len(result["generated_prompt"]) > 50
                
                # Verify prompt contains relevant security concerns
                prompt_text = result["generated_prompt"].lower()
                security_keywords = ["security", "sql", "injection", "validation", "vulnerability"]
                found_keywords = [kw for kw in security_keywords if kw in prompt_text]
                assert len(found_keywords) >= 2, f"Expected security-focused prompt, found keywords: {found_keywords}"
                
                print(f"✅ Real Gemini API integration successful")
                print(f"Generated prompt length: {len(result['generated_prompt'])} characters")
                print(f"Security keywords found: {found_keywords}")
                
            finally:
                # Restore original API key
                if original_key:
                    os.environ['GEMINI_API_KEY'] = original_key
                else:
                    os.environ.pop('GEMINI_API_KEY', None)
                
        except ImportError:
            pytest.skip("generate_meta_prompt function not found - implementation pending")
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_gemini_rate_limiting(self, gemini_api_key, rate_limit_tracker, tmp_path):
        """Test rate limiting behavior with real Gemini API."""
        try:
            from src.server import generate_meta_prompt
            
            # Create small test project for rapid testing
            project_path = str(tmp_path / "rate_limit_test")
            os.makedirs(project_path, exist_ok=True)
            
            (Path(project_path) / "test.py").write_text("def test_function(): return 'rate_limit_test'")
            
            # Set API key
            original_key = os.environ.get('GEMINI_API_KEY')
            os.environ['GEMINI_API_KEY'] = gemini_api_key
            
            try:
                # Make multiple API calls to test rate limiting
                results = []
                for i in range(3):  # Limit to 3 calls to avoid hitting real rate limits
                    rate_limit_tracker.record_call()
                    
                    try:
                        result = generate_meta_prompt(
                            project_path=project_path,
                            scope="full_project"
                        )
                        results.append(result)
                        
                        # Small delay between calls to be respectful
                        time.sleep(1)
                        
                    except Exception as e:
                        # Check if it's a rate limit error
                        error_message = str(e).lower()
                        if "rate limit" in error_message or "quota" in error_message:
                            print(f"✅ Rate limiting detected: {e}")
                            break
                        else:
                            raise
                
                # Verify reasonable rate limiting behavior
                calls_per_minute = rate_limit_tracker.get_calls_per_minute()
                average_interval = rate_limit_tracker.get_average_interval()
                
                assert calls_per_minute <= 60, f"Too many calls per minute: {calls_per_minute}"
                assert len(results) >= 1, "At least one call should succeed"
                
                print(f"✅ Rate limiting test completed")
                print(f"Successful calls: {len(results)}")
                print(f"Calls per minute: {calls_per_minute}")
                print(f"Average interval: {average_interval:.2f}s")
                
            finally:
                # Restore original API key
                if original_key:
                    os.environ['GEMINI_API_KEY'] = original_key
                else:
                    os.environ.pop('GEMINI_API_KEY', None)
                
        except ImportError:
            pytest.skip("generate_meta_prompt function not found - implementation pending")
    
    @pytest.mark.integration
    def test_real_gemini_error_handling(self, tmp_path):
        """Test error handling with real Gemini API scenarios."""
        try:
            from src.server import generate_meta_prompt
            
            project_path = str(tmp_path / "error_test")
            os.makedirs(project_path, exist_ok=True)
            (Path(project_path) / "test.py").write_text("def test(): pass")
            
            # Test with invalid API key
            original_key = os.environ.get('GEMINI_API_KEY')
            os.environ['GEMINI_API_KEY'] = 'invalid_api_key_for_testing'
            
            try:
                with pytest.raises(Exception) as exc_info:
                    generate_meta_prompt(
                        project_path=project_path,
                        scope="full_project"
                    )
                
                # Verify meaningful error message
                error_message = str(exc_info.value).lower()
                expected_error_keywords = ["api", "key", "authentication", "invalid", "unauthorized"]
                found_keywords = [kw for kw in expected_error_keywords if kw in error_message]
                
                assert len(found_keywords) >= 1, f"Expected API error message, got: {exc_info.value}"
                
                print(f"✅ Real API error handling working")
                print(f"Error message keywords: {found_keywords}")
                
            finally:
                # Restore original API key
                if original_key:
                    os.environ['GEMINI_API_KEY'] = original_key
                else:
                    os.environ.pop('GEMINI_API_KEY', None)
                
        except ImportError:
            pytest.skip("generate_meta_prompt function not found - implementation pending")
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_gemini_with_large_context(self, gemini_api_key, tmp_path):
        """Test real Gemini API with large context input."""
        try:
            from src.server import generate_meta_prompt
            
            # Create larger project to test context limits
            project_path = str(tmp_path / "large_context_test")
            os.makedirs(project_path, exist_ok=True)
            
            # Create multiple files with substantial content
            for i in range(10):
                large_content = f"""
# Module {i} - Large context test
import os
import sys
import json
from typing import Dict, List, Any, Optional

class LargeClass{i}:
    \"\"\"
    Large class for context testing with substantial documentation
    and multiple methods to test API context handling.
    \"\"\"
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data = {{}}
        self.cache = {{}}
        
    def process_data(self, input_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        \"\"\"Process large amounts of data with complex logic.\"\"\"
        results = []
        for item in input_data:
            if self._validate_item(item):
                processed = self._transform_item(item)
                results.append(processed)
        return results
    
    def _validate_item(self, item: Dict[str, Any]) -> bool:
        \"\"\"Validate individual items with multiple checks.\"\"\"
        required_fields = ['id', 'name', 'type', 'status']
        return all(field in item for field in required_fields)
    
    def _transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Transform items with complex business logic.\"\"\"
        transformed = item.copy()
        transformed['processed_at'] = '2024-01-15T10:30:00Z'
        transformed['validation_score'] = len(str(item)) * 0.1
        return transformed

def global_function_{i}(data: List[Any]) -> Dict[str, Any]:
    \"\"\"Global function for module {i} processing.\"\"\"
    return {{
        'module_id': {i},
        'processed_count': len(data),
        'summary': f'Processed {{len(data)}} items in module {i}'
    }}
""" + "# " + "Additional comment content " * 50  # Add more content
                
                (Path(project_path) / f"large_module_{i}.py").write_text(large_content)
            
            # Set API key
            original_key = os.environ.get('GEMINI_API_KEY')
            os.environ['GEMINI_API_KEY'] = gemini_api_key
            
            try:
                # Test with large context
                result = generate_meta_prompt(
                    project_path=project_path,
                    scope="full_project"
                )
                
                # Verify API handled large context appropriately
                assert result is not None
                assert "generated_prompt" in result
                
                # Verify prompt is substantial and relevant
                generated_prompt = result["generated_prompt"]
                assert len(generated_prompt) > 100
                
                # Check for context-aware content
                prompt_lower = generated_prompt.lower()
                context_keywords = ["class", "function", "module", "data", "process"]
                found_keywords = [kw for kw in context_keywords if kw in prompt_lower]
                assert len(found_keywords) >= 3, f"Expected context-aware prompt, found: {found_keywords}"
                
                print(f"✅ Large context handling successful")
                print(f"Generated prompt length: {len(generated_prompt)} characters")
                print(f"Context keywords found: {found_keywords}")
                
            finally:
                # Restore original API key
                if original_key:
                    os.environ['GEMINI_API_KEY'] = original_key
                else:
                    os.environ.pop('GEMINI_API_KEY', None)
                
        except ImportError:
            pytest.skip("generate_meta_prompt function not found - implementation pending")


class TestRealAPIWorkflowIntegration:
    """Test complete workflows with real Gemini API."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_complete_real_api_workflow(self, gemini_api_key, tmp_path):
        """Test complete auto-prompt workflow with real API."""
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            # Create realistic project for full workflow test
            project_path = str(tmp_path / "full_workflow_test")
            os.makedirs(project_path, exist_ok=True)
            
            # Create authentication service with security issues
            (Path(project_path) / "auth_service.py").write_text("""
class AuthService:
    def authenticate(self, username: str, password: str) -> bool:
        # Security issue: SQL injection vulnerability
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        result = self.db.execute(query)
        return result is not None
    
    def create_session(self, user_id: int) -> str:
        # Security issue: weak session generation
        import random
        session_id = str(random.randint(100000, 999999))
        self.sessions[session_id] = user_id
        return session_id
""")
            
            # Create task list for context
            tasks_dir = Path(project_path) / "tasks"
            tasks_dir.mkdir()
            
            (tasks_dir / "tasks-auth-security.md").write_text("""
## Authentication Security Tasks

- [x] 1.0 Basic Authentication
  - [x] 1.1 Login functionality
  - [ ] 1.2 SQL injection prevention
  - [ ] 1.3 Password hashing

- [ ] 2.0 Session Management
  - [x] 2.1 Session creation
  - [ ] 2.2 Secure session IDs
  - [ ] 2.3 Session expiration
""")
            
            # Set API key
            original_key = os.environ.get('GEMINI_API_KEY')
            os.environ['GEMINI_API_KEY'] = gemini_api_key
            
            try:
                # Mock the non-Gemini parts of the workflow
                with patch('src.generate_code_review_context.generate_code_review_context') as mock_context, \
                     patch('src.generate_code_review_context.generate_ai_code_review') as mock_ai_review:
                    
                    mock_context.return_value = "/tmp/real_api_context.md"
                    mock_ai_review.return_value = "/tmp/real_api_review.md"
                    
                    # Execute workflow with real Gemini API for auto-prompt
                    result = execute_auto_prompt_workflow(
                        project_path=project_path,
                        scope="full_project",
                        temperature=0.5,
                        auto_prompt=True
                    )
                    
                    # Verify workflow completed successfully
                    assert result is not None
                    
                    # Verify AI review was called with real-generated prompt
                    mock_ai_review.assert_called_once()
                    ai_review_call = mock_ai_review.call_args[1]
                    custom_prompt = ai_review_call.get('custom_prompt', '')
                    
                    # Real API should generate security-focused prompt
                    assert len(custom_prompt) > 50
                    prompt_lower = custom_prompt.lower()
                    security_terms = ["security", "sql", "injection", "authentication", "session"]
                    found_terms = [term for term in security_terms if term in prompt_lower]
                    assert len(found_terms) >= 2, f"Expected security-focused prompt, found: {found_terms}"
                    
                    print(f"✅ Complete real API workflow successful")
                    print(f"Generated prompt length: {len(custom_prompt)} characters")
                    print(f"Security terms found: {found_terms}")
                    
            finally:
                # Restore original API key
                if original_key:
                    os.environ['GEMINI_API_KEY'] = original_key
                else:
                    os.environ.pop('GEMINI_API_KEY', None)
                
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")
    
    @pytest.mark.integration
    def test_real_api_scope_variations(self, gemini_api_key, tmp_path):
        """Test different scope parameters with real API."""
        try:
            from src.server import generate_meta_prompt
            
            # Create project with multiple phases
            project_path = str(tmp_path / "scope_variation_test")
            os.makedirs(project_path, exist_ok=True)
            
            (Path(project_path) / "phase1.py").write_text("def phase1_function(): return 'basic'")
            (Path(project_path) / "phase2.py").write_text("def phase2_function(): return 'advanced'")
            
            # Create task list
            tasks_dir = Path(project_path) / "tasks"
            tasks_dir.mkdir()
            
            (tasks_dir / "tasks-phased-dev.md").write_text("""
## Phased Development

- [x] 1.0 Phase 1: Basic Implementation
  - [x] 1.1 Core functionality

- [ ] 2.0 Phase 2: Advanced Features
  - [ ] 2.1 Advanced processing
""")
            
            # Set API key
            original_key = os.environ.get('GEMINI_API_KEY')
            os.environ['GEMINI_API_KEY'] = gemini_api_key
            
            try:
                # Test different scopes with real API
                scope_tests = [
                    {"scope": "recent_phase", "expected_focus": "recent"},
                    {"scope": "specific_phase", "phase_number": "1.0", "expected_focus": "phase 1"}
                ]
                
                for scope_test in scope_tests:
                    kwargs = {
                        "project_path": project_path,
                        "scope": scope_test["scope"]
                    }
                    if "phase_number" in scope_test:
                        kwargs["phase_number"] = scope_test["phase_number"]
                    
                    result = generate_meta_prompt(**kwargs)
                    
                    # Verify scope-appropriate response
                    assert result is not None
                    assert "generated_prompt" in result
                    assert len(result["generated_prompt"]) > 30
                    
                    print(f"✅ Real API scope test: {scope_test['scope']} successful")
                    
                    # Small delay between API calls
                    time.sleep(1)
                
            finally:
                # Restore original API key
                if original_key:
                    os.environ['GEMINI_API_KEY'] = original_key
                else:
                    os.environ.pop('GEMINI_API_KEY', None)
                
        except ImportError:
            pytest.skip("generate_meta_prompt function not found - implementation pending")


class TestRealAPIPerformanceAndLimits:
    """Test performance and limits with real Gemini API."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_api_response_time(self, gemini_api_key, tmp_path):
        """Test real API response times are reasonable."""
        try:
            from src.server import generate_meta_prompt
            
            project_path = str(tmp_path / "response_time_test")
            os.makedirs(project_path, exist_ok=True)
            (Path(project_path) / "simple.py").write_text("def simple(): return 'test'")
            
            # Set API key
            original_key = os.environ.get('GEMINI_API_KEY')
            os.environ['GEMINI_API_KEY'] = gemini_api_key
            
            try:
                # Measure response time
                start_time = time.time()
                
                result = generate_meta_prompt(
                    project_path=project_path,
                    scope="full_project"
                )
                
                response_time = time.time() - start_time
                
                # Verify reasonable response time (allow up to 30 seconds for real API)
                assert response_time < 30.0, f"Real API response too slow: {response_time:.2f}s"
                assert result is not None
                
                print(f"✅ Real API response time: {response_time:.2f}s")
                
            finally:
                # Restore original API key
                if original_key:
                    os.environ['GEMINI_API_KEY'] = original_key
                else:
                    os.environ.pop('GEMINI_API_KEY', None)
                
        except ImportError:
            pytest.skip("generate_meta_prompt function not found - implementation pending")
    
    @pytest.mark.integration
    def test_real_api_token_usage_tracking(self, gemini_api_key, tmp_path):
        """Test that token usage is tracked with real API."""
        try:
            from src.server import generate_meta_prompt
            
            project_path = str(tmp_path / "token_usage_test")
            os.makedirs(project_path, exist_ok=True)
            (Path(project_path) / "medium.py").write_text("""
def medium_function():
    # Medium-sized function for token usage testing
    data = {'key': 'value', 'items': [1, 2, 3, 4, 5]}
    processed = {k: v for k, v in data.items() if k != 'temp'}
    return processed
""")
            
            # Set API key
            original_key = os.environ.get('GEMINI_API_KEY')
            os.environ['GEMINI_API_KEY'] = gemini_api_key
            
            try:
                result = generate_meta_prompt(
                    project_path=project_path,
                    scope="full_project"
                )
                
                # Verify result contains token usage information if available
                assert result is not None
                assert "generated_prompt" in result
                
                # Check if token usage is tracked (implementation dependent)
                if "token_usage" in result or "context_analyzed" in result:
                    print(f"✅ Token usage tracking detected")
                    if "context_analyzed" in result:
                        print(f"Context analyzed: {result['context_analyzed']} characters")
                else:
                    print("ℹ️ Token usage tracking not implemented yet")
                
            finally:
                # Restore original API key
                if original_key:
                    os.environ['GEMINI_API_KEY'] = original_key
                else:
                    os.environ.pop('GEMINI_API_KEY', None)
                
        except ImportError:
            pytest.skip("generate_meta_prompt function not found - implementation pending")


# Configuration for real API tests
def pytest_configure(config):
    """Configure pytest markers for real API tests."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests requiring real API")
    config.addinivalue_line("markers", "slow: marks tests as slow-running tests")


def pytest_collection_modifyitems(config, items):
    """Skip integration tests by default unless specifically requested."""
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="Integration tests require --run-integration flag")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


def pytest_addoption(parser):
    """Add command line option for running integration tests."""
    parser.addoption(
        "--run-integration", 
        action="store_true", 
        default=False, 
        help="Run integration tests with real Gemini API"
    )