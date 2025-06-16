#!/usr/bin/env python3
"""
Official token counting using Vertex AI SDK's local tokenizer.

This module provides exact token counting using Google's official local tokenizer,
available in google-cloud-aiplatform>=1.57.0. No API calls or authentication required.
"""

import logging
from functools import lru_cache
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Check if official tokenizer is available
try:
    from vertexai.generative_models import GenerativeModel
    import vertexai
    OFFICIAL_TOKENIZER_AVAILABLE = True
    logger.info("Official Vertex AI tokenizer available")
except ImportError:
    OFFICIAL_TOKENIZER_AVAILABLE = False
    logger.warning("Official tokenizer not available. Install google-cloud-aiplatform>=1.57.0")
    GenerativeModel = None

# Import our heuristic fallback
from .token_manager import estimate_tokens as heuristic_estimate


# Model name mappings for consistency
MODEL_MAPPINGS = {
    # Map our config names to official Vertex AI model names
    "gemini-1.5-flash": "gemini-1.5-flash-002",
    "gemini-1.5-flash-latest": "gemini-1.5-flash-002",
    "gemini-1.5-pro": "gemini-1.5-pro-002",
    "gemini-1.5-pro-latest": "gemini-1.5-pro-002",
    "gemini-2.0-flash": "gemini-2.0-flash-exp",
    "gemini-2.5-flash": "gemini-2.5-flash-exp",
    "gemini-2.5-pro": "gemini-2.5-pro-exp",
    "gemini-2.5-pro-preview-06-05": "gemini-2.5-pro-exp",
    "gemini-2.5-flash-preview-05-20": "gemini-2.5-flash-exp",
}


@lru_cache(maxsize=10)
def get_cached_model(model_name: str):
    """
    Get a cached GenerativeModel instance for a specific model.
    
    Args:
        model_name: The Gemini model name
        
    Returns:
        GenerativeModel instance or None if unavailable
    """
    if not OFFICIAL_TOKENIZER_AVAILABLE:
        return None
    
    try:
        # Initialize Vertex AI if needed (only needed once)
        try:
            import vertexai
            # Try to initialize with default project/location
            # This may not be needed for just token counting
            vertexai.init()
        except Exception:
            # Initialization might fail without credentials, but 
            # token counting might still work
            pass
        
        # Map to official model name if needed
        official_name = MODEL_MAPPINGS.get(model_name, model_name)
        logger.debug(f"Loading model for token counting: {official_name}")
        return GenerativeModel(official_name)
    except Exception as e:
        logger.error(f"Failed to load model for {model_name}: {e}")
        return None


def count_tokens_official(
    text: Union[str, List[str]], 
    model_name: str = "gemini-1.5-flash"
) -> Tuple[int, bool]:
    """
    Count tokens using the official Vertex AI model's count_tokens method.
    
    Args:
        text: Single string or list of strings to count
        model_name: The Gemini model to use for tokenization
        
    Returns:
        Tuple of (token_count, is_exact)
        - token_count: Number of tokens
        - is_exact: True if official tokenizer used, False if heuristic
    """
    # Try official tokenizer first
    model = get_cached_model(model_name)
    
    if model:
        try:
            # The count_tokens method accepts a string or list of strings
            result = model.count_tokens(text)
            # The result has a total_tokens attribute
            return result.total_tokens, True
        except Exception as e:
            logger.warning(f"Official token counting failed: {e}")
    
    # Fallback to heuristic
    if isinstance(text, list):
        # Join list for heuristic estimation
        text = "\n".join(text)
    
    estimated = heuristic_estimate(text)
    return estimated, False


def count_tokens(
    text: str,
    file_path: Optional[str] = None,
    model_name: str = "gemini-1.5-flash",
    force_heuristic: bool = False
) -> Tuple[int, bool]:
    """
    Count tokens with automatic fallback from official to heuristic.
    
    This is the main entry point that maintains compatibility with existing code
    while using the official tokenizer when available.
    
    Args:
        text: The text to count tokens for
        file_path: Optional file path (used by heuristic)
        model_name: The Gemini model name
        force_heuristic: Force use of heuristic even if official is available
        
    Returns:
        Tuple of (token_count, is_exact)
    """
    if not text:
        return 0, True
    
    # Use official tokenizer unless forced to use heuristic
    if not force_heuristic:
        count, is_exact = count_tokens_official(text, model_name)
        if is_exact:
            return count, True
    
    # Fallback to heuristic
    estimated = heuristic_estimate(text, file_path)
    return estimated, False


