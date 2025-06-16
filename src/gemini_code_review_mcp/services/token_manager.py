#!/usr/bin/env python3
"""
Token management for context generation with model-aware limits.

This module handles token counting, model-specific limits, and smart
prioritization of files to fit within context windows.
"""

import logging
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import official token counter
try:
    from .token_counter_official import count_tokens as official_count_tokens
    OFFICIAL_COUNTER_AVAILABLE = True
except ImportError:
    OFFICIAL_COUNTER_AVAILABLE = False
    official_count_tokens = None

# Model-specific token limits based on benchmark data
MODEL_TOKEN_LIMITS = {
    # Gemini 2.5 Pro models - excellent up to 192k
    "gemini-2.5-pro-preview-06-05": {
        "default": 180_000,  # ~90% of 192k for safety margin
        "max": 300_000,
        "description": "Handles up to 192k tokens with 90.6% accuracy"
    },
    "gemini-2.5-pro-preview-05-06": {
        "default": 100_000,  # Drops to 72.2% at 192k
        "max": 150_000,
        "description": "Best up to 120k tokens"
    },
    "gemini-2.5-pro-exp-03-25:free": {
        "default": 150_000,  # 90.6% at 192k
        "max": 250_000,
        "description": "Strong performance up to 192k"
    },
    
    # Gemini Flash - good for smaller contexts
    "gemini-2.5-flash-preview-05-20": {
        "default": 60_000,  # 68.8% at 120k, 65.6% at 192k
        "max": 100_000,
        "description": "Optimized for speed, best under 60k tokens"
    },
    "gemini-2.0-flash": {
        "default": 60_000,
        "max": 100_000,
        "description": "Fast model for cost-efficient processing"
    },
    "gemini-1.5-flash": {
        "default": 60_000,
        "max": 100_000,
        "description": "Fast model, best for smaller contexts"
    },
    "gemini-1.5-flash-latest": {
        "default": 60_000,
        "max": 100_000,
        "description": "Fast model, best for smaller contexts"
    },
    "gemini-1.5-pro": {
        "default": 100_000,
        "max": 150_000,
        "description": "Balanced model for medium contexts"
    },
    "gemini-1.5-pro-latest": {
        "default": 100_000,
        "max": 150_000,
        "description": "Balanced model for medium contexts"
    },
    
    # Default for unknown models
    "default": {
        "default": 100_000,
        "max": 150_000,
        "description": "Conservative default for unknown models"
    }
}

# Context strategies with model-aware adjustments
CONTEXT_STRATEGIES = {
    "focused": {
        "multiplier": 0.3,  # 30% of model default
        "description": "Essential files only - fast & cheap",
        "min_tokens": 20_000
    },
    "balanced": {
        "multiplier": 1.0,  # 100% of model default
        "description": "Default - optimal accuracy vs cost",
        "min_tokens": 60_000
    },
    "comprehensive": {
        "multiplier": 1.5,  # 150% of model default
        "description": "Maximum context - thorough but expensive",
        "min_tokens": 100_000
    },
    "unlimited": {
        "multiplier": None,  # No limit, include everything
        "description": "Include all files (warning: may exceed model limits)",
        "min_tokens": None
    }
}


@dataclass
class FileInfo:
    """Information about a file to be included in context."""
    path: str
    content: str
    status: str  # added, modified, deleted
    additions: int = 0
    deletions: int = 0
    
    @property
    def change_size(self) -> int:
        """Total number of changes in the file."""
        return self.additions + self.deletions


@dataclass
class ContextSummary:
    """Summary of context generation results."""
    included_files: List[FileInfo]
    truncated_files: List[Tuple[FileInfo, int, int]]  # (file, original_tokens, truncated_tokens)
    excluded_files: List[FileInfo]
    total_tokens: int
    token_limit: int
    model_name: str
    strategy: str


