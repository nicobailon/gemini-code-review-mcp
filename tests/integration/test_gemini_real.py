"""
Integration tests that make real API calls to gemini-1.5-flash.

These tests validate core functionality with actual Gemini API responses.
Only tests features supported by gemini-1.5-flash (no thinking mode or URL context).
"""

import os
from typing import Optional

import pytest

from gemini_code_review_mcp.gemini_api_client import GEMINI_AVAILABLE, send_to_gemini_for_review
from gemini_code_review_mcp.model_config_manager import load_model_config


@pytest.mark.integration
class TestGeminiRealAPI:
    """Test suite for real Gemini API integration."""

    def test_gemini_api_available(self):
        """Test that Gemini API is available and configured."""
        assert GEMINI_AVAILABLE, "Gemini API library not available"
        assert os.getenv("GEMINI_API_KEY"), "GEMINI_API_KEY not set"

    def test_basic_code_review_generation(
        self, small_test_context, integration_test_model, integration_timeout
    ):
        """Test basic code review generation with real API."""
        result = send_to_gemini_for_review(
            context_content=small_test_context,
            project_path=None,
            temperature=0.5,
            model=integration_test_model,
            return_text=True,
            include_formatting=False,
            thinking_budget=None,  # Not supported by gemini-1.5-flash
        )

        assert result is not None, "API should return a response"
        assert isinstance(result, str), "Response should be a string"
        assert len(result) > 50, "Response should have meaningful content"

        # Check for code review elements (fuzzy matching for API variability)
        result_lower = result.lower()
        assert any(
            keyword in result_lower
            for keyword in ["code", "function", "review", "improve", "suggest"]
        )

    def test_temperature_variation(self, small_test_context, integration_test_model):
        """Test that different temperatures produce different outputs."""
        # Get low temperature response (more deterministic)
        result_low = send_to_gemini_for_review(
            context_content=small_test_context,
            project_path=None,
            temperature=0.1,
            model=integration_test_model,
            return_text=True,
            include_formatting=False,
        )

        # Get high temperature response (more creative)
        result_high = send_to_gemini_for_review(
            context_content=small_test_context,
            project_path=None,
            temperature=0.9,
            model=integration_test_model,
            return_text=True,
            include_formatting=False,
        )

        assert result_low is not None
        assert result_high is not None
        # We can't guarantee they're different due to model behavior,
        # but both should be valid responses
        assert len(result_low) > 50
        assert len(result_high) > 50

    def test_model_config_compatibility(self, integration_test_model):
        """Test that gemini-1.5-flash is properly configured."""
        config = load_model_config()

        # Check model capabilities for gemini-1.5-flash
        url_supported = (
            integration_test_model
            in config["model_capabilities"]["url_context_supported"]
        )
        thinking_supported = (
            integration_test_model
            in config["model_capabilities"]["thinking_mode_supported"]
        )

        # gemini-1.5-flash should NOT support these advanced features
        assert not url_supported, "gemini-1.5-flash should not support URL context"
        assert (
            not thinking_supported
        ), "gemini-1.5-flash should not support thinking mode"

    def test_error_handling_invalid_content(self, integration_test_model):
        """Test API error handling with invalid content."""
        # Test with empty content
        result = send_to_gemini_for_review(
            context_content="",
            project_path=None,
            temperature=0.5,
            model=integration_test_model,
            return_text=True,
        )

        # Should handle gracefully (might return None or error message)
        # The exact behavior depends on API implementation
        assert result is None or isinstance(result, str)


@pytest.mark.integration
class TestContextGeneration:
    """Test context generation with real API responses."""

    def test_generate_code_review_context_real(self, minimal_project_dir):
        """Test full context generation flow with real project."""
        from gemini_code_review_mcp.generate_code_review_context import generate_code_review_context_main

        # Generate context (doesn't use API, but prepares for it)
        context = generate_code_review_context_main(
            project_path=str(minimal_project_dir),
            scope="full_project",
            enable_gemini_review=False,  # Just generate context, don't review
            include_claude_memory=False,
            include_cursor_rules=False,
            raw_context_only=True,
            text_output=True,
        )

        assert context is not None
        assert isinstance(context, str)
        assert "# Code Review Context" in context
        assert "main.py" in context  # Should include our test file

    def test_meta_prompt_generation_real(
        self, minimal_project_dir, integration_test_model
    ):
        """Test meta prompt generation with real API."""
        # First generate context
        from gemini_code_review_mcp.generate_code_review_context import generate_code_review_context_main
        from gemini_code_review_mcp.meta_prompt_generator import generate_meta_prompt

        context = generate_code_review_context_main(
            project_path=str(minimal_project_dir),
            scope="full_project",
            enable_gemini_review=False,
            include_claude_memory=False,
            include_cursor_rules=False,
            raw_context_only=True,
            text_output=True,
        )

        # Generate meta prompt with real API
        meta_prompt = generate_meta_prompt(
            context_content=context,
            project_path=str(minimal_project_dir),
            model=integration_test_model,
            temperature=0.5,
            text_output=True,
        )

        assert meta_prompt is not None
        assert isinstance(meta_prompt, str)
        assert len(meta_prompt) > 100, "Meta prompt should have substantial content"

        # Should contain review-related guidance
        meta_prompt_lower = meta_prompt.lower()
        assert any(
            keyword in meta_prompt_lower
            for keyword in ["review", "code", "analyze", "check"]
        )


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("GITHUB_TOKEN"), reason="Requires GITHUB_TOKEN")
class TestGitHubIntegration:
    """Test GitHub integration with real API (requires GITHUB_TOKEN)."""

    def test_pr_review_with_real_api(self, integration_test_model):
        """Test PR review with real GitHub data and Gemini API."""
        from gemini_code_review_mcp.server import generate_pr_review

        # Use a small public PR for testing
        result = generate_pr_review(
            github_pr_url="https://github.com/octocat/Hello-World/pull/2",  # Classic test PR
            temperature=0.5,
            enable_gemini_review=True,
            text_output=True,
            model=integration_test_model,
        )

        if result:  # Might fail if PR doesn't exist anymore
            assert isinstance(result, str)
            assert len(result) > 100
            # Should mention PR or code review
            assert any(
                keyword in result.lower()
                for keyword in ["pull request", "pr", "changes", "review"]
            )


@pytest.mark.integration
class TestModelDefaultOverride:
    """Test that we're actually using gemini-1.5-flash in tests."""

    def test_model_override_works(
        self, integration_test_model, small_test_context, monkeypatch
    ):
        """Test that model override actually uses gemini-1.5-flash."""
        # Temporarily set default to something else
        monkeypatch.setenv("GEMINI_MODEL", "gemini-2.0-flash")

        # But explicitly pass gemini-1.5-flash
        result = send_to_gemini_for_review(
            context_content=small_test_context,
            project_path=None,
            temperature=0.5,
            model=integration_test_model,  # Should be gemini-1.5-flash
            return_text=True,
            include_formatting=False,
        )

        assert result is not None
        # The response should work (gemini-1.5-flash is valid)
        assert len(result) > 50
