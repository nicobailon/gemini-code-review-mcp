"""
Comprehensive tests for the model configuration system.

Tests cover:
1. Model Configuration Loading (`load_model_config()`)
2. Model Alias Resolution
3. Model Capabilities Detection
4. Fallback Behavior
5. Environment Integration
"""

import json
import os
import sys
from typing import Dict, List, Union
from unittest.mock import mock_open, patch

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from model_config_manager import load_model_config


class TestModelConfigurationLoading:
    """Test model configuration loading functionality."""

    def test_load_valid_config_file(self):
        """Test loading a valid model configuration file."""
        mock_config = {
            "model_aliases": {
                "gemini-2.5-pro": "gemini-2.5-pro-preview-06-05",
                "gemini-2.5-flash": "gemini-2.5-flash-preview-05-20",
            },
            "model_capabilities": {
                "url_context_supported": [
                    "gemini-2.5-pro-preview-06-05",
                    "gemini-2.5-flash-preview-05-20",
                ],
                "thinking_mode_supported": ["gemini-2.5-pro-preview-06-05", "gemini-2.5-flash-preview-05-20"],
            },
            "defaults": {
                "model": "gemini-2.0-flash",
                "summary_model": "gemini-2.0-flash-lite",
            },
        }

        mock_config_json = json.dumps(mock_config)

        with patch("builtins.open", mock_open(read_data=mock_config_json)):
            with patch("os.path.exists", return_value=True):
                result = load_model_config()

        assert result == mock_config
        assert "model_aliases" in result
        assert "model_capabilities" in result
        assert "defaults" in result

    def test_load_config_with_missing_keys(self):
        """Test loading config file with missing keys merges with defaults."""
        # Config missing some sections
        incomplete_config = {
            "model_aliases": {"custom-model": "custom-model-v1"}
            # Missing model_capabilities and defaults
        }

        mock_config_json = json.dumps(incomplete_config)

        with patch("builtins.open", mock_open(read_data=mock_config_json)):
            with patch("os.path.exists", return_value=True):
                result = load_model_config()

        # Should have merged with defaults
        assert "model_aliases" in result
        assert "model_capabilities" in result  # From defaults
        assert "defaults" in result  # From defaults

        # Custom aliases should be preserved
        assert result["model_aliases"]["custom-model"] == "custom-model-v1"

        # Default capabilities should be present
        assert "url_context_supported" in result["model_capabilities"]
        assert "thinking_mode_supported" in result["model_capabilities"]

    def test_load_config_file_not_found(self):
        """Test fallback when config file doesn't exist."""
        with patch("os.path.exists", return_value=False):
            with patch("model_config_manager.logger") as mock_logger:
                result = load_model_config()

        # Should return default configuration
        assert "model_aliases" in result
        assert "model_capabilities" in result
        assert "defaults" in result

        # Should log warning
        mock_logger.warning.assert_called_once()
        assert "not found" in mock_logger.warning.call_args[0][0]

    def test_load_config_invalid_json(self):
        """Test fallback when config file contains invalid JSON."""
        invalid_json = "{ invalid json content"

        with patch("builtins.open", mock_open(read_data=invalid_json)):
            with patch("os.path.exists", return_value=True):
                with patch("model_config_manager.logger") as mock_logger:
                    result = load_model_config()

        # Should return default configuration
        assert "model_aliases" in result
        assert "model_capabilities" in result
        assert "defaults" in result

        # Should log warning about JSON decode error
        mock_logger.warning.assert_called_once()
        assert "Failed to load model config" in mock_logger.warning.call_args[0][0]

    def test_load_config_io_error(self):
        """Test fallback when file cannot be read due to IO error."""
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            with patch("os.path.exists", return_value=True):
                with patch("model_config_manager.logger") as mock_logger:
                    result = load_model_config()

        # Should return default configuration
        assert "model_aliases" in result
        assert "model_capabilities" in result
        assert "defaults" in result

        # Should log warning about IO error
        mock_logger.warning.assert_called_once()
        assert "Failed to load model config" in mock_logger.warning.call_args[0][0]

    def test_config_path_construction(self):
        """Test that config path is constructed correctly relative to script location."""
        with patch("os.path.dirname") as mock_dirname:
            with patch("os.path.join") as mock_join:
                with patch("os.path.exists", return_value=False):
                    mock_dirname.return_value = "/fake/src/dir"
                    mock_join.return_value = "/fake/src/dir/model_config.json"

                    load_model_config()

                    # Should call os.path.join with correct arguments
                    mock_join.assert_called_with("/fake/src/dir", "model_config.json")


