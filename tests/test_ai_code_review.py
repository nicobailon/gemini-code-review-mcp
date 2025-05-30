"""
Tests for standalone AI review tool interface
"""

import pytest
import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestStandaloneAIReviewToolInterface:
    """Test standalone AI review tool interface"""
    
    def test_generate_ai_review_function_exists(self):
        """Test that generate_ai_review function exists and is callable"""
        try:
            from ai_code_review import generate_ai_review
            assert callable(generate_ai_review), "generate_ai_review should be callable"
        except ImportError:
            pytest.fail("ai_code_review module should exist with generate_ai_review function")
    
    def test_generate_ai_review_requires_context_file_path(self):
        """Test that generate_ai_review requires context_file_path parameter"""
        from ai_code_review import generate_ai_review
        
        with pytest.raises((TypeError, ValueError)) as exc_info:
            generate_ai_review()
        
        error_message = str(exc_info.value).lower()
        assert "context_file_path" in error_message or "required" in error_message
    
    def test_generate_ai_review_validates_context_file_exists(self):
        """Test that generate_ai_review validates context file exists"""
        from ai_code_review import generate_ai_review
        
        with pytest.raises((FileNotFoundError, ValueError)) as exc_info:
            generate_ai_review("/nonexistent/context.md")
        
        error_message = str(exc_info.value).lower()
        assert ("not found" in error_message or 
               "does not exist" in error_message or
               "no such file" in error_message)
    
    def test_generate_ai_review_accepts_valid_context_file(self):
        """Test that generate_ai_review accepts valid context file"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "context.md"
            context_file.write_text("# Test Context\nSome context content")
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = str(Path(temp_dir) / "review.md")
                # Removed builtins.open mock that conflicts with real file reading
                result = generate_ai_review(str(context_file))
                assert result is not None


class TestContextFileReadingAndProcessing:
    """Test context file reading and processing"""
    
    def test_reads_context_file_content(self):
        """Test that context file content is read correctly"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "context.md"
            test_content = """# Code Review Context
            
<overall_prd_summary>
Test PRD summary
</overall_prd_summary>

<current_phase_number>
1.0
</current_phase_number>
"""
            context_file.write_text(test_content)
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = str(Path(temp_dir) / "review.md")
                generate_ai_review(str(context_file))
                
                # Verify the context content was passed to Gemini
                mock_gemini.assert_called_once()
                call_args = mock_gemini.call_args[0]
                assert test_content in call_args[0]
    
    def test_handles_large_context_files(self):
        """Test handling of large context files"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "large_context.md"
            large_content = "# Large Context\n" + "Large content line\n" * 1000
            context_file.write_text(large_content)
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = str(Path(temp_dir) / "review.md")
                # Removed builtins.open mock that conflicts with real file reading
                result = generate_ai_review(str(context_file))
                assert result is not None
    
    def test_handles_empty_context_files(self):
        """Test handling of empty context files"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "empty_context.md"
            context_file.write_text("")
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = str(Path(temp_dir) / "review.md")
                # Removed builtins.open mock that conflicts with real file reading

                result = generate_ai_review(str(context_file))
                assert result is not None
    
    def test_validates_context_file_format(self):
        """Test validation of context file format"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "invalid_context.md"
            context_file.write_text("Invalid context format without proper structure")
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = str(Path(temp_dir) / "review.md")
                # Removed builtins.open mock that conflicts with real file reading
                # Should handle gracefully even with invalid format
                result = generate_ai_review(str(context_file))
                assert result is not None


class TestModelParameterHandlingAndValidation:
    """Test model parameter handling and validation"""
    
    def test_accepts_optional_model_parameter(self):
        """Test that model parameter is optional"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "context.md"
            context_file.write_text("# Test Context")
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = str(Path(temp_dir) / "review.md")
                # Removed builtins.open mock that conflicts with real file reading
                # Should work without model parameter
                result = generate_ai_review(str(context_file))
                assert result is not None
    
    def test_accepts_valid_model_parameter(self):
        """Test that valid model parameter is accepted"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "context.md"
            context_file.write_text("# Test Context")
            
            valid_models = ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]
            
            for model in valid_models:
                with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                    mock_gemini.return_value = str(Path(temp_dir) / "review.md")
                    # Removed builtins.open mock that conflicts with real file reading

                    result = generate_ai_review(str(context_file), model=model)
                    assert result is not None
    
    def test_validates_invalid_model_parameter(self):
        """Test validation of invalid model parameter"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "context.md"
            context_file.write_text("# Test Context")
            
            invalid_models = ["invalid-model", "", None, 123, []]
            
            for invalid_model in invalid_models:
                with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                    mock_gemini.return_value = str(Path(temp_dir) / "review.md")
                    # Removed builtins.open mock that conflicts with real file reading
                    # Should handle gracefully or raise appropriate error
                    try:
                        result = generate_ai_review(str(context_file), model=invalid_model)
                        # If it doesn't raise an error, it should still work
                        assert result is not None
                    except (ValueError, TypeError):
                        # Acceptable to raise validation errors
                        pass
    
    def test_model_parameter_passed_to_gemini(self):
        """Test that model parameter is passed to Gemini integration"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "context.md"
            context_file.write_text("# Test Context")
            
            test_model = "gemini-2.0-flash-exp"
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = str(Path(temp_dir) / "review.md")
                # Removed builtins.open mock that conflicts with real file reading

                with patch.dict(os.environ, {}, clear=True):  # Start with clean environment
                    generate_ai_review(str(context_file), model=test_model)
                    
                    # Verify model was passed to Gemini function
                    mock_gemini.assert_called_once()
    
    def test_model_parameter_sets_gemini_model_env_var(self):
        """Test that model parameter correctly sets GEMINI_MODEL environment variable"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "context.md"
            context_file.write_text("# Test Context")
            
            test_model = "gemini-2.5-pro-preview-05-06"
            
            env_var_captured = None
            
            def capture_env_var(*args, **kwargs):
                nonlocal env_var_captured
                env_var_captured = os.environ.get('GEMINI_MODEL')
                return str(Path(temp_dir) / "review.md")
            
            with patch('ai_code_review.send_to_gemini_for_review', side_effect=capture_env_var):
                # Removed builtins.open mock that conflicts with real file reading

                with patch.dict(os.environ, {}, clear=True):  # Start with clean environment
                    generate_ai_review(str(context_file), model=test_model)
                    
                    # Verify GEMINI_MODEL was set correctly during the call
                    assert env_var_captured == test_model
            
            # Verify environment is cleaned up after the call
            assert 'GEMINI_MODEL' not in os.environ or os.environ.get('GEMINI_MODEL') != test_model
    
    def test_model_parameter_restores_original_gemini_model(self):
        """Test that original GEMINI_MODEL environment variable is restored"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "context.md"
            context_file.write_text("# Test Context")
            
            original_model = "gemini-2.5-flash"
            test_model = "gemini-2.5-pro-preview-05-06"
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = str(Path(temp_dir) / "review.md")
                # Removed builtins.open mock that conflicts with real file reading

                with patch.dict(os.environ, {'GEMINI_MODEL': original_model}):
                    generate_ai_review(str(context_file), model=test_model)
                    
                    # Verify original model is restored
                    assert os.environ.get('GEMINI_MODEL') == original_model


class TestAIReviewOutputFormattingAndFileNaming:
    """Test AI review output formatting and file naming"""
    
    def test_generates_appropriately_named_output_file(self):
        """Test that output file has appropriate name"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "context.md"
            context_file.write_text("# Test Context")
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                expected_output = str(Path(temp_dir) / "code-review-ai-feedback-20241201-120000.md")
                mock_gemini.return_value = expected_output
                # Removed builtins.open mock that conflicts with real file reading

                result = generate_ai_review(str(context_file))
                
                assert result is not None
                # Should follow naming convention for AI review files
                assert "ai-feedback" in result or "ai-review" in result
    
    def test_respects_custom_output_path(self):
        """Test that custom output path is respected"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "context.md"
            context_file.write_text("# Test Context")
            custom_output = str(Path(temp_dir) / "custom-ai-review.md")
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = custom_output
                # Removed builtins.open mock that conflicts with real file reading

                result = generate_ai_review(str(context_file), output_path=custom_output)
                
                assert result == custom_output
    
    def test_output_file_naming_includes_timestamp(self):
        """Test that output file naming includes timestamp"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "context.md"
            context_file.write_text("# Test Context")
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = str(Path(temp_dir) / "ai-review.md")
                result = generate_ai_review(str(context_file))
                
                # Should include timestamp pattern
                import re
                timestamp_pattern = r'\d{8}-\d{6}'
                assert re.search(timestamp_pattern, result) is not None
    
    def test_avoids_output_file_conflicts(self):
        """Test that output file naming avoids conflicts"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "context.md"
            context_file.write_text("# Test Context")
            
            # Create existing file
            existing_file = Path(temp_dir) / "code-review-ai-feedback-20241201-120000.md"
            existing_file.write_text("Existing content")
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                new_output = str(Path(temp_dir) / "code-review-ai-feedback-20241201-120001.md")
                mock_gemini.return_value = new_output
                # Removed builtins.open mock that conflicts with real file reading

                result = generate_ai_review(str(context_file))
                
                # Should generate different filename
                assert result != str(existing_file)


class TestErrorHandlingForAIReview:
    """Test error handling for AI review functionality"""
    
    def test_handles_missing_context_files(self):
        """Test handling of missing context files"""
        from ai_code_review import generate_ai_review
        
        with pytest.raises((FileNotFoundError, ValueError)):
            generate_ai_review("/nonexistent/path/context.md")
    
    def test_handles_api_failures(self):
        """Test handling of API failures"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "context.md"
            context_file.write_text("# Test Context")
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.side_effect = Exception("API failure")
                
                with pytest.raises(Exception):
                    generate_ai_review(str(context_file))
    
    def test_handles_invalid_file_permissions(self):
        """Test handling of invalid file permissions"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "context.md"
            context_file.write_text("# Test Context")
            
            # Mock permission error when reading
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                with pytest.raises(PermissionError):
                    generate_ai_review(str(context_file))
    
    def test_handles_gemini_unavailable(self):
        """Test handling when Gemini is unavailable"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "context.md"
            context_file.write_text("# Test Context")
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = None  # Gemini unavailable
                
                result = generate_ai_review(str(context_file))
                # Should handle gracefully
                assert result is None or isinstance(result, str)
    
    def test_provides_clear_error_messages(self):
        """Test that clear error messages are provided"""
        from ai_code_review import generate_ai_review
        
        # Test with invalid context file path
        try:
            generate_ai_review("")
        except (ValueError, FileNotFoundError) as e:
            assert len(str(e)) > 0
            # Error message should be informative
            error_msg = str(e).lower()
            assert any(word in error_msg for word in ["context", "file", "path", "required"])


