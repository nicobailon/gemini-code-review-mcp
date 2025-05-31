"""
Test suite for CLI auto-prompt generation functionality.

Following TDD Protocol: Writing tests first to define expected CLI behavior.
Tests specify that CLI should output to file by default with streaming option.
"""

import pytest
from unittest.mock import patch, Mock, AsyncMock, mock_open
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime
import asyncio


class TestAutoPromptCLIInterface:
    """Test CLI interface for auto-prompt generation."""
    
    @pytest.mark.asyncio
    async def test_cli_auto_prompt_file_output_default(self):
        """Test CLI generates auto-prompt to file by default in current directory."""
        with patch('src.auto_prompt_generator._get_generate_meta_prompt') as mock_get_func:
            # Mock the function that gets returned
            async def mock_generate_meta_prompt(*args, **kwargs):
                return {
                    "generated_prompt": "Generated meta-prompt for code review",
                    "template_used": "default",
                    "configuration_included": True,
                    "analysis_completed": True,
                    "context_analyzed": 1500
                }
            
            mock_get_func.return_value = mock_generate_meta_prompt
            
            # Import and test CLI function
            from src.auto_prompt_generator import cli_generate_meta_prompt
            
            with tempfile.TemporaryDirectory() as temp_dir:
                context_file = Path(temp_dir) / "context.md"
                context_file.write_text("Test context content")
                
                # Change to temp directory to test default current directory behavior
                original_cwd = os.getcwd()
                try:
                    os.chdir(temp_dir)
                    
                    # Test file output (default behavior - should save in current directory)
                    result = await cli_generate_meta_prompt(
                        context_file_path=str(context_file)
                        # No output_dir specified - should default to current directory
                    )
                    
                    # Should return file path, not stream content
                    assert result["status"] == "success"
                    assert "output_file" in result
                    assert result["output_file"].endswith(".md")
                    
                    # File should be in current directory (temp_dir)
                    output_file_path = Path(result["output_file"])
                    assert output_file_path.exists()
                    assert str(output_file_path.parent.resolve()) == str(Path(temp_dir).resolve())
                    
                    # Verify file content format
                    with open(result["output_file"], 'r') as f:
                        content = f.read()
                    assert "# Meta-Prompt for AI Code Review" in content
                    assert "Generated meta-prompt for code review" in content
                    
                finally:
                    os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_cli_auto_prompt_stream_output_flag(self):
        """Test CLI streams output directly with --stream flag."""
        with patch('src.auto_prompt_generator._get_generate_meta_prompt') as mock_get_func:
            # Mock the function that gets returned
            async def mock_generate_meta_prompt(*args, **kwargs):
                return {
                    "generated_prompt": "Streamed meta-prompt content",
                    "template_used": "environment",
                    "configuration_included": False,
                    "analysis_completed": True,
                    "context_analyzed": 800
                }
            
            mock_get_func.return_value = mock_generate_meta_prompt
            
            from src.auto_prompt_generator import cli_generate_meta_prompt
            
            # Test streaming output (--stream flag)
            result = await cli_generate_meta_prompt(
                context_content="Direct context content",
                stream_output=True
            )
            
            # Should return content directly, not file path
            assert result["status"] == "success"
            assert "streamed_content" in result
            assert "output_file" not in result
            assert result["streamed_content"] == "Streamed meta-prompt content"
    
    @pytest.mark.asyncio
    async def test_cli_auto_prompt_custom_output_dir(self):
        """Test CLI respects --output-dir flag to override default directory."""
        with patch('src.auto_prompt_generator._get_generate_meta_prompt') as mock_get_func:
            # Mock the function that gets returned
            async def mock_generate_meta_prompt(*args, **kwargs):
                return {
                    "generated_prompt": "Generated meta-prompt for custom directory",
                    "template_used": "default",
                    "configuration_included": True,
                    "analysis_completed": True,
                    "context_analyzed": 1200
                }
            
            mock_get_func.return_value = mock_generate_meta_prompt
            
            from src.auto_prompt_generator import cli_generate_meta_prompt
            
            with tempfile.TemporaryDirectory() as temp_dir:
                context_file = Path(temp_dir) / "context.md"
                context_file.write_text("Test context content")
                
                # Create a custom output directory
                output_dir = Path(temp_dir) / "custom_output"
                output_dir.mkdir()
                
                # Test custom output directory
                result = await cli_generate_meta_prompt(
                    context_file_path=str(context_file),
                    output_dir=str(output_dir)
                )
                
                # Should return file path in custom directory
                assert result["status"] == "success"
                assert "output_file" in result
                assert result["output_file"].endswith(".md")
                
                # File should be in custom output directory
                output_file_path = Path(result["output_file"])
                assert output_file_path.exists()
                assert str(output_file_path.parent.resolve()) == str(output_dir.resolve())
                
                # Verify file content format
                with open(result["output_file"], 'r') as f:
                    content = f.read()
                assert "# Meta-Prompt for AI Code Review" in content
                assert "Generated meta-prompt for custom directory" in content
    
    def test_cli_argument_parsing_file_output(self):
        """Test CLI argument parsing for file output mode."""
        from src.auto_prompt_generator import parse_cli_arguments
        
        # Test default file output
        args = parse_cli_arguments([
            "--context-file", "context.md",
            "--output-dir", "/tmp/output"
        ])
        
        assert args.context_file == "context.md"
        assert args.output_dir == "/tmp/output"
        assert args.stream is False  # Default behavior
    
    def test_cli_argument_parsing_stream_output(self):
        """Test CLI argument parsing for stream output mode."""
        from src.auto_prompt_generator import parse_cli_arguments
        
        # Test streaming output
        args = parse_cli_arguments([
            "--context-content", "Direct content",
            "--stream"
        ])
        
        assert args.context_content == "Direct content"
        assert args.stream is True
        assert args.output_dir is None  # Not needed for streaming
    
    @pytest.mark.asyncio
    async def test_cli_file_format_alignment(self):
        """Test CLI file output format aligns with existing implementation."""
        with patch('src.auto_prompt_generator._get_generate_meta_prompt') as mock_get_func:
            # Mock the function that gets returned
            async def mock_generate_meta_prompt(*args, **kwargs):
                return {
                    "generated_prompt": "Test meta-prompt with configuration context",
                    "template_used": "custom",
                    "configuration_included": True,
                    "analysis_completed": True,
                    "context_analyzed": 2048
                }
            
            mock_get_func.return_value = mock_generate_meta_prompt
            
            from src.auto_prompt_generator import cli_generate_meta_prompt
            
            with tempfile.TemporaryDirectory() as temp_dir:
                result = await cli_generate_meta_prompt(
                    project_path=temp_dir,
                    output_dir=temp_dir
                )
                
                # Read generated file
                output_file = result["output_file"]
                with open(output_file, 'r') as f:
                    content = f.read()
                
                # Verify format alignment with existing implementation
                expected_sections = [
                    "# Meta-Prompt for AI Code Review",
                    "## Generated Meta-Prompt",
                    "## Template Information",
                    "## Analysis Summary"
                ]
                
                for section in expected_sections:
                    assert section in content
                
                # Verify metadata format
                assert "Template Used: custom" in content
                assert "Configuration Included: Yes" in content
                assert "Context Analyzed: 2048 characters" in content
    
    def test_cli_output_filename_format(self):
        """Test CLI generates properly formatted output filenames."""
        from src.auto_prompt_generator import generate_output_filename
        
        # Test timestamp-based filename
        filename = generate_output_filename()
        
        assert filename.startswith("meta-prompt-")
        assert filename.endswith(".md")
        assert len(filename) == len("meta-prompt-YYYYMMDD-HHMMSS.md")
        
        # Test custom prefix
        filename = generate_output_filename(prefix="custom-prompt")
        assert filename.startswith("custom-prompt-")
        assert filename.endswith(".md")
    
    @pytest.mark.asyncio
    async def test_cli_error_handling_file_mode(self):
        """Test CLI error handling in file output mode."""
        from src.auto_prompt_generator import cli_generate_meta_prompt
        
        # Test invalid context file
        result = await cli_generate_meta_prompt(
            context_file_path="/nonexistent/file.md"
        )
        
        assert result["status"] == "error"
        assert "not found" in result["error"].lower()
        
        # Test invalid output directory
        result = await cli_generate_meta_prompt(
            context_content="Test content",
            output_dir="/invalid/readonly/directory"
        )
        
        assert result["status"] == "error"
        assert "permission" in result["error"].lower() or "directory" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_cli_error_handling_stream_mode(self):
        """Test CLI error handling in stream output mode."""
        from src.auto_prompt_generator import cli_generate_meta_prompt
        
        # Test missing required parameters
        result = await cli_generate_meta_prompt(stream_output=True)
        
        assert result["status"] == "error"
        assert "input parameter" in result["error"].lower()