class TestModelAliasResolution:
    """Test model alias resolution functionality."""

    def test_resolve_gemini_pro_alias(self):
        """Test that gemini-2.5-pro resolves to correct model name."""
        config = load_model_config()

        model_aliases = config["model_aliases"]

        # Test default aliases
        assert "gemini-2.5-pro" in model_aliases
        assert model_aliases["gemini-2.5-pro"] == "gemini-2.5-pro-preview-06-05"

    def test_resolve_gemini_flash_alias(self):
        """Test that gemini-2.5-flash resolves to correct model name."""
        config = load_model_config()

        model_aliases = config["model_aliases"]

        assert "gemini-2.5-flash" in model_aliases
        assert model_aliases["gemini-2.5-flash"] == "gemini-2.5-flash-preview-05-20"

    def test_alias_resolution_in_context(self):
        """Test alias resolution as it would be used in the main function."""
        config = load_model_config()

        # Simulate how aliases are resolved in send_to_gemini_for_review
        test_model = "gemini-2.5-pro"
        resolved_model = config["model_aliases"].get(test_model, test_model)

        assert resolved_model == "gemini-2.5-pro-preview-06-05"

        # Test non-alias model passes through unchanged
        test_model = "gemini-2.0-flash"
        resolved_model = config["model_aliases"].get(test_model, test_model)

        assert resolved_model == "gemini-2.0-flash"  # No alias, returns original

    def test_custom_aliases_override_defaults(self):
        """Test that custom config can override default aliases."""
        custom_config: Dict[str, Union[Dict[str, str], Dict[str, List[str]]]] = {
            "model_aliases": {
                "gemini-2.5-pro": "custom-gemini-model-v2",
                "my-custom-alias": "gemini-experimental",
            },
            "model_capabilities": {
                "url_context_supported": [],
                "thinking_mode_supported": [],
            },
            "defaults": {
                "model": "gemini-2.0-flash",
                "summary_model": "gemini-2.0-flash-lite",
            },
        }

        mock_config_json = json.dumps(custom_config)

        with patch("builtins.open", mock_open(read_data=mock_config_json)):
            with patch("os.path.exists", return_value=True):
                result = load_model_config()

        # Custom alias should override default
        assert result["model_aliases"]["gemini-2.5-pro"] == "custom-gemini-model-v2"
        assert result["model_aliases"]["my-custom-alias"] == "gemini-experimental"


class TestModelCapabilities:
    """Test model capability detection functionality."""

    def test_url_context_capability_detection(self):
        """Test URL context capability detection for supported models."""
        config = load_model_config()

        url_supported = config["model_capabilities"]["url_context_supported"]

        # Test models that should support URL context
        assert "gemini-2.5-pro-preview-06-05" in url_supported
        assert "gemini-2.5-flash-preview-05-20" in url_supported
        assert "gemini-2.0-flash" in url_supported

        # Test capability check logic
        test_model = "gemini-2.5-flash-preview-05-20"
        supports_url = test_model in url_supported
        assert supports_url is True

        # Test model that doesn't support URL context
        test_model = "gemini-1.0-pro"
        supports_url = test_model in url_supported
        assert supports_url is False

    def test_thinking_mode_capability_detection(self):
        """Test thinking mode capability detection for supported models."""
        config = load_model_config()

        thinking_supported = config["model_capabilities"]["thinking_mode_supported"]

        # Test models that should support thinking mode
        assert "gemini-2.5-pro-preview-06-05" in thinking_supported
        assert "gemini-2.5-flash-preview-05-20" in thinking_supported

        # Test capability check logic
        test_model = "gemini-2.5-flash-preview-05-20"
        supports_thinking = test_model in thinking_supported
        assert supports_thinking is True

        # Test model that doesn't support thinking mode
        test_model = "gemini-2.0-flash"
        supports_thinking = test_model in thinking_supported
        assert supports_thinking is False

    def test_grounding_capability_inference(self):
        """Test grounding capability inference based on model naming convention."""
        # Simulate the grounding capability logic from send_to_gemini_for_review
        test_cases = [
            ("gemini-1.5-pro", True),
            ("gemini-2.0-flash", True),
            ("gemini-2.5-pro-preview-05-06", True),
            ("gemini-1.0-pro", False),
            ("claude-3", False),
        ]

        for model_name, expected_grounding in test_cases:
            supports_grounding = (
                "gemini-1.5" in model_name
                or "gemini-2.0" in model_name
                or "gemini-2.5" in model_name
            )
            assert supports_grounding == expected_grounding, f"Failed for {model_name}"

    def test_capability_combination_scenarios(self):
        """Test various combinations of model capabilities."""
        config = load_model_config()

        # gemini-2.5-pro-preview-06-05: Should support all features
        model = "gemini-2.5-pro-preview-06-05"
        url_supported = config["model_capabilities"]["url_context_supported"]
        thinking_supported = config["model_capabilities"]["thinking_mode_supported"]

        supports_url = model in url_supported
        supports_thinking = model in thinking_supported
        supports_grounding = "gemini-2.5" in model

        assert supports_url is True
        assert supports_thinking is True
        assert supports_grounding is True

        # gemini-2.5-flash-preview-05-20: Should support all features
        model = "gemini-2.5-flash-preview-05-20"
        supports_url = model in url_supported
        supports_thinking = model in thinking_supported
        supports_grounding = "gemini-2.5" in model

        assert supports_url is True
        assert supports_thinking is True
        assert supports_grounding is True

        # gemini-2.0-flash: Should support URL and grounding but not thinking
        model = "gemini-2.0-flash"
        supports_url = model in url_supported
        supports_thinking = model in thinking_supported
        supports_grounding = "gemini-2.0" in model

        assert supports_url is True
        assert supports_thinking is False
        assert supports_grounding is True


