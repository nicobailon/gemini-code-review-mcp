#!/usr/bin/env python3
"""
Tests for the generate-file-context CLI command.
"""

import pytest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
import subprocess

# Import from the installed package
try:
    from src.cli_generate_file_context import main as cli_main, create_parser
except ImportError:
    # Fall back to direct imports if package not installed
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from cli_generate_file_context import main as cli_main, create_parser


class TestGenerateFileContextCLI:
    """Test suite for the generate-file-context CLI command."""
    
    def test_parser_creation(self):
        """Test that the argument parser is created correctly."""
        parser = create_parser()
        
        # Check program name
        assert parser.prog == "generate-file-context"
        
        # Parse test arguments
        args = parser.parse_args(["-f", "test.py", "-o", "output.md"])
        assert args.file_selections == ["test.py"]
        assert args.output_path == "output.md"
    
    def test_cli_with_single_file(self, tmp_path):
        """Test CLI with a single file selection."""
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    print('Hello')")
        
        # Create output file path
        output_file = tmp_path / "context.md"
        
        # Mock sys.argv
        test_args = [
            "generate-file-context",
            "-f", str(test_file),
            "-o", str(output_file),
            "--project-path", str(tmp_path)
        ]
        
        with patch.object(sys, 'argv', test_args):
            # Run the CLI
            try:
                cli_main()
            except SystemExit as e:
                # CLI should exit with 0 on success
                assert e.code == 0
        
        # Verify output file was created
        assert output_file.exists()
        content = output_file.read_text()
        assert "def hello():" in content
        assert "print('Hello')" in content
    
    def test_cli_with_line_ranges(self, tmp_path):
        """Test CLI with line range selection."""
        # Create test file with multiple lines
        test_file = tmp_path / "test.py"
        test_file.write_text("\n".join([
            "line1",
            "line2", 
            "line3",
            "line4",
            "line5"
        ]))
        
        # Mock the file context generator to verify correct parsing
        mock_config = MagicMock()
        mock_result = MagicMock()
        mock_result.content = "Mocked content"
        mock_result.included_files = []
        mock_result.excluded_files = []
        mock_result.total_tokens = 100
        
        test_args = [
            "generate-file-context",
            "-f", f"{test_file}:2-4",
            "--no-claude-memory"
        ]
        
        with patch.object(sys, 'argv', test_args):
            with patch('src.cli_generate_file_context.FileContextConfig', return_value=mock_config) as mock_config_class:
                with patch('src.cli_generate_file_context.generate_file_context_data', return_value=mock_result):
                    with patch('builtins.print'):  # Suppress output
                        try:
                            cli_main()
                        except SystemExit:
                            pass
                
                # Verify the file selection was parsed correctly
                config_call = mock_config_class.call_args
                file_selections = config_call.kwargs['file_selections']
                assert len(file_selections) == 1
                assert file_selections[0]["path"] == str(test_file)
                assert file_selections[0]["line_ranges"] == [(2, 4)]
    
    def test_cli_error_invalid_file_selection(self):
        """Test CLI with invalid file selection format."""
        test_args = [
            "generate-file-context",
            "-f", "test.py:invalid-range"
        ]
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stderr'):  # Suppress error output
                with pytest.raises(SystemExit) as exc_info:
                    cli_main()
                
                # Should exit with error code
                assert exc_info.value.code == 1
    
    def test_cli_with_custom_instructions(self, tmp_path):
        """Test CLI with custom user instructions."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# Test file")
        
        mock_config = MagicMock()
        mock_result = MagicMock()
        mock_result.content = "Context with instructions"
        mock_result.included_files = []
        mock_result.excluded_files = []
        mock_result.total_tokens = 50
        
        test_args = [
            "generate-file-context",
            "-f", str(test_file),
            "--user-instructions", "Focus on error handling",
            "--project-path", str(tmp_path)
        ]
        
        with patch.object(sys, 'argv', test_args):
            with patch('src.cli_generate_file_context.FileContextConfig', return_value=mock_config) as mock_config_class:
                with patch('src.cli_generate_file_context.generate_file_context_data', return_value=mock_result):
                    with patch('builtins.print'):  # Suppress output
                        try:
                            cli_main()
                        except SystemExit:
                            pass
                
                # Verify user instructions were passed
                config_call = mock_config_class.call_args
                assert config_call.kwargs['user_instructions'] == "Focus on error handling"
    
    def test_cli_stdout_output(self, tmp_path, capsys):
        """Test CLI output to stdout when no output file specified."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")
        
        test_args = [
            "generate-file-context",
            "-f", str(test_file),
            "--project-path", str(tmp_path)
        ]
        
        with patch.object(sys, 'argv', test_args):
            try:
                cli_main()
            except SystemExit:
                pass
        
        # Check stdout contains the expected output
        captured = capsys.readouterr()
        assert "--- Generated Context ---" in captured.out
        assert "print('test')" in captured.out
        assert "--- End Context ---" in captured.out