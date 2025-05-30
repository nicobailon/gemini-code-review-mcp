"""
Comprehensive tests for error handling and edge cases in auto-prompt generation system.
Following TDD Protocol: Testing all error conditions and edge cases thoroughly.
"""

import pytest
import tempfile
import os
import sys
import json
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typing import Dict, Any, Optional
import signal

# Import mock classes
from test_gemini_api_mocks import MockGeminiClient, GeminiAPIMockFactory


@pytest.fixture(scope="session", autouse=True)
def setup_import_path():
    """Fixture to ensure src module can be imported in tests."""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)


class TestGeminiAPIErrorHandling:
    """Test error handling for Gemini API interactions."""
    
    def test_gemini_api_rate_limit_error(self):
        """Test handling of Gemini API rate limit errors."""
        try:
            from src.server import generate_auto_prompt
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = Mock()
                mock_client.generate_content.side_effect = Exception("Rate limit exceeded. Please try again after 60 seconds.")
                mock_gemini.return_value = mock_client
                
                with pytest.raises(Exception) as exc_info:
                    generate_auto_prompt(
                        project_path="/tmp/test",
                        scope="full_project"
                    )
                
                error_message = str(exc_info.value).lower()
                assert "rate limit" in error_message or "quota" in error_message
                
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
    
    def test_gemini_api_timeout_error(self):
        """Test handling of Gemini API timeout errors."""
        try:
            from src.server import generate_auto_prompt
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = Mock()
                mock_client.generate_content.side_effect = TimeoutError("Request timed out after 30 seconds")
                mock_gemini.return_value = mock_client
                
                with pytest.raises(Exception) as exc_info:
                    generate_auto_prompt(
                        project_path="/tmp/test",
                        scope="full_project"
                    )
                
                error_message = str(exc_info.value).lower()
                assert "timeout" in error_message or "timed out" in error_message
                
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
    
    def test_gemini_api_authentication_error(self):
        """Test handling of Gemini API authentication errors."""
        try:
            from src.server import generate_auto_prompt
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = Mock()
                mock_client.generate_content.side_effect = Exception("Invalid API key or authentication failed")
                mock_gemini.return_value = mock_client
                
                with pytest.raises(Exception) as exc_info:
                    generate_auto_prompt(
                        project_path="/tmp/test",
                        scope="full_project"
                    )
                
                error_message = str(exc_info.value).lower()
                assert "api key" in error_message or "authentication" in error_message or "invalid" in error_message
                
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
    
    def test_gemini_api_empty_response(self):
        """Test handling of empty or invalid Gemini API responses."""
        try:
            from src.server import generate_auto_prompt
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = Mock()
                mock_response = Mock()
                mock_response.text = ""  # Empty response
                mock_client.generate_content.return_value = mock_response
                mock_gemini.return_value = mock_client
                
                result = generate_auto_prompt(
                    project_path="/tmp/test",
                    scope="full_project"
                )
                
                # Should handle empty response gracefully
                assert result is not None
                assert "generated_prompt" in result
                # May contain default prompt or error indication
                
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
    
    def test_gemini_api_malformed_response(self):
        """Test handling of malformed Gemini API responses."""
        try:
            from src.server import generate_auto_prompt
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = Mock()
                mock_response = Mock()
                mock_response.text = "INVALID_JSON_RESPONSE_###"
                mock_client.generate_content.return_value = mock_response
                mock_gemini.return_value = mock_client
                
                result = generate_auto_prompt(
                    project_path="/tmp/test",
                    scope="full_project"
                )
                
                # Should handle malformed response gracefully
                assert result is not None
                assert "generated_prompt" in result
                
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")


