"""
Test suite for auto-prompt integration with code review context generation.

Following TDD Protocol: Writing tests first to define expected integration behavior.
The issue is that auto-prompt generation and context generation are separate,
but they should be integrated when using --auto-prompt flag.
"""

import pytest
from unittest.mock import patch, Mock, AsyncMock, mock_open
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime
import asyncio


class TestAutoPromptIntegration:
    """Test integration between auto-prompt generation and code review context."""
    
    @pytest.mark.asyncio
    async def test_auto_prompt_flag_generates_and_uses_meta_prompt(self):
        """Test that --auto-prompt flag generates meta-prompt and uses it for context."""
        with patch('src.generate_code_review_context.generate_meta_prompt') as mock_generate_meta_prompt:
            with patch('src.generate_code_review_context.generate_ai_code_review') as mock_ai_review:
                with patch('src.generate_code_review_context.main') as mock_main:
                    # Mock auto-prompt generation result
                    mock_generate_meta_prompt.return_value = {
                        "generated_prompt": "Focus on type safety and TDD compliance in authentication system",
                        "template_used": "default",
                        "configuration_included": True,
                        "analysis_completed": True,
                        "context_analyzed": 2800
                    }
                    
                    # Mock context generation result
                    mock_main.return_value = ("context-file.md", None)
                    
                    # Mock AI review result
                    mock_ai_review.return_value = "ai-review-file.md"
                    
                    # Import and test the workflow
                    from src.generate_code_review_context import execute_auto_prompt_workflow
                    
                    result = execute_auto_prompt_workflow(
                        project_path="/test/project",
                        scope="full_project",
                        temperature=0.5,
                        auto_prompt=True,
                        generate_prompt_only=False
                    )
                    
                    # Verify auto-prompt generation was called
                    mock_generate_meta_prompt.assert_called_once_with(
                        project_path="/test/project",
                        scope="full_project"
                    )
                    
                    # Verify context generation was called
                    mock_main.assert_called_once()
                    
                    # Verify AI review was called with custom prompt
                    mock_ai_review.assert_called_once()
                    call_args = mock_ai_review.call_args[1]
                    assert call_args["custom_prompt"] == "Focus on type safety and TDD compliance in authentication system"
                    
                    # Verify result contains completion message
                    assert "Auto-Prompt Code Review Complete!" in result
                    assert "ai-review-file.md" in result
    
    @pytest.mark.asyncio
    async def test_generate_prompt_only_flag_creates_meta_prompt_without_review(self):
        """Test that --generate-prompt-only creates meta-prompt but skips AI review."""
        with patch('src.generate_code_review_context.generate_meta_prompt') as mock_generate_meta_prompt:
            # Mock auto-prompt generation result
            mock_generate_meta_prompt.return_value = {
                "generated_prompt": "Security-focused review of payment processing module",
                "template_used": "security_focused",
                "configuration_included": False,
                "analysis_completed": True,
                "context_analyzed": 1500
            }
            
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            result = execute_auto_prompt_workflow(
                project_path="/test/project",
                scope="specific_phase",
                temperature=0.3,
                auto_prompt=False,
                generate_prompt_only=True
            )
            
            # Verify auto-prompt generation was called
            mock_generate_meta_prompt.assert_called_once_with(
                project_path="/test/project",
                scope="specific_phase"
            )
            
            # Verify result shows prompt generation only
            assert "Optimized Prompt Generated!" in result
            assert "Security-focused review of payment processing module" in result
            assert "Auto-Prompt Code Review Complete!" not in result
    
    def test_cli_auto_prompt_flag_integration(self):
        """Test CLI argument parsing for auto-prompt integration."""
        from src.generate_code_review_context import create_argument_parser, validate_cli_arguments
        
        parser = create_argument_parser()
        
        # Test --auto-prompt flag
        args = parser.parse_args(["/test/project", "--auto-prompt"])
        assert args.auto_prompt is True
        assert args.generate_prompt_only is False
        
        # Should not raise validation error
        validate_cli_arguments(args)
        
        # Test --generate-prompt-only flag
        args = parser.parse_args(["/test/project", "--generate-prompt-only"])
        assert args.auto_prompt is False
        assert args.generate_prompt_only is True
        
        # Should not raise validation error
        validate_cli_arguments(args)
    
    def test_cli_mutually_exclusive_auto_prompt_flags(self):
        """Test that --auto-prompt and --generate-prompt-only are mutually exclusive."""
        from src.generate_code_review_context import create_argument_parser, validate_cli_arguments
        
        parser = create_argument_parser()
        
        # Test conflicting flags
        args = parser.parse_args(["/test/project", "--auto-prompt", "--generate-prompt-only"])
        
        # Should raise validation error
        with pytest.raises(ValueError, match="mutually exclusive"):
            validate_cli_arguments(args)
    
    @pytest.mark.asyncio
    async def test_auto_prompt_workflow_error_handling(self):
        """Test error handling in auto-prompt workflow."""
        with patch('src.generate_code_review_context.generate_meta_prompt') as mock_generate_meta_prompt:
            # Mock auto-prompt generation failure
            mock_generate_meta_prompt.side_effect = Exception("Gemini API error")
            
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            with pytest.raises(Exception, match="Auto-prompt workflow failed"):
                execute_auto_prompt_workflow(
                    project_path="/test/project",
                    scope="full_project",
                    auto_prompt=True,
                    generate_prompt_only=False
                )
    
    @pytest.mark.asyncio
    async def test_auto_prompt_uses_correct_scope_and_parameters(self):
        """Test that auto-prompt generation receives correct scope and parameters."""
        with patch('src.generate_code_review_context.generate_meta_prompt') as mock_generate_meta_prompt:
            with patch('src.generate_code_review_context.main') as mock_main:
                with patch('src.generate_code_review_context.generate_ai_code_review') as mock_ai_review:
                    # Mock responses
                    mock_generate_meta_prompt.return_value = {
                        "generated_prompt": "Test prompt",
                        "template_used": "default",
                        "configuration_included": True,
                        "analysis_completed": True,
                        "context_analyzed": 1000
                    }
                    mock_main.return_value = ("context.md", None)
                    mock_ai_review.return_value = "review.md"
                    
                    from src.generate_code_review_context import execute_auto_prompt_workflow
                    
                    # Test with specific scope
                    execute_auto_prompt_workflow(
                        project_path="/custom/project",
                        scope="specific_phase",
                        temperature=0.7,
                        auto_prompt=True,
                        generate_prompt_only=False
                    )
                    
                    # Verify correct parameters passed
                    mock_generate_meta_prompt.assert_called_once_with(
                        project_path="/custom/project",
                        scope="specific_phase"
                    )
                    
                    # Verify AI review called with correct temperature
                    mock_ai_review.assert_called_once()
                    call_args = mock_ai_review.call_args[1]
                    assert call_args["temperature"] == 0.7


