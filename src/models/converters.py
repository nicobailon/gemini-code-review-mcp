from typing import Dict, List, Optional, TypedDict, Union

from .review_context import ReviewContext
from .review_mode import ReviewMode
from .task_info import TaskInfo


class FilePathDict(TypedDict, total=False):
    """Type for file path dictionary in changed_files."""
    file_path: Union[str, int, float]


# Input data structure - using TypedDict for known fields
class ReviewContextData(TypedDict, total=False):
    """Type definition for review context data."""
    review_mode: str
    total_phases: Union[int, float]
    current_phase_number: Union[str, int, float]
    current_phase_description: str
    task_number: Union[str, int, float, None]
    changed_files: List[Union[str, FilePathDict]]
    auto_prompt_content: str
    user_instructions: str
    scope: str
    prd_summary: Optional[str]


def dict_to_review_context(data: Dict[str, object]) -> ReviewContext:
    """
    Convert legacy dictionary format to ReviewContext.

    This function handles the conversion from the old Dict[str, Any] format
    to the new typed ReviewContext dataclass.
    """
    # Determine review mode
    review_mode_str = data.get("review_mode", "task_list_based")
    if review_mode_str == "github_pr":
        mode = ReviewMode.GITHUB_PR
    elif review_mode_str == "task_list_based":
        # Check if we have task data to determine if it's task driven
        total_phases = data.get("total_phases", 0)
        if isinstance(total_phases, (int, float)) and total_phases > 0:
            mode = ReviewMode.TASK_DRIVEN
        else:
            mode = ReviewMode.GENERAL_REVIEW
    else:
        mode = ReviewMode.GENERAL_REVIEW

    # Extract task info if available
    task_info = None
    phase_num = data.get("current_phase_number")
    phase_desc = data.get("current_phase_description")
    if phase_num is not None and phase_desc is not None and isinstance(phase_desc, str):
        task_info = TaskInfo(
            phase_number=str(phase_num),
            task_number=(
                str(data.get("task_number")) if data.get("task_number") else None
            ),
            description=phase_desc,
        )

    # Extract changed files
    changed_files: List[str] = []
    changed_files_data = data.get("changed_files", [])
    if isinstance(changed_files_data, list):
        # Could be list of dicts or list of strings
        # We handle the unknown item types by checking isinstance
        for idx in range(len(changed_files_data)):
            item = changed_files_data[idx]
            if isinstance(item, dict):
                # Type guard ensures item is dict here
                if "file_path" in item:
                    file_path = item["file_path"]
                    if isinstance(file_path, str):
                        changed_files.append(file_path)
                    elif isinstance(file_path, (int, float)):
                        changed_files.append(str(file_path))
            elif isinstance(item, str):
                changed_files.append(item)

    # Extract default prompt from user instructions or auto prompt
    default_prompt = ""
    auto_prompt = data.get("auto_prompt_content")
    if isinstance(auto_prompt, str):
        default_prompt = auto_prompt
    else:
        user_instructions = data.get("user_instructions")
        if isinstance(user_instructions, str):
            default_prompt = user_instructions
    
    # If still no prompt, generate a default based on scope
    if not default_prompt:
        scope = data.get("scope", "recent_phase")
        if scope == "full_project":
            default_prompt = (
                "Conduct a comprehensive code review for the entire project."
            )
        elif scope == "specific_task":
            default_prompt = "Conduct a code review for this specific task."
        else:
            default_prompt = "Conduct a code review for the completed phase."

    # Get prd_summary safely
    prd_summary = data.get("prd_summary")
    prd_summary_str = str(prd_summary) if isinstance(prd_summary, str) else None
    
    return ReviewContext(
        mode=mode,
        default_prompt=default_prompt,
        prd_summary=prd_summary_str,
        task_info=task_info,
        changed_files=changed_files,
    )


# Output data structure
class ReviewContextDict(TypedDict, total=False):
    """Type definition for review context dictionary output."""
    review_mode: str
    prd_summary: Optional[str]
    changed_files: List[str]
    default_prompt: str
    auto_prompt_content: str
    current_phase_number: str
    current_phase_description: str
    phase_number: Optional[str]
    task_number: Optional[str]


def review_context_to_dict(
    context: ReviewContext, extra_data: Optional[Dict[str, object]] = None
) -> Dict[str, object]:
    """
    Convert ReviewContext to dictionary format for backward compatibility.

    This function converts the typed ReviewContext back to the legacy dictionary
    format for compatibility with existing code that expects Dict[str, Any].

    Args:
        context: The ReviewContext to convert
        extra_data: Additional data to merge into the result dictionary
    """
    result: Dict[str, object] = {
        "review_mode": (
            "github_pr" if context.mode == ReviewMode.GITHUB_PR else "task_list_based"
        ),
        "prd_summary": context.prd_summary,
        "changed_files": list(context.changed_files),
        "default_prompt": context.default_prompt,
        "auto_prompt_content": context.default_prompt,  # For backward compatibility
    }

    # Add task-related fields if we have task info
    if context.task_info:
        result.update(
            {
                "current_phase_number": context.task_info.phase_number,
                "current_phase_description": context.task_info.description,
                "phase_number": (
                    context.task_info.phase_number
                    if context.mode == ReviewMode.TASK_DRIVEN
                    else None
                ),
                "task_number": context.task_info.task_number,
            }
        )

    # Merge extra data if provided
    if extra_data:
        result.update(extra_data)
    
    return result