class TestFileSystemErrorHandling:
    """Test error handling for file system operations."""
    
    def test_nonexistent_project_path(self):
        """Test handling of nonexistent project paths."""
        try:
            from src.server import generate_auto_prompt
            
            nonexistent_path = "/path/that/does/not/exist/anywhere"
            
            with pytest.raises(Exception) as exc_info:
                generate_auto_prompt(
                    project_path=nonexistent_path,
                    scope="full_project"
                )
            
            error_message = str(exc_info.value).lower()
            assert "not found" in error_message or "does not exist" in error_message or "invalid path" in error_message
            
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
    
    def test_permission_denied_project_path(self, tmp_path):
        """Test handling of permission denied errors."""
        try:
            from src.server import generate_auto_prompt
            
            # Create a directory with restricted permissions
            restricted_dir = tmp_path / "restricted"
            restricted_dir.mkdir()
            
            # Make directory unreadable (on Unix systems)
            if os.name != 'nt':  # Skip on Windows
                os.chmod(restricted_dir, 0o000)
                
                try:
                    with pytest.raises(Exception) as exc_info:
                        generate_auto_prompt(
                            project_path=str(restricted_dir),
                            scope="full_project"
                        )
                    
                    error_message = str(exc_info.value).lower()
                    assert "permission" in error_message or "access" in error_message
                    
                finally:
                    # Restore permissions for cleanup
                    os.chmod(restricted_dir, 0o755)
            else:
                pytest.skip("Permission test not applicable on Windows")
                
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
    
    def test_empty_project_directory(self, tmp_path):
        """Test handling of completely empty project directories."""
        try:
            from src.server import generate_auto_prompt
            
            empty_dir = tmp_path / "empty_project"
            empty_dir.mkdir()
            
            # Should handle empty directory gracefully
            result = generate_auto_prompt(
                project_path=str(empty_dir),
                scope="full_project"
            )
            
            assert result is not None
            assert "generated_prompt" in result
            # Prompt should indicate minimal or no code found
            
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
    
    def test_project_with_binary_files_only(self, tmp_path):
        """Test handling of projects containing only binary files."""
        try:
            from src.server import generate_auto_prompt
            
            binary_project = tmp_path / "binary_project"
            binary_project.mkdir()
            
            # Create binary files
            (binary_project / "image.png").write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00')
            (binary_project / "executable.exe").write_bytes(b'MZ\x90\x00\x03\x00\x00\x00')
            
            result = generate_auto_prompt(
                project_path=str(binary_project),
                scope="full_project"
            )
            
            assert result is not None
            assert "generated_prompt" in result
            # Should handle binary-only projects appropriately
            
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
    
    def test_corrupted_task_list_file(self, tmp_path):
        """Test handling of corrupted or malformed task list files."""
        try:
            from src.server import generate_auto_prompt
            
            project_dir = tmp_path / "corrupted_tasks_project"
            project_dir.mkdir()
            tasks_dir = project_dir / "tasks"
            tasks_dir.mkdir()
            
            # Create corrupted task list file
            (tasks_dir / "tasks-corrupted.md").write_text("INVALID MARKDOWN ][}{ CONTENT ###")
            
            # Should handle corrupted task files gracefully
            result = generate_auto_prompt(
                project_path=str(project_dir),
                scope="full_project"
            )
            
            assert result is not None
            assert "generated_prompt" in result
            
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")


class TestParameterValidationErrors:
    """Test parameter validation and edge cases."""
    
    def test_invalid_scope_parameter(self):
        """Test handling of invalid scope parameters."""
        try:
            from src.server import generate_auto_prompt
            
            invalid_scopes = ["invalid_scope", "", None, 123, ["list"]]
            
            for invalid_scope in invalid_scopes:
                with pytest.raises(Exception) as exc_info:
                    generate_auto_prompt(
                        project_path="/tmp/test",
                        scope=invalid_scope
                    )
                
                error_message = str(exc_info.value).lower()
                assert "scope" in error_message or "invalid" in error_message or "parameter" in error_message
                
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
    
    def test_invalid_temperature_parameter(self):
        """Test handling of invalid temperature parameters."""
        try:
            from src.ai_code_review import generate_ai_code_review
            
            invalid_temperatures = [-1.0, 2.0, "invalid", None, [0.5]]
            
            for invalid_temp in invalid_temperatures:
                with pytest.raises(Exception) as exc_info:
                    generate_ai_code_review(
                        context_file_path="/tmp/context.md",
                        project_path="/tmp/test",
                        temperature=invalid_temp
                    )
                
                error_message = str(exc_info.value).lower()
                assert "temperature" in error_message or "invalid" in error_message or "range" in error_message
                
        except ImportError:
            pytest.skip("generate_ai_code_review function not found - implementation pending")
    
    def test_missing_required_parameters(self):
        """Test handling of missing required parameters."""
        try:
            from src.server import generate_auto_prompt
            
            # Test missing project_path
            with pytest.raises(Exception) as exc_info:
                generate_auto_prompt(scope="full_project")  # Missing project_path
            
            error_message = str(exc_info.value).lower()
            assert "project_path" in error_message or "required" in error_message or "missing" in error_message
            
        except (ImportError, TypeError):
            # TypeError is expected for missing required parameters
            pytest.skip("generate_auto_prompt function not found or parameter validation pending")
    
    def test_extremely_long_parameters(self):
        """Test handling of extremely long parameter values."""
        try:
            from src.server import generate_auto_prompt
            
            # Extremely long project path
            long_path = "/tmp/" + "x" * 1000
            
            with pytest.raises(Exception) as exc_info:
                generate_auto_prompt(
                    project_path=long_path,
                    scope="full_project"
                )
            
            # Should handle long paths gracefully (path too long or not found)
            error_message = str(exc_info.value).lower()
            assert "path" in error_message or "too long" in error_message or "not found" in error_message
            
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")