def estimate_tokens(text: str, file_path: Optional[str] = None, model_name: Optional[str] = None) -> int:
    """
    Estimate token count for text.
    
    Uses official Vertex AI tokenizer when available, otherwise falls back to
    character-based heuristics for code vs prose.
    """
    if not text:
        return 0
    
    # Try official tokenizer first if available
    if OFFICIAL_COUNTER_AVAILABLE and model_name:
        try:
            count, is_exact = official_count_tokens(text, file_path, model_name)
            if is_exact:
                logger.debug(f"Using exact token count: {count}")
                return count
        except Exception as e:
            logger.debug(f"Official tokenizer failed, using heuristic: {e}")
    
    # Fallback to heuristic estimation
        
    char_count = len(text)
    
    # Determine content type and appropriate ratio
    if file_path:
        ext = os.path.splitext(file_path.lower())[1].lstrip('.')
        
        # Programming languages use shorter tokens
        if ext in ['py', 'js', 'ts', 'jsx', 'tsx', 'go', 'rs', 'java', 'cpp', 'c']:
            char_per_token = 2.7
            safety_margin = 1.15  # 15% for code
        # Data/markup formats
        elif ext in ['json', 'yaml', 'yml', 'xml', 'html', 'css']:
            char_per_token = 2.8
            safety_margin = 1.12
        # Documentation
        elif ext in ['md', 'txt', 'rst']:
            char_per_token = 3.5
            safety_margin = 1.10
        else:
            char_per_token = 3.0  # Conservative default
            safety_margin = 1.15
    else:
        # No file path - analyze content to guess type
        # Look for code indicators in first 1000 chars
        sample = text[:1000]
        code_indicators = sum(1 for c in sample if c in '{}[]();=<>')
        
        if code_indicators > 50:  # Likely code
            char_per_token = 2.8
            safety_margin = 1.15
        else:
            char_per_token = 3.5
            safety_margin = 1.12
    
    # Calculate tokens
    base_tokens = char_count / char_per_token
    
    # Apply safety margin
    return int(base_tokens * safety_margin)


def get_token_limit(model_name: str, strategy: str, override: Optional[int] = None) -> int:
    """
    Calculate token limit based on model and strategy.
    
    Args:
        model_name: Name of the Gemini model
        strategy: Context strategy (focused, balanced, comprehensive, unlimited)
        override: Optional override for token limit
        
    Returns:
        Token limit for the configuration
    """
    if override:
        logger.info(f"Using override token limit: {override:,}")
        return override
    
    # Find model configuration
    model_config = MODEL_TOKEN_LIMITS.get(model_name)
    if not model_config:
        logger.warning(f"Unknown model '{model_name}', using default limits")
        model_config = MODEL_TOKEN_LIMITS["default"]
    
    base_limit = model_config["default"]
    
    # Apply strategy
    strategy_config = CONTEXT_STRATEGIES.get(strategy, CONTEXT_STRATEGIES["balanced"])
    if strategy_config["multiplier"] is None:
        logger.warning("Using unlimited context strategy - may exceed model limits")
        return float('inf')  # Unlimited
    
    calculated_limit = int(base_limit * strategy_config["multiplier"])
    min_tokens = strategy_config.get("min_tokens", 0)
    
    final_limit = max(calculated_limit, min_tokens)
    
    # Ensure we don't exceed model max
    if final_limit > model_config["max"]:
        final_limit = model_config["max"]
        logger.warning(f"Capping token limit to model maximum: {final_limit:,}")
    
    logger.info(f"Token limit for {model_name} with {strategy} strategy: {final_limit:,}")
    return final_limit


