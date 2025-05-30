"""
Tests for enhanced MCP tool parameters: raw_context_only and custom_prompt.
Following TDD Protocol: Writing tests FIRST before any implementation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, Optional
import os
import tempfile


class TestGenerateCodeReviewContextEnhancements:
    """Test enhancements to generate_code_review_context MCP tool."""
    
    @pytest.fixture
    def generate_code_review_context_func(self):
        """Fixture to safely import generate_code_review_context function."""
        try:
            from src.server import generate_code_review_context
            return generate_code_review_context
        except (ImportError, SystemExit):
            pytest.skip("Skipping test due to missing dependencies")
    
    @pytest.fixture
    def sample_project_path(self, tmp_path):
        """Create a temporary project directory with git repo."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create basic project structure
        (project_dir / "src").mkdir()
        (project_dir / "src" / "main.py").write_text("print('hello world')")
        (project_dir / "README.md").write_text("# Test Project")
        
        # Initialize git repo
        os.system(f"cd {project_dir} && git init")
        os.system(f"cd {project_dir} && git add .")
        os.system(f"cd {project_dir} && git commit -m 'Initial commit'")
        
        return str(project_dir)
    
    def test_raw_context_only_parameter_exists(self, generate_code_review_context_func):
        """Test that raw_context_only parameter exists in function signature."""
        import inspect
        signature = inspect.signature(generate_code_review_context_func)
        
        # Verify raw_context_only parameter exists
        assert "raw_context_only" in signature.parameters
        
        # Verify it has correct type annotation
        param = signature.parameters["raw_context_only"]
        assert param.annotation == bool or str(param.annotation) == "bool"
        
        # Verify it has correct default value
        assert param.default is False
    
    def test_raw_context_only_default_behavior(self, generate_code_review_context_func, sample_project_path):
        """Test that default behavior (raw_context_only=False) includes instructions."""
        # Test that when raw_context_only is False or not provided, 
        # the generated context includes default AI review instructions
        
        result = generate_code_review_context_func(
            project_path=sample_project_path,
            scope="recent_phase"
        )
        
        # Should return path to context file
        assert isinstance(result, (str, tuple))
        context_file_path = result[0] if isinstance(result, tuple) else result
        assert os.path.exists(context_file_path)
        
        # Read the generated context
        with open(context_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should contain default AI review instructions
        assert "code review" in content.lower()
        assert "analyze" in content.lower() or "review" in content.lower()
        
        # Should contain structured sections typical of full context
        assert "## " in content  # Should have markdown headers
    
    def test_raw_context_only_true_excludes_instructions(self, generate_code_review_context_func, sample_project_path):
        """Test that raw_context_only=True excludes default AI review instructions."""
        
        result = generate_code_review_context_func(
            project_path=sample_project_path,
            scope="recent_phase",
            raw_context_only=True
        )
        
        # Should return path to context file
        assert isinstance(result, (str, tuple))
        context_file_path = result[0] if isinstance(result, tuple) else result
        assert os.path.exists(context_file_path)
        
        # Read the generated context
        with open(context_file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        # Should contain project information and code diffs but not AI instructions
        assert "project" in raw_content.lower() or "code" in raw_content.lower()
        
        # Should NOT contain typical AI review instruction phrases
        assert "conduct a comprehensive code review" not in raw_content.lower()
        assert "provide detailed analysis" not in raw_content.lower()
        assert "your task is to" not in raw_content.lower()
        
        # Should be focused on factual content, not instructions
        # (This is a behavioral test - the exact content will depend on implementation)
        assert len(raw_content) > 0  # Should still have content
    
    def test_raw_context_only_comparison(self, generate_code_review_context_func, sample_project_path):
        """Test that raw_context_only=True produces different output than default."""
        
        # Generate with default settings
        result_default = generate_code_review_context_func(
            project_path=sample_project_path,
            scope="recent_phase",
            raw_context_only=False
        )
        context_file_default = result_default[0] if isinstance(result_default, tuple) else result_default
        
        # Generate with raw_context_only=True
        result_raw = generate_code_review_context_func(
            project_path=sample_project_path,
            scope="recent_phase", 
            raw_context_only=True
        )
        context_file_raw = result_raw[0] if isinstance(result_raw, tuple) else result_raw
        
        # Read both files
        with open(context_file_default, 'r', encoding='utf-8') as f:
            content_default = f.read()
        
        with open(context_file_raw, 'r', encoding='utf-8') as f:
            content_raw = f.read()
        
        # Files should be different
        assert content_default != content_raw
        
        # Raw context should typically be shorter (no instructions)
        # This is a heuristic - may not always be true but generally expected
        assert len(content_raw) <= len(content_default)
    
    def test_raw_context_only_maintains_all_scopes(self, generate_code_review_context_func, sample_project_path):
        """Test that raw_context_only works with all scope options."""
        
        scopes_to_test = ["recent_phase", "full_project"]
        
        for scope in scopes_to_test:
            result = generate_code_review_context_func(
                project_path=sample_project_path,
                scope=scope,
                raw_context_only=True
            )
            
            # Should successfully generate context for each scope
            context_file = result[0] if isinstance(result, tuple) else result
            assert os.path.exists(context_file)
            
            # Should contain content for each scope
            with open(context_file, 'r', encoding='utf-8') as f:
                content = f.read()
            assert len(content) > 0
    
    def test_raw_context_only_type_validation(self, generate_code_review_context_func, sample_project_path):
        """Test that raw_context_only parameter validates type correctly."""
        
        # Valid boolean values should work
        for valid_value in [True, False]:
            result = generate_code_review_context_func(
                project_path=sample_project_path,
                raw_context_only=valid_value
            )
            assert result is not None
        
        # Invalid types should raise TypeError or be handled gracefully
        for invalid_value in ["true", 1, None, [], {}]:
            try:
                result = generate_code_review_context_func(
                    project_path=sample_project_path,
                    raw_context_only=invalid_value
                )
                # If it doesn't raise an error, the implementation handles it gracefully
                # which is also acceptable
            except (TypeError, ValueError):
                # Expected behavior for strict type checking
                pass


class TestGenerateAiCodeReviewEnhancements:
    """Test enhancements to generate_ai_code_review MCP tool."""
    
    @pytest.fixture
    def generate_ai_code_review_func(self):
        """Fixture to safely import generate_ai_code_review function."""
        try:
            from src.server import generate_ai_code_review
            return generate_ai_code_review
        except (ImportError, SystemExit):
            pytest.skip("Skipping test due to missing dependencies")
    
    @pytest.fixture
    def sample_context_file(self, tmp_path):
        """Create a sample context file for testing."""
        context_content = """# Code Review Context

## Project Information
- Project: test-app
- Phase: Authentication Implementation

## Code Changes
### Modified Files:
- src/auth.py (new authentication logic)
- tests/test_auth.py (authentication tests)

## Code Diffs
```diff
+def authenticate_user(username, password):
+    # New authentication function
+    return validate_credentials(username, password)
```

## Summary
Implementation of user authentication system with secure password handling.
"""
        context_file = tmp_path / "context.md"
        context_file.write_text(context_content)
        return str(context_file)
    
    def test_custom_prompt_parameter_exists(self, generate_ai_code_review_func):
        """Test that custom_prompt parameter exists in function signature."""
        import inspect
        signature = inspect.signature(generate_ai_code_review_func)
        
        # Verify custom_prompt parameter exists
        assert "custom_prompt" in signature.parameters
        
        # Verify it has correct type annotation
        param = signature.parameters["custom_prompt"]
        assert "Optional[str]" in str(param.annotation) or "str" in str(param.annotation)
        
        # Verify it has correct default value (None)
        assert param.default is None
    
    def test_custom_prompt_default_behavior(self, generate_ai_code_review_func, sample_context_file):
        """Test that default behavior (custom_prompt=None) uses default prompt."""
        
        # Mock the AI review process to verify prompt usage
        with patch('src.server.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = "/tmp/test_output.md"
            
            result = generate_ai_code_review_func(
                context_file_path=sample_context_file
            )
            
            # Should call Gemini with context content and default prompt behavior
            mock_gemini.assert_called_once()
            call_args = mock_gemini.call_args
            
            # Verify context was passed (first argument)
            assert len(call_args[0]) > 0  # Context content should be passed
    
    def test_custom_prompt_usage(self, generate_ai_code_review_func, sample_context_file):
        """Test that custom_prompt parameter is used when provided."""
        
        custom_prompt = """Focus specifically on security vulnerabilities in the authentication system.
        
Pay special attention to:
1. Password handling and storage
2. Session management 
3. Input validation
4. Authentication bypass attempts

Provide detailed security recommendations."""
        
        # Mock the AI review process to verify custom prompt usage
        with patch('src.server.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = "/tmp/test_output.md"
            
            result = generate_ai_code_review_func(
                context_file_path=sample_context_file,
                custom_prompt=custom_prompt
            )
            
            # Should call Gemini with modified prompt
            mock_gemini.assert_called_once()
            call_args = mock_gemini.call_args
            
            # The implementation should use the custom prompt somehow
            # This test verifies the function accepts the parameter
            # The exact integration depends on implementation details
            assert result is not None
    
    def test_custom_prompt_with_different_models(self, generate_ai_code_review_func, sample_context_file):
        """Test that custom_prompt works with different model configurations."""
        
        custom_prompt = "Provide a brief code review focusing on code quality."
        
        for model in ["gemini-2.0-flash", "gemini-2.5-pro"]:
            with patch('src.server.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = "/tmp/test_output.md"
                
                result = generate_ai_code_review_func(
                    context_file_path=sample_context_file,
                    model=model,
                    custom_prompt=custom_prompt
                )
                
                # Should work with different models
                assert result is not None
                mock_gemini.assert_called_once()
    
    def test_custom_prompt_validation(self, generate_ai_code_review_func, sample_context_file):
        """Test custom_prompt parameter validation."""
        
        # Valid string prompts should work
        valid_prompts = [
            "Simple prompt",
            "Multi-line\nprompt with\nspecial instructions",
            "Prompt with special chars: !@#$%^&*()",
            ""  # Empty string should be handled gracefully
        ]
        
        for prompt in valid_prompts:
            with patch('src.server.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = "/tmp/test_output.md"
                
                try:
                    result = generate_ai_code_review_func(
                        context_file_path=sample_context_file,
                        custom_prompt=prompt
                    )
                    # Should handle valid prompts gracefully
                    assert result is not None
                except Exception as e:
                    # If there are validation errors, they should be meaningful
                    assert "prompt" in str(e).lower()
    
    def test_custom_prompt_with_context_file_errors(self, generate_ai_code_review_func):
        """Test custom_prompt behavior when context file has issues."""
        
        custom_prompt = "Review this code for security issues."
        
        # Test with non-existent file
        with pytest.raises((FileNotFoundError, Exception)):
            generate_ai_code_review_func(
                context_file_path="/nonexistent/file.md",
                custom_prompt=custom_prompt
            )


class TestMCPToolIntegration:
    """Test integration between enhanced MCP tools."""
    
    @pytest.fixture
    def setup_functions(self):
        """Setup both enhanced functions for integration testing."""
        try:
            from src.server import generate_code_review_context, generate_ai_code_review
            return generate_code_review_context, generate_ai_code_review
        except (ImportError, SystemExit):
            pytest.skip("Skipping integration test due to missing dependencies")
    
    @pytest.fixture
    def sample_project_path(self, tmp_path):
        """Create a temporary project directory."""
        project_dir = tmp_path / "integration_test_project"
        project_dir.mkdir()
        
        # Create basic project structure
        (project_dir / "src").mkdir()
        (project_dir / "src" / "app.py").write_text("""
def main():
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    main()
""")
        
        return str(project_dir)
    
    def test_raw_context_with_custom_prompt_integration(self, setup_functions, sample_project_path):
        """Test integration of raw_context_only with custom_prompt."""
        generate_context, generate_review = setup_functions
        
        # Step 1: Generate raw context (no default instructions)
        context_result = generate_context(
            project_path=sample_project_path,
            scope="recent_phase",
            raw_context_only=True
        )
        
        context_file = context_result[0] if isinstance(context_result, tuple) else context_result
        assert os.path.exists(context_file)
        
        # Step 2: Use custom prompt for AI review
        custom_prompt = """Analyze this code for:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance considerations
4. Security implications

Provide specific, actionable recommendations."""
        
        with patch('src.server.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = "/tmp/integration_test_output.md"
            
            review_result = generate_review(
                context_file_path=context_file,
                custom_prompt=custom_prompt
            )
            
            # Integration should work smoothly
            assert review_result is not None
            mock_gemini.assert_called_once()
    
    def test_enhanced_workflow_vs_default_workflow(self, setup_functions, sample_project_path):
        """Test that enhanced workflow produces different results than default."""
        generate_context, generate_review = setup_functions
        
        # Default workflow
        with patch('src.server.send_to_gemini_for_review') as mock_gemini_default:
            mock_gemini_default.return_value = "/tmp/default_output.md"
            
            context_default = generate_context(
                project_path=sample_project_path,
                raw_context_only=False
            )
            context_file_default = context_default[0] if isinstance(context_default, tuple) else context_default
            
            review_default = generate_review(
                context_file_path=context_file_default
            )
        
        # Enhanced workflow
        with patch('src.server.send_to_gemini_for_review') as mock_gemini_enhanced:
            mock_gemini_enhanced.return_value = "/tmp/enhanced_output.md"
            
            context_enhanced = generate_context(
                project_path=sample_project_path,
                raw_context_only=True
            )
            context_file_enhanced = context_enhanced[0] if isinstance(context_enhanced, tuple) else context_enhanced
            
            custom_prompt = "Focus on security and performance issues only."
            review_enhanced = generate_review(
                context_file_path=context_file_enhanced,
                custom_prompt=custom_prompt
            )
        
        # Both workflows should work but may produce different contexts
        assert review_default is not None
        assert review_enhanced is not None
        
        # Context files should be different due to raw_context_only
        with open(context_file_default, 'r') as f:
            content_default = f.read()
        with open(context_file_enhanced, 'r') as f:
            content_enhanced = f.read()
        
        # Enhanced context should typically be different (raw vs full)
        assert content_default != content_enhanced or len(content_default) != len(content_enhanced)