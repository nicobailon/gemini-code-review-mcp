"""
Configuration loader with precedence handling.

This module implements configuration loading with the following precedence:
1. CLI flags (highest priority)
2. Environment variables
3. pyproject.toml [tool.gemini] section
4. Built-in defaults (lowest priority)
"""

import os
import warnings
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib
except ImportError:
    # Python < 3.11
    import tomli as tomllib  # type: ignore[import-not-found,no-redef]

from ..config_types import CodeReviewConfig
from ..errors import ConfigurationError

# Built-in defaults
DEFAULTS = {
    "temperature": 0.5,
    "default_prompt": "Conduct a comprehensive code review focusing on code quality, best practices, security, performance, and testing coverage.",
    "default_model": "gemini-1.5-flash",
    "include_claude_memory": True,
    "include_cursor_rules": False,
    "enable_cache": True,
    "cache_ttl_seconds": 900,
}

# Environment variable mappings
ENV_MAPPINGS = {
    "GEMINI_TEMPERATURE": "temperature",
    "GEMINI_DEFAULT_PROMPT": "default_prompt",
    "GEMINI_MODEL": "default_model",
    "GEMINI_INCLUDE_CLAUDE_MEMORY": "include_claude_memory",
    "GEMINI_INCLUDE_CURSOR_RULES": "include_cursor_rules",
    "GEMINI_ENABLE_CACHE": "enable_cache",
    "GEMINI_CACHE_TTL": "cache_ttl_seconds",
}


class ConfigurationLoader:
    """Loads configuration with proper precedence handling."""

    def __init__(self, project_path: Optional[Path] = None):
        """
        Initialize the configuration loader.

        Args:
            project_path: Path to the project root. If None, uses current directory.
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self._pyproject_config: Optional[Dict[str, Any]] = None
        self._model_config_warned = False

    def load_pyproject_config(self) -> Dict[str, Any]:
        """Load configuration from pyproject.toml."""
        if self._pyproject_config is not None:
            return self._pyproject_config

        pyproject_path = self.project_path / "pyproject.toml"
        if not pyproject_path.exists():
            self._pyproject_config = {}
            return self._pyproject_config

        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                tool_section = data.get("tool") if isinstance(data, dict) else None
                if tool_section and isinstance(tool_section, dict):
                    gemini_section = tool_section.get("gemini")
                    self._pyproject_config = gemini_section if isinstance(gemini_section, dict) else {}
                else:
                    self._pyproject_config = {}
                return self._pyproject_config
        except Exception as e:
            raise ConfigurationError(f"Failed to load pyproject.toml: {e}")

    def check_deprecated_config(self) -> None:
        """Check for deprecated model_config.json and warn if found."""
        if self._model_config_warned:
            return

        model_config_path = self.project_path / "model_config.json"
        if model_config_path.exists():
            warnings.warn(
                "model_config.json is deprecated and will be removed in v0.22.0. "
                "Please migrate your configuration to pyproject.toml [tool.gemini] section.",
                DeprecationWarning,
                stacklevel=2,
            )
            self._model_config_warned = True

    def get_value(self, key: str, cli_value: Optional[Any] = None) -> Any:
        """
        Get a configuration value with proper precedence.

        Args:
            key: Configuration key
            cli_value: Value from CLI (highest priority)

        Returns:
            Configuration value
        """
        # 1. CLI flag (highest priority)
        if cli_value is not None:
            return cli_value

        # 2. Environment variable
        env_key = None
        for env_var, config_key in ENV_MAPPINGS.items():
            if config_key == key:
                env_key = env_var
                break

        if env_key and env_key in os.environ:
            value = os.environ[env_key]
            # Convert boolean strings
            if value.lower() in ("true", "1", "yes", "on"):
                return True
            elif value.lower() in ("false", "0", "no", "off"):
                return False
            # Try to convert numbers
            try:
                if "." in value:
                    return float(value)
                return int(value)
            except ValueError:
                return value

        # 3. pyproject.toml
        pyproject_config = self.load_pyproject_config()
        if key in pyproject_config:
            return pyproject_config[key]

        # 4. Built-in defaults (lowest priority)
        return DEFAULTS.get(key)

    def load_config(self, **cli_args: Any) -> Dict[str, Any]:
        """
        Load complete configuration with precedence handling.

        Args:
            **cli_args: Command-line arguments

        Returns:
            Dictionary of configuration values
        """
        # Check for deprecated config
        self.check_deprecated_config()

        # Build config dict
        config = {}

        # Get all possible keys
        all_keys = set(DEFAULTS.keys())
        all_keys.update(self.load_pyproject_config().keys())
        all_keys.update(ENV_MAPPINGS.values())

        # Load each value with precedence
        for key in all_keys:
            cli_value = cli_args.get(key)
            config[key] = self.get_value(key, cli_value)

        # Also include CLI-only args that don't have defaults
        for key, value in cli_args.items():
            if key not in config and value is not None:
                config[key] = value

        return config

    def create_code_review_config(self, **cli_args: Any) -> CodeReviewConfig:
        """
        Create a CodeReviewConfig instance with loaded configuration.

        Args:
            **cli_args: Command-line arguments

        Returns:
            CodeReviewConfig instance
        """
        config_dict = self.load_config(**cli_args)

        # Map to CodeReviewConfig fields
        return CodeReviewConfig(
            project_path=config_dict.get("project_path"),
            phase=config_dict.get("phase"),
            output=config_dict.get("output"),
            enable_gemini_review=config_dict.get("enable_gemini_review", True),
            scope=config_dict.get("scope", "recent_phase"),
            phase_number=config_dict.get("phase_number"),
            task_number=config_dict.get("task_number"),
            temperature=config_dict.get("temperature", DEFAULTS["temperature"]),
            task_list=config_dict.get("task_list"),
            default_prompt=config_dict.get(
                "default_prompt", DEFAULTS["default_prompt"]
            ),
            compare_branch=config_dict.get("compare_branch"),
            target_branch=config_dict.get("target_branch"),
            github_pr_url=config_dict.get("github_pr_url"),
            include_claude_memory=config_dict.get(
                "include_claude_memory", DEFAULTS["include_claude_memory"]
            ),
            include_cursor_rules=config_dict.get(
                "include_cursor_rules", DEFAULTS["include_cursor_rules"]
            ),
            raw_context_only=config_dict.get("raw_context_only", False),
            auto_prompt_content=config_dict.get("auto_prompt_content"),
            thinking_budget=config_dict.get("thinking_budget"),
            url_context=config_dict.get("url_context"),
        )


# Global instance
_loader: Optional[ConfigurationLoader] = None


def get_configuration_loader(
    project_path: Optional[Path] = None,
) -> ConfigurationLoader:
    """Get or create the global configuration loader."""
    global _loader
    if _loader is None or (project_path and _loader.project_path != project_path):
        _loader = ConfigurationLoader(project_path)
    return _loader