class TestAIReviewIntegrationWithGemini:
    """Test AI review integration with Gemini"""
    
    def test_calls_gemini_integration_correctly(self):
        """Test that Gemini integration is called correctly"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "context.md"
            test_content = "# Test Context Content"
            context_file.write_text(test_content)
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = str(Path(temp_dir) / "review.md")
                # Removed builtins.open mock that conflicts with real file reading

                generate_ai_review(str(context_file))
                
                # Verify Gemini was called with correct parameters
                mock_gemini.assert_called_once()
                call_args = mock_gemini.call_args[0]
                assert test_content in call_args[0]
    
    def test_passes_project_path_to_gemini(self):
        """Test that project path is passed to Gemini correctly"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "context.md"
            context_file.write_text("# Test Context")
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = str(Path(temp_dir) / "review.md")
                # Removed builtins.open mock that conflicts with real file reading

                generate_ai_review(str(context_file))
                
                # Verify project path was passed (derived from context file location)
                mock_gemini.assert_called_once()
                call_args = mock_gemini.call_args
                # Project path should be derived from context file path
                assert len(call_args[0]) >= 2  # context content and project path
    
    def test_handles_gemini_response_correctly(self):
        """Test that Gemini response is handled correctly"""
        from ai_code_review import generate_ai_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "context.md"
            context_file.write_text("# Test Context")
            
            expected_output = str(Path(temp_dir) / "gemini-review.md")
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = expected_output
                # Removed builtins.open mock that conflicts with real file reading

                result = generate_ai_review(str(context_file))
                
                assert result == expected_output