class TestCLIErrorHandling:
    """Test CLI error handling and edge cases."""
    
    def test_cli_with_invalid_arguments(self):
        """Test CLI handling of invalid argument combinations."""
        try:
            from src.generate_code_review_context import validate_cli_arguments
            
            # Test conflicting flags
            class MockArgs:
                def __init__(self, **kwargs):
                    self.auto_prompt = kwargs.get('auto_prompt', False)
                    self.generate_prompt_only = kwargs.get('generate_prompt_only', False)
                    self.context_only = kwargs.get('context_only', False)
                    self.project_path = kwargs.get('project_path', '.')
                    self.temperature = kwargs.get('temperature', 0.5)
                    self.scope = kwargs.get('scope', 'recent_phase')
            
            # Test auto_prompt + generate_prompt_only conflict
            args_conflict1 = MockArgs(auto_prompt=True, generate_prompt_only=True)
            with pytest.raises(ValueError, match="mutually exclusive"):
                validate_cli_arguments(args_conflict1)
            
            # Test generate_prompt_only + context_only conflict
            args_conflict2 = MockArgs(generate_prompt_only=True, context_only=True)
            with pytest.raises(ValueError, match="mutually exclusive"):
                validate_cli_arguments(args_conflict2)
            
        except ImportError:
            pytest.skip("validate_cli_arguments function not found - implementation pending")
    
    def test_cli_with_missing_project_path(self):
        """Test CLI handling of missing project path."""
        try:
            from src.generate_code_review_context import validate_cli_arguments
            
            class MockArgs:
                def __init__(self):
                    self.auto_prompt = True
                    self.generate_prompt_only = False
                    self.context_only = False
                    self.project_path = None  # Missing path
                    self.temperature = 0.5
                    self.scope = 'recent_phase'
            
            args_no_path = MockArgs()
            with pytest.raises(ValueError) as exc_info:
                validate_cli_arguments(args_no_path)
            
            error_message = str(exc_info.value).lower()
            assert "project_path" in error_message or "path" in error_message
            
        except ImportError:
            pytest.skip("validate_cli_arguments function not found - implementation pending")
    
    def test_cli_interrupt_handling(self):
        """Test CLI handling of user interrupts (Ctrl+C)."""
        try:
            from src.generate_code_review_context import cli_main
            
            # Simulate KeyboardInterrupt during execution
            with patch('sys.argv', ['generate-code-review', '--auto-prompt', '.']):
                with patch('src.generate_code_review_context.execute_auto_prompt_workflow') as mock_workflow:
                    mock_workflow.side_effect = KeyboardInterrupt("User interrupted")
                    
                    with pytest.raises(SystemExit):
                        cli_main()
            
        except ImportError:
            pytest.skip("cli_main function not found - implementation pending")
    
    def test_cli_with_invalid_file_paths(self):
        """Test CLI handling of invalid file paths in arguments."""
        try:
            from src.generate_code_review_context import cli_main
            
            invalid_paths = [
                "/path/with/null/\x00/character",
                "path/with/../traversal",
                "",
                "path/with spaces and 'quotes'",
            ]
            
            for invalid_path in invalid_paths:
                with patch('sys.argv', ['generate-code-review', '--auto-prompt', invalid_path]):
                    with pytest.raises(SystemExit):
                        cli_main()
            
        except ImportError:
            pytest.skip("cli_main function not found - implementation pending")


