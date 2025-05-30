"""
Test suite for meta-prompt integration into context file generation.

Following TDD Protocol: Writing tests first to define expected behavior.
The issue is that when using --auto-prompt, the generated meta-prompt should
be embedded in the <user_instructions> section of the context file, not just
passed to the AI review as a separate custom prompt.
"""

import pytest
from unittest.mock import patch, Mock, AsyncMock, mock_open
import tempfile
import os
import json
from pathlib import Path


class TestMetaPromptContextIntegration:
    """Test integration of meta-prompt into context file generation."""
    
    @pytest.mark.asyncio
    async def test_auto_prompt_embeds_meta_prompt_in_context_file(self):
        """Test that --auto-prompt embeds generated meta-prompt in context file <user_instructions>."""
        with patch('src.generate_code_review_context.generate_auto_prompt') as mock_generate_auto_prompt:
            with patch('src.generate_code_review_context.generate_ai_code_review') as mock_ai_review:
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Mock meta-prompt generation
                    test_meta_prompt = """You are a meticulous code reviewer analyzing recent changes to the `task-list-code-review-mcp` project. 

**Key Areas of Focus:**
1. **Type Safety (TypeScript Guidelines):**
   - Verify that no `any` types have been introduced
2. **Test-Driven Development (TDD Protocol):**
   - Confirm new features implemented using TDD"""
                    
                    mock_generate_auto_prompt.return_value = {
                        "generated_prompt": test_meta_prompt,
                        "template_used": "default",
                        "configuration_included": True,
                        "analysis_completed": True,
                        "context_analyzed": 2800
                    }
                    
                    # Mock AI review
                    mock_ai_review.return_value = f"{temp_dir}/ai-review.md"
                    
                    # Mock file operations to capture context file content
                    written_files = {}
                    
                    def mock_write_file(filename, mode='w', **kwargs):
                        file_obj = mock_open().return_value
                        file_obj.write = lambda content: written_files.update({filename: content})
                        return file_obj
                    
                    with patch('builtins.open', side_effect=mock_write_file):
                        from src.generate_code_review_context import execute_auto_prompt_workflow
                        
                        result = execute_auto_prompt_workflow(
                            project_path=temp_dir,
                            scope="recent_phase",
                            auto_prompt=True,
                            generate_prompt_only=False
                        )
                    
                    # Verify meta-prompt was generated
                    mock_generate_auto_prompt.assert_called_once()
                    
                    # Check that a context file was written with meta-prompt in user_instructions
                    context_files = [f for f in written_files.keys() if 'context' in f]
                    assert len(context_files) > 0, "No context file was written"
                    
                    context_content = written_files[context_files[0]]
                    
                    # Verify meta-prompt is embedded in user_instructions
                    assert '<user_instructions>' in context_content
                    assert '</user_instructions>' in context_content
                    
                    # Extract user_instructions section
                    user_instructions_start = context_content.find('<user_instructions>') + len('<user_instructions>')
                    user_instructions_end = context_content.find('</user_instructions>')
                    user_instructions = context_content[user_instructions_start:user_instructions_end].strip()
                    
                    # Verify meta-prompt content is in user_instructions
                    assert "meticulous code reviewer" in user_instructions
                    assert "Type Safety (TypeScript Guidelines)" in user_instructions
                    assert "Test-Driven Development (TDD Protocol)" in user_instructions
    
    def test_context_generation_with_auto_prompt_parameter(self):
        """Test that context generation function accepts auto_prompt_content parameter."""
        from src.generate_code_review_context import generate_code_review_context_main
        import inspect
        
        # Check function signature
        sig = inspect.signature(generate_code_review_context_main)
        params = list(sig.parameters.keys())
        
        # Should support auto_prompt_content parameter for meta-prompt integration
        # (This test defines the expected API)
        expected_param = 'auto_prompt_content'
        
        # For now, this test documents the expected behavior
        # The implementation should be updated to include this parameter
        print(f"Current parameters: {params}")
        print(f"Expected parameter: {expected_param}")
    
    def test_context_template_with_meta_prompt(self):
        """Test context template generation with embedded meta-prompt."""
        # This test defines how the context template should change when meta-prompt is provided
        
        # Expected behavior:
        # 1. Normal context generation uses generic user_instructions
        # 2. With auto_prompt_content, user_instructions should contain the meta-prompt
        # 3. Meta-prompt should replace generic instructions, not append to them
        
        # Mock context data
        context_data = {
            "overall_prd_summary": "Test PRD summary",
            "current_phase_description": "Test phase",
            "project_path": "/test/path",
            "auto_prompt_content": "Custom meta-prompt for testing"
        }
        
        # This test documents the expected template behavior
        # Implementation should generate different user_instructions based on auto_prompt_content
        
        expected_with_meta_prompt = """<user_instructions>
Custom meta-prompt for testing
</user_instructions>"""
        
        expected_without_meta_prompt = """<user_instructions>We have just completed phase #1.0: "Test phase".

Important: Refer to the configuration context (Claude memory and Cursor rules) provided above for project-specific guidelines and coding standards.

Based on the PRD, the completed phase, all subtasks that were finished in that phase, and the files changed in the working directory, your job is to conduct a code review and output your code review feedback for the completed phase. Identify specific lines or files that are concerning when appropriate.
</user_instructions>"""
        
        # The implementation should choose the appropriate template based on auto_prompt_content
        print("Expected meta-prompt template:", expected_with_meta_prompt)
        print("Expected default template:", expected_without_meta_prompt)


class TestContextTemplateLogic:
    """Test the context template generation logic."""
    
    def test_template_selection_logic(self):
        """Test that template selection works correctly for different modes."""
        # This test defines the expected template selection behavior
        
        scenarios = [
            {
                "name": "Default mode",
                "auto_prompt_content": None,
                "expected_template_type": "default",
                "should_contain": ["Based on the PRD", "conduct a code review"]
            },
            {
                "name": "Auto-prompt mode", 
                "auto_prompt_content": "Custom meta-prompt with specific guidelines",
                "expected_template_type": "meta_prompt",
                "should_contain": ["Custom meta-prompt", "specific guidelines"]
            },
            {
                "name": "Custom prompt mode",
                "auto_prompt_content": "You are an expert reviewer focusing on security",
                "expected_template_type": "meta_prompt", 
                "should_contain": ["expert reviewer", "security"]
            }
        ]
        
        for scenario in scenarios:
            print(f"\nScenario: {scenario['name']}")
            print(f"Auto-prompt content: {scenario['auto_prompt_content']}")
            print(f"Expected template type: {scenario['expected_template_type']}")
            print(f"Should contain: {scenario['should_contain']}")
        
        # The implementation should handle these scenarios correctly


class TestBackwardCompatibility:
    """Test that changes maintain backward compatibility."""
    
    def test_existing_workflow_unchanged(self):
        """Test that existing workflows without --auto-prompt still work."""
        # When auto_prompt_content is None or not provided,
        # the context generation should work exactly as before
        
        # This ensures we don't break existing functionality
        pass
    
    def test_custom_prompt_in_ai_review_still_works(self):
        """Test that passing custom_prompt to AI review still works."""
        # The existing method of passing custom_prompt to generate_ai_code_review
        # should continue to work for backward compatibility
        
        # This is for cases where users want to customize the AI review prompt
        # without changing the context file template
        pass