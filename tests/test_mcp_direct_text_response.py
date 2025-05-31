"""
Test suite for MCP tools direct text response and chaining capabilities.

Following TDD Protocol: Writing tests first to define expected behavior.
These tests specify that MCP tools should return text content directly 
for AI agent consumption and support chaining operations.
"""

import pytest
from unittest.mock import patch, Mock, AsyncMock
import tempfile
import os
from pathlib import Path


class TestMCPDirectTextResponse:
    """Test direct text response behavior for all MCP tools."""
    
    @pytest.mark.asyncio
    async def test_generate_meta_prompt_returns_text_content(self):
        """Test generate_meta_prompt returns the generated prompt text directly."""
        from src.server import generate_meta_prompt
        
        # Test with real Gemini API using .env key
        result = await generate_meta_prompt(
            context_content="Test context content for meta-prompt generation"
        )
        
        # Should return structured response with generated_prompt text
        assert isinstance(result, dict)
        assert "generated_prompt" in result
        assert isinstance(result["generated_prompt"], str)
        assert len(result["generated_prompt"]) > 50
        assert "meta-prompt" in result["generated_prompt"].lower() or "prompt" in result["generated_prompt"].lower()
        
        # Verify other expected keys exist
        assert "template_used" in result
        assert "analysis_completed" in result
        assert "context_analyzed" in result
        assert result["analysis_completed"] is True
        assert isinstance(result["context_analyzed"], int)
        assert result["context_analyzed"] > 0
        
        # Should NOT create files by default
        assert "output_file" not in result or result.get("output_file") is None
    
    def test_generate_code_review_context_returns_context_text(self):
        """Test generate_code_review_context returns context content directly."""
        from src.server import generate_code_review_context
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create minimal project structure
            project_path = temp_dir
            
            with patch('src.server.generate_review_context') as mock_context_gen:
                # Mock should return context content directly, not file paths
                mock_context_gen.return_value = (
                    "# Code Review Context\n\nProject analysis and context...",
                    None  # No AI review file
                )
                
                result = generate_code_review_context(
                    project_path=project_path,
                    raw_context_only=True
                )
                
                # Should return the context content as text
                assert isinstance(result, str)
                assert "Code Review Context" in result
                assert len(result) > 100
                
                # Should NOT mention file paths in response
                assert "Generated review context:" not in result
                assert "Files generated:" not in result
    
    def test_generate_ai_code_review_returns_review_text(self):
        """Test generate_ai_code_review returns AI review content directly."""
        from src.server import generate_ai_code_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test context file
            context_file = Path(temp_dir) / "test-context.md"
            context_file.write_text("# Test Context\n\nCode changes and analysis...")
            
            with patch('src.server.generate_ai_review') as mock_ai_review:
                # Mock should return AI review content directly
                mock_ai_review.return_value = "## AI Code Review\n\nDetailed analysis of changes..."
                
                result = generate_ai_code_review(
                    context_file_path=str(context_file)
                )
                
                # Should return the AI review content as text
                assert isinstance(result, str)
                assert "AI Code Review" in result
                assert len(result) > 50
                
                # Should NOT mention file creation
                assert "Successfully generated AI code review:" not in result
                assert "output_file" not in result.lower()


class TestMCPToolChaining:
    """Test chaining capabilities between MCP tools."""
    
    @pytest.mark.asyncio
    async def test_auto_prompt_to_context_to_ai_review_chain(self):
        """Test complete chain: generate_meta_prompt -> generate_code_review_context -> generate_ai_code_review."""
        from src.server import generate_meta_prompt, generate_code_review_context, generate_ai_code_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = temp_dir
            
            # Step 1: Generate auto-prompt
            with patch('src.server.send_to_gemini_for_review') as mock_gemini:
                mock_gemini.return_value = "Meta-prompt for authentication review"
                
                auto_prompt_result = await generate_meta_prompt(
                    context_content="Authentication system implementation complete"
                )
                
                assert "generated_prompt" in auto_prompt_result
                generated_prompt = auto_prompt_result["generated_prompt"]
            
            # Step 2: Use the generated prompt in context generation
            with patch('src.server.generate_review_context') as mock_context:
                mock_context.return_value = (
                    "# Context with Authentication Focus\n\nDetailed context...",
                    None
                )
                
                context_result = generate_code_review_context(
                    project_path=project_path,
                    raw_context_only=True
                )
                
                assert isinstance(context_result, str)
                assert "Authentication" in context_result
            
            # Step 3: Use context for AI review with the generated prompt
            with patch('src.server.generate_ai_review') as mock_ai:
                mock_ai.return_value = "## Authentication Security Review\n\nBased on the meta-prompt..."
                
                # In real implementation, this would use generated_prompt as custom_prompt
                ai_review_result = generate_ai_code_review(
                    context_file_path="dummy",  # Would be context_result in real chaining
                    custom_prompt=generated_prompt
                )
                
                assert isinstance(ai_review_result, str)
                assert "Authentication" in ai_review_result
                assert len(ai_review_result) > 50
    
    def test_context_content_parameter_for_chaining(self):
        """Test that tools accept content parameters for chaining without file I/O."""
        from src.server import generate_ai_code_review
        
        # Should be able to pass context content directly instead of file path
        context_content = "# Generated Context\n\nThis context was generated by previous tool..."
        
        with patch('src.server.generate_ai_review') as mock_ai:
            mock_ai.return_value = "AI review based on provided context"
            
            # This test defines that we should support context_content parameter
            # for seamless chaining without temporary files
            result = generate_ai_code_review(
                context_content=context_content,  # Direct content, not file path
                custom_prompt="Focus on security patterns"
            )
            
            assert isinstance(result, str)
            assert len(result) > 20


