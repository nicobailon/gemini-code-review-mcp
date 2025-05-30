#!/usr/bin/env python3
"""
Standalone AI code review tool for processing context files with Gemini AI.

This module provides a clean separation between context generation and AI review,
allowing for independent operation and clear tool boundaries.
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Gemini integration from the main module
try:
    from .generate_code_review_context import send_to_gemini_for_review
except ImportError:
    try:
        from generate_code_review_context import send_to_gemini_for_review
    except ImportError:
        try:
            import sys
            import os
            # Add current directory to path for standalone execution
            current_dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.insert(0, current_dir)
            from generate_code_review_context import send_to_gemini_for_review
        except ImportError:
            logger.error("Could not import Gemini integration. Ensure generate_code_review_context.py is available.")
            sys.exit(1)


def suggest_context_file_corrections(provided_path: str) -> str:
    """
    Generate helpful suggestions for context file path issues.
    
    Args:
        provided_path: The path the user provided
    
    Returns:
        String with suggestion messages
    """
    suggestions = []
    current_dir = Path.cwd()
    
    # Check if tasks directory exists
    tasks_dir = current_dir / 'tasks'
    if tasks_dir.exists():
        context_files = list(tasks_dir.glob('*context*.md'))
        if context_files:
            latest_context = max(context_files, key=lambda p: p.stat().st_mtime)
            suggestions.append(f"  # Found context files in tasks/:")
            for f in sorted(context_files, key=lambda p: p.stat().st_mtime, reverse=True)[:3]:
                suggestions.append(f"  review-with-ai {f}")
        else:
            suggestions.append(f"  # No context files found. Generate one first:")
            suggestions.append(f"  generate-code-review . && review-with-ai tasks/code-review-context-*.md")
    
    # Check if it's a path case issue
    path_obj = Path(provided_path)
    if path_obj.parent.exists():
        similar_files = []
        try:
            pattern = path_obj.stem.lower()
            for item in path_obj.parent.iterdir():
                if item.is_file() and pattern[:5] in item.name.lower():
                    similar_files.append(item)
            if similar_files:
                suggestions.append(f"  # Found similar files:")
                for f in similar_files[:3]:
                    suggestions.append(f"  review-with-ai {f}")
        except PermissionError:
            suggestions.append(f"  # Permission denied accessing {path_obj.parent}")
    
    # Check for glob pattern
    if '*' not in provided_path and not path_obj.exists():
        glob_pattern = path_obj.parent / f"*{path_obj.stem}*{path_obj.suffix}"
        matching_files = list(glob_pattern.parent.glob(glob_pattern.name))
        if matching_files:
            suggestions.append(f"  # Try with glob pattern:")
            suggestions.append(f"  review-with-ai {glob_pattern}")
    
    return '\n'.join(suggestions) if suggestions else "  # Check the file path and try again"


def generate_ai_review(context_file_path: str, output_path: Optional[str] = None, 
                      model: Optional[str] = None, temperature: float = 0.5,
                      custom_prompt: Optional[str] = None) -> Optional[str]:
    """
    Generate AI-powered code review from existing context file.
    
    This function provides a standalone interface for generating AI reviews
    without requiring the full context generation pipeline.
    
    Args:
        context_file_path: Path to existing code review context file
        output_path: Optional custom output file path
        model: Optional model name for Gemini (e.g., 'gemini-2.0-flash-exp')
        temperature: Temperature setting for AI model (default: 0.5)
        custom_prompt: Optional custom prompt to override default AI instructions
        
    Returns:
        Path to generated AI review file, or None if generation failed
        
    Raises:
        FileNotFoundError: If context file doesn't exist
        ValueError: If context file path is invalid
        PermissionError: If file permissions prevent reading
    """
    # Validate input parameters
    if not context_file_path:
        error_msg = """context_file_path is required

