"""
Integration tests for package installation and execution
"""

import os
import subprocess
import sys
import tempfile
import pytest
from pathlib import Path


class TestPackageInstallation:
    """Test package installation and basic functionality"""
    
    def test_package_builds_successfully(self):
        """Test that the package builds without errors"""
        result = subprocess.run(
            ["uvx", "--from", "build", "pyproject-build", "."],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Build failed: {result.stderr}"
        assert "Successfully built" in result.stdout
        
    def test_package_installs_from_local(self):
        """Test that uvx can install the package from local directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test installation
            result = subprocess.run(
                ["uvx", "--from", ".", "python", "-c", "import src.server; print('✓ Import successful')"],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"Installation failed: {result.stderr}"
            assert "✓ Import successful" in result.stdout
    
    def test_entry_point_exists(self):
        """Test that the main entry point function exists and is callable"""
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c", 
             "import src.server; assert hasattr(src.server, 'main'); print('✓ Entry point exists')"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Entry point test failed: {result.stderr}"
        assert "✓ Entry point exists" in result.stdout
    
    def test_dependencies_install_correctly(self):
        """Test that all required dependencies are available"""
        # Test the actual package imports that are used in the code
        dependencies = [
            ("mcp", "import mcp"),
            ("google-genai", "from google import genai"),  # google-genai provides google.genai
            ("python-dotenv", "import dotenv")  # python-dotenv provides dotenv
        ]
        
        for package_name, import_stmt in dependencies:
            result = subprocess.run(
                ["uvx", "--from", ".", "python", "-c", 
                 f"{import_stmt}; print('✓ {package_name} imported successfully')"],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"Dependency {package_name} import failed: {result.stderr}"
            assert f"✓ {package_name} imported successfully" in result.stdout


class TestPackageMetadata:
    """Test package metadata and configuration"""
    
    def test_package_metadata(self):
        """Test that package metadata is correctly configured"""
        import tomllib
        
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            config = tomllib.load(f)
        
        # Check basic metadata
        project = config["project"]
        assert project["name"] == "ai-dev-tasks-mcp"
        assert project["version"] == "1.0.0"
        assert "MCP server for generating code review context" in project["description"]
        assert project["requires-python"] == ">=3.8"
        
        # Check dependencies
        deps = project["dependencies"]
        assert "mcp>=0.1.0" in deps
        assert "google-genai>=0.1.0" in deps
        assert "python-dotenv>=1.0.0" in deps
        
        # Check scripts
        scripts = project["scripts"]
        assert "ai-dev-tasks-mcp" in scripts
        assert scripts["ai-dev-tasks-mcp"] == "src.server:main"
        
        # Check build system
        build_system = config["build-system"]
        assert build_system["requires"] == ["hatchling"]
        assert build_system["build-backend"] == "hatchling.build"


class TestPackageStructure:
    """Test package file structure and content"""
    
    def test_required_files_exist(self):
        """Test that all required package files exist"""
        base_path = Path(__file__).parent.parent
        required_files = [
            "pyproject.toml",
            "README.md", 
            "src/server.py",
            "src/generate_code_review_context.py"
        ]
        
        for file_path in required_files:
            full_path = base_path / file_path
            assert full_path.exists(), f"Required file missing: {file_path}"
    
    def test_source_imports_work(self):
        """Test that source modules can be imported correctly"""
        # Test that source files can be imported in a uvx environment with dependencies
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c", 
             "import sys; sys.path.insert(0, 'src'); "
             "import server; import generate_code_review_context; "
             "assert hasattr(server, 'main'); "
             "assert hasattr(generate_code_review_context, 'main'); "
             "print('✓ Source modules imported successfully')"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Source import failed: {result.stderr}"
        assert "✓ Source modules imported successfully" in result.stdout


class TestBuildArtifacts:
    """Test build artifacts and distribution files"""
    
    def test_dist_files_created(self):
        """Test that build creates proper distribution files"""
        dist_path = Path(__file__).parent.parent / "dist"
        
        if dist_path.exists():
            # Check for wheel file
            wheel_files = list(dist_path.glob("*.whl"))
            assert len(wheel_files) > 0, "No wheel file found in dist/"
            
            # Check for source distribution
            sdist_files = list(dist_path.glob("*.tar.gz"))
            assert len(sdist_files) > 0, "No source distribution found in dist/"
            
            # Check naming convention
            for wheel in wheel_files:
                assert "mcp_server_code_review" in wheel.name
                assert "1.0.0" in wheel.name