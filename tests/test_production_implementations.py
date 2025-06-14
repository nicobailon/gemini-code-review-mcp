"""
Test production implementations with real filesystem operations.
These tests use temporary directories to ensure isolation.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from src.interfaces import ProductionFileSystem


class TestProductionFileSystem:
    def setup_method(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.fs = ProductionFileSystem()

    def teardown_method(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basic_operations(self):
        test_path = Path(self.temp_dir) / "test.txt"

        # Test exists
        assert not self.fs.exists(test_path)

        # Write and read
        self.fs.write_text(test_path, "Hello World")
        assert self.fs.exists(test_path)
        assert self.fs.is_file(test_path)
        assert not self.fs.is_dir(test_path)
        assert self.fs.read_text(test_path) == "Hello World"

        # Remove
        self.fs.remove(test_path)
        assert not self.fs.exists(test_path)

    def test_directory_operations(self):
        dir_path = Path(self.temp_dir) / "subdir"

        # Create directory
        self.fs.mkdir(dir_path)
        assert self.fs.exists(dir_path)
        assert self.fs.is_dir(dir_path)
        assert not self.fs.is_file(dir_path)

        # Create nested directory
        nested_path = dir_path / "nested"
        self.fs.mkdir(nested_path, parents=True)
        assert self.fs.exists(nested_path)

        # List directory
        test_file = dir_path / "test.txt"
        self.fs.write_text(test_file, "test")
        items = self.fs.list_dir(dir_path)
        assert len(items) == 2  # nested dir and test.txt

        # Remove directory
        self.fs.remove(test_file)
        self.fs.rmdir(nested_path)
        self.fs.rmdir(dir_path)
        assert not self.fs.exists(dir_path)

    def test_glob_operations(self):
        # Create test structure
        src_dir = Path(self.temp_dir) / "src"
        self.fs.mkdir(src_dir)
        self.fs.write_text(src_dir / "main.py", "")
        self.fs.write_text(src_dir / "utils.py", "")
        self.fs.write_text(src_dir / "README.md", "")

        # Test glob
        py_files = self.fs.glob(src_dir, "*.py")
        assert len(py_files) == 2
        assert all(f.suffix == ".py" for f in py_files)

        # Test recursive glob
        sub_dir = src_dir / "sub"
        self.fs.mkdir(sub_dir)
        self.fs.write_text(sub_dir / "helper.py", "")

        all_py = self.fs.glob(src_dir, "**/*.py")
        assert len(all_py) == 3

    def test_resolve_and_cwd(self):
        # Test resolve
        relative_path = Path("./test.txt")
        resolved = self.fs.resolve(relative_path)
        assert resolved.is_absolute()

        # Test get_cwd
        cwd = self.fs.get_cwd()
        assert cwd.is_absolute()
        assert cwd.exists()