Working examples:
  # Review existing context file
  review-with-ai tasks/review-context-20250101-120000.md
  
  # Generate context first, then review
  generate-code-review . && review-with-ai tasks/review-context-*.md
  
  # Use custom model and temperature
  review-with-ai context.md --model gemini-2.0-flash --temperature 0.3"""
        raise ValueError(error_msg)
    
    context_path = Path(context_file_path)
    
    # Validate context file exists and is readable
    if not context_path.exists():
        suggestions = suggest_context_file_corrections(context_file_path)
        error_msg = f"""Context file not found: {context_file_path}

💡 FILE PATH SUGGESTIONS:
{suggestions}

📋 WORKING EXAMPLES:
  # Generate context first
  generate-code-review . 
  
  # Then review the generated file
  review-with-ai tasks/code-review-context-*.md
  
  # Or generate and review in one step
  generate-code-review . && review-with-ai tasks/code-review-context-*.md
  
  # Use absolute path if needed
  review-with-ai /full/path/to/context.md"""
        
        raise FileNotFoundError(error_msg)
    
    if not context_path.is_file():
        if context_path.is_dir():
            context_files = list(context_path.glob('review-context-*.md'))
            if context_files:
                latest_context = max(context_files, key=lambda p: p.stat().st_mtime)
                error_msg = f"""Context path is a directory, not a file: {context_file_path}

Found context files in directory:
  {chr(10).join(f'  {f.name}' for f in sorted(context_files, key=lambda p: p.stat().st_mtime, reverse=True)[:5])}

Working examples:
  # Use specific context file
  review-with-ai {latest_context}
  
  # Use most recent context file with wildcard
  review-with-ai {context_path}/review-context-*.md"""
            else:
                error_msg = f"""Context path is a directory with no context files: {context_file_path}

Working examples:
  # Generate context first
  generate-code-review {context_path.parent if context_path.name == 'tasks' else context_path}
  
  # Then review generated file
  review-with-ai {context_path}/review-context-*.md"""
        else:
            error_msg = f"""Context path must be a file: {context_file_path}

Working examples:
  # Use .md context file
  review-with-ai tasks/review-context-20250101-120000.md
  
  # Generate context first if none exists
  generate-code-review . && review-with-ai tasks/review-context-*.md"""
        
        raise ValueError(error_msg)
    
    try:
        # Read context file content
        with open(context_path, 'r', encoding='utf-8') as f:
            context_content = f.read()
    except PermissionError as e:
        logger.error(f"Permission denied reading context file: {context_file_path}")
        raise e
    except Exception as e:
        logger.error(f"Error reading context file: {e}")
        raise e
    
    # Validate content is not empty
    if not context_content.strip():
        logger.warning(f"Context file is empty: {context_file_path}")
        # Continue anyway - Gemini might still provide useful feedback
    
    # Derive project path from context file location
    project_path = str(context_path.parent)
    
    # Validate model parameter if provided
    if model is not None:
        if not isinstance(model, str):
            error_msg = f"""Model must be a string, got {type(model)}

Working examples:
  # Use default model
  review-with-ai context.md
  
  # Specify model explicitly
  review-with-ai context.md --model gemini-2.0-flash
  
  # Use environment variable
  GEMINI_MODEL=gemini-2.5-pro-preview review-with-ai context.md"""
            raise ValueError(error_msg)
        if not model.strip():
            error_msg = """Model cannot be empty string

