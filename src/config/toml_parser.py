"""Safe TOML parser wrapper to handle type issues with tomllib."""

from pathlib import Path
from typing import Dict, Optional, Union

try:
    import tomllib
except ImportError:
    # Python < 3.11
    import tomli as tomllib  # type: ignore[import-not-found]


# Define our config value types
ConfigValue = Union[str, int, float, bool, None]


def parse_pyproject_toml(file_path: Path) -> Optional[Dict[str, ConfigValue]]:
    """
    Parse pyproject.toml and extract gemini configuration.
    
    Returns None if file doesn't exist or doesn't contain gemini config.
    """
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, "rb") as f:
            # Parse TOML file - we handle the untyped nature here
            data = tomllib.load(f)
            
            # Validate it's a dictionary
            if not isinstance(data, dict):
                return None
            
            # Get tool section
            tool = data.get("tool")
            if not isinstance(tool, dict):
                return None
            
            # Get gemini section
            gemini = tool.get("gemini") 
            if not isinstance(gemini, dict):
                return None
            
            # Extract and validate config values
            result: Dict[str, ConfigValue] = {}
            for key in gemini:
                if isinstance(key, str):
                    value = gemini[key]
                    # Only keep values of our allowed types
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        result[key] = value
            
            return result
            
    except Exception:
        return None