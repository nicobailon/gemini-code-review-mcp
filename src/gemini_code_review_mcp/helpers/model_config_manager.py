#!/usr/bin/env python3
"""
Model configuration and meta-prompt template management module.

This module centralizes all logic related to loading, validating, and managing
model configurations and meta-prompt templates.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, cast

logger = logging.getLogger(__name__)


def load_model_config() -> Dict[str, Any]:
    """Load model configuration from JSON file with fallback defaults."""
    config_path = os.path.join(os.path.dirname(__file__), "model_config.json")

    # Default configuration as fallback
    default_config = {
        "model_aliases": {
            "gemini-2.5-pro": "gemini-2.5-flash-preview-05-20",
            "gemini-2.5-flash": "gemini-2.5-flash-preview-05-20",
        },
        "model_capabilities": {
            "url_context_supported": [
                "gemini-2.5-flash-preview-05-20",
                "gemini-2.0-flash",
                "gemini-2.0-flash-live-001",
                "gemini-2.5-flash",
            ],
            "thinking_mode_supported": [
                "gemini-2.5-flash-preview-05-20",
            ],
        },
        "defaults": {
            "model": "gemini-2.0-flash",
            "default_model": "gemini-1.5-flash",  # Add default_model key
            "summary_model": "gemini-2.0-flash-lite",
            "default_prompt": "Generate comprehensive code review for recent development changes focusing on code quality, security, performance, and best practices.",
        },
    }

    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
        else:
            logger.warning(
                f"Model config file not found at {config_path}, using defaults"
            )
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load model config: {e}, using defaults")

    return default_config


def load_meta_prompt_templates(
    config_path: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Load meta-prompt templates from model_config.json with robust error handling.

    Args:
        config_path: Optional path to config file (defaults to model_config.json)

    Returns:
        Dictionary of validated meta-prompt templates

    Raises:
        ValueError: If config file is invalid or templates fail validation
        FileNotFoundError: If specified config file doesn't exist
    """
    try:
        if config_path is None:
            config = load_model_config()
        else:
            # Validate config file exists and is readable
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file not found: {config_path}")

            if not os.access(config_path, os.R_OK):
                raise PermissionError(f"Config file not readable: {config_path}")

            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config: Any = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in config file {config_path}: {e}")
            except UnicodeDecodeError as e:
                raise ValueError(f"Config file encoding error {config_path}: {e}")
            except IOError as e:
                raise ValueError(f"Failed to read config file {config_path}: {e}")

        # Validate config structure
        if not isinstance(config, dict):
            raise ValueError("Config file must contain a JSON object")

        # Get meta_prompt_templates section, fallback to empty dict
        config_dict = cast(Dict[str, Any], config)
        templates: Dict[str, Any] = config_dict.get("meta_prompt_templates", {})

        # Validate each template with detailed error reporting
        validation_errors: List[str] = []
        for template_name, template_data in templates.items():
            try:
                validation_result = validate_meta_prompt_template(template_data)
                if not validation_result["valid"]:
                    validation_errors.append(
                        f"Template '{template_name}': {', '.join(validation_result['errors'])}"
                    )
            except Exception as e:
                validation_errors.append(
                    f"Template '{template_name}': Validation failed - {e}"
                )

        if validation_errors:
            raise ValueError(
                "Template validation failed:\n- " + "\n- ".join(validation_errors)
            )

        return templates

    except Exception as e:
        # Log the error for debugging while preserving the original exception
        logger.warning(f"Failed to load meta-prompt templates: {e}")
        raise


