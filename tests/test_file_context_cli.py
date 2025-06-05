#!/usr/bin/env python3
"""
Tests for the generate-file-context CLI command.
"""

from unittest.mock import patch, MagicMock
import sys

from src.file_context_cli import parse_file_argument, main
from src.file_context_types import FileContextResult, FileContentData


class TestParseFileArgument:
    """Test file argument parsing."""
    
    def test_simple_path(self):
        """Test parsing a simple file path."""
        result = parse_file_argument("src/main.py")
        assert result == {"path": "src/main.py"}
    
    def test_single_range(self):
        """Test parsing file with single line range."""
        result = parse_file_argument("utils.py:10-20")
        assert result == {
            "path": "utils.py",
            "line_ranges": [(10, 20)]
        }
    
    def test_multiple_ranges(self):
        """Test parsing file with multiple ranges."""
        result = parse_file_argument("app.py:5-10,20-30,40-50")
        assert result == {
            "path": "app.py",
            "line_ranges": [(5, 10), (20, 30), (40, 50)]
        }
    
    def test_single_lines(self):
        """Test parsing single line numbers."""
        result = parse_file_argument("test.py:15,25,35")
        assert result == {
            "path": "test.py",
            "line_ranges": [(15, 15), (25, 25), (35, 35)]
        }
    
    def test_mixed_ranges_and_lines(self):
        """Test parsing mixed ranges and single lines."""
        result = parse_file_argument("code.py:1-5,10,15-20")
        assert result == {
            "path": "code.py",
            "line_ranges": [(1, 5), (10, 10), (15, 20)]
        }
    
    def test_invalid_range_order(self):
        """Test invalid range where start > end."""
        with patch('builtins.print') as mock_print:
            result = parse_file_argument("file.py:20-10")
            assert result == {"path": "file.py"}  # No line_ranges key when empty
            mock_print.assert_called_with("Warning: Invalid range 20-10, start > end")
    
    def test_invalid_range_format(self):
        """Test invalid range format."""
        with patch('builtins.print') as mock_print:
            result = parse_file_argument("file.py:10-20,abc,30-40")
            assert result == {
                "path": "file.py",
                "line_ranges": [(10, 20), (30, 40)]
            }
            mock_print.assert_called_with("Warning: Invalid line number 'abc', skipping")


