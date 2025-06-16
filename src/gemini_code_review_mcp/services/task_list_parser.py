#!/usr/bin/env python3
"""
Task list parsing and PRD summary generation module.

This module handles parsing of markdown task lists, extracting phase information,
and generating PRD-style summaries.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional, TypedDict, TypeGuard

# Import model configuration functions
try:
    from .gemini_api_client import load_api_key
    from ..helpers.model_config_manager import load_model_config
except ImportError:
    from gemini_api_client import load_api_key
    from helpers.model_config_manager import load_model_config

# Optional Gemini import for LLM summarization
genai: Any = None
types: Any = None

try:
    import google.genai as genai  # type: ignore
    from google.genai import types  # type: ignore
except ImportError:
    pass

GEMINI_AVAILABLE = genai is not None

logger = logging.getLogger(__name__)




# Type definitions for task list data structures
class SubtaskData(TypedDict):
    number: str
    description: str
    complete: bool


class PhaseData(TypedDict):
    number: str
    description: str
    subtasks: List[SubtaskData]
    subtasks_complete: bool
    subtasks_completed: List[str]


class PhaseInfo(TypedDict):
    current_phase_number: str
    current_phase_description: str
    previous_phase_completed: str
    next_phase: str
    subtasks_completed: List[str]


class TaskData(TypedDict):
    phases: List[PhaseData]
    total_phases: int
    current_phase_number: str
    current_phase_description: str
    previous_phase_completed: str
    next_phase: str
    subtasks_completed: List[str]


def create_minimal_task_data(number: str, description: str) -> TaskData:
    """Create minimal task data structure for non-task-driven reviews.
    
    Args:
        number: Phase number or review type (e.g., "PR Review", "General Review")
        description: Description of the review context
        
    Returns:
        Minimal TaskData dictionary
    """
    return {
        "total_phases": 0,
        "current_phase_number": number,
        "current_phase_description": description,
        "previous_phase_completed": "",
        "next_phase": "",
        "subtasks_completed": [],
        "phases": [],
    }


def is_phase_data(obj: Any) -> TypeGuard[PhaseData]:
    """Type guard for PhaseData validation."""
    return (
        isinstance(obj, dict)
        and "number" in obj
        and "description" in obj
        and "subtasks" in obj
    )


def parse_task_list(content: str) -> TaskData:
    """
    Parse task list content and extract phase information.

    Args:
        content: Raw markdown content of task list

    Returns:
        Dictionary with phase information
    """
    lines = content.strip().split("\n")
    phases: List[PhaseData] = []
    current_phase: Optional[PhaseData] = None

    # Phase pattern: ^- \[([ x])\] (\d+\.\d+) (.+)$
    phase_pattern = r"^- \[([ x])\] (\d+\.\d+) (.+)$"
    # Subtask pattern: ^  - \[([ x])\] (\d+\.\d+) (.+)$
    subtask_pattern = r"^  - \[([ x])\] (\d+\.\d+) (.+)$"

    for line in lines:
        phase_match = re.match(phase_pattern, line)
        if phase_match:
            completed = phase_match.group(1) == "x"
            number = phase_match.group(2)
            description = phase_match.group(3).strip()

            current_phase_dict: PhaseData = {
                "number": number,
                "description": description,
                "subtasks": [],
                "subtasks_complete": False,
                "subtasks_completed": [],
            }
            current_phase = current_phase_dict
            phases.append(current_phase)
            continue

        subtask_match = re.match(subtask_pattern, line)
        if subtask_match and current_phase:
            completed = subtask_match.group(1) == "x"
            number = subtask_match.group(2)
            description = subtask_match.group(3).strip()

            subtask: SubtaskData = {
                "number": number,
                "description": description,
                "complete": completed,
            }
            current_phase["subtasks"].append(subtask)

            if completed:
                current_phase["subtasks_completed"].append(f"{number} {description}")

    # Determine if each phase is complete (all subtasks complete)
    for phase in phases:
        if phase["subtasks"]:
            phase["subtasks_complete"] = all(st["complete"] for st in phase["subtasks"])
        else:
            phase["subtasks_complete"] = True

    result: TaskData = {
        "phases": phases,
        "total_phases": len(phases),
        **detect_current_phase(phases),
    }
    return result


def detect_current_phase(phases: List[PhaseData]) -> PhaseInfo:
    """
    Detect the most recently completed phase for code review.

    The logic prioritizes reviewing completed phases over in-progress ones:
    1. Find the most recently completed phase (all subtasks done)
    2. If no phases are complete, fall back to the current in-progress phase
    3. If all phases are complete, use the last phase

    Args:
        phases: List of phase dictionaries

    Returns:
        Dictionary with phase information for code review
    """
    if not phases:
        result: PhaseInfo = {
            "current_phase_number": "",
            "current_phase_description": "",
            "previous_phase_completed": "",
            "next_phase": "",
            "subtasks_completed": [],
        }
        return result

    # Find the most recently completed phase (all subtasks complete)
    review_phase = None
    for i in range(len(phases) - 1, -1, -1):  # Start from the end
        phase = phases[i]
        if phase["subtasks_complete"] and phase["subtasks"]:
            review_phase = phase
            break

    # If no completed phases found, find first phase with incomplete subtasks
    if review_phase is None:
        for phase in phases:
            if not phase["subtasks_complete"]:
                review_phase = phase
                break

    # If all phases complete or no phases found, use last phase
    if review_phase is None:
        review_phase = phases[-1]

    # Find the index of the review phase
    review_idx = None
    for i, phase in enumerate(phases):
        if phase["number"] == review_phase["number"]:
            review_idx = i
            break

    # Find previous completed phase
    previous_phase_completed = ""
    if review_idx is not None and review_idx > 0:
        prev_phase = phases[review_idx - 1]
        previous_phase_completed = f"{prev_phase['number']} {prev_phase['description']}"

    # Find next phase
    next_phase = ""
    if review_idx is not None and review_idx < len(phases) - 1:
        next_phase_obj = phases[review_idx + 1]
        next_phase = f"{next_phase_obj['number']} {next_phase_obj['description']}"

    result: PhaseInfo = {
        "current_phase_number": review_phase["number"],
        "current_phase_description": review_phase["description"],
        "previous_phase_completed": previous_phase_completed,
        "next_phase": next_phase,
        "subtasks_completed": review_phase["subtasks_completed"],
    }
    return result


def generate_prd_summary_from_task_list(task_data: TaskData) -> str:
    """
    Generate a PRD-style summary from task list content.

    Args:
        task_data: Parsed task list data

    Returns:
        Generated project summary string
    """
    phases: List[PhaseData] = task_data.get("phases", [])
    if not phases:
        return "Development project focused on code quality and feature implementation."

    # Extract high-level goals from phase descriptions
    phase_descriptions: List[str] = [p.get("description", "") for p in phases]

    # Create a coherent summary
    if len(phases) == 1:
        summary = f"Development project focused on {phase_descriptions[0].lower()}."
    elif len(phases) <= 3:
        summary = f"Development project covering: {', '.join(phase_descriptions[:-1]).lower()}, and {phase_descriptions[-1].lower()}."
    else:
        key_phases: List[str] = phase_descriptions[:3]
        summary = f"Multi-phase development project including {', '.join(key_phases).lower()}, and {len(phases) - 3} additional phases."

    return summary


def extract_prd_summary(content: str) -> str:
    """
    Extract PRD summary using multiple strategies.

    Args:
        content: Raw markdown content of PRD

    Returns:
        Extracted or generated summary
    """
    # Strategy 1: Look for explicit summary sections
    summary_patterns = [
        r"## Summary\n(.+?)(?=\n##|\Z)",
        r"## Overview\n(.+?)(?=\n##|\Z)",
        r"### Summary\n(.+?)(?=\n###|\Z)",
        r"## Executive Summary\n(.+?)(?=\n##|\Z)",
    ]

    for pattern in summary_patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            summary = match.group(1).strip()
            # Clean up the summary (remove extra whitespace, newlines)
            summary = re.sub(r"\s+", " ", summary)
            return summary

    # Strategy 2: Use Gemini if available and API key provided
    if GEMINI_AVAILABLE:
        try:
            api_key = load_api_key()
        except Exception:
            api_key = None
    else:
        api_key = None

    if GEMINI_AVAILABLE and api_key and genai is not None:
        try:
            client = genai.Client(api_key=api_key)
            first_2000_chars = content[:2000]

            # Use configurable model for PRD summarization
            config = load_model_config()
            summary_model = os.getenv(
                "GEMINI_SUMMARY_MODEL", config["defaults"]["summary_model"]
            )

            response = client.models.generate_content(
                model=summary_model,
                contents=[
                    f"Summarize this PRD in 2-3 sentences focusing on the main goal and key deliverables:\\n\\n{first_2000_chars}"
                ],
                config=(
                    types.GenerateContentConfig(max_output_tokens=150, temperature=0.1)
                    if types is not None
                    else None
                ),
            )

            return response.text.strip() if response.text else ""
        except Exception as e:
            logger.warning(f"Failed to generate LLM summary: {e}")

    # Strategy 3: Fallback - use first paragraph or first 200 characters
    lines = content.split("\n")
    content_lines = [
        line.strip() for line in lines if line.strip() and not line.startswith("#")
    ]

    if content_lines:
        first_paragraph = content_lines[0]
        if len(first_paragraph) > 200:
            first_paragraph = first_paragraph[:200] + "..."
        return first_paragraph

    # Ultimate fallback
    return "No summary available."