def calculate_file_priority(file_info: FileInfo) -> int:
    """
    Calculate priority score for a file.
    
    Higher scores indicate higher priority for inclusion.
    
    Args:
        file_info: Information about the file
        
    Returns:
        Priority score (0-300+)
    """
    score = 0
    
    # File type scoring (most important factor)
    if file_info.path.endswith(('.py', '.ts', '.js', '.tsx', '.jsx')):
        score += 100
    elif file_info.path.endswith(('.go', '.rs', '.java', '.cpp', '.c')):
        score += 90
    elif file_info.path.endswith(('.vue', '.svelte', '.html', '.css', '.scss')):
        score += 70
    elif file_info.path.endswith(('.json', '.yaml', '.yml', '.toml')):
        score += 50
    elif file_info.path.endswith(('.md', '.txt', '.rst')):
        score += 30
    
    # Location scoring
    if '/src/' in file_info.path or '/lib/' in file_info.path:
        score += 80
    elif '/app/' in file_info.path or '/pages/' in file_info.path:
        score += 70
    elif '/components/' in file_info.path:
        score += 60
    elif '/test' in file_info.path or '/spec' in file_info.path:
        score += 40
    elif '/docs/' in file_info.path:
        score += 20
    
    # Status scoring
    if file_info.status == "modified":
        score += 50  # Modified files are usually most important
    elif file_info.status == "added":
        score += 40
    elif file_info.status == "deleted":
        score += 20  # Still important to see what was removed
    
    # Change size scoring (cap at 100 points)
    change_score = min(file_info.change_size, 100)
    score += change_score
    
    # Special files get bonus
    basename = file_info.path.split('/')[-1]
    if basename in ['__init__.py', 'index.ts', 'index.js', 'main.py', 'app.py']:
        score += 50
    elif basename in ['package.json', 'requirements.txt', 'Cargo.toml', 'go.mod']:
        score += 40
    
    return score


def truncate_content(content: str, max_tokens: int, file_path: Optional[str] = None, model_name: Optional[str] = None) -> str:
    """
    Truncate content to fit within token limit.
    
    Tries to truncate at logical boundaries (functions, classes).
    
    Args:
        content: Original content
        max_tokens: Maximum tokens allowed
        
    Returns:
        Truncated content with indicator
    """
    if not content:
        return content
    
    # Quick check if truncation needed
    estimated = estimate_tokens(content, file_path, model_name)
    if estimated <= max_tokens:
        return content
    
    # Calculate approximate character limit
    # Be conservative - better to include less than exceed
    char_limit = int(max_tokens * 3.5)  # Conservative ratio
    
    if len(content) <= char_limit:
        return content
    
    # Try to find a good truncation point
    lines = content.split('\n')
    truncated_lines = []
    current_chars = 0
    
    for line in lines:
        if current_chars + len(line) + 1 > char_limit:
            break
        truncated_lines.append(line)
        current_chars += len(line) + 1
    
    # Add truncation indicator
    truncated_lines.append("\n... [TRUNCATED - Content exceeds token limit] ...")
    
    return '\n'.join(truncated_lines)


class ContextBuilder:
    """Builds context with smart prioritization and token management."""
    
    def __init__(
        self,
        model_name: str,
        strategy: str = "balanced",
        max_tokens_override: Optional[int] = None,
        per_file_limit: int = 10_000
    ):
        """
        Initialize context builder.
        
        Args:
            model_name: Gemini model name
            strategy: Context strategy
            max_tokens_override: Optional override for max tokens
            per_file_limit: Maximum tokens per file
        """
        self.model_name = model_name
        self.strategy = strategy
        self.token_limit = get_token_limit(model_name, strategy, max_tokens_override)
        self.per_file_limit = per_file_limit
        
        # Track results
        self.current_tokens = 0
        self.included_files: List[FileInfo] = []
        self.truncated_files: List[Tuple[FileInfo, int, int]] = []
        self.excluded_files: List[FileInfo] = []
    
    def build_context(self, files: List[FileInfo]) -> ContextSummary:
        """
        Build context from files with smart prioritization.
        
        Args:
            files: List of files to potentially include
            
        Returns:
            Summary of what was included/excluded
        """
        # Reset state
        self.current_tokens = 0
        self.included_files = []
        self.truncated_files = []
        self.excluded_files = []
        
        # Prioritize files
        scored_files = [(f, calculate_file_priority(f)) for f in files]
        scored_files.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Processing {len(files)} files with token limit {self.token_limit:,}")
        
        # Process files in priority order
        for file_info, priority in scored_files:
            file_tokens = estimate_tokens(file_info.content, file_info.path, self.model_name)
            
            if self.current_tokens + file_tokens <= self.token_limit:
                # Include full file
                self.included_files.append(file_info)
                self.current_tokens += file_tokens
                logger.debug(f"Including {file_info.path} ({file_tokens:,} tokens, priority: {priority})")
                
            elif self.current_tokens < self.token_limit and file_tokens > 0:
                # Try to truncate file to fit
                remaining_tokens = self.token_limit - self.current_tokens
                max_file_tokens = min(remaining_tokens, self.per_file_limit)
                
                if max_file_tokens >= 1000:  # Only include if we can fit meaningful content
                    truncated_content = truncate_content(file_info.content, max_file_tokens, file_info.path, self.model_name)
                    truncated_tokens = estimate_tokens(truncated_content, file_info.path, self.model_name)
                    
                    # Create truncated file info
                    truncated_file = FileInfo(
                        path=file_info.path,
                        content=truncated_content,
                        status=file_info.status,
                        additions=file_info.additions,
                        deletions=file_info.deletions
                    )
                    
                    self.included_files.append(truncated_file)
                    self.truncated_files.append((file_info, file_tokens, truncated_tokens))
                    self.current_tokens += truncated_tokens
                    
                    logger.info(f"Truncated {file_info.path}: {truncated_tokens:,}/{file_tokens:,} tokens")
                    
                    # Check if we're at limit
                    if self.current_tokens >= self.token_limit * 0.95:
                        # Close enough to limit, stop processing
                        self.excluded_files.extend([f for f, _ in scored_files[scored_files.index((file_info, priority)) + 1:]])
                        break
                else:
                    self.excluded_files.append(file_info)
            else:
                # Exclude file
                self.excluded_files.append(file_info)
        
        return ContextSummary(
            included_files=self.included_files,
            truncated_files=self.truncated_files,
            excluded_files=self.excluded_files,
            total_tokens=self.current_tokens,
            token_limit=self.token_limit,
            model_name=self.model_name,
            strategy=self.strategy
        )