class TestAutoPromptCLIIntegration:
    """Test CLI integration with existing auto-prompt functionality."""
    
    @pytest.mark.asyncio
    async def test_cli_integrates_with_mcp_tool(self):
        """Test CLI uses same underlying function as MCP tool."""
        with patch('src.server.generate_meta_prompt') as mock_mcp_tool:
            mock_mcp_tool.return_value = {
                "generated_prompt": "MCP tool generated prompt",
                "template_used": "default",
                "configuration_included": True,
                "analysis_completed": True,
                "context_analyzed": 1024
            }
            
            from src.auto_prompt_generator import cli_generate_meta_prompt
            
            # CLI should use same function as MCP tool
            result = await cli_generate_meta_prompt(
                context_content="Test integration",
                stream_output=True
            )
            
            # Verify MCP tool function was called
            mock_mcp_tool.assert_called_once()
            call_args = mock_mcp_tool.call_args[1]
            assert call_args["context_content"] == "Test integration"
    
    def test_cli_argument_validation_alignment(self):
        """Test CLI argument validation aligns with MCP tool validation."""
        from src.auto_prompt_generator import validate_cli_arguments
        
        # Test mutual exclusivity (same as MCP tool)
        with pytest.raises(ValueError, match="Only one input parameter"):
            validate_cli_arguments({
                'context_file_path': 'file.md',
                'context_content': 'content',
                'project_path': '/path'
            })
        
        # Test missing parameters (same as MCP tool)
        with pytest.raises(ValueError, match="At least one input parameter"):
            validate_cli_arguments({})
    
    @pytest.mark.asyncio
    async def test_cli_template_priority_alignment(self):
        """Test CLI template priority aligns with MCP tool."""
        with patch('src.auto_prompt_generator.generate_meta_prompt') as mock_generate:
            mock_generate.return_value = {
                "generated_prompt": "Custom template result",
                "template_used": "custom",
                "configuration_included": False,
                "analysis_completed": True,
                "context_analyzed": 512
            }
            
            from src.auto_prompt_generator import cli_generate_meta_prompt
            
            # Test custom template takes priority
            result = await cli_generate_meta_prompt(
                context_content="Test content",
                custom_template="Custom CLI template: {context}",
                stream_output=True
            )
            
            # Verify custom template was passed to underlying function
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args[1]
            assert call_args["custom_template"] == "Custom CLI template: {context}"