Working examples:
  # Use default model (recommended)
  review-with-ai context.md
  
  # Popular model choices
  review-with-ai context.md --model gemini-2.0-flash        # Fast
  review-with-ai context.md --model gemini-2.5-pro-preview  # Advanced
  review-with-ai context.md --model gemini-1.5-pro         # Reliable"""
            raise ValueError(error_msg)
        # Note: We don't validate specific model names as they may change
        # The Gemini integration will handle invalid models appropriately
    
    try:
        # Generate custom output filename if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            output_filename = f"code-review-ai-feedback-{timestamp}.md"
            output_path = str(context_path.parent / output_filename)
        
        # Modify context if custom prompt is provided
        if custom_prompt:
            logger.info("Using custom prompt for AI review")
            # Replace or modify the <user_instructions> section with custom prompt
            if '<user_instructions>' in context_content and '</user_instructions>' in context_content:
                # Extract everything before <user_instructions>
                before_instructions = context_content.split('<user_instructions>')[0]
                # Replace instructions with custom prompt
                modified_context = f"""{before_instructions}<user_instructions>
{custom_prompt}
</user_instructions>"""
                context_content = modified_context
            else:
                # If no <user_instructions> section exists, append custom prompt
                context_content += f"""

<user_instructions>
{custom_prompt}
</user_instructions>"""
        
        # Call Gemini integration
        logger.info(f"Generating AI review for context: {context_file_path}")
        
        # Send to Gemini with model parameter passed directly
        gemini_output = send_to_gemini_for_review(context_content, project_path, temperature, model)
        
        if gemini_output:
            logger.info(f"AI review generated successfully: {gemini_output}")
            return gemini_output
        else:
            logger.warning("AI review generation failed or returned no output")
            return None
            
    except Exception as e:
        logger.error(f"Error generating AI review: {e}")
        raise e


def validate_context_file_format(content: str) -> dict:
    """
    Validate and parse context file format.
    
    Args:
        content: Raw context file content
        
    Returns:
        Dictionary with parsed context information
    """
    # Basic validation - look for expected sections
    sections_found = {}
    
    expected_sections = [
        'overall_prd_summary',
        'current_phase_number',
        'total_phases'
    ]
    
    for section in expected_sections:
        if f"<{section}>" in content:
            sections_found[section] = True
        else:
            sections_found[section] = False
    
    # Extract scope information if present
    scope_info = "unknown"
    if "Review Scope:" in content:
        # Extract scope from header
        lines = content.split('\n')
        for line in lines:
            if "Review Scope:" in line:
                scope_info = line.split("Review Scope:")[-1].strip()
                break
    
    return {
        'sections_found': sections_found,
        'scope': scope_info,
        'valid_format': any(sections_found.values())
    }