class TestAutoPromptStandaloneVsIntegrated:
    """Test differences between standalone auto-prompt and integrated workflow."""
    
    def test_standalone_auto_prompt_saves_to_file(self):
        """Test that standalone auto-prompt generator saves meta-prompt to file."""
        # This represents the current behavior that we tested earlier
        # The standalone CLI saves meta-prompt to timestamped .md file
        pass  # Already tested in test_cli_auto_prompt.py
    
    def test_integrated_auto_prompt_uses_meta_prompt_for_ai_review(self):
        """Test that integrated workflow uses generated meta-prompt for AI review."""
        # This is the behavior we need to ensure works correctly
        # The --auto-prompt flag should generate meta-prompt AND use it for AI review
        pass  # Covered by test_auto_prompt_flag_generates_and_uses_meta_prompt
    
    @pytest.mark.asyncio
    async def test_auto_prompt_integration_preserves_meta_prompt_content(self):
        """Test that meta-prompt content is preserved when used in AI review."""
        with patch('src.generate_code_review_context.generate_meta_prompt') as mock_generate_meta_prompt:
            with patch('src.generate_code_review_context.main') as mock_main:
                with patch('src.generate_code_review_context.generate_ai_code_review') as mock_ai_review:
                    # Create detailed meta-prompt like the one we generated
                    detailed_meta_prompt = """You are a meticulous code reviewer analyzing recent changes to the `task-list-code-review-mcp` project. Your goal is to identify potential issues and ensure adherence to project guidelines, focusing on type safety, test-driven development, and proper tool usage.

**Key Areas of Focus:**
1. **Type Safety (TypeScript Guidelines):**
   - Verify that no `any` types have been introduced
   - Check Zod schema migrations
2. **Test-Driven Development (TDD Protocol):**
   - Confirm new features implemented using TDD
   - Verify tests written before implementation"""
                    
                    mock_generate_meta_prompt.return_value = {
                        "generated_prompt": detailed_meta_prompt,
                        "template_used": "default",
                        "configuration_included": True,
                        "analysis_completed": True,
                        "context_analyzed": 2800
                    }
                    mock_main.return_value = ("context.md", None)
                    mock_ai_review.return_value = "review.md"
                    
                    from src.generate_code_review_context import execute_auto_prompt_workflow
                    
                    execute_auto_prompt_workflow(
                        project_path="/test/project",
                        scope="full_project",
                        auto_prompt=True,
                        generate_prompt_only=False
                    )
                    
                    # Verify the detailed meta-prompt was passed to AI review
                    mock_ai_review.assert_called_once()
                    call_args = mock_ai_review.call_args[1]
                    passed_prompt = call_args["custom_prompt"]
                    
                    # Verify key content is preserved
                    assert "meticulous code reviewer" in passed_prompt
                    assert "Type Safety (TypeScript Guidelines)" in passed_prompt
                    assert "Test-Driven Development (TDD Protocol)" in passed_prompt
                    assert "any` types" in passed_prompt


class TestAutoPromptWorkflowOutputFormat:
    """Test output formatting for auto-prompt workflows."""
    
    def test_auto_prompt_workflow_output_format(self):
        """Test that auto-prompt workflow produces correctly formatted output."""
        from src.generate_code_review_context import format_auto_prompt_output
        
        prompt_result = {
            "generated_prompt": "Focus on security vulnerabilities in authentication",
            "template_used": "security_focused", 
            "configuration_included": True,
            "analysis_completed": True,
            "context_analyzed": 2500
        }
        
        # Test auto-prompt mode (with AI review)
        output = format_auto_prompt_output(
            prompt_result, 
            auto_prompt_mode=True, 
            ai_review_file="/path/to/review.md"
        )
        
        # Verify output format
        assert "Auto-Prompt Code Review Complete!" in output
        assert "Template: security_focused" in output
        assert "Context analyzed: 2500 characters" in output
        assert "Focus on security vulnerabilities in authentication" in output
        assert "review.md" in output
        assert "Auto-prompt code review workflow completed!" in output
        
        # Test prompt-only mode
        output = format_auto_prompt_output(
            prompt_result, 
            auto_prompt_mode=False
        )
        
        # Verify prompt-only format
        assert "Optimized Prompt Generated!" in output
        assert "Prompt generation completed!" in output
        assert "Auto-Prompt Code Review Complete!" not in output
        assert "Use this prompt with --custom-prompt" in output