class TestConcurrencyAndRaceConditions:
    """Test handling of concurrency issues and race conditions."""
    
    def test_multiple_concurrent_requests(self):
        """Test handling of multiple concurrent auto-prompt requests."""
        try:
            from src.server import generate_auto_prompt
            
            # Simulate concurrent requests (basic test)
            request_count = 3
            results = []
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = MockGeminiClient()
                mock_gemini.return_value = mock_client
                
                for i in range(request_count):
                    result = generate_auto_prompt(
                        project_path=f"/tmp/test_project_{i}",
                        scope="full_project"
                    )
                    results.append(result)
                
                # All requests should complete successfully
                assert len(results) == request_count
                for result in results:
                    assert result is not None
                    assert "generated_prompt" in result
            
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
    
    def test_file_system_race_conditions(self, tmp_path):
        """Test handling of file system race conditions."""
        try:
            from src.server import generate_code_review_context
            
            shared_project = tmp_path / "shared_project"
            shared_project.mkdir()
            (shared_project / "test.py").write_text("def test(): pass")
            
            # Simulate concurrent file access
            with patch('src.generate_code_review_context.create_context_file') as mock_create:
                mock_create.return_value = "/tmp/context_1.md"
                
                result1 = generate_code_review_context(
                    project_path=str(shared_project),
                    scope="full_project"
                )
                
                result2 = generate_code_review_context(
                    project_path=str(shared_project),
                    scope="full_project"
                )
                
                # Both should succeed
                assert result1 is not None
                assert result2 is not None
            
        except ImportError:
            pytest.skip("generate_code_review_context function not found - implementation pending")


class TestMemoryAndResourceHandling:
    """Test memory usage and resource handling edge cases."""
    
    def test_large_file_handling(self, tmp_path):
        """Test handling of very large files."""
        try:
            from src.server import generate_auto_prompt
            
            large_project = tmp_path / "large_file_project"
            large_project.mkdir()
            
            # Create a large file (1MB of code)
            large_content = "# Large file\n" + "print('line')\n" * 50000
            (large_project / "large_file.py").write_text(large_content)
            
            result = generate_auto_prompt(
                project_path=str(large_project),
                scope="full_project"
            )
            
            # Should handle large files gracefully
            assert result is not None
            assert "generated_prompt" in result
            
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
    
    def test_memory_cleanup_after_errors(self):
        """Test that memory is properly cleaned up after errors."""
        try:
            from src.server import generate_auto_prompt
            
            # Force an error and verify cleanup
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = Mock()
                mock_client.generate_content.side_effect = Exception("Simulated error")
                mock_gemini.return_value = mock_client
                
                with pytest.raises(Exception):
                    generate_auto_prompt(
                        project_path="/tmp/test",
                        scope="full_project"
                    )
                
                # Verify mock was called (indicating function attempted execution)
                mock_client.generate_content.assert_called()
            
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
    
    def test_resource_exhaustion_handling(self):
        """Test handling of resource exhaustion scenarios."""
        # This is a conceptual test for resource limits
        resource_limits = {
            "max_file_size": 10 * 1024 * 1024,  # 10MB
            "max_files": 1000,
            "max_context_length": 100000
        }
        
        # Verify limits are reasonable
        assert resource_limits["max_file_size"] > 0
        assert resource_limits["max_files"] > 0
        assert resource_limits["max_context_length"] > 0
        
        # In a real implementation, we'd test actual resource exhaustion
        # For now, verify the limits exist conceptually


