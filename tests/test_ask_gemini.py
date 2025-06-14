#!/usr/bin/env python3
"""
Tests for the ask_gemini MCP tool.

This module tests the new ask_gemini tool which combines context generation
with direct Gemini API calls.
"""

import os
import sys
from unittest.mock import MagicMock, call, patch

import pytest

# Import from the installed package
try:
    from src.file_context_types import FileContentData, FileContextResult
except ImportError:
    # Fall back to direct imports if package not installed
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from src.file_context_types import FileContentData, FileContextResult


class TestAskGeminiTool:
    """Test suite for the ask_gemini MCP tool."""
    
    def _get_ask_gemini_func(self):
        """Helper to get the actual ask_gemini function, handling FunctionTool wrapper."""
        from src.server import ask_gemini
        
        # If it's a FunctionTool object, extract the actual function
        if hasattr(ask_gemini, 'func') and callable(ask_gemini.func):
            return ask_gemini.func
        elif callable(ask_gemini):
            return ask_gemini
        else:
            # This shouldn't happen, but handle it gracefully
            raise TypeError(f"ask_gemini is not callable: {type(ask_gemini)}")

    def test_ask_gemini_with_user_instructions_only(self):
        """Test ask_gemini with just user instructions (no files)."""
        # Get the actual function to test
        test_func = self._get_ask_gemini_func()
            
        # Mock the dependencies
        mock_config = MagicMock()
        mock_result = FileContextResult(
            content="Generated context with user instructions",
            total_tokens=100,
            included_files=[],
            excluded_files=[],
            configuration_content="",
            meta_prompt=None,
        )

        with patch(
            "src.server.FileContextConfig", return_value=mock_config
        ) as mock_config_class:
            with patch(
                "src.server.generate_file_context_data", return_value=mock_result
            ) as mock_generate:
                with patch(
                    "src.server.send_to_gemini_for_review",
                    return_value="AI response text",
                ) as mock_gemini:
                    # Call the function
                    result = test_func(
                        user_instructions="Review this code for security issues",
                        text_output=True,
                    )

                    # Verify the result
                    assert result == "AI response text"

                    # Verify FileContextConfig was called correctly
                    mock_config_class.assert_called_once()
                    config_call = mock_config_class.call_args
                    assert config_call.kwargs["file_selections"] == []
                    assert (
                        config_call.kwargs["user_instructions"]
                        == "Review this code for security issues"
                    )
                    assert config_call.kwargs["include_claude_memory"] is True
                    assert config_call.kwargs["temperature"] == 0.5

                    # Verify generate_file_context_data was called
                    mock_generate.assert_called_once_with(mock_config)

                    # Verify send_to_gemini_for_review was called
                    mock_gemini.assert_called_once()
                    gemini_call = mock_gemini.call_args
                    assert (
                        gemini_call.kwargs["context_content"]
                        == "Generated context with user instructions"
                    )
                    assert gemini_call.kwargs["return_text"] is True

    def test_ask_gemini_with_file_selections(self):
        """Test ask_gemini with file selections."""
        # Get the actual function to test
        test_func = self._get_ask_gemini_func()
        
        file_selections = [
            {"path": "src/main.py", "line_ranges": [(10, 50)]},
            {"path": "src/utils.py", "include_full": True},
        ]

        mock_config = MagicMock()
        mock_result = FileContextResult(
            content="Context from selected files",
            total_tokens=500,
            included_files=[
                FileContentData(
                    path="src/main.py",
                    absolute_path="/path/to/project/src/main.py",
                    content="file content",
                    included_lines=40,
                    total_lines=100,
                    line_ranges=[(10, 50)],
                    estimated_tokens=100,
                )
            ],
            excluded_files=[],
            configuration_content="",
            meta_prompt=None,
        )

        with patch(
            "src.server.FileContextConfig", return_value=mock_config
        ) as mock_config_class:
            with patch(
                "src.server.generate_file_context_data", return_value=mock_result
            ) as mock_generate:
                with patch(
                    "src.server.send_to_gemini_for_review",
                    return_value="AI analysis of files",
                ) as mock_gemini:
                    # Call the function
                    result = test_func(
                        user_instructions="Analyze these files",
                        file_selections=file_selections,
                        project_path="/path/to/project",
                        temperature=0.7,
                    )

                    # Verify the result
                    assert result == "AI analysis of files"

                    # Verify FileSelection objects were created correctly
                    mock_config_class.assert_called_once()
                    config_call = mock_config_class.call_args
                    assert len(config_call.kwargs["file_selections"]) == 2
                    assert config_call.kwargs["project_path"] == "/path/to/project"
                    assert config_call.kwargs["temperature"] == 0.7

    def test_ask_gemini_invalid_file_selection(self):
        """Test ask_gemini with invalid file selection (missing path)."""
        # Get the actual function to test
        test_func = self._get_ask_gemini_func()
        
        file_selections = [{"line_ranges": [(10, 50)]}]  # Missing 'path' field

        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            test_func(user_instructions="Test", file_selections=file_selections)

        # Check the error message
        assert "path" in str(exc_info.value).lower()

    def test_ask_gemini_with_output_file(self):
        """Test ask_gemini with text_output=False (save to file)."""
        # Get the actual function to test
        test_func = self._get_ask_gemini_func()
        
        mock_config = MagicMock()
        mock_result = FileContextResult(
            content="Context content",
            total_tokens=100,
            included_files=[],
            excluded_files=[],
            configuration_content="",
            meta_prompt=None,
        )

        with patch("src.server.FileContextConfig", return_value=mock_config):
            with patch(
                "src.server.generate_file_context_data", return_value=mock_result
            ):
                with patch(
                    "src.server.send_to_gemini_for_review", return_value="output.md"
                ) as mock_gemini:
                    # Call the function
                    result = test_func(
                        user_instructions="Generate review", text_output=False
                    )

                    # Verify the result
                    assert result == "output.md"

                    # Verify send_to_gemini_for_review was called with correct params
                    mock_gemini.assert_called_once()
                    gemini_call = mock_gemini.call_args
                    assert gemini_call.kwargs["return_text"] is False
                    # Should not have output_path argument
                    assert "output_path" not in gemini_call.kwargs

    def test_ask_gemini_gemini_failure(self):
        """Test ask_gemini when Gemini API fails."""
        # Get the actual function to test
        test_func = self._get_ask_gemini_func()
        
        mock_config = MagicMock()
        mock_result = FileContextResult(
            content="Context content",
            total_tokens=100,
            included_files=[],
            excluded_files=[],
            configuration_content="",
            meta_prompt=None,
        )

        with patch("src.server.FileContextConfig", return_value=mock_config):
            with patch(
                "src.server.generate_file_context_data", return_value=mock_result
            ):
                with patch("src.server.send_to_gemini_for_review", return_value=None):
                    # Should raise RuntimeError
                    with pytest.raises(RuntimeError) as exc_info:
                        test_func(user_instructions="Test")

                    assert "Failed to get a response from Gemini" in str(exc_info.value)

    def test_ask_gemini_unexpected_exception(self):
        """Test ask_gemini handling of unexpected exceptions."""
        # Get the actual function to test
        test_func = self._get_ask_gemini_func()
        
        # Should re-raise the exception
        with patch(
            "src.server.FileContextConfig", side_effect=Exception("Unexpected error")
        ):
            with pytest.raises(Exception) as exc_info:
                test_func(user_instructions="Test")

            assert str(exc_info.value) == "Unexpected error"

    def test_ask_gemini_with_all_parameters(self):
        """Test ask_gemini with all parameters specified."""
        # Get the actual function to test
        test_func = self._get_ask_gemini_func()
        
        file_selections = [{"path": "test.py"}]

        mock_config = MagicMock()
        mock_result = FileContextResult(
            content="Full context",
            total_tokens=1000,
            included_files=[],
            excluded_files=[],
            configuration_content="Config content",
            meta_prompt="Generated meta prompt",
        )

        with patch(
            "src.server.FileContextConfig", return_value=mock_config
        ) as mock_config_class:
            with patch(
                "src.server.generate_file_context_data", return_value=mock_result
            ):
                with patch(
                    "src.server.send_to_gemini_for_review",
                    return_value="Complete response",
                ) as mock_gemini:
                    # Call the function
                    result = test_func(
                        user_instructions="Custom instructions",
                        file_selections=file_selections,
                        project_path="/project",
                        include_claude_memory=False,
                        include_cursor_rules=True,
                        auto_meta_prompt=False,
                        temperature=0.3,
                        model="gemini-2.0-flash-exp",
                        thinking_budget=5000,
                        text_output=True,
                    )

                    # Verify the result
                    assert result == "Complete response"

                    # Verify configuration
                    config_call = mock_config_class.call_args
                    assert config_call.kwargs["include_claude_memory"] is False
                    assert config_call.kwargs["include_cursor_rules"] is True
                    assert config_call.kwargs["auto_meta_prompt"] is False
                    assert config_call.kwargs["temperature"] == 0.3

                    # Verify Gemini call
                    gemini_call = mock_gemini.call_args
                    assert gemini_call.kwargs["model"] == "gemini-2.0-flash-exp"
                    assert gemini_call.kwargs["thinking_budget"] == 5000
