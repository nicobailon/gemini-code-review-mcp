from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class TaskInfo:
    phase_number: str
    task_number: Optional[str]
    description: str
