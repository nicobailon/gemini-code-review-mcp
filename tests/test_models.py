from typing import get_type_hints

import pytest

from gemini_code_review_mcp.models import ReviewContext, ReviewMode, TaskInfo


class TestReviewMode:
    def test_review_mode_enum_values(self):
        assert ReviewMode.TASK_DRIVEN.name == "TASK_DRIVEN"
        assert ReviewMode.GENERAL_REVIEW.name == "GENERAL_REVIEW"
        assert ReviewMode.GITHUB_PR.name == "GITHUB_PR"

    def test_review_mode_string_values(self):
        assert ReviewMode.TASK_DRIVEN.value == "task_driven"
        assert ReviewMode.GENERAL_REVIEW.value == "general_review"
        assert ReviewMode.GITHUB_PR.value == "github_pr"
        assert isinstance(ReviewMode.TASK_DRIVEN.value, str)
        assert isinstance(ReviewMode.GENERAL_REVIEW.value, str)
        assert isinstance(ReviewMode.GITHUB_PR.value, str)


class TestTaskInfo:
    def test_task_info_creation(self):
        task = TaskInfo(
            phase_number="1.0", task_number="1.1", description="Implement feature X"
        )
        assert task.phase_number == "1.0"
        assert task.task_number == "1.1"
        assert task.description == "Implement feature X"

    def test_task_info_optional_task_number(self):
        task = TaskInfo(
            phase_number="2.0", task_number=None, description="Phase-level task"
        )
        assert task.phase_number == "2.0"
        assert task.task_number is None
        assert task.description == "Phase-level task"

    def test_task_info_frozen(self):
        task = TaskInfo(phase_number="1.0", task_number="1.1", description="Test task")
        with pytest.raises(AttributeError):
            task.phase_number = "2.0"

    def test_task_info_slots(self):
        assert hasattr(TaskInfo, "__slots__")
        task = TaskInfo(phase_number="1.0", task_number=None, description="Test")
        # Slots prevent adding new attributes
        # In Python 3.10+, we'd expect AttributeError, but with dataclasses
        # and slots, we might get TypeError. Let's test the behavior exists.
        with pytest.raises((AttributeError, TypeError)):
            task.new_attribute = "value"

    def test_task_info_type_hints(self):
        hints = get_type_hints(TaskInfo)
        assert hints["phase_number"] == str
        assert str(hints["task_number"]).startswith(
            "typing.Union[str, NoneType]"
        ) or str(hints["task_number"]).startswith("typing.Optional[str]")
        assert hints["description"] == str


class TestReviewContext:
    def test_review_context_creation_full(self):
        task_info = TaskInfo(
            phase_number="1.0", task_number="1.1", description="Test task"
        )
        context = ReviewContext(
            mode=ReviewMode.TASK_DRIVEN,
            prd_summary="Project summary",
            task_info=task_info,
            changed_files=["file1.py", "file2.ts"],
            default_prompt="Review the code",
        )
        assert context.mode == ReviewMode.TASK_DRIVEN
        assert context.prd_summary == "Project summary"
        assert context.task_info == task_info
        assert list(context.changed_files) == ["file1.py", "file2.ts"]
        assert context.default_prompt == "Review the code"

    def test_review_context_creation_minimal(self):
        context = ReviewContext(
            mode=ReviewMode.GENERAL_REVIEW,
            prd_summary=None,
            task_info=None,
            changed_files=[],
            default_prompt="General review",
        )
        assert context.mode == ReviewMode.GENERAL_REVIEW
        assert context.prd_summary is None
        assert context.task_info is None
        assert list(context.changed_files) == []
        assert context.default_prompt == "General review"

    def test_review_context_frozen(self):
        context = ReviewContext(
            mode=ReviewMode.GITHUB_PR,
            prd_summary=None,
            task_info=None,
            changed_files=["README.md"],
            default_prompt="PR review",
        )
        with pytest.raises(AttributeError):
            context.mode = ReviewMode.GENERAL_REVIEW

    def test_review_context_slots(self):
        assert hasattr(ReviewContext, "__slots__")
        context = ReviewContext(
            mode=ReviewMode.GENERAL_REVIEW,
            prd_summary=None,
            task_info=None,
            changed_files=[],
            default_prompt="Test",
        )
        # Slots prevent adding new attributes
        with pytest.raises((AttributeError, TypeError)):
            context.new_attribute = "value"

    def test_review_context_type_hints(self):
        hints = get_type_hints(ReviewContext)
        assert hints["mode"] == ReviewMode
        assert (
            str(hints["prd_summary"]).startswith("typing.Union[str, NoneType]")
            or str(hints["prd_summary"]).startswith("typing.Optional[str]")
            or str(hints["prd_summary"]) == "str | None"
        )
        assert (
            str(hints["task_info"]).startswith("typing.Union[")
            or str(hints["task_info"]).startswith("typing.Optional[")
        ) and "TaskInfo" in str(hints["task_info"])
        assert "Sequence" in str(hints["changed_files"]) or "typing.Sequence" in str(
            hints["changed_files"]
        )
        assert hints["default_prompt"] == str

    def test_review_context_sequence_immutability(self):
        files = ["file1.py", "file2.py"]
        context = ReviewContext(
            mode=ReviewMode.TASK_DRIVEN,
            prd_summary="Summary",
            task_info=None,
            changed_files=files,
            default_prompt="Review",
        )
        files.append("file3.py")
        assert len(context.changed_files) == 2