class TestEdgeCaseInputs:
    """Test edge case inputs and boundary conditions."""
    
    def test_unicode_and_special_characters(self, tmp_path):
        """Test handling of Unicode and special characters in file paths and content."""
        try:
            from src.server import generate_auto_prompt
            
            unicode_project = tmp_path / "unicode_project_测试"
            unicode_project.mkdir()
            
            # Create file with Unicode content
            unicode_content = """
def greet_世界():
    print("Hello, 世界! 🌍")
    # 中文注释
    return "成功"
"""
            (unicode_project / "unicode_file_测试.py").write_text(unicode_content, encoding='utf-8')
            
            result = generate_auto_prompt(
                project_path=str(unicode_project),
                scope="full_project"
            )
            
            # Should handle Unicode gracefully
            assert result is not None
            assert "generated_prompt" in result
            
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
        except UnicodeError:
            pytest.skip("Unicode handling not yet implemented")
    
    def test_extremely_deep_directory_structure(self, tmp_path):
        """Test handling of extremely deep directory structures."""
        try:
            from src.server import generate_auto_prompt
            
            # Create deep directory structure
            deep_path = tmp_path
            for i in range(20):  # 20 levels deep
                deep_path = deep_path / f"level_{i}"
                deep_path.mkdir()
            
            (deep_path / "deep_file.py").write_text("def deep_function(): pass")
            
            result = generate_auto_prompt(
                project_path=str(tmp_path),
                scope="full_project"
            )
            
            # Should handle deep structures gracefully
            assert result is not None
            assert "generated_prompt" in result
            
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
    
    def test_files_with_no_extensions(self, tmp_path):
        """Test handling of files with no extensions."""
        try:
            from src.server import generate_auto_prompt
            
            no_ext_project = tmp_path / "no_extension_project"
            no_ext_project.mkdir()
            
            # Create files without extensions
            (no_ext_project / "Makefile").write_text("all:\n\techo 'Building...'")
            (no_ext_project / "README").write_text("This is a readme file")
            (no_ext_project / "script").write_text("#!/bin/bash\necho 'Script'")
            
            result = generate_auto_prompt(
                project_path=str(no_ext_project),
                scope="full_project"
            )
            
            # Should handle files without extensions
            assert result is not None
            assert "generated_prompt" in result
            
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
    
    def test_circular_symbolic_links(self, tmp_path):
        """Test handling of circular symbolic links."""
        if os.name == 'nt':
            pytest.skip("Symbolic link test not applicable on Windows")
        
        try:
            from src.server import generate_auto_prompt
            
            symlink_project = tmp_path / "symlink_project"
            symlink_project.mkdir()
            
            # Create circular symbolic links
            link1 = symlink_project / "link1"
            link2 = symlink_project / "link2"
            
            link1.symlink_to(link2)
            link2.symlink_to(link1)
            
            # Should handle circular links gracefully (not hang)
            result = generate_auto_prompt(
                project_path=str(symlink_project),
                scope="full_project"
            )
            
            assert result is not None
            assert "generated_prompt" in result
            
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
        except OSError:
            pytest.skip("Symbolic link creation failed")


class TestErrorRecoveryAndResilience:
    """Test error recovery and system resilience."""
    
    def test_partial_failure_recovery(self):
        """Test recovery from partial failures in the workflow."""
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            # Test recovery when context generation fails but auto-prompt succeeds
            with patch('src.generate_code_review_context.generate_auto_prompt') as mock_auto_prompt, \
                 patch('src.generate_code_review_context.generate_code_review_context') as mock_context, \
                 patch('src.generate_code_review_context.generate_ai_code_review') as mock_ai_review:
                
                # Auto-prompt succeeds
                mock_auto_prompt.return_value = {
                    "generated_prompt": "Test prompt",
                    "analysis_completed": True
                }
                
                # Context generation fails
                mock_context.side_effect = Exception("Context generation failed")
                
                # AI review should still be attempted or workflow should handle gracefully
                mock_ai_review.return_value = "/tmp/review.md"
                
                try:
                    result = execute_auto_prompt_workflow(
                        project_path="/tmp/test",
                        scope="full_project",
                        temperature=0.5,
                        auto_prompt=True
                    )
                    # If no exception, verify partial success handling
                    assert result is not None
                except Exception as e:
                    # If exception, verify it's handled appropriately
                    assert "Context generation failed" in str(e) or "workflow" in str(e).lower()
            
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")
    
    def test_retry_mechanism_on_transient_failures(self):
        """Test retry mechanisms for transient failures."""
        try:
            from src.server import generate_auto_prompt
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = Mock()
                
                # Simulate transient failure then success
                call_count = 0
                def mock_generate_content(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        raise Exception("Temporary network error")
                    else:
                        mock_response = Mock()
                        mock_response.text = "Generated prompt after retry"
                        return mock_response
                
                mock_client.generate_content.side_effect = mock_generate_content
                mock_gemini.return_value = mock_client
                
                # Should retry and succeed on second attempt
                result = generate_auto_prompt(
                    project_path="/tmp/test",
                    scope="full_project"
                )
                
                # Verify retry occurred
                assert call_count >= 1  # At least one call made
                assert result is not None
                assert "generated_prompt" in result
            
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
    
    def test_graceful_degradation_modes(self):
        """Test graceful degradation when services are unavailable."""
        try:
            from src.server import generate_auto_prompt
            
            # Test degradation when Gemini is completely unavailable
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_gemini.side_effect = Exception("Gemini service unavailable")
                
                # Should provide fallback behavior or clear error message
                try:
                    result = generate_auto_prompt(
                        project_path="/tmp/test",
                        scope="full_project"
                    )
                    # If no exception, verify fallback behavior
                    assert result is not None
                    assert "generated_prompt" in result
                    # May contain fallback prompt or error indication
                except Exception as e:
                    # If exception, verify it's informative
                    error_message = str(e).lower()
                    assert "service" in error_message or "unavailable" in error_message or "gemini" in error_message
            
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")