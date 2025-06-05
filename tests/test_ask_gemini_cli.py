#!/usr/bin/env python3
"""
Tests for the ask_gemini CLI commands.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys

from src.ask_gemini_cli import parse_file_selection, main, direct_main


class TestParseFileSelection:
    """Test the file selection parsing function."""
    
    def test_simple_path(self):
        """Test parsing a simple file path."""
        result = parse_file_selection("src/main.py")
        assert result == {"path": "src/main.py"}
    
    def test_single_line_range(self):
        """Test parsing a file with single line range."""
        result = parse_file_selection("src/utils.py:10-20")
        assert result == {
            "path": "src/utils.py",
            "line_ranges": [(10, 20)]
        }
    
    def test_multiple_line_ranges(self):
        """Test parsing a file with multiple line ranges."""
        result = parse_file_selection("src/module.py:10-20,30-40,50-60")
        assert result == {
            "path": "src/module.py", 
            "line_ranges": [(10, 20), (30, 40), (50, 60)]
        }
    
    def test_single_line_number(self):
        """Test parsing a single line number."""
        result = parse_file_selection("test.py:42")
        assert result == {
            "path": "test.py",
            "line_ranges": [(42, 42)]
        }
    
    def test_mixed_ranges_and_lines(self):
        """Test parsing mixed ranges and single lines."""
        result = parse_file_selection("file.py:10-20,25,30-35")
        assert result == {
            "path": "file.py",
            "line_ranges": [(10, 20), (25, 25), (30, 35)]
        }
    
    def test_invalid_ranges_skipped(self):
        """Test that invalid ranges are skipped with warning."""
        with patch('builtins.print') as mock_print:
            result = parse_file_selection("file.py:10-20,invalid,30-40")
            assert result == {
                "path": "file.py",
                "line_ranges": [(10, 20), (30, 40)]
            }
            mock_print.assert_called_with("Warning: Invalid line number 'invalid', skipping")


class TestAskGeminiCLI:
    """Test the main ask-gemini CLI command."""
    
    def test_simple_question(self):
        """Test asking a simple question."""
        test_args = ["ask-gemini", "What is Python?"]
        
        with patch('sys.argv', test_args):
            with patch('src.ask_gemini_cli.require_api_key'):
                with patch('src.ask_gemini_cli.ask_gemini') as mock_ask:
                    mock_ask.return_value = "Python is a programming language."
                    
                    with patch('builtins.print') as mock_print:
                        exit_code = main()
                    
                    assert exit_code == 0
                    mock_ask.assert_called_once_with(
                        question="What is Python?",
                        file_selections=None,
                        project_path=None,
                        user_instructions=None,
                        temperature=0.5,
                        include_claude_memory=True,
                        include_cursor_rules=False,
                        text_output=True,
                        output_path=None,
                        model=None
                    )
                    mock_print.assert_called_with("Python is a programming language.")
    
    def test_question_with_files(self):
        """Test asking with file context."""
        test_args = [
            "ask-gemini",
            "How can I optimize this?",
            "--files", "src/slow.py:45-90", "src/utils.py"
        ]
        
        with patch('sys.argv', test_args):
            with patch('src.ask_gemini_cli.require_api_key'):
                with patch('src.ask_gemini_cli.ask_gemini') as mock_ask:
                    mock_ask.return_value = "Here are optimization suggestions."
                    
                    exit_code = main()
                    
                    assert exit_code == 0
                    call_args = mock_ask.call_args[1]
                    assert call_args['file_selections'] == [
                        {"path": "src/slow.py", "line_ranges": [(45, 90)]},
                        {"path": "src/utils.py"}
                    ]
    
    def test_all_parameters(self):
        """Test with all CLI parameters."""
        test_args = [
            "ask-gemini",
            "Review this code",
            "--files", "main.py:10-20",
            "--project-path", "/project",
            "--instructions", "Focus on security",
            "--temperature", "0.7",
            "--model", "gemini-2.0-flash",
            "--output", "review.md",
            "--include-cursor-rules"
        ]
        
        with patch('sys.argv', test_args):
            with patch('src.ask_gemini_cli.require_api_key'):
                with patch('src.ask_gemini_cli.ask_gemini') as mock_ask:
                    mock_ask.return_value = "Saved to review.md"
                    
                    exit_code = main()
                    
                    assert exit_code == 0
                    call_args = mock_ask.call_args[1]
                    assert call_args['question'] == "Review this code"
                    assert call_args['project_path'] == "/project"
                    assert call_args['user_instructions'] == "Focus on security"
                    assert call_args['temperature'] == 0.7
                    assert call_args['model'] == "gemini-2.0-flash"
                    assert call_args['text_output'] is False
                    assert call_args['output_path'] == "review.md"
                    assert call_args['include_cursor_rules'] is True
    
    def test_error_handling(self):
        """Test error handling."""
        test_args = ["ask-gemini", "Test question"]
        
        with patch('sys.argv', test_args):
            with patch('src.ask_gemini_cli.require_api_key'):
                with patch('src.ask_gemini_cli.ask_gemini') as mock_ask:
                    mock_ask.side_effect = Exception("API error")
                    
                    with patch('builtins.print') as mock_print:
                        exit_code = main()
                    
                    assert exit_code == 1
                    mock_print.assert_called_with("Error: API error", file=sys.stderr)


class TestAskGeminiDirectCLI:
    """Test the ask-gemini-direct CLI command."""
    
    def test_simple_direct_question(self):
        """Test direct question without context."""
        test_args = ["ask-gemini-direct", "What is recursion?"]
        
        with patch('sys.argv', test_args):
            with patch('src.ask_gemini_cli.require_api_key'):
                with patch('src.ask_gemini_cli.ask_gemini_direct') as mock_direct:
                    mock_direct.return_value = "Recursion is..."
                    
                    with patch('builtins.print') as mock_print:
                        exit_code = direct_main()
                    
                    assert exit_code == 0
                    mock_direct.assert_called_once_with(
                        question="What is recursion?",
                        context=None,
                        temperature=0.5,
                        model=None
                    )
                    mock_print.assert_called_with("Recursion is...")
    
    def test_direct_with_context(self):
        """Test direct question with context."""
        test_args = [
            "ask-gemini-direct",
            "What does this do?",
            "--context", "def add(a, b): return a + b"
        ]
        
        with patch('sys.argv', test_args):
            with patch('src.ask_gemini_cli.require_api_key'):
                with patch('src.ask_gemini_cli.ask_gemini_direct') as mock_direct:
                    mock_direct.return_value = "This is an addition function."
                    
                    exit_code = direct_main()
                    
                    assert exit_code == 0
                    call_args = mock_direct.call_args[1]
                    assert call_args['context'] == "def add(a, b): return a + b"
    
    def test_direct_with_all_params(self):
        """Test direct with all parameters."""
        test_args = [
            "ask-gemini-direct",
            "Explain this",
            "--context", "Complex code here",
            "--temperature", "0.3",
            "--model", "gemini-1.5-pro"
        ]
        
        with patch('sys.argv', test_args):
            with patch('src.ask_gemini_cli.require_api_key'):
                with patch('src.ask_gemini_cli.ask_gemini_direct') as mock_direct:
                    mock_direct.return_value = "Explanation..."
                    
                    exit_code = direct_main()
                    
                    assert exit_code == 0
                    call_args = mock_direct.call_args[1]
                    assert call_args['temperature'] == 0.3
                    assert call_args['model'] == "gemini-1.5-pro"