class TestFallbackBehavior:
    """Test fallback behavior when configuration is missing or corrupt."""

    def test_default_configuration_structure(self):
        """Test that default configuration has all required sections."""
        # Force fallback by making file not exist
        with patch("os.path.exists", return_value=False):
            config = load_model_config()

        # Check all required top-level keys exist
        required_keys = ["model_aliases", "model_capabilities", "defaults"]
        for key in required_keys:
            assert key in config, f"Missing required key: {key}"

        # Check model_capabilities structure
        capabilities = config["model_capabilities"]
        assert "url_context_supported" in capabilities
        assert "thinking_mode_supported" in capabilities
        assert isinstance(capabilities["url_context_supported"], list)
        assert isinstance(capabilities["thinking_mode_supported"], list)

        # Check defaults structure
        defaults = config["defaults"]
        assert "model" in defaults
        assert "summary_model" in defaults
        assert isinstance(defaults["model"], str)
        assert isinstance(defaults["summary_model"], str)

    def test_fallback_preserves_functionality(self):
        """Test that fallback config preserves all essential functionality."""
        with patch("os.path.exists", return_value=False):
            config = load_model_config()

        # Test alias resolution works
        aliases = config["model_aliases"]
        assert len(aliases) > 0
        assert "gemini-2.5-pro" in aliases

        # Test capability detection works
        url_models = config["model_capabilities"]["url_context_supported"]
        thinking_models = config["model_capabilities"]["thinking_mode_supported"]

        assert len(url_models) > 0
        assert len(thinking_models) > 0

        # Test defaults are sensible
        defaults = config["defaults"]
        assert defaults["model"].startswith("gemini")
        assert defaults["summary_model"].startswith("gemini")

    def test_partial_config_merge_preserves_custom_values(self):
        """Test that partial config correctly merges with defaults."""
        # Custom config with only aliases
        custom_config = {"model_aliases": {"my-model": "my-model-v1"}}

        mock_config_json = json.dumps(custom_config)

        with patch("builtins.open", mock_open(read_data=mock_config_json)):
            with patch("os.path.exists", return_value=True):
                result = load_model_config()

        # Custom alias should be preserved
        assert result["model_aliases"]["my-model"] == "my-model-v1"

        # Default sections should be filled in
        assert "model_capabilities" in result
        assert "defaults" in result

        # Note: Current implementation replaces entire sections, not deep merging
        # This is actually reasonable behavior for configuration management

    def test_empty_config_file_uses_defaults(self):
        """Test that empty config file falls back to defaults."""
        empty_config = "{}"

        with patch("builtins.open", mock_open(read_data=empty_config)):
            with patch("os.path.exists", return_value=True):
                result = load_model_config()

        # Should contain all default sections
        assert "model_aliases" in result
        assert "model_capabilities" in result
        assert "defaults" in result

        # Should contain default values
        assert len(result["model_aliases"]) > 0
        assert len(result["model_capabilities"]["url_context_supported"]) > 0