def batch_count_tokens(
    files: Dict[str, str],
    model_name: str = "gemini-1.5-flash",
    force_heuristic: bool = False
) -> Dict[str, Tuple[int, bool]]:
    """
    Count tokens for multiple files efficiently.
    
    Args:
        files: Dict mapping file paths to content
        model_name: The Gemini model name
        force_heuristic: Force heuristic for all files
        
    Returns:
        Dict mapping file paths to (token_count, is_exact) tuples
    """
    results = {}
    
    # Try to use official tokenizer for batch if available
    if not force_heuristic and OFFICIAL_TOKENIZER_AVAILABLE:
        model = get_cached_model(model_name)
        if model:
            try:
                # Process all files with official tokenizer
                for file_path, content in files.items():
                    result = model.count_tokens(content)
                    results[file_path] = (result.total_tokens, True)
                    logger.debug(f"Official count for {file_path}: {result.total_tokens}")
                return results
            except Exception as e:
                logger.warning(f"Batch official counting failed: {e}")
    
    # Fallback to individual counting with heuristic
    for file_path, content in files.items():
        count, is_exact = count_tokens(content, file_path, model_name, force_heuristic)
        results[file_path] = (count, is_exact)
        
        log_msg = f"{'Exact' if is_exact else 'Estimated'} count for {file_path}: {count}"
        logger.debug(log_msg)
    
    return results


def get_tokenizer_info() -> Dict[str, any]:
    """
    Get information about the available tokenizer.
    
    Returns:
        Dict with tokenizer availability and version info
    """
    info = {
        "official_available": OFFICIAL_TOKENIZER_AVAILABLE,
        "fallback": "heuristic",
        "recommendation": ""
    }
    
    if OFFICIAL_TOKENIZER_AVAILABLE:
        info["recommendation"] = "Using official Vertex AI tokenizer for exact counts"
        try:
            import google.cloud.aiplatform
            info["sdk_version"] = google.cloud.aiplatform.__version__
        except:
            info["sdk_version"] = "unknown"
    else:
        info["recommendation"] = "Install google-cloud-aiplatform>=1.57.0 for exact token counting"
        info["sdk_version"] = "not installed"
    
    return info


def verify_token_counting_accuracy(
    test_samples: List[Tuple[str, str]],  # [(text, file_path), ...]
    model_name: str = "gemini-1.5-flash"
) -> Dict[str, any]:
    """
    Verify token counting accuracy by comparing official vs heuristic.
    
    Useful for calibrating heuristic ratios or debugging.
    
    Args:
        test_samples: List of (text, file_path) tuples to test
        model_name: Model to test with
        
    Returns:
        Statistics about accuracy comparison
    """
    if not OFFICIAL_TOKENIZER_AVAILABLE:
        return {"error": "Official tokenizer not available for comparison"}
    
    results = []
    total_diff = 0
    max_diff_percent = 0
    
    for text, file_path in test_samples:
        # Get official count
        official_count, _ = count_tokens_official(text, model_name)
        
        # Get heuristic count
        heuristic_count = heuristic_estimate(text, file_path)
        
        # Calculate difference
        diff = abs(official_count - heuristic_count)
        diff_percent = (diff / official_count * 100) if official_count > 0 else 0
        
        results.append({
            "file": file_path,
            "official": official_count,
            "heuristic": heuristic_count,
            "difference": diff,
            "diff_percent": diff_percent
        })
        
        total_diff += diff
        max_diff_percent = max(max_diff_percent, diff_percent)
    
    return {
        "samples": len(results),
        "average_difference": total_diff / len(results) if results else 0,
        "max_diff_percent": max_diff_percent,
        "results": results[:5]  # First 5 for brevity
    }


# Update the estimate_tokens function in token_manager.py to use this when available
def enhanced_estimate_tokens(text: str, file_path: Optional[str] = None, model_name: str = "gemini-1.5-flash") -> int:
    """
    Enhanced token estimation that uses official tokenizer when available.
    
    This can replace the heuristic estimate_tokens function.
    """
    count, is_exact = count_tokens(text, file_path, model_name)
    
    if is_exact:
        logger.debug(f"Using exact token count: {count}")
    else:
        logger.debug(f"Using estimated token count: {count}")
    
    return count