class TestStandaloneToolSeparation:
    """Test that AI review tool is properly separated from context generation"""
    
    def test_ai_review_module_is_separate(self):
        """Test that AI review is in separate module"""
        # Should be able to import ai_code_review separately
        try:
            import ai_code_review
            assert hasattr(ai_code_review, 'generate_ai_review')
        except ImportError:
            pytest.fail("ai_code_review should be a separate module")
    
    def test_ai_review_does_not_depend_on_context_generation(self):
        """Test that AI review doesn't directly depend on context generation"""
        from ai_code_review import generate_ai_review
        
        # Should work independently of generate_code_review_context
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "standalone_context.md"
            context_file.write_text("# Standalone Context for AI Review")
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = str(Path(temp_dir) / "review.md")
                # Removed builtins.open mock that conflicts with real file reading

                result = generate_ai_review(str(context_file))
                assert result is not None
    
    def test_clean_api_separation(self):
        """Test clean API separation between tools"""
        # Context generation and AI review should have distinct interfaces
        from ai_code_review import generate_ai_review
        
        # AI review should only need context file path, not project setup
        with tempfile.TemporaryDirectory() as temp_dir:
            context_file = Path(temp_dir) / "clean_context.md"
            context_file.write_text("# Clean API Test")
            
            with patch('ai_code_review.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = str(Path(temp_dir) / "review.md")
                # Removed builtins.open mock that conflicts with real file reading
                # Should only need context file path
                result = generate_ai_review(str(context_file))
                assert result is not None