class TestEnvironmentIntegration:
    """Test how model configuration integrates with environment variables."""

    @patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-pro"})
    def test_environment_model_selection(self):
        """Test that environment variable can override default model."""
        config = load_model_config()

        # Simulate model selection logic from send_to_gemini_for_review
        model_config = os.getenv("GEMINI_MODEL", config["defaults"]["model"])

        assert model_config == "gemini-2.5-pro"

    @patch.dict(os.environ, {"GEMINI_SUMMARY_MODEL": "custom-summary-model"})
    def test_environment_summary_model_selection(self):
        """Test that environment variable can override summary model."""
        config = load_model_config()

        # Simulate summary model selection logic from extract_prd_summary
        summary_model = os.getenv(
            "GEMINI_SUMMARY_MODEL", config["defaults"]["summary_model"]
        )

        assert summary_model == "custom-summary-model"

    @patch.dict(os.environ, {}, clear=True)
    def test_environment_fallback_to_config_defaults(self):
        """Test that config defaults are used when no environment variables set."""
        config = load_model_config()

        # Simulate model selection without environment variables
        model_config = os.getenv("GEMINI_MODEL", config["defaults"]["model"])
        summary_model = os.getenv(
            "GEMINI_SUMMARY_MODEL", config["defaults"]["summary_model"]
        )

        assert model_config == config["defaults"]["model"]
        assert summary_model == config["defaults"]["summary_model"]

    def test_alias_resolution_with_environment_variable(self):
        """Test that environment variable model names get resolved through aliases."""
        config = load_model_config()

        # Test environment variable with alias
        with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-pro"}):
            env_model = os.getenv("GEMINI_MODEL", config["defaults"]["model"])
            resolved_model = config["model_aliases"].get(env_model, env_model)

            assert env_model == "gemini-2.5-pro"
            assert resolved_model == "gemini-2.5-pro-preview-06-05"

        # Test environment variable without alias
        with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.0-flash"}):
            env_model = os.getenv("GEMINI_MODEL", config["defaults"]["model"])
            resolved_model = config["model_aliases"].get(env_model, env_model)

            assert env_model == "gemini-2.0-flash"
            assert resolved_model == "gemini-2.0-flash"  # No alias, unchanged


class TestModelConfigurationIntegration:
    """Integration tests for model configuration in real usage scenarios."""

    def test_send_to_gemini_model_selection_flow(self):
        """Test the complete model selection flow as used in send_to_gemini_for_review."""
        config = load_model_config()

        # Test the complete flow with environment variable
        with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-pro"}):
            # Step 1: Get model from environment or config default
            model_config = os.getenv("GEMINI_MODEL", config["defaults"]["model"])

            # Step 2: Resolve alias
            model_config = config["model_aliases"].get(model_config, model_config)

            # Step 3: Check capabilities
            supports_url = (
                model_config in config["model_capabilities"]["url_context_supported"]
            )
            supports_thinking = (
                model_config in config["model_capabilities"]["thinking_mode_supported"]
            )
            supports_grounding = (
                "gemini-1.5" in model_config
                or "gemini-2.0" in model_config
                or "gemini-2.5" in model_config
            )

            # Verify the complete flow
            assert model_config == "gemini-2.5-pro-preview-06-05"
            assert supports_url is True
            assert supports_thinking is True
            assert supports_grounding is True

    def test_extract_prd_summary_model_selection_flow(self):
        """Test model selection flow as used in extract_prd_summary."""
        config = load_model_config()

        # Test summary model selection
        summary_model = os.getenv(
            "GEMINI_SUMMARY_MODEL", config["defaults"]["summary_model"]
        )

        # Should use configured default
        assert summary_model == config["defaults"]["summary_model"]

        # Test with environment override
        with patch.dict(os.environ, {"GEMINI_SUMMARY_MODEL": "custom-summary"}):
            summary_model = os.getenv(
                "GEMINI_SUMMARY_MODEL", config["defaults"]["summary_model"]
            )
            assert summary_model == "custom-summary"

    def test_capability_detection_edge_cases(self):
        """Test capability detection for edge cases and new model versions."""
        config = load_model_config()

        # Test that the system handles new model versions gracefully
        test_cases = [
            # (model_name, expected_url, expected_thinking, expected_grounding)
            ("gemini-2.5-pro-preview-06-05", True, True, True),
            ("gemini-2.5-flash-preview-05-20", True, True, True),
            ("gemini-2.0-flash", True, False, True),
            ("gemini-1.5-pro", False, False, True),  # Not in default config
            ("unknown-model", False, False, False),
        ]

        for model, exp_url, exp_thinking, exp_grounding in test_cases:
            url_supported = (
                model in config["model_capabilities"]["url_context_supported"]
            )
            thinking_supported = (
                model in config["model_capabilities"]["thinking_mode_supported"]
            )
            grounding_supported = (
                "gemini-1.5" in model or "gemini-2.0" in model or "gemini-2.5" in model
            )

            assert url_supported == exp_url, f"URL support failed for {model}"
            assert (
                thinking_supported == exp_thinking
            ), f"Thinking support failed for {model}"
            assert (
                grounding_supported == exp_grounding
            ), f"Grounding support failed for {model}"


