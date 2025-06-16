#!/usr/bin/env python3
"""
Enhanced token counting with Gemini API integration and improved heuristics.

This module provides both exact token counting via Gemini's API and improved
estimation for when API calls aren't practical.
"""

import logging
import os
from typing import Dict, Optional, Tuple
from functools import lru_cache

logger = logging.getLogger(__name__)

# File type to average characters per token mapping
# Based on empirical observations for code vs prose
FILE_TYPE_RATIOS = {
    # Programming languages (shorter tokens)
    'py': 2.7,      # Python
    'js': 2.8,      # JavaScript
    'ts': 2.8,      # TypeScript  
    'tsx': 2.8,     # TypeScript React
    'jsx': 2.8,     # JavaScript React
    'go': 2.7,      # Go
    'rs': 2.7,      # Rust
    'java': 2.8,    # Java
    'cpp': 2.7,     # C++
    'c': 2.7,       # C
    'cs': 2.8,      # C#
    'rb': 2.7,      # Ruby
    'php': 2.8,     # PHP
    'swift': 2.8,   # Swift
    'kt': 2.8,      # Kotlin
    
    # Markup and data formats
    'json': 2.5,    # JSON (lots of punctuation)
    'yaml': 3.0,    # YAML
    'yml': 3.0,     # YAML
    'xml': 2.8,     # XML
    'html': 2.8,    # HTML
    'css': 2.7,     # CSS
    'scss': 2.7,    # SCSS
    'sql': 3.0,     # SQL
    
    # Documentation formats
    'md': 3.2,      # Markdown
    'markdown': 3.2,
    'rst': 3.5,     # reStructuredText
    'txt': 4.0,     # Plain text
    
    # Configuration files
    'toml': 3.0,    # TOML
    'ini': 3.5,     # INI files
    'cfg': 3.5,     # Config files
    'conf': 3.5,    # Config files
    
    # Shell scripts
    'sh': 2.8,      # Shell scripts
    'bash': 2.8,    # Bash scripts
    'zsh': 2.8,     # Zsh scripts
    'fish': 2.8,    # Fish scripts
    
    # Default for unknown types
    'default': 3.5  # Conservative estimate
}

# Safety margins by content type
SAFETY_MARGINS = {
    'code': 1.15,      # 15% margin for code
    'markup': 1.12,    # 12% margin for markup/data
    'prose': 1.10,     # 10% margin for documentation
    'default': 1.15    # 15% default margin
}


def get_file_extension(file_path: str) -> str:
    """Extract file extension from path."""
    _, ext = os.path.splitext(file_path.lower())
    return ext.lstrip('.') if ext else ''


def get_content_type(file_extension: str) -> str:
    """Determine content type from file extension."""
    if file_extension in ['py', 'js', 'ts', 'jsx', 'tsx', 'go', 'rs', 'java', 'cpp', 'c', 'cs', 'rb', 'php', 'swift', 'kt', 'sh', 'bash']:
        return 'code'
    elif file_extension in ['json', 'yaml', 'yml', 'xml', 'html', 'css', 'scss', 'toml', 'ini', 'cfg', 'conf']:
        return 'markup'
    elif file_extension in ['md', 'markdown', 'rst', 'txt']:
        return 'prose'
    else:
        return 'default'


