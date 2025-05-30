"""
Test configurable meta-prompt templates in model_config.json.
Following TDD Protocol: Testing template loading, validation, and override functionality.
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
from typing import Dict, Any, List, Optional

# Setup import path for tests
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMetaPromptTemplateLoading:
    """Test loading meta-prompt templates from model_config.json."""
    
    def test_load_default_meta_prompt_templates(self):
        """Test loading default meta-prompt templates from model_config.json."""
        # Expected default templates structure
        expected_templates = {
            "default": {
                "name": "Comprehensive Code Review Meta-Prompt",
                "template": str,  # Should be a string
                "focus_areas": list,  # Should be a list
                "output_format": str
            },
            "security_focused": {
                "name": "Security-First Code Review Meta-Prompt",
                "template": str,
                "focus_areas": list,
                "output_format": str
            },
            "performance_focused": {
                "name": "Performance-Optimized Code Review Meta-Prompt", 
                "template": str,
                "focus_areas": list,
                "output_format": str
            }
        }
        
        # Import function that should exist
        from src.generate_code_review_context import load_meta_prompt_templates
        
        templates = load_meta_prompt_templates()
        
        # Verify structure
        assert isinstance(templates, dict)
        assert "default" in templates
        assert "security_focused" in templates
        assert "performance_focused" in templates
        
        # Verify each template has required fields
        for template_name, template_data in templates.items():
            assert "name" in template_data
            assert "template" in template_data
            assert "focus_areas" in template_data
            assert "output_format" in template_data
            
            assert isinstance(template_data["name"], str)
            assert isinstance(template_data["template"], str)
            assert isinstance(template_data["focus_areas"], list)
            assert isinstance(template_data["output_format"], str)
            
            # Template should not be empty
            assert len(template_data["template"]) > 100
            assert len(template_data["focus_areas"]) > 0
    
    def test_meta_prompt_template_content_quality(self):
        """Test that meta-prompt templates contain high-quality content."""
        from src.generate_code_review_context import load_meta_prompt_templates
        
        templates = load_meta_prompt_templates()
        
        # Test default template quality
        default_template = templates["default"]["template"]
        
        # Should contain meta-prompt engineering keywords
        meta_keywords = ["analyze", "generate", "prompt", "code review", "patterns"]
        found_keywords = [kw for kw in meta_keywords if kw.lower() in default_template.lower()]
        assert len(found_keywords) >= 3, f"Default template should contain meta-prompt keywords, found: {found_keywords}"
        
        # Should contain analysis framework
        analysis_keywords = ["security", "performance", "architecture", "testing"]
        found_analysis = [kw for kw in analysis_keywords if kw.lower() in default_template.lower()]
        assert len(found_analysis) >= 3, f"Default template should contain analysis framework, found: {found_analysis}"
        
        # Should contain output instructions
        output_keywords = ["output", "format", "structure", "generate"]
        found_output = [kw for kw in output_keywords if kw.lower() in default_template.lower()]
        assert len(found_output) >= 2, f"Default template should contain output instructions, found: {found_output}"
    
    def test_security_focused_template_specificity(self):
        """Test that security-focused template is specifically tailored for security analysis."""
        from src.generate_code_review_context import load_meta_prompt_templates
        
        templates = load_meta_prompt_templates()
        security_template = templates["security_focused"]
        
        # Should have security-specific focus areas
        security_focus_areas = security_template["focus_areas"]
        expected_security_areas = ["security", "input_validation", "authentication"]
        found_security_areas = [area for area in expected_security_areas if area in security_focus_areas]
        assert len(found_security_areas) >= 2, f"Security template should focus on security areas, found: {found_security_areas}"
        
        # Template content should emphasize security
        template_text = security_template["template"].lower()
        security_keywords = ["security", "vulnerability", "exploit", "validation", "authentication"]
        found_security_keywords = [kw for kw in security_keywords if kw in template_text]
        assert len(found_security_keywords) >= 3, f"Security template should emphasize security, found: {found_security_keywords}"
    
    def test_performance_focused_template_specificity(self):
        """Test that performance-focused template is specifically tailored for performance analysis."""
        from src.generate_code_review_context import load_meta_prompt_templates
        
        templates = load_meta_prompt_templates()
        performance_template = templates["performance_focused"]
        
        # Should have performance-specific focus areas
        performance_focus_areas = performance_template["focus_areas"]
        expected_performance_areas = ["performance", "scalability", "resource_usage"]
        found_performance_areas = [area for area in expected_performance_areas if area in performance_focus_areas]
        assert len(found_performance_areas) >= 2, f"Performance template should focus on performance areas, found: {found_performance_areas}"
        
        # Template content should emphasize performance
        template_text = performance_template["template"].lower()
        performance_keywords = ["performance", "scalability", "optimization", "efficiency", "resource"]
        found_performance_keywords = [kw for kw in performance_keywords if kw in template_text]
        assert len(found_performance_keywords) >= 3, f"Performance template should emphasize performance, found: {found_performance_keywords}"


class TestMetaPromptTemplateValidation:
    """Test validation of meta-prompt template structure and content."""
    
    def test_validate_meta_prompt_template_structure(self):
        """Test validation of individual meta-prompt template structure."""
        from src.generate_code_review_context import validate_meta_prompt_template
        
        # Valid template
        valid_template = {
            "name": "Test Meta-Prompt Template",
            "template": "You are an expert code reviewer analyzing {context} for {focus_areas}. Generate comprehensive meta-prompt.",
            "focus_areas": ["security", "performance", "maintainability"],
            "output_format": "structured_meta_prompt"
        }
        
        validation_result = validate_meta_prompt_template(valid_template)
        assert validation_result["valid"] is True
        assert len(validation_result["errors"]) == 0
        
        # Invalid template - missing required fields
        invalid_template = {
            "name": "Incomplete Template",
            "template": "Basic template"
            # Missing focus_areas and output_format
        }
        
        validation_result = validate_meta_prompt_template(invalid_template)
        assert validation_result["valid"] is False
        assert "focus_areas" in str(validation_result["errors"])
        assert "output_format" in str(validation_result["errors"])
        
        # Invalid template - empty template text
        empty_template = {
            "name": "Empty Template",
            "template": "",
            "focus_areas": ["security"],
            "output_format": "basic"
        }
        
        validation_result = validate_meta_prompt_template(empty_template)
        assert validation_result["valid"] is False
        assert "template cannot be empty" in str(validation_result["errors"]).lower()
    
    def test_validate_template_placeholder_variables(self):
        """Test validation of template placeholder variables."""
        from src.generate_code_review_context import validate_meta_prompt_template
        
        # Template with valid placeholders
        template_with_placeholders = {
            "name": "Template with Placeholders",
            "template": "Analyze {context} focusing on {focus_areas} and generate {output_format}",
            "focus_areas": ["security", "performance"],
            "output_format": "structured_meta_prompt"
        }
        
        validation_result = validate_meta_prompt_template(template_with_placeholders)
        assert validation_result["valid"] is True
        
        # Should identify placeholder variables
        assert "placeholders" in validation_result
        placeholders = validation_result["placeholders"]
        assert "context" in placeholders
        assert "focus_areas" in placeholders
        assert "output_format" in placeholders
    
    def test_template_focus_areas_validation(self):
        """Test validation of focus_areas field."""
        from src.generate_code_review_context import validate_meta_prompt_template
        
        # Valid focus areas
        valid_focus_areas = ["security", "performance", "architecture", "testing", "maintainability"]
        template = {
            "name": "Valid Focus Areas",
            "template": "Test template",
            "focus_areas": valid_focus_areas,
            "output_format": "structured"
        }
        
        validation_result = validate_meta_prompt_template(template)
        assert validation_result["valid"] is True
        
        # Invalid focus areas - not a list
        template["focus_areas"] = "security,performance"  # String instead of list
        validation_result = validate_meta_prompt_template(template)
        assert validation_result["valid"] is False
        assert "focus_areas must be a list" in str(validation_result["errors"]).lower()
        
        # Invalid focus areas - empty list
        template["focus_areas"] = []
        validation_result = validate_meta_prompt_template(template)
        assert validation_result["valid"] is False
        assert "focus_areas cannot be empty" in str(validation_result["errors"]).lower()


class TestMetaPromptTemplateOverrides:
    """Test override functionality for meta-prompt templates."""
    
    def test_load_custom_meta_prompt_template(self):
        """Test loading custom meta-prompt template from model_config.json."""
        # Create custom model config with additional templates
        custom_config = {
            "model_aliases": {"gemini-2.0-flash": "models/gemini-2.0-flash-exp"},
            "meta_prompt_templates": {
                "custom_template": {
                    "name": "Custom Project Meta-Prompt",
                    "template": "Custom template for project-specific analysis focusing on {focus_areas}",
                    "focus_areas": ["custom_area1", "custom_area2"],
                    "output_format": "custom_format"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_config, f)
            config_path = f.name
        
        try:
            from src.generate_code_review_context import load_meta_prompt_templates
            
            # Load templates from custom config
            templates = load_meta_prompt_templates(config_path)
            
            # Should contain custom template
            assert "custom_template" in templates
            custom_template = templates["custom_template"]
            
            assert custom_template["name"] == "Custom Project Meta-Prompt"
            assert "custom_area1" in custom_template["focus_areas"]
            assert "custom_area2" in custom_template["focus_areas"]
            assert custom_template["output_format"] == "custom_format"
            
        finally:
            os.unlink(config_path)
    
    def test_template_override_priority(self):
        """Test that custom templates override default templates."""
        # Custom config that overrides default template
        custom_config = {
            "meta_prompt_templates": {
                "default": {
                    "name": "Overridden Default Template",
                    "template": "This is a custom override of the default template",
                    "focus_areas": ["override_area"],
                    "output_format": "override_format"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_config, f)
            config_path = f.name
        
        try:
            from src.generate_code_review_context import load_meta_prompt_templates
            
            templates = load_meta_prompt_templates(config_path)
            
            # Default template should be overridden
            default_template = templates["default"]
            assert default_template["name"] == "Overridden Default Template"
            assert "override_area" in default_template["focus_areas"]
            assert default_template["output_format"] == "override_format"
            
        finally:
            os.unlink(config_path)
    
    def test_get_meta_prompt_template_by_name(self):
        """Test retrieving specific meta-prompt template by name."""
        from src.generate_code_review_context import get_meta_prompt_template
        
        # Get default template
        default_template = get_meta_prompt_template("default")
        assert default_template is not None
        assert default_template["name"] is not None
        assert len(default_template["template"]) > 50
        
        # Get security template
        security_template = get_meta_prompt_template("security_focused")
        assert security_template is not None
        assert "security" in security_template["name"].lower()
        
        # Get non-existent template
        non_existent = get_meta_prompt_template("non_existent_template")
        assert non_existent is None
    
    def test_list_available_meta_prompt_templates(self):
        """Test listing all available meta-prompt template names."""
        from src.generate_code_review_context import list_meta_prompt_templates
        
        available_templates = list_meta_prompt_templates()
        
        assert isinstance(available_templates, list)
        assert "default" in available_templates
        assert "security_focused" in available_templates
        assert "performance_focused" in available_templates
        assert len(available_templates) >= 3


class TestMetaPromptConfigIntegration:
    """Test integration of meta-prompt config with existing model config."""
    
    def test_load_meta_prompt_config_section(self):
        """Test loading meta_prompt_config section from model_config.json."""
        from src.generate_code_review_context import load_meta_prompt_config
        
        config = load_meta_prompt_config()
        
        # Should have configuration options
        assert isinstance(config, dict)
        assert "default_template" in config
        assert "max_context_size" in config
        assert "analysis_depth" in config
        assert "include_examples" in config
        assert "technology_specific" in config
        
        # Verify types and reasonable defaults
        assert isinstance(config["default_template"], str)
        assert isinstance(config["max_context_size"], int)
        assert config["max_context_size"] > 0
        assert isinstance(config["analysis_depth"], str)
        assert config["analysis_depth"] in ["basic", "comprehensive", "advanced"]
        assert isinstance(config["include_examples"], bool)
        assert isinstance(config["technology_specific"], bool)
    
    def test_meta_prompt_config_override(self):
        """Test overriding meta_prompt_config via custom model_config.json."""
        custom_config = {
            "meta_prompt_config": {
                "default_template": "security_focused",
                "max_context_size": 150000,
                "analysis_depth": "advanced",
                "include_examples": False,
                "technology_specific": True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_config, f)
            config_path = f.name
        
        try:
            from src.generate_code_review_context import load_meta_prompt_config
            
            config = load_meta_prompt_config(config_path)
            
            assert config["default_template"] == "security_focused"
            assert config["max_context_size"] == 150000
            assert config["analysis_depth"] == "advanced"
            assert config["include_examples"] is False
            assert config["technology_specific"] is True
            
        finally:
            os.unlink(config_path)
    
    def test_validate_meta_prompt_config(self):
        """Test validation of meta_prompt_config section."""
        from src.generate_code_review_context import validate_meta_prompt_config
        
        # Valid config
        valid_config = {
            "default_template": "default",
            "max_context_size": 100000,
            "analysis_depth": "comprehensive",
            "include_examples": True,
            "technology_specific": True
        }
        
        validation_result = validate_meta_prompt_config(valid_config)
        assert validation_result["valid"] is True
        assert len(validation_result["errors"]) == 0
        
        # Invalid config - invalid analysis_depth
        invalid_config = valid_config.copy()
        invalid_config["analysis_depth"] = "invalid_depth"
        
        validation_result = validate_meta_prompt_config(invalid_config)
        assert validation_result["valid"] is False
        assert "analysis_depth" in str(validation_result["errors"])
        
        # Invalid config - negative max_context_size
        invalid_config = valid_config.copy()
        invalid_config["max_context_size"] = -1000
        
        validation_result = validate_meta_prompt_config(invalid_config)
        assert validation_result["valid"] is False
        assert "max_context_size" in str(validation_result["errors"])


# Type validation tests to ensure proper typing
class TestMetaPromptTemplateTypes:
    """Test type safety for meta-prompt template functions."""
    
    def test_load_meta_prompt_templates_return_type(self):
        """Test that load_meta_prompt_templates returns correct type."""
        from src.generate_code_review_context import load_meta_prompt_templates
        
        templates = load_meta_prompt_templates()
        
        # Type assertions using inspect module since this is Python
        import inspect
        
        # Should return Dict[str, Dict[str, Any]]
        assert isinstance(templates, dict)
        for template_name, template_data in templates.items():
            assert isinstance(template_name, str)
            assert isinstance(template_data, dict)
    
    def test_validate_meta_prompt_template_return_type(self):
        """Test that validate_meta_prompt_template returns correct type."""
        from src.generate_code_review_context import validate_meta_prompt_template
        
        test_template = {
            "name": "Test",
            "template": "Test template",
            "focus_areas": ["test"],
            "output_format": "test"
        }
        
        result = validate_meta_prompt_template(test_template)
        
        # Should return Dict[str, Any] with specific structure
        assert isinstance(result, dict)
        assert "valid" in result
        assert isinstance(result["valid"], bool)
        assert "errors" in result
        assert isinstance(result["errors"], list)
    
    def test_get_meta_prompt_template_return_type(self):
        """Test that get_meta_prompt_template returns correct type."""
        from src.generate_code_review_context import get_meta_prompt_template
        
        # Valid template should return Dict[str, Any]
        template = get_meta_prompt_template("default")
        if template is not None:  # Optional return type
            assert isinstance(template, dict)
        
        # Invalid template should return None
        invalid_template = get_meta_prompt_template("non_existent")
        assert invalid_template is None