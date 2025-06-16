import pytest

from gemini_code_review_mcp.models import (
    ReviewContext,
    ReviewMode,
    TaskInfo,
    dict_to_review_context,
    review_context_to_dict,
)


class TestDictToReviewContext:
    def test_github_pr_mode(self):
        data = {
            "review_mode": "github_pr",
            "prd_summary": "PR description",
            "changed_files": ["file1.py", "file2.ts"],
            "auto_prompt_content": "Review this PR",
        }
        context = dict_to_review_context(data)
        assert context.mode == ReviewMode.GITHUB_PR
        assert context.prd_summary == "PR description"
        assert list(context.changed_files) == ["file1.py", "file2.ts"]
        assert context.default_prompt == "Review this PR"
        assert context.task_info is None

    def test_task_driven_mode(self):
        data = {
            "review_mode": "task_list_based",
            "total_phases": 5,
            "current_phase_number": "2.0",
            "current_phase_description": "Implement feature X",
            "task_number": "2.1",
            "prd_summary": "Project summary",
            "changed_files": [
                {"file_path": "src/feature.py", "additions": 50},
                {"file_path": "tests/test_feature.py", "additions": 30},
            ],
            "user_instructions": "Review phase 2",
        }
        context = dict_to_review_context(data)
        assert context.mode == ReviewMode.TASK_DRIVEN
        assert context.prd_summary == "Project summary"
        assert list(context.changed_files) == [
            "src/feature.py",
            "tests/test_feature.py",
        ]
        assert context.default_prompt == "Review phase 2"
        assert context.task_info is not None
        assert context.task_info.phase_number == "2.0"
        assert context.task_info.task_number == "2.1"
        assert context.task_info.description == "Implement feature X"

    def test_general_review_mode(self):
        data = {
            "review_mode": "task_list_based",
            "total_phases": 0,  # No task list
            "prd_summary": None,
            "changed_files": [],
            "scope": "full_project",
        }
        context = dict_to_review_context(data)
        assert context.mode == ReviewMode.GENERAL_REVIEW
        assert context.prd_summary is None
        assert list(context.changed_files) == []
        assert (
            context.default_prompt
            == "Conduct a comprehensive code review for the entire project."
        )
        assert context.task_info is None

    def test_minimal_data(self):
        data = {}
        context = dict_to_review_context(data)
        assert context.mode == ReviewMode.GENERAL_REVIEW
        assert context.prd_summary is None
        assert list(context.changed_files) == []
        assert (
            context.default_prompt == "Conduct a code review for the completed phase."
        )
        assert context.task_info is None


class TestReviewContextToDict:
    def test_github_pr_conversion(self):
        context = ReviewContext(
            mode=ReviewMode.GITHUB_PR,
            default_prompt="Review PR",
            prd_summary="PR summary",
            changed_files=["file1.py", "file2.py"],
        )
        data = review_context_to_dict(context)
        assert data["review_mode"] == "github_pr"
        assert data["prd_summary"] == "PR summary"
        assert data["changed_files"] == ["file1.py", "file2.py"]
        assert data["default_prompt"] == "Review PR"
        assert data["auto_prompt_content"] == "Review PR"

    def test_task_driven_conversion(self):
        task_info = TaskInfo(
            phase_number="3.0", task_number="3.2", description="Add tests"
        )
        context = ReviewContext(
            mode=ReviewMode.TASK_DRIVEN,
            default_prompt="Review task",
            prd_summary="Project PRD",
            task_info=task_info,
            changed_files=["test_file.py"],
        )
        data = review_context_to_dict(context)
        assert data["review_mode"] == "task_list_based"
        assert data["prd_summary"] == "Project PRD"
        assert data["changed_files"] == ["test_file.py"]
        assert data["current_phase_number"] == "3.0"
        assert data["current_phase_description"] == "Add tests"
        assert data["phase_number"] == "3.0"
        assert data["task_number"] == "3.2"

    def test_extra_data_merge(self):
        context = ReviewContext(
            mode=ReviewMode.GENERAL_REVIEW, default_prompt="General review"
        )
        extra_data = {
            "project_path": "/path/to/project",
            "file_tree": "tree output",
            "scope": "full_project",
        }
        data = review_context_to_dict(context, extra_data)
        assert data["review_mode"] == "task_list_based"
        assert data["project_path"] == "/path/to/project"
        assert data["file_tree"] == "tree output"
        assert data["scope"] == "full_project"

    def test_round_trip_conversion(self):
        original_data = {
            "review_mode": "task_list_based",
            "total_phases": 3,
            "current_phase_number": "1.0",
            "current_phase_description": "Setup project",
            "prd_summary": "Build a web app",
            "changed_files": ["src/app.py", "src/models.py"],
            "auto_prompt_content": "Review the setup phase",
        }

        # Convert to ReviewContext and back
        context = dict_to_review_context(original_data)
        converted_data = review_context_to_dict(context)

        # Check key fields are preserved
        assert converted_data["prd_summary"] == original_data["prd_summary"]
        assert converted_data["changed_files"] == original_data["changed_files"]
        assert (
            converted_data["current_phase_number"]
            == original_data["current_phase_number"]
        )
        assert (
            converted_data["current_phase_description"]
            == original_data["current_phase_description"]
        )
        assert (
            converted_data["auto_prompt_content"]
            == original_data["auto_prompt_content"]
        )