class TestMCPResponseStructure:
    """Test consistent response structure across MCP tools."""
    
    @pytest.mark.asyncio
    async def test_generate_meta_prompt_response_structure(self):
        """Test generate_meta_prompt returns consistent structured response."""
        from src.server import generate_meta_prompt
        
        with patch('src.server.send_to_gemini_for_review') as mock_gemini:
            mock_gemini.return_value = "Generated meta-prompt content"
            
            result = await generate_meta_prompt(
                context_content="Test context"
            )
            
            # Must be dict with specific keys
            assert isinstance(result, dict)
            assert "generated_prompt" in result
            assert "template_used" in result
            assert "analysis_completed" in result
            assert "context_analyzed" in result
            
            # Text content should be in generated_prompt
            assert isinstance(result["generated_prompt"], str)
            assert len(result["generated_prompt"]) > 0
    
    def test_text_output_mode_parameter(self):
        """Test all tools support text_output mode for direct content return."""
        from src.server import generate_code_review_context, generate_ai_code_review
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = temp_dir
            
            # Test context generation with text output
            with patch('src.server.generate_review_context') as mock_context:
                mock_context.return_value = ("Context content", None)
                
                result = generate_code_review_context(
                    project_path=project_path,
                    text_output=True  # New parameter to force text output
                )
                
                # Should return text content directly
                assert isinstance(result, str)
                assert "Context content" in result
            
            # Test AI review with text output  
            context_file = Path(temp_dir) / "context.md"
            context_file.write_text("Test context")
            
            with patch('src.server.generate_ai_review') as mock_ai:
                mock_ai.return_value = "AI review content"
                
                result = generate_ai_code_review(
                    context_file_path=str(context_file),
                    text_output=True  # New parameter to force text output
                )
                
                # Should return text content directly
                assert isinstance(result, str)
                assert "AI review content" in result


class TestMCPBackwardCompatibility:
    """Test that enhanced tools maintain backward compatibility."""
    
    def test_file_output_still_supported(self):
        """Test that file output is still available when explicitly requested."""
        from src.server import generate_code_review_context
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = temp_dir
            output_file = Path(temp_dir) / "output.md"
            
            with patch('src.server.generate_review_context') as mock_context:
                mock_context.return_value = (str(output_file), None)
                output_file.write_text("Generated content")
                
                result = generate_code_review_context(
                    project_path=project_path,
                    output_path=str(output_file),  # Explicit file output
                    text_output=False  # Explicitly request file mode
                )
                
                # Should return file information when explicitly requested
                assert "output.md" in result or str(output_file) in result
    
    def test_default_behavior_change(self):
        """Test that default behavior is now text output, not file output."""
        from src.server import generate_code_review_context
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = temp_dir
            
            with patch('src.server.generate_review_context') as mock_context:
                mock_context.return_value = ("Context content text", None)
                
                result = generate_code_review_context(
                    project_path=project_path
                    # No text_output parameter - should default to True
                )
                
                # Default should now be text output
                assert isinstance(result, str)
                assert "Context content text" in result
                
                # Should NOT contain file path references
                assert "Generated review context:" not in result
                assert "Files generated:" not in result


class TestMCPErrorHandling:
    """Test error handling for direct text response mode."""
    
    @pytest.mark.asyncio
    async def test_generate_meta_prompt_error_handling_text_mode(self):
        """Test error handling returns structured response in text mode."""
        from src.server import generate_meta_prompt
        
        # Test with invalid input
        try:
            result = await generate_meta_prompt()  # No parameters
            
            # Should raise ValueError for validation
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "At least one input parameter must be provided" in str(e)
    
    def test_context_generation_error_handling_text_mode(self):
        """Test context generation error handling in text mode."""
        from src.server import generate_code_review_context
        
        # Test with invalid project path
        result = generate_code_review_context(
            project_path="/nonexistent/path"
        )
        
        # Should return error message as text
        assert isinstance(result, str)
        assert "ERROR:" in result
        assert "does not exist" in result


class TestMCPContentParameterSupport:
    """Test support for content parameters to enable chaining."""
    
    def test_ai_review_accepts_context_content_parameter(self):
        """Test generate_ai_code_review accepts context_content for chaining."""
        from src.server import generate_ai_code_review
        
        context_content = "# Code Review Context\n\nGenerated by previous tool..."
        
        with patch('src.server.generate_ai_review') as mock_ai:
            mock_ai.return_value = "AI review based on content"
            
            # Should accept context_content instead of context_file_path
            result = generate_ai_code_review(
                context_content=context_content
            )
            
            assert isinstance(result, str)
            assert "AI review" in result
    
    def test_mutual_exclusivity_of_content_parameters(self):
        """Test that content parameters are mutually exclusive."""
        from src.server import generate_ai_code_review
        
        # Should reject both context_file_path and context_content
        result = generate_ai_code_review(
            context_file_path="/some/file.md",
            context_content="Some content"
        )
        
        # Should return error message
        assert isinstance(result, str)
        assert "ERROR:" in result
        assert "Only one of context_file_path or context_content should be provided" in result