def validate_meta_prompt_template(template: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate meta-prompt template structure and content with comprehensive edge case handling.

    Args:
        template: Template dictionary to validate

    Returns:
        Dictionary with 'valid', 'errors', and 'placeholders' keys
    """
    errors: List[str] = []

    # Handle None or non-dict input
    if template is None:
        errors.append("Template cannot be None")
        return {"valid": False, "errors": errors, "placeholders": []}

    # At this point template is guaranteed to be a dict by type annotation

    # Check required fields with proper None handling
    required_fields = ["name", "template"]
    for field in required_fields:
        if field not in template:
            errors.append(f"Missing required field: {field}")
        elif template[field] is None:
            errors.append(f"Field '{field}' cannot be None")
        elif isinstance(template[field], str) and not template[field].strip():
            errors.append(f"Field '{field}' cannot be empty or whitespace-only")
        elif not template[field]:  # handles empty containers
            errors.append(f"Field '{field}' cannot be empty")

    # Validate name field with edge cases
    if "name" in template and template["name"] is not None:
        if not isinstance(template["name"], str):
            errors.append("Field 'name' must be a string")
        elif len(template["name"].strip()) == 0:
            errors.append("Template name cannot be empty or whitespace-only")
        elif len(template["name"]) > 100:
            errors.append("Template name is too long (maximum 100 characters)")

    # Validate template field with comprehensive checks
    if "template" in template and template["template"] is not None:
        if not isinstance(template["template"], str):
            errors.append("Field 'template' must be a string")
        else:
            template_content = template["template"].strip()
            if len(template_content) == 0:
                errors.append("Template content cannot be empty or whitespace-only")
            elif len(template_content) < 50:
                errors.append("Template content is too short (minimum 50 characters)")
            elif len(template_content) > 10000:
                errors.append(
                    "Template content is too long (maximum 10,000 characters)"
                )

    # Validate focus_areas with edge case handling
    if "focus_areas" in template:
        focus_areas = template["focus_areas"]
        if focus_areas is None:
            errors.append("Field 'focus_areas' cannot be None")
        elif not isinstance(focus_areas, list):
            errors.append("Field 'focus_areas' must be a list")
        else:
            # Cast to List[Any] since we've confirmed it's a list
            focus_areas_list = cast(List[Any], focus_areas)
            if len(focus_areas_list) == 0:
                errors.append("Field 'focus_areas' cannot be empty")
            else:
                # Validate each focus area
                for i, area in enumerate(focus_areas_list):
                    if not isinstance(area, str):
                        errors.append(f"Focus area {i} must be a string")
                    elif not area.strip():
                        errors.append(
                            f"Focus area {i} cannot be empty or whitespace-only"
                        )

    # Validate output_format with edge cases
    if "output_format" in template:
        output_format = template["output_format"]
        if output_format is not None and not isinstance(output_format, str):
            errors.append("Field 'output_format' must be a string")
        elif isinstance(output_format, str) and not output_format.strip():
            errors.append("Field 'output_format' cannot be empty or whitespace-only")

    # Check for placeholder variables with error handling
    placeholders: List[str] = []
    if "template" in template and isinstance(template["template"], str):
        try:
            placeholders = re.findall(r"\{(\w+)\}", template["template"])
            # Remove duplicates while preserving order
            placeholders = list(dict.fromkeys(placeholders))
        except Exception as e:
            errors.append(f"Failed to parse template placeholders: {e}")

    result = {"valid": len(errors) == 0, "errors": errors, "placeholders": placeholders}

    return result


def get_meta_prompt_template(
    template_name: str, config_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Get a specific meta-prompt template by name."""
    try:
        templates = load_meta_prompt_templates(config_path)
        return templates.get(template_name)
    except Exception:
        return None


def list_meta_prompt_templates(config_path: Optional[str] = None) -> List[str]:
    """List all available meta-prompt template names."""
    try:
        templates = load_meta_prompt_templates(config_path)
        return list(templates.keys())
    except Exception:
        return []


def load_meta_prompt_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load meta-prompt configuration section from model_config.json."""
    if config_path is None:
        config = load_model_config()
    else:
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise ValueError(f"Failed to load config from {config_path}: {e}")

    # Default meta-prompt config
    default_meta_config = {
        "default_template": "default",
        "max_context_size": 100000,
        "analysis_depth": "comprehensive",
        "include_examples": True,
        "technology_specific": True,
    }

    # Get meta_prompt_config section, merge with defaults
    meta_config = config.get("meta_prompt_config", {})
    for key, value in default_meta_config.items():
        if key not in meta_config:
            meta_config[key] = value

    return meta_config


def validate_meta_prompt_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate meta-prompt configuration."""
    errors: List[str] = []

    # Validate analysis_depth
    if "analysis_depth" in config:
        valid_depths = ["basic", "comprehensive", "advanced"]
        if config["analysis_depth"] not in valid_depths:
            errors.append(f"analysis_depth must be one of {valid_depths}")

    # Validate max_context_size
    if "max_context_size" in config:
        if (
            not isinstance(config["max_context_size"], int)
            or config["max_context_size"] <= 0
        ):
            errors.append("max_context_size must be a positive integer")

    # Validate boolean fields
    bool_fields = ["include_examples", "technology_specific"]
    for field in bool_fields:
        if field in config and not isinstance(config[field], bool):
            errors.append(f"Field '{field}' must be a boolean")

    return {"valid": len(errors) == 0, "errors": errors}


def merge_template_overrides(
    base_templates: Dict[str, Dict[str, Any]], config_path: str
) -> Dict[str, Dict[str, Any]]:
    """Merge template overrides from config file with base templates."""
    try:
        with open(config_path, "r") as f:
            override_config = json.load(f)
    except (json.JSONDecodeError, IOError):
        return base_templates

    override_templates = override_config.get("meta_prompt_templates", {})
    merged_templates = base_templates.copy()

    for template_name, override_data in override_templates.items():
        if template_name in merged_templates:
            # Merge override with base template
            merged_template = merged_templates[template_name].copy()
            merged_template.update(override_data)
            merged_templates[template_name] = merged_template
        else:
            # Add new template
            merged_templates[template_name] = override_data

    return merged_templates


def load_meta_prompt_templates_from_env() -> Dict[str, Dict[str, Any]]:
    """Load meta-prompt templates from environment variable path."""
    env_config_path = os.getenv("META_PROMPT_CONFIG_PATH")
    if env_config_path and os.path.exists(env_config_path):
        return load_meta_prompt_templates(env_config_path)
    else:
        return load_meta_prompt_templates()


def load_meta_prompt_with_precedence(
    config_path: Optional[str] = None, cli_overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Dict[str, Any]]:
    """Load meta-prompt templates with precedence: CLI > Environment > Config File > Defaults."""
    # Start with base config
    templates = load_meta_prompt_templates(config_path)

    # Apply environment overrides
    env_config_path = os.getenv("META_PROMPT_CONFIG_PATH")
    if env_config_path and os.path.exists(env_config_path):
        env_templates = load_meta_prompt_templates(env_config_path)
        templates.update(env_templates)

    # Apply CLI overrides (highest precedence)
    if cli_overrides:
        for template_name, override_data in cli_overrides.items():
            if template_name in templates:
                templates[template_name].update(override_data)
            else:
                templates[template_name] = override_data

    return templates


def get_default_meta_prompt_template(
    config_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Get the default meta-prompt template based on configuration."""
    meta_config = load_meta_prompt_config(config_path)
    default_template_name = meta_config.get("default_template", "default")

    template = get_meta_prompt_template(default_template_name, config_path)
    if template is None:
        # Fallback to 'default' template if specified default doesn't exist
        template = get_meta_prompt_template("default", config_path)

    # If still None, return a basic fallback template
    if template is None:
        return {
            "name": "fallback",
            "description": "Basic fallback template",
            "template": "Please review the following code:\n\n{context}",
        }

    return template


def analyze_project_completion_status(task_list_content: str) -> Dict[str, Any]:
    """Analyze project completion status from task list content."""
    lines = task_list_content.split("\n")

    completed_phases: List[str] = []
    current_phase = None
    next_priorities: List[str] = []
    total_tasks = 0
    completed_tasks = 0

    # Parse task list for completion status
    for line in lines:
        line = line.strip()

        # Look for main phase tasks (e.g., "- [x] 1.0 Authentication System")
        if re.match(r"- \[(x| )\] (\d+\.\d+)", line):
            total_tasks += 1
            if "[x]" in line:
                completed_tasks += 1
                # Extract phase number
                phase_match = re.search(r"(\d+\.\d+)", line)
                if phase_match:
                    completed_phases.append(phase_match.group(1))
            else:
                # This is an incomplete phase
                if current_phase is None:
                    phase_match = re.search(r"(\d+\.\d+)", line)
                    if phase_match:
                        current_phase = phase_match.group(1)
                        # Extract priority from phase name
                        if "security" in line.lower():
                            next_priorities.append("security")
                        if "performance" in line.lower():
                            next_priorities.append("performance")
                        if "testing" in line.lower():
                            next_priorities.append("testing")

    completion_percentage = (
        (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    )

    return {
        "completed_phases": completed_phases,
        "current_phase": current_phase,
        "next_priorities": next_priorities,
        "completion_percentage": completion_percentage,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
    }


def validate_meta_prompt_config_file(config_path: str) -> Dict[str, Any]:
    """Validate entire meta-prompt configuration file."""
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        return {"valid": False, "errors": [f"Invalid JSON: {e}"]}
    except IOError as e:
        return {"valid": False, "errors": [f"File error: {e}"]}

    errors: List[str] = []

    # Validate templates section
    if "meta_prompt_templates" in config:
        templates = config["meta_prompt_templates"]
        for template_name, template_data in templates.items():
            validation_result = validate_meta_prompt_template(template_data)
            if not validation_result["valid"]:
                errors.extend(
                    [
                        f"Template {template_name}: {error}"
                        for error in validation_result["errors"]
                    ]
                )

    # Validate config section
    if "meta_prompt_config" in config:
        config_validation = validate_meta_prompt_config(config["meta_prompt_config"])
        if not config_validation["valid"]:
            errors.extend(config_validation["errors"])

    return {"valid": len(errors) == 0, "errors": errors}


def load_meta_prompt_templates_with_fallback(
    config_path: str,
) -> Dict[str, Dict[str, Any]]:
    """Load meta-prompt templates with fallback to defaults on error."""
    try:
        return load_meta_prompt_templates(config_path)
    except Exception:
        # Fallback to default templates
        return load_meta_prompt_templates()
