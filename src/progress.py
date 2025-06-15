"""
Progress indicators for long-running operations.

This module provides simple console-based progress feedback
for operations like Git analysis and file processing.
"""

import sys
import time
from contextlib import contextmanager
from typing import Any, Callable, Optional


class ProgressIndicator:
    """Simple progress indicator for console output."""

    def __init__(self, message: str = "Processing", show_spinner: bool = True):
        self.message = message
        # Disable spinner for non-TTY environments (e.g., when piping output)
        self.is_tty = sys.stdout.isatty()
        self.show_spinner = show_spinner and self.is_tty
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0
        self.start_time = None
        self.is_running = False
        self.dot_count = 0

    def start(self) -> None:
        """Start showing progress."""
        self.start_time = time.time()
        self.is_running = True
        if self.is_tty and self.show_spinner:
            sys.stdout.write(f"\r{self.message} {self.spinner_chars[0]} ")
            sys.stdout.flush()
        elif not self.is_tty:
            # For non-TTY, print message once without carriage return
            sys.stdout.write(f"{self.message}")
            sys.stdout.flush()

    def update(self, additional_info: Optional[str] = None) -> None:
        """Update the progress indicator."""
        if not self.is_running:
            return

        if self.is_tty:
            # TTY environment - use spinner with carriage return
            if self.show_spinner:
                self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
                spinner = self.spinner_chars[self.spinner_index]
            else:
                spinner = "..."

            if additional_info:
                output = f"\r{self.message} {spinner} {additional_info} "
            else:
                output = f"\r{self.message} {spinner} "

            sys.stdout.write(output)
            sys.stdout.flush()
        else:
            # Non-TTY environment - print dots periodically
            self.dot_count += 1
            if self.dot_count % 10 == 0:  # Print a dot every 10 updates
                sys.stdout.write(".")
                sys.stdout.flush()

    def stop(self, final_message: Optional[str] = None) -> None:
        """Stop showing progress and show final message."""
        if not self.is_running:
            return

        self.is_running = False
        elapsed = time.time() - self.start_time if self.start_time else 0

        if self.is_tty:
            # TTY environment - use carriage return to overwrite line
            if final_message:
                sys.stdout.write(f"\r{final_message} ({elapsed:.1f}s)\n")
            else:
                sys.stdout.write(f"\r{self.message} ✓ ({elapsed:.1f}s)\n")
        else:
            # Non-TTY environment - complete the line
            if final_message:
                sys.stdout.write(f" {final_message} ({elapsed:.1f}s)\n")
            else:
                sys.stdout.write(f" done ({elapsed:.1f}s)\n")
        sys.stdout.flush()


@contextmanager
def progress(message: str = "Processing", show_spinner: bool = True):
    """
    Context manager for showing progress.

    Example:
        with progress("Analyzing Git history"):
            # Long running operation
            time.sleep(2)
    """
    indicator = ProgressIndicator(message, show_spinner)
    indicator.start()
    try:
        yield indicator
    finally:
        indicator.stop()


def progress_callback(message: str = "Processing") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for functions that need progress indication.

    Example:
        @progress_callback("Loading files")
        def load_large_dataset():
            # Long operation
            pass
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with progress(message):
                return func(*args, **kwargs)

        return wrapper

    return decorator


class MultiStepProgress:
    """Progress indicator for multi-step operations."""

    def __init__(self, steps: list[str]):
        self.steps = steps
        self.current_step = 0
        self.total_steps = len(steps)
        self.start_time = time.time()

    def next_step(self) -> None:
        """Move to the next step."""
        if self.current_step < self.total_steps:
            step_name = self.steps[self.current_step]
            print(f"[{self.current_step + 1}/{self.total_steps}] {step_name}...")
            self.current_step += 1

    def complete(self) -> None:
        """Mark all steps as complete."""
        elapsed = time.time() - self.start_time
        print(f"✅ All steps completed ({elapsed:.1f}s total)")


# Console output helpers
def print_info(message: str) -> None:
    """Print an informational message."""
    print(f"ℹ️  {message}")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"✅ {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"⚠️  {message}", file=sys.stderr)


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"❌ {message}", file=sys.stderr)


def print_step(step_number: int, total_steps: int, message: str) -> None:
    """Print a step in a multi-step process."""
    print(f"[{step_number}/{total_steps}] {message}")
