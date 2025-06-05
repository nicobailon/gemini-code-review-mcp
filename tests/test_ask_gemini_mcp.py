#!/usr/bin/env python3
"""
MCP integration tests for the ask_gemini tool.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.server import ask_gemini as ask_gemini_mcp_tool


class TestAskGeminiMCPTool:
    """Test the ask_gemini MCP tool integration."""
    
    def test_mcp_tool_simple_question(self):
        """Test MCP tool with simple question."""
        with patch('src.ask_gemini.ask_gemini') as mock_impl:
            mock_impl.return_value = "MCP tool response"
            
            result = ask_gemini_mcp_tool("What is MCP?")
            
            assert result == "MCP tool response"
            mock_impl.assert_called_once_with(
                question="What is MCP?",
                file_selections=None,
                project_path=None,
                user_instructions=None,
                temperature=0.5,
                include_claude_memory=True,
                include_cursor_rules=False,
                text_output=True,
                output_path=None,
                model=None,
            )
    
    def test_mcp_tool_with_all_parameters(self):
        """Test MCP tool with all parameters."""
        with patch('src.ask_gemini.ask_gemini') as mock_impl:
            mock_impl.return_value = "Complete response"
            
            result = ask_gemini_mcp_tool(
                question="Explain this code",
                file_selections=[{"path": "main.py", "line_ranges": [(1, 10)]}],
                project_path="/project",
                user_instructions="Be concise",
                temperature=0.7,
                include_claude_memory=False,
                include_cursor_rules=True,
                text_output=False,
                output_path="/output/response.md",
                model="gemini-2.0-flash"
            )
            
            assert result == "Complete response"
            mock_impl.assert_called_once()
            
            # Verify all parameters were passed
            call_args = mock_impl.call_args[1]
            assert call_args['question'] == "Explain this code"
            assert call_args['file_selections'] == [{"path": "main.py", "line_ranges": [(1, 10)]}]
            assert call_args['project_path'] == "/project"
            assert call_args['user_instructions'] == "Be concise"
            assert call_args['temperature'] == 0.7
            assert call_args['include_claude_memory'] is False
            assert call_args['include_cursor_rules'] is True
            assert call_args['text_output'] is False
            assert call_args['output_path'] == "/output/response.md"
            assert call_args['model'] == "gemini-2.0-flash"
    
    def test_mcp_tool_value_error_handling(self):
        """Test MCP tool handles ValueError gracefully."""
        with patch('src.ask_gemini.ask_gemini') as mock_impl:
            mock_impl.side_effect = ValueError("Invalid question")
            
            result = ask_gemini_mcp_tool("")
            
            assert result == "ERROR: Invalid question"
    
    def test_mcp_tool_general_error_handling(self):
        """Test MCP tool handles general exceptions gracefully."""
        with patch('src.ask_gemini.ask_gemini') as mock_impl:
            mock_impl.side_effect = Exception("API error")
            
            result = ask_gemini_mcp_tool("Test question")
            
            assert result == "ERROR: Failed to process question: API error"
    
    def test_mcp_tool_in_tools_list(self):
        """Test that ask_gemini is in the MCP tools list."""
        from src.server import get_mcp_tools
        
        tools = get_mcp_tools()
        assert "ask_gemini" in tools
    
    def test_mcp_tool_file_selections_format(self):
        """Test MCP tool handles various file selection formats."""
        with patch('src.ask_gemini.ask_gemini') as mock_impl:
            mock_impl.return_value = "Success"
            
            # Test with simple file selection
            ask_gemini_mcp_tool(
                question="Test",
                file_selections=[{"path": "file1.py"}]
            )
            
            # Test with line ranges
            ask_gemini_mcp_tool(
                question="Test",
                file_selections=[
                    {"path": "file2.py", "line_ranges": [(10, 20), (30, 40)]}
                ]
            )
            
            # Test with multiple files
            ask_gemini_mcp_tool(
                question="Test",
                file_selections=[
                    {"path": "file1.py"},
                    {"path": "file2.py", "line_ranges": [(1, 50)]},
                    {"path": "file3.py", "include_full": False}
                ]
            )
            
            assert mock_impl.call_count == 3