class TestGenerateFileContextCLI:
    """Test the generate-file-context CLI command."""
    
    def test_basic_file_context(self):
        """Test basic file context generation."""
        test_args = ["generate-file-context", "main.py", "utils.py"]
        
        mock_file_data = FileContentData(
            path="main.py",
            absolute_path="/project/main.py",
            content="# Main file",
            line_ranges=None,
            included_lines=1,
            total_lines=1,
            estimated_tokens=5
        )
        
        mock_result = FileContextResult(
            content="# File Context\nFile: main.py\n# Main file",
            total_tokens=10,
            included_files=[mock_file_data],
            excluded_files=[],
            configuration_content="",
            meta_prompt=None
        )
        
        with patch('sys.argv', test_args):
            with patch('src.file_context_cli.load_api_key') as mock_api:
                with patch('src.file_context_cli.generate_file_context_data') as mock_gen:
                    with patch('src.file_context_cli.save_file_context') as mock_save:
                        mock_api.return_value = "test-key"
                        mock_gen.return_value = mock_result
                        mock_save.return_value = "file-context-20240101-120000.md"
                        
                        with patch('builtins.print') as mock_print:
                            exit_code = main()
                        
                        assert exit_code == 0
                        # Verify configuration
                        config = mock_gen.call_args[0][0]
                        assert len(config.file_selections) == 2
                        assert config.file_selections[0]["path"] == "main.py"
                        assert config.file_selections[1]["path"] == "utils.py"
                        
                        # Verify output messages
                        print_calls = [call[0][0] for call in mock_print.call_args_list]
                        assert any("✅ File context generated successfully!" in call for call in print_calls)
    
    def test_file_with_line_ranges(self):
        """Test file context with line ranges."""
        test_args = [
            "generate-file-context",
            "auth.py:50-100",
            "db.py:20-40,60-80"
        ]
        
        with patch('sys.argv', test_args):
            with patch('src.file_context_cli.load_api_key') as mock_api:
                with patch('src.file_context_cli.generate_file_context_data') as mock_gen:
                    with patch('src.file_context_cli.save_file_context') as mock_save:
                        mock_api.return_value = None  # No API key
                        mock_gen.return_value = MagicMock(
                            content="test",
                            total_tokens=100,
                            included_files=[],
                            excluded_files=[],
                            meta_prompt=None
                        )
                        mock_save.return_value = "output.md"
                        
                        exit_code = main()
                        
                        assert exit_code == 0
                        config = mock_gen.call_args[0][0]
                        assert config.file_selections[0]["path"] == "auth.py"
                        assert config.file_selections[0]["line_ranges"] == [(50, 100)]
                        assert config.file_selections[1]["path"] == "db.py"
                        assert config.file_selections[1]["line_ranges"] == [(20, 40), (60, 80)]
    
    def test_stdout_output(self):
        """Test output to stdout."""
        test_args = ["generate-file-context", "test.py", "--stdout"]
        
        mock_result = MagicMock(
            content="File context content here",
            included_files=[],
            excluded_files=[]
        )
        
        with patch('sys.argv', test_args):
            with patch('src.file_context_cli.load_api_key') as mock_api:
                with patch('src.file_context_cli.generate_file_context_data') as mock_gen:
                    mock_api.return_value = None
                    mock_gen.return_value = mock_result
                    
                    with patch('builtins.print') as mock_print:
                        exit_code = main()
                    
                    assert exit_code == 0
                    mock_print.assert_called_with("File context content here")
    
    def test_all_options(self):
        """Test with all CLI options."""
        test_args = [
            "generate-file-context",
            "src/core.py:1-50",
            "--project-path", "/project",
            "--instructions", "Review for security",
            "--output", "context.md",
            "--include-cursor-rules",
            "--no-claude-memory",
            "--no-meta-prompt",
            "--temperature", "0.7",
            "--token-limit", "100000",
            "--model", "gemini-2.0-flash"
        ]
        
        with patch('sys.argv', test_args):
            with patch('src.file_context_cli.load_api_key'):
                with patch('src.file_context_cli.generate_file_context_data') as mock_gen:
                    with patch('src.file_context_cli.save_file_context') as mock_save:
                        mock_gen.return_value = MagicMock(
                            content="test",
                            total_tokens=50,
                            included_files=[],
                            excluded_files=[],
                            meta_prompt=None
                        )
                        mock_save.return_value = "context.md"
                        
                        exit_code = main()
                        
                        assert exit_code == 0
                        config = mock_gen.call_args[0][0]
                        assert config.project_path == "/project"
                        assert config.user_instructions == "Review for security"
                        assert config.include_cursor_rules is True
                        assert config.include_claude_memory is False
                        assert config.auto_meta_prompt is False
                        assert config.temperature == 0.7
                        assert config.token_limit == 100000
                        assert config.model == "gemini-2.0-flash"
                        
                        # Verify save was called with correct args
                        mock_save.assert_called_once()
                        assert mock_save.call_args[0][1] == "context.md"
    
    def test_excluded_files_reporting(self):
        """Test reporting of excluded files."""
        test_args = ["generate-file-context", "big_file.py"]
        
        mock_result = MagicMock(
            content="context",
            total_tokens=1000,
            included_files=[],
            excluded_files=[
                ("file1.py", "File not found"),
                ("file2.py", "Token limit exceeded"),
                ("file3.py", "Permission denied"),
                ("file4.py", "Invalid path"),
                ("file5.py", "Too large"),
                ("file6.py", "Binary file"),
            ],
            meta_prompt=None
        )
        
        with patch('sys.argv', test_args):
            with patch('src.file_context_cli.load_api_key'):
                with patch('src.file_context_cli.generate_file_context_data') as mock_gen:
                    with patch('src.file_context_cli.save_file_context') as mock_save:
                        mock_gen.return_value = mock_result
                        mock_save.return_value = "output.md"
                        
                        with patch('builtins.print') as mock_print:
                            exit_code = main()
                        
                        assert exit_code == 0
                        print_calls = [call[0][0] for call in mock_print.call_args_list]
                        
                        # Check that excluded files are reported
                        assert any("Excluded 6 files:" in call for call in print_calls)
                        # Only first 5 should be shown
                        assert any("file1.py: File not found" in call for call in print_calls)
                        assert any("file5.py: Too large" in call for call in print_calls)
                        assert any("... and 1 more" in call for call in print_calls)
                        # file6.py should not be shown (beyond limit of 5)
                        assert not any("file6.py" in call for call in print_calls)
    
    def test_error_handling(self):
        """Test error handling."""
        test_args = ["generate-file-context", "test.py"]
        
        with patch('sys.argv', test_args):
            with patch('src.file_context_cli.load_api_key'):
                with patch('src.file_context_cli.generate_file_context_data') as mock_gen:
                    mock_gen.side_effect = Exception("Generation failed")
                    
                    with patch('builtins.print') as mock_print:
                        exit_code = main()
                    
                    assert exit_code == 1
                    mock_print.assert_called_with("Error: Generation failed", file=sys.stderr)