class TestAutoPromptCLIOutput:
    """Test CLI output formatting and file generation."""
    
    def test_format_meta_prompt_output_file(self):
        """Test meta-prompt file formatting function."""
        from src.auto_prompt_generator import format_meta_prompt_output
        
        prompt_data = {
            "generated_prompt": "Focus on type safety and TDD compliance",
            "template_used": "environment",
            "configuration_included": True,
            "analysis_completed": True,
            "context_analyzed": 1800
        }
        
        formatted_content = format_meta_prompt_output(prompt_data)
        
        # Verify required sections
        assert "# Meta-Prompt for AI Code Review" in formatted_content
        assert "## Generated Meta-Prompt" in formatted_content
        assert "Focus on type safety and TDD compliance" in formatted_content
        
        # Verify metadata sections
        assert "## Template Information" in formatted_content
        assert "Template Used: environment" in formatted_content
        assert "Configuration Included: Yes" in formatted_content
        
        # Verify analysis summary
        assert "## Analysis Summary" in formatted_content
        assert "Context Analyzed: 1800 characters" in formatted_content
        assert "Analysis Status: Completed" in formatted_content
    
    def test_format_meta_prompt_output_stream(self):
        """Test meta-prompt stream formatting (just the prompt)."""
        from src.auto_prompt_generator import format_meta_prompt_stream
        
        prompt_data = {
            "generated_prompt": "Stream output meta-prompt content",
            "template_used": "default",
            "configuration_included": False,
            "analysis_completed": True,
            "context_analyzed": 900
        }
        
        stream_content = format_meta_prompt_stream(prompt_data)
        
        # Stream should just return the prompt content
        assert stream_content == "Stream output meta-prompt content"
    
    def test_cli_main_function_file_mode(self):
        """Test CLI main function in file output mode."""
        with patch('src.auto_prompt_generator.parse_cli_arguments') as mock_args:
            with patch('src.auto_prompt_generator.cli_generate_meta_prompt') as mock_cli:
                mock_args.return_value = Mock(
                    context_file='context.md',
                    output_dir='/tmp',
                    stream=False,
                    verbose=False
                )
                mock_cli.return_value = {
                    "status": "success",
                    "output_file": "/tmp/meta-prompt-20250101-120000.md"
                }
                
                from src.auto_prompt_generator import main
                
                # Should not raise exception
                with patch('builtins.print') as mock_print:
                    main()
                    
                    # Verify success message printed
                    mock_print.assert_called()
                    printed_args = [call[0][0] for call in mock_print.call_args_list]
                    assert any("meta-prompt-20250101-120000.md" in arg for arg in printed_args)
    
    def test_cli_main_function_stream_mode(self):
        """Test CLI main function in stream output mode."""
        with patch('src.auto_prompt_generator.parse_cli_arguments') as mock_args:
            with patch('src.auto_prompt_generator.cli_generate_meta_prompt') as mock_cli:
                mock_args.return_value = Mock(
                    context_content='Direct content',
                    stream=True,
                    verbose=False
                )
                mock_cli.return_value = {
                    "status": "success",
                    "streamed_content": "Direct prompt output"
                }
                
                from src.auto_prompt_generator import main
                
                # Should not raise exception
                with patch('builtins.print') as mock_print:
                    main()
                    
                    # Verify streamed content printed
                    mock_print.assert_called_with("Direct prompt output")


