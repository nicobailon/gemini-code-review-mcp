from typing import Any, Dict, List, Optional, Union

from .review_context import ReviewContext
from .review_mode import ReviewMode
from .task_info import TaskInfo


def dict_to_review_context(data: Dict[str, Any]) -> ReviewContext:
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
        if data.get("total_phases", 0) > 0:
            mode = ReviewMode.TASK_DRIVEN
        else:
            mode = ReviewMode.GENERAL_REVIEW
    else:
        mode = ReviewMode.GENERAL_REVIEW

    # Extract task info if available
    task_info = None
    if data.get("current_phase_number") and data.get("current_phase_description"):
        task_info = TaskInfo(
            phase_number=str(data["current_phase_number"]),
            task_number=(
                str(data.get("task_number")) if data.get("task_number") else None
            ),
            description=data["current_phase_description"],
        )

    # Extract changed files
    changed_files_data: Union[List[Union[str, Dict[str, Any]]], Any] = data.get("changed_files", [])
    changed_files: List[str] = []
    if isinstance(changed_files_data, list):
        # Could be list of dicts or list of strings
        item: Union[str, Dict[str, Any]]
        for item in changed_files_data:
            if isinstance(item, dict) and "file_path" in item:
                file_path: Optional[Any] = item.get("file_path")
                if file_path is not None and isinstance(file_path, (str, int, float)):
                    changed_files.append(str(file_path))
            elif isinstance(item, str):
                changed_files.append(item)
    else:
        changed_files = []

    # Extract default prompt from user instructions or auto prompt
    default_prompt = ""
    if data.get("auto_prompt_content"):
        default_prompt = data["auto_prompt_content"]
    elif data.get("user_instructions"):
        default_prompt = data["user_instructions"]
    else:
        # Generate a default prompt based on scope
        scope = data.get("scope", "recent_phase")
        if scope == "full_project":
            default_prompt = (
                "Conduct a comprehensive code review for the entire project."
            )
        elif scope == "specific_task":
            default_prompt = "Conduct a code review for this specific task."
        else:
            default_prompt = "Conduct a code review for the completed phase."

    return ReviewContext(
        mode=mode,
        default_prompt=default_prompt,
        prd_summary=data.get("prd_summary"),
        task_info=task_info,
        changed_files=changed_files,
    )


def review_context_to_dict(
    context: ReviewContext, extra_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convert ReviewContext to dictionary format for backward compatibility.

    This function converts the typed ReviewContext back to the legacy dictionary
    format for compatibility with existing code that expects Dict[str, Any].

    Args:
        context: The ReviewContext to convert
        extra_data: Additional data to merge into the result dictionary
    """
    result = {
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