def main():
    """
    Command-line interface for standalone AI code review generation.
    """
    parser = argparse.ArgumentParser(
        description="Generate AI-powered code review from context file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚀 QUICK START:
  # Step 1: Generate context (if you haven't already)
  generate-code-review .
  
  # Step 2: Review with AI
  review-with-ai tasks/code-review-context-*.md

📋 COMMON WORKFLOWS:
  # Generate and review in one step
  generate-code-review . && review-with-ai tasks/code-review-context-*.md
  
  # Review existing context file
  review-with-ai tasks/code-review-context-recent-phase-20241201-120000.md
  
  # Review with custom output location
  review-with-ai context.md --output reviews/ai-feedback-$(date +%Y%m%d).md

🎛️ TEMPERATURE CONTROL:
  # Focused/deterministic review (good for production code)
  review-with-ai context.md --temperature 0.0
  
  # Balanced review (default, recommended)
  review-with-ai context.md --temperature 0.5
  
  # Creative review (good for brainstorming)
  review-with-ai context.md --temperature 1.0

🤖 MODEL SELECTION:
  # Fast model (default, cost-effective)
  review-with-ai context.md --model gemini-2.0-flash
  
  # Advanced model (more detailed analysis)
  review-with-ai context.md --model gemini-2.5-pro-preview
  
  # Environment variable override
  GEMINI_MODEL=gemini-1.5-pro review-with-ai context.md

⚙️ ENVIRONMENT SETUP:
  # Using uvx (recommended)
  GEMINI_API_KEY=your_key uvx task-list-code-review-mcp review-with-ai context.md
  
  # With environment variable file
  echo "GEMINI_API_KEY=your_key" > .env && review-with-ai context.md
  
  # Temperature via environment
  GEMINI_TEMPERATURE=0.3 review-with-ai context.md

🛠️ UTILITY OPTIONS:
  # Validate context file format only (no AI call)
  review-with-ai context.md --validate-only
  
  # Verbose logging for debugging
  review-with-ai context.md --verbose
  
  # Custom model with specific temperature
  review-with-ai context.md --model gemini-2.5-pro-preview --temperature 0.2

💡 TIPS:
  - Use lower temperature (0.0-0.3) for production code reviews
  - Use higher temperature (0.7-1.0) for creative feedback
  - Always validate context files with --validate-only first
  - Use --verbose to debug API key or connection issues

🌐 GET API KEY: https://ai.google.dev/gemini-api/docs/api-key
        """
    )
    
    parser.add_argument(
        "context_file", 
        help="Path to code review context file (.md)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Custom output file path for AI review"
    )
    parser.add_argument(
        "--model", "-m",
        help="Gemini model to use (e.g., gemini-2.0-flash-exp, gemini-1.5-pro)"
    )
    parser.add_argument(
        "--validate-only", 
        action="store_true",
        help="Only validate context file format without generating review"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--temperature", 
        type=float, 
        default=0.5,
        help="Temperature for AI model (default: 0.5, range: 0.0-2.0)"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    try:
        # Validate and improve argument handling
        
        # Validate temperature range
        if not (0.0 <= args.temperature <= 2.0):
            error_msg = f"""Temperature must be between 0.0 and 2.0, got {args.temperature}

Working examples:
  # Deterministic/focused (good for code review)
  review-with-ai context.md --temperature 0.0
  
  # Balanced (default)
  review-with-ai context.md --temperature 0.5
  
  # Creative (good for brainstorming)
  review-with-ai context.md --temperature 1.0
  
  # Use environment variable
  GEMINI_TEMPERATURE=0.3 review-with-ai context.md"""
            logger.error(error_msg)
            sys.exit(1)
        
        # Validate output path if provided
        if args.output:
            output_dir = os.path.dirname(args.output)
            if output_dir and not os.path.exists(output_dir):
                error_msg = f"""Output directory does not exist: {output_dir}

Working examples:
  # Use existing directory
  review-with-ai context.md --output /tmp/review.md
  
  # Use relative path 
  review-with-ai context.md --output ./output/review.md
  
  # Create directory first
  mkdir -p /path/to/output && review-with-ai context.md --output /path/to/output/review.md
  
  # Or let tool auto-generate in project
  review-with-ai context.md  # creates in same directory as context"""
                logger.error(error_msg)
                sys.exit(1)
        
        # Validate context file path format (before checking existence for better error messages)
        if not args.context_file.endswith('.md'):
            logger.warning(f"Context file doesn't end with .md: {args.context_file}. Continuing anyway...")
        
        # Validate context file exists (with improved error handling in the function)
        context_path = Path(args.context_file)
        
        # Validate format if requested
        if args.validate_only:
            with open(context_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            validation_result = validate_context_file_format(content)
            
            print(f"Context file validation for: {args.context_file}")
            print(f"Valid format: {validation_result['valid_format']}")
            print(f"Scope: {validation_result['scope']}")
            print(f"Sections found: {validation_result['sections_found']}")
            
            if validation_result['valid_format']:
                print("✓ Context file format is valid")
                sys.exit(0)
            else:
                print("✗ Context file format is invalid or incomplete")
                sys.exit(1)
        
        # Handle temperature: CLI arg takes precedence, then env var, then default 0.5
        temperature = args.temperature
        if temperature == 0.5:  # Default value, check if env var should override
            temperature = float(os.getenv('GEMINI_TEMPERATURE', '0.5'))
        
        # Generate AI review
        logger.info(f"Processing context file: {args.context_file}")
        
        output_path = generate_ai_review(
            context_file_path=args.context_file,
            output_path=args.output,
            model=args.model,
            temperature=temperature
        )
        
        if output_path:
            print(f"AI review generated: {output_path}")
            sys.exit(0)
        else:
            print("AI review generation failed")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        sys.exit(1)
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


# Alias for test compatibility
generate_ai_code_review = generate_ai_review

if __name__ == "__main__":
    main()