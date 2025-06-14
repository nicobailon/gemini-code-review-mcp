"""Tests for configuration loader with precedence handling."""

import os
import warnings
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config.loader import ConfigurationLoader, get_configuration_loader
from src.config_types import CodeReviewConfig
from src.errors import ConfigurationError


class TestConfigurationLoader:
    def setup_method(self):
        self.test_dir = Path("/test/project")
        self.loader = ConfigurationLoader(self.test_dir)

    def test_defaults_loaded(self):
        """Test that built-in defaults are returned when no other config exists."""
        value = self.loader.get_value("temperature")
        assert value == 0.5

        value = self.loader.get_value("enable_cache")
        assert value is True

        value = self.loader.get_value("cache_ttl_seconds")
        assert value == 900

    def test_cli_precedence_highest(self):
        """Test that CLI values have highest precedence."""
        # Set up environment variable and pyproject config
        with patch.dict(os.environ, {"GEMINI_TEMPERATURE": "0.8"}):
            self.loader._pyproject_config = {"temperature": 0.7}

            # CLI value should win
            value = self.loader.get_value("temperature", cli_value=0.9)
            assert value == 0.9

    def test_env_var_precedence(self):
        """Test that environment variables override pyproject.toml and defaults."""
        self.loader._pyproject_config = {"temperature": 0.7}

        with patch.dict(os.environ, {"GEMINI_TEMPERATURE": "0.8"}):
            value = self.loader.get_value("temperature")
            assert value == 0.8

    def test_pyproject_precedence(self):
        """Test that pyproject.toml overrides defaults."""
        self.loader._pyproject_config = {"temperature": 0.7}

        value = self.loader.get_value("temperature")
        assert value == 0.7

    def test_env_var_boolean_conversion(self):
        """Test boolean environment variable conversion."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
            ("off", False),
        ]

        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"GEMINI_ENABLE_CACHE": env_value}):
                value = self.loader.get_value("enable_cache")
                assert value == expected, f"Failed for {env_value}"

    def test_env_var_numeric_conversion(self):
        """Test numeric environment variable conversion."""
        with patch.dict(os.environ, {"GEMINI_TEMPERATURE": "0.75"}):
            value = self.loader.get_value("temperature")
            assert value == 0.75
            assert isinstance(value, float)

        with patch.dict(os.environ, {"GEMINI_CACHE_TTL": "1800"}):
            value = self.loader.get_value("cache_ttl_seconds")
            assert value == 1800
            assert isinstance(value, int)

    def test_env_var_string_passthrough(self):
        """Test that non-numeric strings are passed through."""
        with patch.dict(os.environ, {"GEMINI_DEFAULT_PROMPT": "Custom prompt"}):
            value = self.loader.get_value("default_prompt")
            assert value == "Custom prompt"

    @patch("src.config.loader.Path.exists")
    @patch("builtins.open", create=True)
    @patch("src.config.loader.tomllib.load")
    def test_load_pyproject_config(self, mock_toml_load, mock_open, mock_exists):
        """Test loading configuration from pyproject.toml."""
        mock_exists.return_value = True
        mock_toml_load.return_value = {
            "tool": {"gemini": {"temperature": 0.7, "enable_cache": False}}
        }

        config = self.loader.load_pyproject_config()
        assert config == {"temperature": 0.7, "enable_cache": False}
        mock_open.assert_called_once()

    @patch("src.config.loader.Path.exists")
    def test_load_pyproject_config_not_exists(self, mock_exists):
        """Test behavior when pyproject.toml doesn't exist."""
        mock_exists.return_value = False

        config = self.loader.load_pyproject_config()
        assert config == {}

    @patch("src.config.loader.Path.exists")
    @patch("builtins.open", side_effect=IOError("File not found"))
    def test_load_pyproject_config_error(self, mock_open, mock_exists):
        """Test error handling when loading pyproject.toml fails."""
        mock_exists.return_value = True

        with pytest.raises(ConfigurationError, match="Failed to load pyproject.toml"):
            self.loader.load_pyproject_config()

    def test_deprecation_warning_model_config(self):
        """Test that deprecation warning is shown for model_config.json."""
        with patch("src.config.loader.Path.exists") as mock_exists:
            mock_exists.return_value = True

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                self.loader.check_deprecated_config()

                assert len(w) == 1
                assert issubclass(w[0].category, DeprecationWarning)
                assert "model_config.json is deprecated" in str(w[0].message)
                assert "v0.22.0" in str(w[0].message)

    def test_deprecation_warning_only_once(self):
        """Test that deprecation warning is only shown once."""
        with patch("src.config.loader.Path.exists") as mock_exists:
            mock_exists.return_value = True

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                self.loader.check_deprecated_config()
                self.loader.check_deprecated_config()  # Second call

                # Should only warn once
                assert len(w) == 1

    def test_load_config_complete(self):
        """Test complete configuration loading with all sources."""
        # Setup pyproject config
        self.loader._pyproject_config = {
            "temperature": 0.7,
            "enable_cache": False,
            "custom_field": "from_pyproject",
        }

        # Setup environment
        with patch.dict(
            os.environ,
            {"GEMINI_TEMPERATURE": "0.8", "GEMINI_INCLUDE_CLAUDE_MEMORY": "true"},
        ):
            # Load config with some CLI args
            config = self.loader.load_config(
                temperature=0.9,  # CLI wins
                default_model="gpt-4",  # CLI only
                include_cursor_rules=True,  # CLI only
            )

            # Check precedence
            assert config["temperature"] == 0.9  # CLI wins
            assert config["include_claude_memory"] is True  # ENV wins over default
            assert config["enable_cache"] is False  # pyproject wins over default
            assert config["custom_field"] == "from_pyproject"  # From pyproject
            assert config["default_model"] == "gpt-4"  # CLI only
            assert config["include_cursor_rules"] is True  # CLI only
            assert config["cache_ttl_seconds"] == 900  # Default

    def test_load_config_calls_deprecation_check(self):
        """Test that load_config checks for deprecated config."""
        with patch.object(self.loader, "check_deprecated_config") as mock_check:
            self.loader.load_config()
            mock_check.assert_called_once()

    def test_create_code_review_config(self):
        """Test creating CodeReviewConfig from loaded configuration."""
        with patch.object(self.loader, "load_config") as mock_load:
            mock_load.return_value = {
                "project_path": "/test/path",
                "phase": "1.0",
                "scope": "specific_phase",
                "temperature": 0.7,
                "enable_gemini_review": True,
                "include_claude_memory": True,
                "default_prompt": "Test prompt",
            }

            config = self.loader.create_code_review_config(
                project_path="/test/path", phase="1.0"
            )

            assert isinstance(config, CodeReviewConfig)
            assert config.project_path == "/test/path"
            assert config.phase == "1.0"
            assert config.scope == "specific_phase"
            assert config.temperature == 0.7
            assert config.enable_gemini_review is True
            assert config.include_claude_memory is True
            assert config.default_prompt == "Test prompt"

    def test_all_env_mappings_covered(self):
        """Test that all environment variable mappings work correctly."""
        test_values = {
            "GEMINI_TEMPERATURE": "0.9",
            "GEMINI_DEFAULT_PROMPT": "Custom prompt",
            "GEMINI_MODEL": "gemini-pro",
            "GEMINI_INCLUDE_CLAUDE_MEMORY": "true",
            "GEMINI_INCLUDE_CURSOR_RULES": "false",
            "GEMINI_ENABLE_CACHE": "false",
            "GEMINI_CACHE_TTL": "1200",
        }

        expected_values = {
            "temperature": 0.9,
            "default_prompt": "Custom prompt",
            "default_model": "gemini-pro",
            "include_claude_memory": True,
            "include_cursor_rules": False,
            "enable_cache": False,
            "cache_ttl_seconds": 1200,
        }

        with patch.dict(os.environ, test_values):
            for key, expected in expected_values.items():
                value = self.loader.get_value(key)
                assert value == expected, f"Failed for {key}"


class TestGlobalConfigurationLoader:
    def test_get_configuration_loader_singleton(self):
        """Test that get_configuration_loader returns the same instance."""
        loader1 = get_configuration_loader()
        loader2 = get_configuration_loader()
        assert loader1 is loader2

    def test_get_configuration_loader_new_path(self):
        """Test that providing a new path creates a new loader."""
        loader1 = get_configuration_loader(Path("/path1"))
        loader2 = get_configuration_loader(Path("/path2"))
        assert loader1 is not loader2
        assert loader1.project_path == Path("/path1")
        assert loader2.project_path == Path("/path2")

    def test_get_configuration_loader_same_path(self):
        """Test that providing the same path returns the same loader."""
        path = Path("/test/path")
        loader1 = get_configuration_loader(path)
        loader2 = get_configuration_loader(path)
        assert loader1 is loader2
