"""Enhanced AI code review tool with multi-phase support."""

import os
from datetime import datetime
from typing import List, Optional, Tuple, Union, cast

from ..config_types import CodeReviewConfig
from ..services.context_generator_enhanced import (
    generate_context_data_multi_phase,
    process_and_output_multi_phase_review,
)
from ..services.gemini_api_client import send_to_gemini_for_review
from ..services.meta_prompt_analyzer import generate_optimized_meta_prompt


async def generate_ai_code_review(
    context_file_path: Optional[str] = None,
    context_content: Optional[str] = None,
    project_path: Optional[str] = None,
    scope: str = "recent_phase",
    phase_number: Optional[str] = None,
    task_number: Optional[str] = None,
    task_list: Optional[str] = None,
    default_prompt: Optional[str] = None,
    output_path: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.5,
    custom_prompt: Optional[str] = None,
    text_output: bool = True,
    auto_meta_prompt: bool = True,
    include_claude_memory: bool = True,
    include_cursor_rules: bool = False,
    thinking_budget: Optional[int] = None,
    url_context: Optional[Union[str, List[str]]] = None,
    context_strategy: str = "balanced",
    max_context_tokens: Optional[int] = None,
    per_file_token_limit: int = 10_000,
    review_mode: str = "multi-phase",
    save_intermediate_files: bool = False,
) -> str:
    """
    Enhanced AI code review with automatic multi-phase support for large codebases.
    
    Same parameters as before, plus:
        context_strategy: Token management strategy
        max_context_tokens: Override token limit
        per_file_token_limit: Max tokens per file
        review_mode: "single", "multi-phase", or "overview-only"
    """
    try:
        # Validate input parameters
        provided_params = sum([
            context_file_path is not None,
            context_content is not None,
            project_path is not None,
        ])
        
        if provided_params == 0:
            raise ValueError(
                "One of context_file_path, context_content, or project_path is required"
            )
        elif provided_params > 1:
            raise ValueError(
                "Only one of context_file_path, context_content, or project_path should be provided"
            )
        
        # Handle temperature
        if temperature == 0.5:
            temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.5"))
        
        # Case 1: Review from existing context file or content
        if context_file_path is not None or context_content is not None:
            # Read context if file provided
            if context_file_path:
                if not os.path.isabs(context_file_path):
                    return "ERROR: context_file_path must be an absolute path"
                if not os.path.exists(context_file_path):
                    return f"ERROR: Context file does not exist: {context_file_path}"
                
                with open(context_file_path, "r", encoding="utf-8") as f:
                    context_content = f.read().strip()
            
            # Generate AI review
            if custom_prompt:
                review_content = f"{custom_prompt}\n\n{context_content}"
            else:
                review_content = f"""Please provide a comprehensive code review analysis for the following code context:

{context_content}

Focus on:
1. Code quality and best practices
2. Security vulnerabilities
3. Performance optimizations
4. Maintainability improvements
5. Documentation suggestions

Provide specific, actionable feedback with code examples where appropriate."""
            
            ai_review_content = send_to_gemini_for_review(
                context_content=review_content,
                temperature=temperature,
                model=model,
                return_text=True,
                thinking_budget=thinking_budget,
            )
            
            if not ai_review_content:
                return "ERROR: Gemini API failed to generate AI review"
            
            if text_output:
                return ai_review_content
            else:
                # Save to file
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                output_file = output_path or f"code-review-ai-feedback-{timestamp}.md"
                
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(ai_review_content)
                
                return f"AI code review saved to: {os.path.basename(output_file)}"
        
        # Case 2: Generate context from project and review
        if project_path is not None:
            if not os.path.isabs(project_path):
                return "ERROR: project_path must be an absolute path"
            if not os.path.exists(project_path):
                return f"ERROR: Project path does not exist: {project_path}"
            if not os.path.isdir(project_path):
                return f"ERROR: Project path must be a directory: {project_path}"
            
            # Generate meta prompt if requested
            auto_prompt_content = None
            if auto_meta_prompt:
                try:
                    meta_prompt_result = generate_optimized_meta_prompt(
                        project_path=project_path,
                        scope=scope,
                        temperature=temperature,
                        thinking_budget=thinking_budget,
                    )
                    auto_prompt_content = meta_prompt_result.get("generated_prompt")
                except Exception:
                    auto_prompt_content = None
            
            # Create configuration
            config = CodeReviewConfig(
                project_path=project_path,
                scope=scope,
                phase_number=phase_number,
                task_number=task_number,
                task_list=task_list,
                default_prompt=default_prompt or custom_prompt,
                temperature=temperature,
                enable_gemini_review=True,
                include_claude_memory=include_claude_memory,
                include_cursor_rules=include_cursor_rules,
                auto_prompt_content=auto_prompt_content,
                thinking_budget=thinking_budget,
                url_context=url_context,
                context_strategy=context_strategy,
                max_context_tokens=max_context_tokens,
                per_file_token_limit=per_file_token_limit,
                review_mode=review_mode,
                save_intermediate_files=save_intermediate_files,
            )
            
            # Generate context with multi-phase support
            base_data, multi_phase_context = generate_context_data_multi_phase(config)
            
            # Handle multi-phase
            if multi_phase_context and review_mode != "single":
                # Multi-phase review - handle both text and file output
                from ..services.context_generator_enhanced import PhaseResult
                
                if text_output:
                    # When text_output=True, we need PhaseResult objects
                    phase_results_raw = process_and_output_multi_phase_review(
                        config, base_data, multi_phase_context, return_phase_results=True
                    )
                    # Cast to List[PhaseResult] since we know return_phase_results=True
                    phase_results: List[PhaseResult] = cast(List[PhaseResult], phase_results_raw)
                    phase_file_results: List[Tuple[str, Optional[str]]] = []  # Initialize empty for type safety
                else:
                    # For file output, we get tuples
                    phase_results_raw = process_and_output_multi_phase_review(
                        config, base_data, multi_phase_context, return_phase_results=False
                    )
                    # Cast to List[Tuple] for file output
                    phase_file_results = cast(List[Tuple[str, Optional[str]]], phase_results_raw)
                    phase_results: List[PhaseResult] = []  # Initialize empty for type safety
                
                if text_output:
                    try:
                        # For text output, provide structured format with clear phase delimiters
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        review_parts = [
                            "# 🔄 MULTI-PHASE CODE REVIEW REPORT",
                            f"Generated: {timestamp}",
                            f"Project: {project_path}",
                            f"Model: {os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')}",
                            f"Total Phases: {len(phase_results)}",
                            f"Review Strategy: {config.context_strategy}",
                            "",
                            "=" * 80,
                            "",
                        ]
                        
                        # Add phase manifest information
                        if multi_phase_context and hasattr(multi_phase_context, 'manifest'):
                            review_parts.extend([
                                "## 📊 PHASE MANIFEST",
                                "",
                                multi_phase_context.manifest.to_markdown(),
                                "",
                                "=" * 80,
                                "",
                            ])
                        
                        # Process each phase with clear delimiters
                        phase_reviews = []
                        for phase_result in phase_results:
                            if hasattr(phase_result, 'review_content') and phase_result.review_content:
                                phase_reviews.append({
                                    'number': phase_result.phase_number,
                                    'name': phase_result.phase_name,
                                    'content': phase_result.review_content,
                                    'file_count': len(phase_result.context_content.split('### File:')) - 1 if hasattr(phase_result, 'context_content') else 0
                                })
                        
                        # Add individual phase reviews
                        for phase in phase_reviews:
                            review_parts.extend([
                                f"## 📄 PHASE {phase['number']}/{len(phase_results)}: {phase['name']}",
                                f"Files in phase: ~{phase['file_count']}",
                                "",
                                "### Phase Review Content:",
                                "",
                                phase['content'],
                                "",
                                "=" * 80,
                                "",
                            ])
                        
                        # Add synthesis section if multi-phase
                        if len(phase_results) > 1:
                            review_parts.extend([
                                "## 🎯 MULTI-PHASE SYNTHESIS",
                                "",
                                "### Key Findings Across All Phases:",
                                "- Review the individual phase feedback above for detailed analysis",
                                "- Each phase focuses on a specific subset of changes",
                                "- Combined, they provide comprehensive coverage of all modifications",
                                "",
                                "### Recommended Action Items:",
                                "1. Address critical issues identified in each phase",
                                "2. Review cross-phase dependencies and impacts",
                                "3. Prioritize based on severity and scope",
                                "",
                                "=" * 80,
                                "",
                            ])
                        
                        # Add metadata footer
                        review_parts.extend([
                            "## 📋 REVIEW METADATA",
                            f"- Review Type: Multi-Phase ({len(phase_results)} phases)",
                            f"- Total Token Count: {getattr(multi_phase_context, 'total_tokens', 'N/A')}",
                            f"- Token Limit per Phase: {getattr(multi_phase_context, 'token_limit', 60000)}",
                            f"- Save Intermediate Files: {config.save_intermediate_files}",
                            "",
                            "---",
                            "End of Multi-Phase Code Review Report",
                        ])
                        
                        return '\n'.join(review_parts)
                    except Exception as e:
                        import traceback
                        return f"ERROR: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                else:
                    # When not text output, phase_file_results are tuples
                    return f"Multi-phase AI review completed: {len(phase_file_results)} phases generated"
            else:
                # Single phase review
                from ..services.context_generator import (
                    generate_review_context_data,
                    process_and_output_review,
                )
                
                template_data = generate_review_context_data(config)
                _, review_path = process_and_output_review(config, template_data)
                
                if text_output and review_path:
                    with open(review_path, 'r', encoding='utf-8') as f:
                        return f.read()
                else:
                    return f"AI code review saved to: {os.path.basename(review_path) if review_path else 'N/A'}"
    
    except Exception as e:
        return f"ERROR: {str(e)}"
    
    # This should never be reached due to the validation at the beginning
    return "ERROR: No valid input provided"