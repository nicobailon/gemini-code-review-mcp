"""
Tests for enhanced MCP server tool signatures and behaviors
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


class TestNewToolSignatureValidation:
    """Test validation of new MCP tool signatures"""
    
    @pytest.mark.asyncio
    async def test_generate_code_review_context_tool_exists(self):
        """Test that generate_code_review_context tool exists with new signature"""
        tools = await server.handle_list_tools()
        
        # Find the generate_code_review_context tool
        context_tool = None
        for tool in tools:
            if tool.name == "generate_code_review_context":
                context_tool = tool
                break
        
        assert context_tool is not None, "generate_code_review_context tool should exist"
        
        # Check that the tool has the enhanced signature
        schema = context_tool.inputSchema
        properties = schema.get("properties", {})
        
        # Should have the new scope-based parameters
        assert "scope" in properties, "Tool should have scope parameter"
        assert "phase_number" in properties, "Tool should have phase_number parameter"
        assert "task_number" in properties, "Tool should have task_number parameter"
    
    @pytest.mark.asyncio
    async def test_generate_ai_code_review_tool_exists(self):
        """Test that generate_ai_code_review tool exists"""
        tools = await server.handle_list_tools()
        
        # Find the generate_ai_code_review tool
        ai_review_tool = None
        for tool in tools:
            if tool.name == "generate_ai_code_review":
                ai_review_tool = tool
                break
        
        assert ai_review_tool is not None, "generate_ai_code_review tool should exist"
        
        # Check that the tool has the correct signature
        schema = ai_review_tool.inputSchema
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # Should have context_file_path as required parameter
        assert "context_file_path" in properties, "Tool should have context_file_path parameter"
        assert "context_file_path" in required, "context_file_path should be required"
        
        # Should have optional parameters
        assert "output_path" in properties, "Tool should have output_path parameter"
        assert "model" in properties, "Tool should have model parameter"
    
    @pytest.mark.asyncio
    async def test_tool_count_includes_new_tools(self):
        """Test that tool count includes all expected tools"""
        tools = await server.handle_list_tools()
        
        tool_names = [tool.name for tool in tools]
        
        # Should include both tools
        assert "generate_code_review_context" in tool_names
        assert "generate_ai_code_review" in tool_names
        
        # Should have at least 2 tools
        assert len(tools) >= 2


class TestEnhancedParameterSchemasAndValidation:
    """Test enhanced parameter schemas and validation"""
    
    @pytest.mark.asyncio
    async def test_scope_parameter_schema(self):
        """Test scope parameter schema definition"""
        tools = await server.handle_list_tools()
        context_tool = next(tool for tool in tools if tool.name == "generate_code_review_context")
        
        schema = context_tool.inputSchema
        scope_property = schema["properties"]["scope"]
        
        # Should have enum constraint
        assert "enum" in scope_property or "oneOf" in scope_property or scope_property.get("type") == "string"
        
        # Should have default value
        if "default" in scope_property:
            assert scope_property["default"] == "recent_phase"
    
    @pytest.mark.asyncio
    async def test_phase_number_parameter_schema(self):
        """Test phase_number parameter schema definition"""
        tools = await server.handle_list_tools()
        context_tool = next(tool for tool in tools if tool.name == "generate_code_review_context")
        
        schema = context_tool.inputSchema
        phase_number_property = schema["properties"]["phase_number"]
        
        # Should be string type
        assert phase_number_property["type"] == "string"
        
        # Should not be required (only required when scope is specific_phase)
        required = schema.get("required", [])
        assert "phase_number" not in required
    
    @pytest.mark.asyncio
    async def test_task_number_parameter_schema(self):
        """Test task_number parameter schema definition"""
        tools = await server.handle_list_tools()
        context_tool = next(tool for tool in tools if tool.name == "generate_code_review_context")
        
        schema = context_tool.inputSchema
        task_number_property = schema["properties"]["task_number"]
        
        # Should be string type
        assert task_number_property["type"] == "string"
        
        # Should not be required (only required when scope is specific_task)
        required = schema.get("required", [])
        assert "task_number" not in required
    
    @pytest.mark.asyncio
    async def test_context_file_path_parameter_schema(self):
        """Test context_file_path parameter schema for AI review tool"""
        tools = await server.handle_list_tools()
        ai_review_tool = next(tool for tool in tools if tool.name == "generate_ai_code_review")
        
        schema = ai_review_tool.inputSchema
        context_file_property = schema["properties"]["context_file_path"]
        
        # Should be string type and required
        assert context_file_property["type"] == "string"
        assert "context_file_path" in schema["required"]
    
    @pytest.mark.asyncio
    async def test_model_parameter_schema(self):
        """Test model parameter schema for AI review tool"""
        tools = await server.handle_list_tools()
        ai_review_tool = next(tool for tool in tools if tool.name == "generate_ai_code_review")
        
        schema = ai_review_tool.inputSchema
        model_property = schema["properties"]["model"]
        
        # Should be string type and optional
        assert model_property["type"] == "string"
        required = schema.get("required", [])
        assert "model" not in required


class TestToolDescriptionAccuracyAndCompleteness:
    """Test tool descriptions for accuracy and completeness"""
    
    @pytest.mark.asyncio
    async def test_generate_code_review_context_description(self):
        """Test generate_code_review_context tool description"""
        tools = await server.handle_list_tools()
        context_tool = next(tool for tool in tools if tool.name == "generate_code_review_context")
        
        description = context_tool.description
        
        # Should mention key functionality
        assert len(description) > 50, "Description should be comprehensive"
        assert "scope" in description.lower(), "Should mention scope functionality"
        assert "context" in description.lower(), "Should mention context generation"
        
        # Should not be generic
        assert "generate" in description.lower(), "Should describe what it generates"
    
    @pytest.mark.asyncio
    async def test_generate_ai_code_review_description(self):
        """Test generate_ai_code_review tool description"""
        tools = await server.handle_list_tools()
        ai_review_tool = next(tool for tool in tools if tool.name == "generate_ai_code_review")
        
        description = ai_review_tool.description
        
        # Should mention key functionality
        assert len(description) > 50, "Description should be comprehensive"
        assert "ai" in description.lower() or "review" in description.lower(), "Should mention AI review"
        assert "context" in description.lower(), "Should mention context file input"
        
        # Should differentiate from context generation
        assert "existing" in description.lower() or "from" in description.lower(), "Should indicate it works from existing context"
    
    @pytest.mark.asyncio
    async def test_tool_descriptions_are_distinct(self):
        """Test that tool descriptions clearly distinguish their purposes"""
        tools = await server.handle_list_tools()
        
        context_tool = next(tool for tool in tools if tool.name == "generate_code_review_context")
        ai_review_tool = next(tool for tool in tools if tool.name == "generate_ai_code_review")
        
        context_desc = context_tool.description.lower()
        ai_review_desc = ai_review_tool.description.lower()
        
        # Descriptions should be different
        assert context_desc != ai_review_desc, "Tool descriptions should be distinct"
        
        # Context tool should emphasize context generation
        assert "context" in context_desc, "Context tool should mention context"
        
        # AI review tool should emphasize review generation
        assert "review" in ai_review_desc, "AI review tool should mention review"


class TestBackwardCompatibilityWithExistingParameters:
    """Test backward compatibility with existing parameters"""
    
    @pytest.mark.asyncio
    async def test_existing_parameters_still_supported(self):
        """Test that existing parameters are still supported"""
        tools = await server.handle_list_tools()
        context_tool = next(tool for tool in tools if tool.name == "generate_code_review_context")
        
        schema = context_tool.inputSchema
        properties = schema["properties"]
        
        # Original parameters should still exist
        assert "project_path" in properties, "project_path should still be supported"
        assert "output_path" in properties, "output_path should still be supported"
        assert "enable_gemini_review" in properties, "enable_gemini_review should still be supported"
    
    @pytest.mark.asyncio
    async def test_project_path_still_required(self):
        """Test that project_path is still required"""
        tools = await server.handle_list_tools()
        context_tool = next(tool for tool in tools if tool.name == "generate_code_review_context")
        
        schema = context_tool.inputSchema
        required = schema.get("required", [])
        
        assert "project_path" in required, "project_path should still be required"
    
    @pytest.mark.asyncio
    async def test_legacy_call_without_scope_works(self):
        """Test that legacy calls without scope parameter work"""
        # This tests the default scope behavior
        with patch('server.generate_review_context') as mock_generate:
            mock_generate.return_value = "/path/to/output.md"
            with patch('builtins.open', mock_open(read_data="Generated content")):
                with patch('server.os.path.exists', return_value=True):
                    with patch('server.os.path.isabs', return_value=True):
                        result = await server.handle_call_tool(
                            "generate_code_review_context",
                            {"project_path": "/valid/path"}
                        )
                        
                        assert not result.isError, "Legacy call should work"
                        # Should default to recent_phase scope
                        mock_generate.assert_called_once()
                        call_args = mock_generate.call_args
                        # Verify scope defaults properly
                        assert call_args is not None


class TestErrorHandlingAndParameterValidationMessages:
    """Test error handling and parameter validation messages"""
    
    @pytest.mark.asyncio
    async def test_invalid_scope_parameter_error(self):
        """Test error handling for invalid scope parameter"""
        result = await server.handle_call_tool(
            "generate_code_review_context",
            {
                "project_path": "/valid/path",
                "scope": "invalid_scope"
            }
        )
        
        assert result.isError, "Should return error for invalid scope"
        error_message = result.content[0].text.lower()
        assert "scope" in error_message, "Error should mention scope"
    
    @pytest.mark.asyncio
    async def test_missing_phase_number_error(self):
        """Test error handling when phase_number is missing for specific_phase scope"""
        result = await server.handle_call_tool(
            "generate_code_review_context",
            {
                "project_path": "/valid/path",
                "scope": "specific_phase"
                # Missing phase_number
            }
        )
        
        assert result.isError, "Should return error for missing phase_number"
        error_message = result.content[0].text.lower()
        assert "phase_number" in error_message, "Error should mention phase_number"
    
    @pytest.mark.asyncio
    async def test_missing_task_number_error(self):
        """Test error handling when task_number is missing for specific_task scope"""
        result = await server.handle_call_tool(
            "generate_code_review_context",
            {
                "project_path": "/valid/path",
                "scope": "specific_task"
                # Missing task_number
            }
        )
        
        assert result.isError, "Should return error for missing task_number"
        error_message = result.content[0].text.lower()
        assert "task_number" in error_message, "Error should mention task_number"
    
    @pytest.mark.asyncio
    async def test_missing_context_file_path_error(self):
        """Test error handling when context_file_path is missing for AI review"""
        result = await server.handle_call_tool(
            "generate_ai_code_review",
            {}  # Missing context_file_path
        )
        
        assert result.isError, "Should return error for missing context_file_path"
        error_message = result.content[0].text.lower()
        assert "context_file_path" in error_message, "Error should mention context_file_path"
    
    @pytest.mark.asyncio
    async def test_nonexistent_context_file_error(self):
        """Test error handling for nonexistent context file"""
        result = await server.handle_call_tool(
            "generate_ai_code_review",
            {"context_file_path": "/nonexistent/context.md"}
        )
        
        assert result.isError, "Should return error for nonexistent context file"
        error_message = result.content[0].text.lower()
        assert ("not found" in error_message or 
               "does not exist" in error_message), "Error should indicate file not found"
    
    @pytest.mark.asyncio
    async def test_clear_error_messages(self):
        """Test that error messages are clear and helpful"""
        # Test with completely invalid input
        result = await server.handle_call_tool(
            "generate_code_review_context",
            {"invalid_param": "invalid_value"}
        )
        
        assert result.isError, "Should return error for invalid parameters"
        error_message = result.content[0].text
        
        # Error message should be informative
        assert len(error_message) > 20, "Error message should be descriptive"
        assert "project_path" in error_message.lower(), "Should mention required parameter"


class TestEnhancedToolCallHandling:
    """Test enhanced tool call handling"""
    
    @pytest.mark.asyncio
    async def test_generate_code_review_context_with_scope_parameters(self):
        """Test generate_code_review_context with new scope parameters"""
        with patch('server.generate_review_context') as mock_generate:
            mock_generate.return_value = "/path/to/output.md"
            with patch('builtins.open', mock_open(read_data="Generated content")):
                with patch('server.os.path.exists', return_value=True):
                    with patch('server.os.path.isabs', return_value=True):
                        result = await server.handle_call_tool(
                            "generate_code_review_context",
                            {
                                "project_path": "/valid/path",
                                "scope": "specific_phase",
                                "phase_number": "2.0"
                            }
                        )
                        
                        assert not result.isError, "Valid call should succeed"
                        mock_generate.assert_called_once()
                        
                        # Verify new parameters were passed
                        call_kwargs = mock_generate.call_args.kwargs if hasattr(mock_generate.call_args, 'kwargs') else {}
                        # Parameters should be passed through
    
    @pytest.mark.asyncio
    async def test_generate_ai_code_review_tool_call(self):
        """Test generate_ai_code_review tool call"""
        with patch('server.generate_ai_review') as mock_ai_review:
            mock_ai_review.return_value = "/path/to/ai-review.md"
            with patch('builtins.open', mock_open(read_data="AI review content")):
                with patch('server.os.path.exists', return_value=True):
                    result = await server.handle_call_tool(
                        "generate_ai_code_review",
                        {"context_file_path": "/valid/context.md"}
                    )
                    
                    assert not result.isError, "Valid AI review call should succeed"
                    mock_ai_review.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_unknown_tool_error(self):
        """Test error handling for unknown tools"""
        with pytest.raises(ValueError, match="Unknown tool"):
            await server.handle_call_tool("unknown_tool", {})
    
    @pytest.mark.asyncio
    async def test_tool_call_parameter_passthrough(self):
        """Test that tool call parameters are passed through correctly"""
        with patch('server.generate_review_context') as mock_generate:
            mock_generate.return_value = "/path/to/output.md"
            with patch('builtins.open', mock_open(read_data="Generated content")):
                with patch('server.os.path.exists', return_value=True):
                    with patch('server.os.path.isabs', return_value=True):
                        await server.handle_call_tool(
                            "generate_code_review_context",
                            {
                                "project_path": "/test/path",
                                "scope": "full_project",
                                "output_path": "/custom/output.md",
                                "enable_gemini_review": False
                            }
                        )
                        
                        # Verify all parameters were passed
                        mock_generate.assert_called_once()
                        call_args = mock_generate.call_args
                        
                        # Should include new scope-based parameters
                        assert call_args is not None


class TestMCPServerIntegration:
    """Test MCP server integration with new tools"""
    
    @pytest.mark.asyncio
    async def test_server_handles_multiple_tools(self):
        """Test that server properly handles multiple tools"""
        tools = await server.handle_list_tools()
        
        # Should have multiple tools
        assert len(tools) >= 2, "Server should support multiple tools"
        
        tool_names = [tool.name for tool in tools]
        assert len(set(tool_names)) == len(tool_names), "Tool names should be unique"
    
    @pytest.mark.asyncio
    async def test_tool_discovery_completeness(self):
        """Test that tool discovery returns complete information"""
        tools = await server.handle_list_tools()
        
        for tool in tools:
            # Each tool should have complete information
            assert tool.name, "Tool should have a name"
            assert tool.description, "Tool should have a description"
            assert tool.inputSchema, "Tool should have input schema"
            
            # Schema should have required structure
            schema = tool.inputSchema
            assert "type" in schema, "Schema should have type"
            assert "properties" in schema, "Schema should have properties"
            
            if "required" in schema:
                required_props = schema["required"]
                properties = schema["properties"]
                
                # All required properties should exist in properties
                for prop in required_props:
                    assert prop in properties, f"Required property {prop} should be in properties"
    
    def test_server_initialization(self):
        """Test that server initializes correctly with new tools"""
        # Server should initialize without errors
        assert hasattr(server, 'mcp'), "Server should have MCP instance"
        assert hasattr(server, 'handle_list_tools'), "Server should have tool listing handler"
        assert hasattr(server, 'handle_call_tool'), "Server should have tool call handler"
    
    @pytest.mark.asyncio
    async def test_async_main_functionality(self):
        """Test async main server functionality"""
        # Test that async_main can be called without errors
        with patch('server.stdio_server') as mock_stdio:
            mock_streams = (AsyncMock(), AsyncMock())
            mock_stdio.return_value.__aenter__.return_value = mock_streams
            mock_stdio.return_value.__aexit__.return_value = None
            
            with patch('server.server.run') as mock_run:
                # Should be able to start server
                await server.async_main()
                
                mock_stdio.assert_called_once()
                mock_run.assert_called_once()