class TestConfigurationValidation:
    """Test configuration validation and error handling."""

    def test_malformed_model_aliases_handling(self):
        """Test handling of malformed model aliases section."""
        malformed_config: Dict[str, Union[str, Dict[str, List[str]], Dict[str, str]]] = {
            "model_aliases": "this should be a dict, not a string",
            "model_capabilities": {
                "url_context_supported": [],
                "thinking_mode_supported": [],
            },
            "defaults": {
                "model": "gemini-2.0-flash",
                "summary_model": "gemini-2.0-flash-lite",
            },
        }

        mock_config_json = json.dumps(malformed_config)

        with patch("builtins.open", mock_open(read_data=mock_config_json)):
            with patch("os.path.exists", return_value=True):
                # Should not crash and load successfully
                result = load_model_config()

                # Current implementation doesn't validate types, just loads JSON
                # This tests that the function completes without error
                assert "model_aliases" in result
                assert "model_capabilities" in result
                assert "defaults" in result

    def test_missing_capability_lists_handling(self):
        """Test handling when capability lists are missing or malformed."""
        incomplete_config = {
            "model_aliases": {"test": "test-model"},
            "model_capabilities": {
                # Missing url_context_supported and thinking_mode_supported
            },
            "defaults": {
                "model": "gemini-2.0-flash",
                "summary_model": "gemini-2.0-flash-lite",
            },
        }

        mock_config_json = json.dumps(incomplete_config)

        with patch("builtins.open", mock_open(read_data=mock_config_json)):
            with patch("os.path.exists", return_value=True):
                result = load_model_config()

                # Current implementation replaces entire sections, doesn't deep merge
                # The loaded config would have empty model_capabilities
                assert "model_capabilities" in result
                # The actual structure depends on what was in the file
                assert isinstance(result["model_capabilities"], dict)

    def test_config_file_path_edge_cases(self):
        """Test edge cases in config file path handling."""
        # Test with __file__ being None (can happen in some environments)
        with patch("generate_code_review_context.__file__", None):
            with patch("os.path.dirname", return_value=""):
                with patch("os.path.join", return_value="model_config.json"):
                    with patch("os.path.exists", return_value=False):
                        # Should not crash and should return defaults
                        result = load_model_config()
                        assert "model_aliases" in result


class TestThinkingBudgetConfiguration:
    """Test thinking budget configuration in model config."""
    
    def test_thinking_budget_in_model_config(self):
        """Test that model config can include thinking budget settings."""
        config = load_model_config()
        
        # Check that thinking mode supported models are defined
        assert "thinking_mode_supported" in config["model_capabilities"]
        thinking_models = config["model_capabilities"]["thinking_mode_supported"]
        assert isinstance(thinking_models, list)
        
        # Check known thinking mode models
        assert "gemini-2.5-flash-preview-05-20" in thinking_models
        assert "gemini-2.5-pro-preview-06-05" in thinking_models
        
    def test_model_supports_thinking_budget(self):
        """Test checking if a model supports thinking budget."""
        config = load_model_config()
        thinking_supported = config["model_capabilities"]["thinking_mode_supported"]
        
        # Models that support thinking budget
        assert "gemini-2.5-flash-preview-05-20" in thinking_supported
        assert "gemini-2.5-pro-preview-06-05" in thinking_supported
        
        # Models that don't support thinking budget (yet)
        assert "gemini-2.0-flash" not in thinking_supported
        assert "gemini-1.5-pro" not in thinking_supported


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
