"""
Unit tests for server entry point functionality
"""

import pytest
import sys
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import server


class TestServerEntryPoint:
    """Test server entry point and main function"""
    
    def test_main_function_exists(self):
        """Test that main function exists and is callable"""
        assert hasattr(server, 'main'), "main function should exist"
        assert callable(server.main), "main function should be callable"
    
    def test_async_main_function_exists(self):
        """Test that async_main function exists and is callable"""
        assert hasattr(server, 'async_main'), "async_main function should exist"
        assert callable(server.async_main), "async_main function should be callable"
    
    @patch('server.asyncio.run')
    def test_main_calls_asyncio_run(self, mock_asyncio_run):
        """Test that main function calls asyncio.run with async_main"""
        mock_asyncio_run.return_value = None
        
        server.main()
        
        # Check that asyncio.run was called once with a coroutine
        mock_asyncio_run.assert_called_once()
        call_args = mock_asyncio_run.call_args[0]
        assert len(call_args) == 1, "Should call asyncio.run with one argument"
        assert hasattr(call_args[0], '__await__'), "Should call with a coroutine"
    
    @patch('server.asyncio.run')
    @patch('server.logger')
    def test_main_handles_keyboard_interrupt(self, mock_logger, mock_asyncio_run):
        """Test that main function handles KeyboardInterrupt gracefully"""
        mock_asyncio_run.side_effect = KeyboardInterrupt()
        
        server.main()
        
        mock_logger.info.assert_called_with("Server stopped by user")
    
    @patch('server.asyncio.run')
    @patch('server.logger')
    @patch('server.sys.exit')
    def test_main_handles_exceptions(self, mock_exit, mock_logger, mock_asyncio_run):
        """Test that main function handles exceptions and exits with error code"""
        test_error = Exception("Test error")
        mock_asyncio_run.side_effect = test_error
        
        server.main()
        
        mock_logger.error.assert_called_with(f"Server error: {test_error}")
        mock_exit.assert_called_with(1)


class TestServerConfiguration:
    """Test server configuration and setup"""
    
    def test_server_instance_created(self):
        """Test that MCP server instance is created with correct name"""
        assert hasattr(server, 'server'), "Server instance should exist"
        # Note: Cannot easily test server name without accessing private attributes
    
    def test_logging_configured(self):
        """Test that logging is properly configured"""
        assert hasattr(server, 'logger'), "Logger should exist"
        assert server.logger.name == 'server', "Logger should have correct name"


class TestServerHandlers:
    """Test MCP server request handlers"""
    
    @pytest.mark.asyncio
    async def test_handle_list_tools(self):
        """Test that list_tools handler returns expected tools"""
        tools = await server.handle_list_tools()
        
        assert isinstance(tools, list), "Should return a list of tools"
        assert len(tools) == 1, "Should return exactly one tool"
        
        tool = tools[0]
        assert tool.name == "generate_code_review_context", "Tool should have correct name"
        assert "Generate code review context" in tool.description, "Tool should have description"
        assert tool.inputSchema is not None, "Tool should have input schema"
        
        # Check required properties in schema
        schema = tool.inputSchema
        assert schema["type"] == "object", "Schema should be object type"
        assert "project_path" in schema["properties"], "Should require project_path"
        assert "project_path" in schema["required"], "project_path should be required"
    
    @pytest.mark.asyncio
    async def test_handle_call_tool_unknown_tool(self):
        """Test that call_tool handler rejects unknown tools"""
        with pytest.raises(ValueError, match="Unknown tool"):
            await server.handle_call_tool("unknown_tool", {})
    
    @pytest.mark.asyncio
    async def test_handle_call_tool_missing_project_path(self):
        """Test that call_tool handler requires project_path"""
        result = await server.handle_call_tool("generate_code_review_context", {})
        
        assert result.isError is True, "Should return error for missing project_path"
        assert "project_path is required" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_handle_call_tool_invalid_project_path(self):
        """Test that call_tool handler validates project_path exists"""
        result = await server.handle_call_tool(
            "generate_code_review_context", 
            {"project_path": "/nonexistent/path"}
        )
        
        assert result.isError is True, "Should return error for nonexistent path"
        assert "does not exist" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_handle_call_tool_relative_path(self):
        """Test that call_tool handler requires absolute path"""
        result = await server.handle_call_tool(
            "generate_code_review_context", 
            {"project_path": "relative/path"}
        )
        
        assert result.isError is True, "Should return error for relative path"
        assert "must be an absolute path" in result.content[0].text
    
    @pytest.mark.asyncio
    @patch('server.generate_review_context')
    @patch('builtins.open')
    @patch('server.os.path.exists')
    @patch('server.os.path.isabs')
    async def test_handle_call_tool_success(self, mock_isabs, mock_exists, mock_open, mock_generate):
        """Test successful tool call execution"""
        # Setup mocks
        mock_exists.return_value = True
        mock_isabs.return_value = True
        mock_generate.return_value = "/path/to/output.md"
        
        # Mock file reading
        mock_file = MagicMock()
        mock_file.read.return_value = "Generated content"
        mock_open.return_value.__enter__.return_value = mock_file
        
        result = await server.handle_call_tool(
            "generate_code_review_context", 
            {"project_path": "/valid/path"}
        )
        
        assert result.isError is not True, "Should not return error for valid request"
        assert "Successfully generated" in result.content[0].text
        assert "Generated content" in result.content[0].text
        
        # Verify function was called with correct parameters
        mock_generate.assert_called_once_with(
            project_path="/valid/path",
            phase=None,
            output=None,
            enable_gemini_review=True
        )


class TestServerIntegration:
    """Test server integration and async functionality"""
    
    @pytest.mark.asyncio
    @patch('server.stdio_server')
    @patch('server.server.run')
    async def test_async_main_server_setup(self, mock_server_run, mock_stdio_server):
        """Test that async_main sets up server correctly"""
        # Mock stdio_server context manager
        mock_streams = AsyncMock(), AsyncMock()
        mock_stdio_server.return_value.__aenter__.return_value = mock_streams
        mock_stdio_server.return_value.__aexit__.return_value = None
        
        await server.async_main()
        
        # Verify stdio_server was called
        mock_stdio_server.assert_called_once()
        
        # Verify server.run was called with streams and options
        mock_server_run.assert_called_once()
        args = mock_server_run.call_args[0]
        assert len(args) == 3, "Should call with read_stream, write_stream, options"
    
    def test_initialization_options(self):
        """Test that InitializationOptions are properly configured"""
        # This test would require running async_main and checking the options
        # For now, we can at least verify the imports work
        from mcp.server.models import InitializationOptions
        
        # Test that we can create options (basic smoke test)
        options = InitializationOptions(
            server_name="test",
            server_version="1.0.0",
            capabilities={"tools": {}}
        )
        assert options.server_name == "test"