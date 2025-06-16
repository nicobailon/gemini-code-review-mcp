"""Test progress indicators."""

import sys
import time
from io import StringIO

import pytest

from gemini_code_review_mcp.progress import (
    MultiStepProgress,
    ProgressIndicator,
    print_error,
    print_info,
    print_step,
    print_success,
    print_warning,
    progress,
    progress_callback,
)


class TestProgressIndicator:
    def test_basic_progress_indicator(self, capsys):
        indicator = ProgressIndicator("Testing", show_spinner=False)
        indicator.start()
        indicator.stop()

        captured = capsys.readouterr()
        assert "Testing" in captured.out
        # In non-TTY environments (like tests), it prints "done" instead of "✓"
        assert "done" in captured.out or "✓" in captured.out

    def test_progress_with_spinner(self, capsys):
        indicator = ProgressIndicator("Processing", show_spinner=True)
        indicator.start()
        indicator.update()
        indicator.update("50% complete")
        indicator.stop("Done")

        captured = capsys.readouterr()
        assert "Processing" in captured.out
        assert "Done" in captured.out

    def test_progress_not_running(self):
        indicator = ProgressIndicator("Test")
        # Should not crash when update/stop called without start
        indicator.update()
        indicator.stop()


class TestProgressContext:
    def test_progress_context_manager(self, capsys):
        with progress("Loading data"):
            time.sleep(0.01)  # Simulate work

        captured = capsys.readouterr()
        assert "Loading data" in captured.out
        # In non-TTY environments (like tests), it prints "done" instead of "✓"
        assert "done" in captured.out or "✓" in captured.out

    def test_progress_context_with_error(self, capsys):
        try:
            with progress("Processing"):
                raise ValueError("Test error")
        except ValueError:
            pass

        captured = capsys.readouterr()
        assert "Processing" in captured.out

    def test_progress_decorator(self, capsys):
        @progress_callback("Decorated function")
        def test_function():
            return "result"

        result = test_function()
        assert result == "result"

        captured = capsys.readouterr()
        assert "Decorated function" in captured.out


class TestMultiStepProgress:
    def test_multi_step_progress(self, capsys):
        steps = ["Step 1", "Step 2", "Step 3"]
        progress = MultiStepProgress(steps)

        progress.next_step()
        progress.next_step()
        progress.next_step()
        progress.complete()

        captured = capsys.readouterr()
        assert "[1/3] Step 1..." in captured.out
        assert "[2/3] Step 2..." in captured.out
        assert "[3/3] Step 3..." in captured.out
        assert "✅ All steps completed" in captured.out

    def test_multi_step_beyond_limit(self):
        steps = ["Step 1"]
        progress = MultiStepProgress(steps)

        # Should not crash when going beyond steps
        progress.next_step()
        progress.next_step()  # Beyond limit
        progress.complete()


class TestConsoleHelpers:
    def test_print_info(self, capsys):
        print_info("Information message")
        captured = capsys.readouterr()
        assert "ℹ️  Information message" in captured.out

    def test_print_success(self, capsys):
        print_success("Success message")
        captured = capsys.readouterr()
        assert "✅ Success message" in captured.out

    def test_print_warning(self, capsys):
        print_warning("Warning message")
        captured = capsys.readouterr()
        assert "⚠️  Warning message" in captured.err

    def test_print_error(self, capsys):
        print_error("Error message")
        captured = capsys.readouterr()
        assert "❌ Error message" in captured.err

    def test_print_step(self, capsys):
        print_step(2, 5, "Processing item")
        captured = capsys.readouterr()
        assert "[2/5] Processing item" in captured.out
