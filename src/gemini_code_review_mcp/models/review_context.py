from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Sequence

from .review_mode import ReviewMode
from .task_info import TaskInfo


@dataclass(frozen=True, slots=True)
class ReviewContext:
    mode: ReviewMode
    default_prompt: str
    prd_summary: Optional[str] = None
    task_info: Optional[TaskInfo] = None
    changed_files: Sequence[str] = field(default_factory=tuple)
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if isinstance(self.changed_files, list):
            object.__setattr__(self, "changed_files", tuple(self.changed_files))