def generate_context_summary_message(summary: ContextSummary) -> str:
    """
    Generate a helpful summary message about context generation.
    
    Args:
        summary: Context generation summary
        
    Returns:
        Formatted summary message
    """
    model_config = MODEL_TOKEN_LIMITS.get(summary.model_name, MODEL_TOKEN_LIMITS["default"])
    strategy_config = CONTEXT_STRATEGIES.get(summary.strategy, CONTEXT_STRATEGIES["balanced"])
    
    lines = [
        "📊 Context Generation Summary",
        "━" * 50,
        f"Model: {summary.model_name}",
        f"Strategy: {summary.strategy} ({strategy_config['description']})",
        f"Token Limit: {summary.token_limit:,} / {model_config['max']:,} (model max)",
        "",
        f"✅ Included: {len(summary.included_files)} files ({summary.total_tokens:,} tokens)",
        f"⚠️  Truncated: {len(summary.truncated_files)} files",
        f"❌ Excluded: {len(summary.excluded_files)} files"
    ]
    
    if summary.truncated_files:
        lines.append("\n⚠️  Truncated files:")
        for file_info, orig_tokens, trunc_tokens in summary.truncated_files[:5]:
            lines.append(f"   - {file_info.path}: {trunc_tokens:,}/{orig_tokens:,} tokens")
        if len(summary.truncated_files) > 5:
            lines.append(f"   ... and {len(summary.truncated_files) - 5} more")
    
    if summary.excluded_files and len(summary.excluded_files) <= 10:
        lines.append("\n❌ Excluded files:")
        for file_info in summary.excluded_files[:10]:
            lines.append(f"   - {file_info.path}")
        if len(summary.excluded_files) > 10:
            lines.append(f"   ... and {len(summary.excluded_files) - 10} more")
    
    # Add recommendations
    if summary.excluded_files:
        lines.append("")
        if summary.model_name.startswith("gemini-2.5-pro"):
            lines.append(f"💡 Tip: This model supports up to {model_config['max']:,} tokens.")
            lines.append("   Use --context-strategy comprehensive for more files")
        else:
            lines.append("💡 Tip: Consider using gemini-2.5-pro-preview-06-05 for larger contexts")
            lines.append("   Or use --context-strategy focused to fit within limits")
    
    # Add cost warning for large contexts
    if summary.total_tokens > 100_000:
        lines.append("")
        lines.append("💰 Note: Large contexts increase API costs. Consider --context-strategy focused for routine reviews.")
    
    return "\n".join(lines)