#!/usr/bin/env python3
"""
Gemini API client module.

This module manages API key loading and encapsulates the core interaction logic
with the Gemini API, including advanced features like thinking mode and grounding.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import model configuration functions
try:
    from ..helpers.model_config_manager import load_model_config
except ImportError:
    from helpers.model_config_manager import load_model_config

# Optional Gemini import
genai: Any = None
types: Any = None

try:
    import google.genai as genai  # type: ignore
    from google.genai import types  # type: ignore
except ImportError:
    pass

GEMINI_AVAILABLE = genai is not None

logger = logging.getLogger(__name__)


def load_api_key() -> Optional[str]:
    """Load API key with multiple fallback strategies for uvx compatibility"""
    # Strategy 1: Direct environment variables
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        logger.debug("API key loaded from environment variable")
        return api_key

    # Strategy 2: .env file in current directory
    env_file = Path(".env")
    if env_file.exists():
        try:
            from dotenv import load_dotenv

            load_dotenv(env_file)
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if api_key:
                logger.debug("API key loaded from .env file")
                return api_key
        except ImportError:
            logger.debug("python-dotenv not available, skipping .env file")

    # Strategy 3: User's home directory .env file
    home_env = Path.home() / ".gemini-code-review-mcp.env"
    if home_env.exists():
        try:
            api_key = home_env.read_text().strip()
            if api_key:
                logger.debug(f"API key loaded from {home_env}")
                return api_key
        except IOError:
            pass

    return None


def require_api_key():
    """Ensure API key is available with uvx-specific guidance"""
    api_key = load_api_key()

    if not api_key:
        error_msg = """
🔑 GEMINI_API_KEY not found. Choose the setup method that works for your environment:

📋 QUICKSTART (Recommended):
   # 1. Get API key: https://ai.google.dev/gemini-api/docs/api-key
   # 2. Set environment variable:
   export GEMINI_API_KEY=your_key_here
   
   # 3. Run tool:
   generate-code-review .

🔧 FOR UVX USERS:
   # Method 1: Environment variable prefix (most reliable)
   GEMINI_API_KEY=your_key uvx gemini-code-review-mcp generate-code-review .
   
   # Method 2: Create project .env file
   echo "GEMINI_API_KEY=your_key_here" > .env
   uvx gemini-code-review-mcp generate-code-review .
   
   # Method 3: Global user config
   echo "GEMINI_API_KEY=your_key_here" > ~/.gemini-code-review-mcp.env
   uvx gemini-code-review-mcp generate-code-review .

📝 FOR MCP SERVER USERS:
   Add to your Claude Desktop configuration:
   {
     "mcpServers": {
       "task-list-reviewer": {
         "command": "uvx",
         "args": ["gemini-code-review-mcp"],
         "env": {
           "GEMINI_API_KEY": "your_key_here"
         }
       }
     }
   }

🚨 TROUBLESHOOTING:
   # Check if environment variable is set:
   echo $GEMINI_API_KEY
   
   # Test API key with minimal command:
   GEMINI_API_KEY=your_key uvx gemini-code-review-mcp generate-code-review . --no-gemini
   
   # Verify current directory structure:
   ls -la tasks/