def estimate_tokens_heuristic(text: str, file_path: Optional[str] = None) -> int:
    """
    Estimate token count using improved heuristics based on file type.
    
    Args:
        text: The text content to estimate
        file_path: Optional file path to determine file type
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    # Determine file type and get appropriate ratio
    if file_path:
        ext = get_file_extension(file_path)
        ratio = FILE_TYPE_RATIOS.get(ext, FILE_TYPE_RATIOS['default'])
        content_type = get_content_type(ext)
    else:
        # Analyze content to guess type
        code_indicators = sum(1 for c in text[:1000] if c in '{}[]();=')
        if code_indicators > 50:  # Likely code
            ratio = 2.8
            content_type = 'code'
        else:
            ratio = FILE_TYPE_RATIOS['default']
            content_type = 'default'
    
    # Base calculation
    char_count = len(text)
    base_tokens = char_count / ratio
    
    # Get appropriate safety margin
    margin = SAFETY_MARGINS.get(content_type, SAFETY_MARGINS['default'])
    
    # Apply margin and return
    return int(base_tokens * margin)


# Optional: Gemini API integration for exact counts
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.debug("Google Generative AI SDK not available for exact token counting")


@lru_cache(maxsize=128)
def count_tokens_exact(text: str, model_name: str = "gemini-1.5-flash") -> Optional[int]:
    """
    Get exact token count using Gemini's countTokens API.
    
    This is cached to avoid repeated API calls for the same content.
    
    Args:
        text: The text to count tokens for
        model_name: The Gemini model to use for counting
        
    Returns:
        Exact token count or None if API unavailable
    """
    if not GEMINI_AVAILABLE:
        return None
    
    try:
        # Initialize with API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.debug("GEMINI_API_KEY not set, falling back to estimation")
            return None
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        # Count tokens
        response = model.count_tokens(text)
        return response.total_tokens
        
    except Exception as e:
        logger.warning(f"Failed to get exact token count: {e}")
        return None


def count_tokens(
    text: str, 
    file_path: Optional[str] = None,
    use_exact: bool = False,
    model_name: str = "gemini-1.5-flash"
) -> Tuple[int, bool]:
    """
    Count tokens with fallback from exact to estimation.
    
    Args:
        text: The text to count tokens for
        file_path: Optional file path for better estimation
        use_exact: Whether to try exact counting first
        model_name: Model to use for exact counting
        
    Returns:
        Tuple of (token_count, is_exact)
    """
    # Try exact counting first if requested
    if use_exact:
        exact_count = count_tokens_exact(text, model_name)
        if exact_count is not None:
            return exact_count, True
    
    # Fall back to heuristic
    estimated = estimate_tokens_heuristic(text, file_path)
    return estimated, False


def batch_count_tokens(
    files: Dict[str, str],
    use_exact: bool = False,
    model_name: str = "gemini-1.5-flash"
) -> Dict[str, Tuple[int, bool]]:
    """
    Count tokens for multiple files.
    
    Args:
        files: Dict mapping file paths to content
        use_exact: Whether to try exact counting
        model_name: Model for exact counting
        
    Returns:
        Dict mapping file paths to (token_count, is_exact) tuples
    """
    results = {}
    
    for file_path, content in files.items():
        count, is_exact = count_tokens(content, file_path, use_exact, model_name)
        results[file_path] = (count, is_exact)
        
        if is_exact:
            logger.debug(f"Exact token count for {file_path}: {count}")
        else:
            logger.debug(f"Estimated token count for {file_path}: {count}")
    
    return results


# Calibration system for improving estimates over time
class TokenCalibrator:
    """Tracks actual vs estimated tokens to improve heuristics."""
    
    def __init__(self, cache_file: Optional[str] = None):
        self.cache_file = cache_file or os.path.expanduser("~/.gemini_token_calibration.json")
        self.data: Dict[str, list] = self._load_cache()
    
    def _load_cache(self) -> Dict[str, list]:
        """Load calibration data from cache."""
        if os.path.exists(self.cache_file):
            try:
                import json
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def record_measurement(self, file_ext: str, char_count: int, actual_tokens: int):
        """Record an actual token count for calibration."""
        if file_ext not in self.data:
            self.data[file_ext] = []
        
        self.data[file_ext].append({
            'chars': char_count,
            'tokens': actual_tokens,
            'ratio': char_count / actual_tokens if actual_tokens > 0 else 0
        })
        
        # Keep only last 100 measurements per type
        if len(self.data[file_ext]) > 100:
            self.data[file_ext] = self.data[file_ext][-100:]
        
        self._save_cache()
    
    def _save_cache(self):
        """Save calibration data to cache."""
        try:
            import json
            with open(self.cache_file, 'w') as f:
                json.dump(self.data, f)
        except Exception as e:
            logger.warning(f"Failed to save calibration cache: {e}")
    
    def get_calibrated_ratio(self, file_ext: str) -> Optional[float]:
        """Get calibrated character/token ratio for file type."""
        if file_ext in self.data and len(self.data[file_ext]) >= 5:
            # Use median of recent measurements
            ratios = [m['ratio'] for m in self.data[file_ext][-20:] if m['ratio'] > 0]
            if ratios:
                ratios.sort()
                return ratios[len(ratios) // 2]
        return None


# Global calibrator instance
_calibrator = TokenCalibrator()


def count_tokens_with_calibration(
    text: str,
    file_path: Optional[str] = None,
    record_actual: Optional[int] = None
) -> int:
    """
    Count tokens using calibrated ratios when available.
    
    Args:
        text: Text to count
        file_path: File path for type detection
        record_actual: If provided, record this as the actual count for calibration
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    ext = get_file_extension(file_path) if file_path else 'default'
    
    # Record measurement if actual count provided
    if record_actual is not None:
        _calibrator.record_measurement(ext, len(text), record_actual)
    
    # Try calibrated ratio first
    calibrated_ratio = _calibrator.get_calibrated_ratio(ext)
    if calibrated_ratio:
        content_type = get_content_type(ext)
        margin = SAFETY_MARGINS.get(content_type, SAFETY_MARGINS['default'])
        return int((len(text) / calibrated_ratio) * margin)
    
    # Fall back to standard estimation
    return estimate_tokens_heuristic(text, file_path)