class TestAutoPromptCLIArgumentParser:
    """Test comprehensive CLI argument parsing."""
    
    def test_argument_parser_creation(self):
        """Test that argument parser is properly configured."""
        from src.auto_prompt_generator import create_argument_parser
        
        parser = create_argument_parser()
        
        # Test that parser exists and is configured
        assert parser is not None
        assert parser.description is not None
        assert "meta-prompt" in parser.description.lower()
    
    def test_mutually_exclusive_input_arguments(self):
        """Test that input arguments are mutually exclusive."""
        from src.auto_prompt_generator import create_argument_parser
        
        parser = create_argument_parser()
        
        # Test valid single inputs
        args1 = parser.parse_args(['--context-file', 'test.md'])
        assert args1.context_file == 'test.md'
        assert args1.context_content is None
        assert args1.project_path is None
        
        args2 = parser.parse_args(['--context-content', 'direct content'])
        assert args2.context_content == 'direct content'
        assert args2.context_file is None
        assert args2.project_path is None
        
        args3 = parser.parse_args(['--project-path', '/path/to/project'])
        assert args3.project_path == '/path/to/project'
        assert args3.context_file is None
        assert args3.context_content is None
    
    def test_output_mode_arguments(self):
        """Test output mode argument parsing."""
        from src.auto_prompt_generator import create_argument_parser
        
        parser = create_argument_parser()
        
        # Test file output (default)
        args1 = parser.parse_args(['--context-file', 'test.md'])
        assert args1.stream is False
        assert args1.output_dir is None  # Uses default
        
        # Test stream output
        args2 = parser.parse_args(['--context-content', 'content', '--stream'])
        assert args2.stream is True
        
        # Test custom output directory
        args3 = parser.parse_args(['--project-path', '/path', '--output-dir', '/custom'])
        assert args3.output_dir == '/custom'
    
    def test_template_arguments(self):
        """Test template-related arguments."""
        from src.auto_prompt_generator import create_argument_parser
        
        parser = create_argument_parser()
        
        # Test custom template
        args = parser.parse_args([
            '--context-file', 'test.md',
            '--custom-template', 'Custom: {context}'
        ])
        assert args.custom_template == 'Custom: {context}'
        
        # Test scope argument
        args2 = parser.parse_args([
            '--project-path', '/path',
            '--scope', 'full_project'
        ])
        assert args2.scope == 'full_project'
    
    def test_help_text_quality(self):
        """Test that help text is comprehensive and helpful."""
        from src.auto_prompt_generator import create_argument_parser
        
        parser = create_argument_parser()
        help_text = parser.format_help()
        
        # Verify key concepts are explained
        assert "meta-prompt" in help_text.lower()
        assert "stream" in help_text.lower()
        assert "file" in help_text.lower()
        assert "output" in help_text.lower()
        
        # Verify examples are provided
        assert "example" in help_text.lower() or "usage" in help_text.lower()