🌐 Get your API key: https://ai.google.dev/gemini-api/docs/api-key
"""
        logger.error(error_msg)
        raise ValueError(error_msg)

    return api_key


def send_to_gemini_for_review(
    context_content: str,
    project_path: Optional[str] = None,
    temperature: float = 0.5,
    model: Optional[str] = None,
    return_text: bool = False,
    include_formatting: bool = True,
    thinking_budget: Optional[int] = None,
) -> Optional[str]:
    """
    Send review context to Gemini for comprehensive code review with advanced features.

    Features enabled by default:
    - Thinking mode (for supported models)
    - URL context (for supported models)
    - Google Search grounding (for supported models)

    Args:
        context_content: The formatted review context content
        project_path: Path to project root for saving output (optional if return_text=True)
        temperature: Temperature for AI model (default: 0.5)
        model: Optional model override (default: uses GEMINI_MODEL env var or config default)
        return_text: If True, return generated text directly; if False, save to file and return file path
        include_formatting: If True, include headers and metadata; if False, return raw response (default: True)
        thinking_budget: Optional token budget for thinking mode (if supported by model)

    Returns:
        Generated text (if return_text=True) or path to saved file (if return_text=False), or None if failed
    """
    # Check if Gemini is available first
    if not GEMINI_AVAILABLE or genai is None:
        logger.warning("Gemini API not available. Skipping Gemini review.")
        return None

    # Use enhanced API key loading with multiple strategies
    try:
        api_key = require_api_key()
    except ValueError as e:
        logger.warning(f"API key not found: {e}")
        return None

    try:
        client = genai.Client(api_key=api_key)

        # Load model configuration from JSON file
        config = load_model_config()

        # Configure model selection with precedence: parameter > env var > config default
        model_config = model or os.getenv("GEMINI_MODEL", config["defaults"]["model"])

        # Resolve model aliases to actual API model names
        model_config = config["model_aliases"].get(model_config, model_config)

        # Model capability detection using configuration
        supports_url_context = (
            model_config in config["model_capabilities"]["url_context_supported"]
        )
        supports_grounding = (
            "gemini-1.5" in model_config
            or "gemini-2.0" in model_config
            or "gemini-2.5" in model_config
        )
        supports_thinking = (
            model_config in config["model_capabilities"]["thinking_mode_supported"]
        )

        # Determine what features will actually be enabled (considering disable flags)
        actual_capabilities: List[str] = []
        disable_url_context = (
            os.getenv("DISABLE_URL_CONTEXT", "false").lower() == "true"
        )
        disable_grounding = os.getenv("DISABLE_GROUNDING", "false").lower() == "true"
        disable_thinking = os.getenv("DISABLE_THINKING", "false").lower() == "true"

        # Check what will actually be enabled
        url_context_enabled = supports_url_context and not disable_url_context
        grounding_enabled = supports_grounding and not disable_grounding
        thinking_enabled = supports_thinking and not disable_thinking

        # Build capabilities list for user feedback
        if url_context_enabled:
            actual_capabilities.append("URL context")
        if grounding_enabled:
            actual_capabilities.append("web grounding")
        if thinking_enabled:
            actual_capabilities.append("thinking mode")

        # Enhanced user feedback for CLI
        print(f"🤖 Using Gemini model: {model_config}")
        if actual_capabilities:
            print(f"✨ Enhanced features enabled: {', '.join(actual_capabilities)}")
            if thinking_enabled:
                if thinking_budget is not None:
                    budget_info = f" (budget: {thinking_budget} tokens)"
                else:
                    budget_info = " (auto-budget)"
                print(f"   💭 Thinking mode: Deep reasoning{budget_info}")
            if grounding_enabled:
                print("   🌐 Web grounding: Real-time information lookup")
            if url_context_enabled:
                print("   🔗 URL context: Enhanced web content understanding")
        else:
            print("⚡ Standard features: Basic text generation")

        # Log for debugging (less verbose than user output)
        capabilities_text = (
            f" (features: {', '.join(actual_capabilities)})"
            if actual_capabilities
            else " (basic)"
        )
        logger.info(f"Gemini configuration: {model_config}{capabilities_text}")

        # Configure tools (enabled by default with opt-out)
        tools: List[Any] = []

        # URL Context - enabled by default for supported models
        if url_context_enabled and types is not None:
            try:
                tools.append(types.Tool(url_context=types.UrlContext()))
            except (AttributeError, TypeError) as e:
                logger.warning(f"URL context configuration failed: {e}")

        # Google Search Grounding - enabled by default for supported models
        if grounding_enabled and types is not None:
            try:
                # Use GoogleSearch for newer models (Gemini 2.0+, 2.5+)
                if "gemini-2.0" in model_config or "gemini-2.5" in model_config:
                    google_search_tool = types.Tool(google_search=types.GoogleSearch())
                    tools.append(google_search_tool)
                else:
                    # Fallback to GoogleSearchRetrieval for older models
                    grounding_config = types.GoogleSearchRetrieval()
                    tools.append(types.Tool(google_search_retrieval=grounding_config))
            except (AttributeError, TypeError) as e:
                logger.warning(f"Grounding configuration failed: {e}")

        # Configure thinking mode - enabled by default for supported models
        thinking_config = None
        # Use parameter thinking_budget if provided, otherwise check env var
        if thinking_budget is None:
            thinking_budget_str = os.getenv("THINKING_BUDGET")
            if thinking_budget_str and thinking_budget_str.strip():
                try:
                    thinking_budget = int(thinking_budget_str)
                except (ValueError, TypeError):
                    thinking_budget = None
        include_thoughts = os.getenv("INCLUDE_THOUGHTS", "true").lower() == "true"

        if thinking_enabled:
            try:
                config_params = {"include_thoughts": include_thoughts}

                # Handle thinking budget based on model type
                if "gemini-2.5-flash" in model_config:
                    # Flash model: 0-24,576 tokens (can disable with 0)
                    if thinking_budget is not None:
                        validated_budget = max(0, min(thinking_budget, 24576))
                        config_params["thinking_budget"] = validated_budget
                        if thinking_budget != validated_budget:
                            logger.info(
                                f"Thinking budget adjusted from {thinking_budget} to {validated_budget} (Flash limit: 0-24,576)"
                            )
                elif "gemini-2.5-pro" in model_config:
                    # Pro model: 128-32,768 tokens (cannot disable)
                    if thinking_budget is not None:
                        validated_budget = max(128, min(thinking_budget, 32768))
                        config_params["thinking_budget"] = validated_budget
                        if thinking_budget != validated_budget:
                            logger.info(
                                f"Thinking budget adjusted from {thinking_budget} to {validated_budget} (Pro limit: 128-32,768)"
                            )

                thinking_config = (
                    types.ThinkingConfig(**config_params) if types is not None else None
                )
            except (AttributeError, TypeError) as e:
                logger.warning(f"Thinking configuration failed: {e}")

        # Use the provided temperature (from CLI arg or function parameter)
        # Environment variable is handled at the caller level

        # Build configuration parameters
        config_params: Dict[str, Any] = {
            "max_output_tokens": 8000,
            "temperature": temperature,
        }

        if tools:
            config_params["tools"] = tools

        if thinking_config:
            config_params["thinking_config"] = thinking_config

        if types is not None:
            config = types.GenerateContentConfig(**config_params)
        else:
            config = None

        # Create comprehensive review prompt
        review_prompt = f"""You are an expert code reviewer conducting a comprehensive code review. Based on the provided context, please provide detailed feedback.

