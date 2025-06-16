from enum import Enum


class ReviewMode(Enum):
    """Review mode enumeration with explicit string values for serialization."""
    TASK_DRIVEN = "task_driven"
    GENERAL_REVIEW = "general_review"
    GITHUB_PR = "github_pr"
