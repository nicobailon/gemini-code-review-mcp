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
from typing import Dict, List, Optional, Union

try:
    import tomllib
except ImportError:
    # Python < 3.11
    import tomli as tomllib  # type: ignore[import-not-found,no-redef]

from ..config_types import CodeReviewConfig
from ..errors import ConfigurationError

# Type for configuration values
ConfigValue = Union[str, int, float, bool, None]

# Built-in defaults with specific types
DEFAULT_TEMPERATURE: float = 0.5
DEFAULT_PROMPT: str = "Conduct a comprehensive code review focusing on code quality, best practices, security, performance, and testing coverage."
DEFAULT_MODEL: str = "gemini-1.5-flash"
DEFAULT_INCLUDE_CLAUDE_MEMORY: bool = True
DEFAULT_INCLUDE_CURSOR_RULES: bool = False
DEFAULT_ENABLE_CACHE: bool = True
DEFAULT_CACHE_TTL_SECONDS: int = 900

# Defaults dictionary for lookup
DEFAULTS: Dict[str, ConfigValue] = {
    "temperature": DEFAULT_TEMPERATURE,
    "default_prompt": DEFAULT_PROMPT,
    "default_model": DEFAULT_MODEL,
    "include_claude_memory": DEFAULT_INCLUDE_CLAUDE_MEMORY,
    "include_cursor_rules": DEFAULT_INCLUDE_CURSOR_RULES,
    "enable_cache": DEFAULT_ENABLE_CACHE,
    "cache_ttl_seconds": DEFAULT_CACHE_TTL_SECONDS,
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
        self._pyproject_config: Optional[Dict[str, ConfigValue]] = None
        self._model_config_warned = False

    def load_pyproject_config(self) -> Dict[str, ConfigValue]:
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
                if not isinstance(data, dict):
                    self._pyproject_config = {}
                    return self._pyproject_config
                    
                tool_section = data.get("tool", {})
                if isinstance(tool_section, dict):
                    gemini_section = tool_section.get("gemini", {})
                    if isinstance(gemini_section, dict):
                        # Validate and convert values to our ConfigValue type
                        validated_config: Dict[str, ConfigValue] = {}
                        for k, v in gemini_section.items():
                            if isinstance(k, str) and (isinstance(v, (str, int, float, bool)) or v is None):
                                validated_config[k] = v
                        self._pyproject_config = validated_config
                    else:
                        self._pyproject_config = {}
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

    def get_value(self, key: str, cli_value: Optional[ConfigValue] = None) -> Optional[ConfigValue]:
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

    def load_config(self, **cli_args: Union[str, int, float, bool, None]) -> Dict[str, ConfigValue]:
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
        config: Dict[str, ConfigValue] = {}

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

    def create_code_review_config(self, **cli_args: Union[str, int, float, bool, None]) -> CodeReviewConfig:
        """
        Create a CodeReviewConfig instance with loaded configuration.

        Args:
            **cli_args: Command-line arguments

        Returns:
            CodeReviewConfig instance
        """
        config_dict = self.load_config(**cli_args)

        # Helper function to safely get string values
        def get_str(key: str, default: Optional[str] = None) -> Optional[str]:
            val = config_dict.get(key, default)
            return str(val) if val is not None and val != default else default
            
        # Helper function to safely get bool values
        def get_bool(key: str, default: bool) -> bool:
            val = config_dict.get(key, default)
            return bool(val) if isinstance(val, bool) else default
            
        # Helper function to safely get float values
        def get_float(key: str, default: float) -> float:
            val = config_dict.get(key, default)
            if isinstance(val, (int, float)):
                return float(val)
            return default
            
        # Helper function to safely get int values
        def get_int(key: str, default: Optional[int] = None) -> Optional[int]:
            val = config_dict.get(key, default)
            if val is not None and isinstance(val, (int, float)):
                return int(val)
            return default

        # Map to CodeReviewConfig fields with proper type conversion
        return CodeReviewConfig(
            project_path=get_str("project_path"),
            phase=get_str("phase"),
            output=get_str("output"),
            enable_gemini_review=get_bool("enable_gemini_review", True),
            scope=get_str("scope", "recent_phase") or "recent_phase",
            phase_number=get_str("phase_number"),
            task_number=get_str("task_number"),
            temperature=get_float("temperature", DEFAULT_TEMPERATURE),
            task_list=get_str("task_list"),
            default_prompt=get_str(
                "default_prompt", DEFAULT_PROMPT
            ),
            compare_branch=get_str("compare_branch"),
            target_branch=get_str("target_branch"),
            github_pr_url=get_str("github_pr_url"),
            include_claude_memory=get_bool(
                "include_claude_memory", DEFAULT_INCLUDE_CLAUDE_MEMORY
            ),
            include_cursor_rules=get_bool(
                "include_cursor_rules", DEFAULT_INCLUDE_CURSOR_RULES
            ),
            raw_context_only=get_bool("raw_context_only", False),
            auto_prompt_content=get_str("auto_prompt_content"),
            thinking_budget=get_int("thinking_budget"),
            url_context=self._get_url_context(config_dict),
        )

    def _get_url_context(self, config_dict: Dict[str, ConfigValue]) -> Optional[Union[str, List[str]]]:
        """Get url_context which can be string or list of strings."""
        val = config_dict.get("url_context")
        if val is None:
            return None
        if isinstance(val, str):
            return val
        if isinstance(val, list) and all(isinstance(item, str) for item in val):
            return [str(item) for item in val]
        return None


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
