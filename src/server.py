"""
FastMCP server for generating code review context from PRDs and git changes
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from fastmcp import FastMCP
    from generate_code_review_context import main as generate_review_context, load_model_config
    from ai_code_review import generate_ai_review
except ImportError as e:
    print(f"Required dependencies not available: {e}", file=sys.stderr)
    sys.exit(1)

# Create FastMCP server with ERROR log level to avoid info noise
mcp = FastMCP("MCP Server - Code Review Context Generator")

# Create alias for the app to match test expectations
app = mcp

# Create alias for main function to match test expectations
main = generate_review_context


@mcp.tool()
async def generate_branch_comparison_review(
    project_path: Optional[str] = None,
    compare_branch: Optional[str] = None,
    target_branch: Optional[str] = None,
    temperature: float = 0.5,
    enable_gemini_review: bool = True,
    include_claude_memory: bool = True,
    include_cursor_rules: bool = False
) -> dict:
    """Generate code review by comparing git branches with configuration discovery.
    
    Args:
        project_path: Absolute path to project root directory
        compare_branch: Source branch to compare (e.g., 'feature/auth-system')
        target_branch: Target branch for comparison (default: auto-detect main/master)
        temperature: Temperature for AI model (default: 0.5, range: 0.0-2.0)
        enable_gemini_review: Enable Gemini AI code review generation (default: true)
        include_claude_memory: Include CLAUDE.md files in context (default: true)
        include_cursor_rules: Include Cursor rules files in context (default: false)
    
    Returns:
        Success message with branch comparison results and generated files
    """
    try:
        # Validate required parameters per test expectations
        if not project_path:
            return {
                "status": "error",
                "error": "project_path is required"
            }
        
        if not compare_branch:
            return {
                "status": "error", 
                "error": "compare_branch is required"
            }
        
        if not os.path.isabs(project_path):
            return {
                "status": "error",
                "error": "project_path must be an absolute path"
            }
        
        if not os.path.exists(project_path):
            return {
                "status": "error", 
                "error": f"Project path does not exist: {project_path}"
            }
        
        if not os.path.isdir(project_path):
            return {
                "status": "error",
                "error": f"Project path must be a directory: {project_path}"
            }
        
        # Generate branch comparison review  
        import io
        import sys
        from contextlib import redirect_stdout, redirect_stderr
        
        # Capture stdout to detect error messages
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                output_file, gemini_file = generate_review_context(
                    project_path=project_path,
                    enable_gemini_review=enable_gemini_review,
                    temperature=temperature,
                    compare_branch=compare_branch,
                    target_branch=target_branch,
                    include_claude_memory=include_claude_memory,
                    include_cursor_rules=include_cursor_rules
                )
            
            # Check captured output for error indicators
            captured_output = stdout_capture.getvalue()
            if ("❌ Failed to compare branches" in captured_output or 
                "Source branch" in captured_output and "does not exist" in captured_output):
                return {
                    "status": "error", 
                    "error": f"Branch comparison failed: Source branch '{compare_branch}' does not exist"
                }
                
        except ValueError as e:
            # This catches explicit errors from the generate_review_context function
            return {
                "status": "error",
                "error": f"Branch comparison failed: {str(e)}"
            }
        
        # Build response with user-friendly feedback
        response_parts = []
        response_parts.append(f"🔍 Analyzed project: {os.path.basename(os.path.abspath(project_path))}")
        response_parts.append(f"🌿 Branch comparison: {compare_branch} → {target_branch or 'auto-detected'}")
        response_parts.append(f"🌡️ AI temperature: {temperature}")
        response_parts.append(f"📝 Generated review context: {os.path.basename(output_file)}")
        
        if gemini_file:
            response_parts.append(f"✅ AI code review completed: {os.path.basename(gemini_file)}")
        else:
            response_parts.append(f"⚠️ AI code review failed or was skipped (check API key and model availability)")
        
        response_parts.append(f"🎉 Branch comparison review completed!")
        
        # List generated files
        files_generated = [os.path.basename(output_file)]
        if gemini_file:
            files_generated.append(os.path.basename(gemini_file))
        response_parts.append(f"📄 Files generated: {', '.join(files_generated)}")
        
        # Return structured response for MCP tools
        return {
            "status": "success",
            "context_file": output_file,
            "ai_review_file": gemini_file,
            "branch_comparison_summary": {
                "project": os.path.basename(os.path.abspath(project_path)),
                "source_branch": compare_branch,
                "target_branch": target_branch or "auto-detected",
                "temperature": temperature,
                "files_generated": files_generated
            },
            "message": "\n".join(response_parts)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to generate branch comparison review: {str(e)}"
        }


@mcp.tool()
async def generate_pr_review(
    github_pr_url: Optional[str] = None,
    project_path: Optional[str] = None,
    temperature: float = 0.5,
    enable_gemini_review: bool = True,
    include_claude_memory: bool = True,
    include_cursor_rules: bool = False
) -> dict:
    """Generate code review for a GitHub Pull Request with configuration discovery.
    
    Args:
        github_pr_url: GitHub PR URL (e.g., 'https://github.com/owner/repo/pull/123')
        project_path: Optional local project path for context (default: current directory)
        temperature: Temperature for AI model (default: 0.5, range: 0.0-2.0)
        enable_gemini_review: Enable Gemini AI code review generation (default: true)
        include_claude_memory: Include CLAUDE.md files in context (default: true)
        include_cursor_rules: Include Cursor rules files in context (default: false)
    
    Returns:
        Success message with PR analysis results and generated files
    """
    try:
        # Validate required parameters per test expectations  
        if not github_pr_url:
            return {
                "status": "error",
                "error": "github_pr_url is required"
            }
        
        # Use current directory if project_path not provided
        if not project_path:
            project_path = os.getcwd()
        
        if not os.path.isabs(project_path):
            return {
                "status": "error",
                "error": "project_path must be an absolute path"
            }
        
        if not os.path.exists(project_path):
            return {
                "status": "error",
                "error": f"Project path does not exist: {project_path}"
            }
        
        if not os.path.isdir(project_path):
            return {
                "status": "error",
                "error": f"Project path must be a directory: {project_path}"
            }
        
        # Generate GitHub PR review
        import io
        import sys
        from contextlib import redirect_stdout, redirect_stderr
        
        # Capture stdout to detect error messages
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                output_file, gemini_file = generate_review_context(
                    project_path=project_path,
                    enable_gemini_review=enable_gemini_review,
                    temperature=temperature,
                    github_pr_url=github_pr_url,
                    include_claude_memory=include_claude_memory,
                    include_cursor_rules=include_cursor_rules
                )
            
            # Check captured output for error indicators
            captured_output = stdout_capture.getvalue()
            if ("❌ Failed to fetch PR data" in captured_output):
                # Extract the specific error message
                if "Invalid GitHub token" in captured_output:
                    error_msg = "Invalid GitHub token or insufficient permissions"
                elif "PR not found" in captured_output:
                    error_msg = "PR not found"
                elif "Invalid GitHub PR URL" in captured_output:
                    error_msg = "Invalid GitHub PR URL"
                else:
                    error_msg = "Failed to fetch PR data"
                
                return {
                    "status": "error",
                    "error": f"GitHub PR review failed: {error_msg}"
                }
                
        except ValueError as e:
            # This catches explicit errors from the generate_review_context function
            return {
                "status": "error",
                "error": f"GitHub PR review failed: {str(e)}"
            }
        
        # Build response with user-friendly feedback
        response_parts = []
        response_parts.append(f"🔍 Analyzed project: {os.path.basename(os.path.abspath(project_path))}")
        response_parts.append(f"🔗 GitHub PR: {github_pr_url}")
        response_parts.append(f"🌡️ AI temperature: {temperature}")
        response_parts.append(f"📝 Generated review context: {os.path.basename(output_file)}")
        
        if gemini_file:
            response_parts.append(f"✅ AI code review completed: {os.path.basename(gemini_file)}")
        else:
            response_parts.append(f"⚠️ AI code review failed or was skipped (check API key and model availability)")
        
        response_parts.append(f"🎉 GitHub PR review completed!")
        
        # List generated files
        files_generated = [os.path.basename(output_file)]
        if gemini_file:
            files_generated.append(os.path.basename(gemini_file))
        response_parts.append(f"📄 Files generated: {', '.join(files_generated)}")
        
        # Return structured response for MCP tools
        return {
            "status": "success",
            "context_file": output_file,
            "ai_review_file": gemini_file,
            "pr_summary": {
                "project": os.path.basename(os.path.abspath(project_path)),
                "pr_url": github_pr_url,
                "temperature": temperature,
                "files_generated": files_generated
            },
            "message": "\n".join(response_parts)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to generate GitHub PR review: {str(e)}"
        }


@mcp.tool()
def generate_code_review_context(
    project_path: str,
    scope: str = "recent_phase",
    phase_number: Optional[str] = None,
    task_number: Optional[str] = None,
    current_phase: Optional[str] = None,
    output_path: Optional[str] = None,
    enable_gemini_review: bool = True,
    temperature: float = 0.5,
    include_claude_memory: bool = True,
    include_cursor_rules: bool = False
) -> str:
    """Generate code review context with flexible scope options and configuration discovery.
    
    Args:
        project_path: Absolute path to project root directory
        scope: Review scope - 'recent_phase' (default), 'full_project', 'specific_phase', 'specific_task'
        phase_number: Phase number for specific_phase scope (e.g., '2.0')
        task_number: Task number for specific_task scope (e.g., '1.2')
        current_phase: Legacy phase override (e.g., '2.0'). If not provided, auto-detects from task list
        output_path: Custom output file path. If not provided, uses default timestamped path
        enable_gemini_review: Enable Gemini AI code review generation (default: true)
        temperature: Temperature for AI model (default: 0.5, range: 0.0-2.0)
        include_claude_memory: Include CLAUDE.md files in context (default: true)
        include_cursor_rules: Include Cursor rules files in context (default: false)
    
    Returns:
        Success message with generated content and output file path
    """
    
    # Comprehensive error handling to prevent TaskGroup issues
    try:
        # Validate project_path
        if not project_path:
            return "ERROR: project_path is required"
        
        if not os.path.isabs(project_path):
            return "ERROR: project_path must be an absolute path"
        
        if not os.path.exists(project_path):
            return f"ERROR: Project path does not exist: {project_path}"
        
        if not os.path.isdir(project_path):
            return f"ERROR: Project path must be a directory: {project_path}"
        
        # Handle temperature: MCP parameter takes precedence, then env var, then default 0.5
        if temperature == 0.5:  # Default value, check if env var should override
            temperature = float(os.getenv('GEMINI_TEMPERATURE', '0.5'))
        
        # Load model config to show capabilities info
        config = load_model_config()
        model_config = os.getenv('GEMINI_MODEL', config['defaults']['model'])
        # Resolve model aliases to actual API model names
        resolved_model = config['model_aliases'].get(model_config, model_config)
        
        # Detect capabilities
        supports_url_context = resolved_model in config['model_capabilities']['url_context_supported']
        supports_grounding = 'gemini-1.5' in resolved_model or 'gemini-2.0' in resolved_model or 'gemini-2.5' in resolved_model
        supports_thinking = resolved_model in config['model_capabilities']['thinking_mode_supported']
        
        # Check if features are actually enabled (considering disable flags)
        disable_url_context = os.getenv('DISABLE_URL_CONTEXT', 'false').lower() == 'true'
        disable_grounding = os.getenv('DISABLE_GROUNDING', 'false').lower() == 'true'
        disable_thinking = os.getenv('DISABLE_THINKING', 'false').lower() == 'true'
        
        actual_capabilities = []
        if supports_url_context and not disable_url_context: actual_capabilities.append("URL context")
        if supports_grounding and not disable_grounding: actual_capabilities.append("web grounding")
        if supports_thinking and not disable_thinking: actual_capabilities.append("thinking mode")
        
        # Generate review context using enhanced logic
        try:
            # Call the main function which now returns a tuple (context_file, gemini_file)
            output_file, gemini_file = generate_review_context(
                project_path=project_path,
                phase=current_phase,  # Legacy parameter
                output=output_path,
                enable_gemini_review=enable_gemini_review,
                scope=scope,
                phase_number=phase_number,
                task_number=task_number,
                temperature=temperature,
                include_claude_memory=include_claude_memory,
                include_cursor_rules=include_cursor_rules
            )
            
            # Build response with same feedback format as CLI
            response_parts = []
            response_parts.append(f"🔍 Analyzed project: {os.path.basename(os.path.abspath(project_path))}")
            response_parts.append(f"📊 Review scope: {scope}")
            if enable_gemini_review:
                response_parts.append(f"🌡️ AI temperature: {temperature}")
            
            response_parts.append(f"\n📝 Generated review context: {os.path.basename(output_file)}")
            
            if enable_gemini_review:
                response_parts.append(f"\n🤖 Using Gemini model: {resolved_model}")
                if actual_capabilities:
                    response_parts.append(f"✨ Enhanced features enabled: {', '.join(actual_capabilities)}")
                else:
                    response_parts.append(f"⚡ Standard features: Basic text generation")
                    
                if gemini_file:
                    response_parts.append(f"✅ AI code review completed: {os.path.basename(gemini_file)}")
                else:
                    response_parts.append(f"⚠️ AI code review failed or was skipped")
            
            # List generated files
            files_generated = [os.path.basename(output_file)]
            if gemini_file:
                files_generated.append(os.path.basename(gemini_file))
            response_parts.append(f"\n🎉 Code review process completed!")
            response_parts.append(f"📄 Files generated: {', '.join(files_generated)}")
            
            # Add file paths for reference
            response_parts.append(f"\nOutput files:")
            response_parts.append(f"- Context: {output_file}")
            if gemini_file:
                response_parts.append(f"- AI Review: {gemini_file}")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"ERROR: Error generating code review context: {str(e)}"
            
    except Exception as e:
        # Catch-all to ensure no exceptions escape the tool function
        return f"ERROR: Unexpected error: {str(e)}"


@mcp.tool()
def generate_ai_code_review(
    context_file_path: str,
    output_path: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.5
) -> str:
    """Generate AI-powered code review from existing context file.
    
    Args:
        context_file_path: Path to existing code review context file (.md)
        output_path: Custom output file path for AI review. If not provided, uses default timestamped path
        model: Optional Gemini model name (e.g., 'gemini-2.0-flash-exp', 'gemini-1.5-pro')
        temperature: Temperature for AI model (default: 0.5, range: 0.0-2.0)
    
    Returns:
        Success message with generated AI review content and output file path
    """
    
    # Comprehensive error handling
    try:
        # Validate context_file_path
        if not context_file_path:
            return "ERROR: context_file_path is required"
        
        if not os.path.isabs(context_file_path):
            return "ERROR: context_file_path must be an absolute path"
        
        if not os.path.exists(context_file_path):
            return f"ERROR: Context file does not exist: {context_file_path}"
        
        if not os.path.isfile(context_file_path):
            return f"ERROR: Context file path must be a file: {context_file_path}"
        
        # Handle temperature: MCP parameter takes precedence, then env var, then default 0.5
        if temperature == 0.5:  # Default value, check if env var should override
            temperature = float(os.getenv('GEMINI_TEMPERATURE', '0.5'))
        
        # Generate AI review using standalone tool
        try:
            output_file = generate_ai_review(
                context_file_path=context_file_path,
                output_path=output_path,
                model=model,
                temperature=temperature
            )
            
            if output_file:
                # Read the generated content to return
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    return f"Successfully generated AI code review: {output_file}\n\n{content}"
                    
                except Exception as e:
                    return f"AI review generated at {output_file}, but could not read content: {str(e)}"
            else:
                return "ERROR: AI review generation failed - no output file created"
            
        except Exception as e:
            return f"ERROR: Error generating AI code review: {str(e)}"
            
    except Exception as e:
        # Catch-all to ensure no exceptions escape the tool function
        return f"ERROR: Unexpected error: {str(e)}"



def main():
    """Entry point for uvx execution"""
    # FastMCP handles all the server setup, protocol, and routing
    # Use stdio transport explicitly (more reliable than SSE/streamable-http)
    mcp.run(transport="stdio", log_level="ERROR")


if __name__ == "__main__":
    main()