{context_content}

Please provide a thorough code review that includes:
1. **Overall Assessment** - High-level evaluation of the implementation
2. **Code Quality & Best Practices** - Specific line-by-line feedback where applicable
3. **Architecture & Design** - Comments on system design and patterns
4. **Security Considerations** - Any security concerns or improvements
5. **Performance Implications** - Performance considerations and optimizations
6. **Testing & Maintainability** - Suggestions for testing and long-term maintenance
7. **Next Steps** - Recommendations for future work or improvements

Focus on being specific and actionable. When referencing files, include line numbers where relevant."""

        # Generate review
        logger.info("Sending context to Gemini for code review...")
        response = client.models.generate_content(
            model=model_config, contents=[review_prompt], config=config
        )

        # Format response metadata
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        # Format the response with metadata
        enabled_features: List[str] = []
        if supports_url_context and not disable_url_context and tools:
            # Check if URL context tool was actually added
            if any(hasattr(tool, "url_context") for tool in tools):
                enabled_features.append("URL context")
        if supports_grounding and not disable_grounding and tools:
            # Check if grounding tool was actually added
            if any(
                hasattr(tool, "google_search")
                or hasattr(tool, "google_search_retrieval")
                for tool in tools
            ):
                enabled_features.append("web grounding")
        if thinking_config:
            enabled_features.append("thinking mode")

        features_text = (
            ", ".join(enabled_features) if enabled_features else "basic capabilities"
        )

        # Format response based on include_formatting parameter
        response_text = response.text or "No response generated"
        if include_formatting:
            formatted_response = f"""# Comprehensive Code Review Feedback
*Generated on {datetime.now().strftime("%Y-%m-%d at %H:%M:%S")} using {model_config}*

{response_text}

---
*Review conducted by Gemini AI with {features_text}*
"""
        else:
            # Return raw response without headers/footers
            formatted_response = response_text

        # Return text directly or save to file based on return_text parameter
        if return_text:
            return formatted_response
        else:
            # Validate project_path is provided when saving to file
            if not project_path:
                raise ValueError("project_path is required when return_text=False")

            # Define output file path only when saving to file
            output_file = os.path.join(
                project_path, f"code-review-comprehensive-feedback-{timestamp}.md"
            )

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(formatted_response)

            logger.info(f"Gemini review saved to: {output_file}")
            return output_file

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to generate Gemini review: {error_msg}")
        
        # Check for specific error types that might be retryable
        if "400 INVALID_ARGUMENT" in error_msg:
            # This might be due to content size or format issues
            logger.info("Attempting retry with reduced content...")
            
            # Try to reduce content size if it's a phase 3 issue
            if len(context_content) > 50000:
                # Truncate content and retry
                truncated_content = context_content[:45000] + "\n\n[Content truncated due to size limits]"
                logger.info(f"Retrying with truncated content ({len(truncated_content)} chars)")
                
                try:
                    # Recursive call with truncated content
                    return send_to_gemini_for_review(
                        truncated_content,
                        project_path,
                        temperature,
                        model,
                        return_text,
                        include_formatting,
                        thinking_budget,
                    )
                except Exception as retry_error:
                    logger.error(f"Retry also failed: {retry_error}")
        
        return None
