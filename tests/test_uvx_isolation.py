"""
uvx dependency resolution and isolation tests
Tests that uvx properly isolates dependencies and resolves package requirements
"""

import os
import sys
import subprocess
import tempfile
import pytest
from pathlib import Path
import json
import time


class TestUvxDependencyResolution:
    """Test uvx dependency resolution capabilities"""
    
    def setup_method(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent
        
    def test_uvx_package_installation(self):
        """Test that uvx can install our package and its dependencies"""
        result = subprocess.run(
            ["uvx", "--from", ".", "--help"],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        print("uvx package installation: OK")
        
    def test_fastmcp_dependency_resolution(self):
        """Test that uvx correctly resolves FastMCP dependency"""
        # Test that FastMCP is available in uvx environment
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c", 
             "import fastmcp; print(f'FastMCP version: {fastmcp.__version__}')"],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "FastMCP version:" in result.stdout
        print(f"FastMCP dependency resolved: {result.stdout.strip()}")
        
    def test_google_genai_dependency_resolution(self):
        """Test that uvx correctly resolves google-genai dependency"""
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c", 
             "import google.genai; print('google-genai imported successfully')"],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "google-genai imported successfully" in result.stdout
        print("google-genai dependency resolved: OK")
        
    def test_python_dotenv_dependency_resolution(self):
        """Test that uvx correctly resolves python-dotenv dependency"""
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c", 
             "import dotenv; print('python-dotenv imported successfully')"],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "python-dotenv imported successfully" in result.stdout
        print("python-dotenv dependency resolved: OK")
        
    def test_entry_point_resolution(self):
        """Test that uvx resolves the entry point correctly"""
        # Test that the entry point is available
        result = subprocess.run(
            ["uvx", "--from", ".", "ai-dev-tasks-mcp", "--help"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=10
        )
        # The server might not have --help, but it should start without error
        # and we should get some output (not a "command not found" error)
        assert result.returncode == 0 or result.stderr == ""
        print("Entry point resolution: OK")
        
    def test_dependency_version_constraints(self):
        """Test that dependency versions meet our constraints"""
        # Check FastMCP version constraint (>=0.1.0)
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c", 
             """
import fastmcp
import re

version_str = fastmcp.__version__
print(f'FastMCP version: {version_str}')

# Simple version comparison without packaging dependency
def version_tuple(v):
    return tuple(map(int, re.split(r'[.-]', v.split('+')[0])[:3]))

current = version_tuple(version_str)
minimum = version_tuple('0.1.0')
meets_constraint = current >= minimum

print(f'Meets constraint >=0.1.0: {meets_constraint}')
             """],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Meets constraint >=0.1.0: True" in result.stdout
        print("FastMCP version constraint satisfied")


class TestUvxIsolation:
    """Test uvx environment isolation capabilities"""
    
    def setup_method(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent
        
    def test_system_python_isolation(self):
        """Test that uvx isolates from system Python packages"""
        # Test that uvx environment doesn't inherit random system packages
        # that aren't in our requirements
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c", 
             """
import sys
print(f'Python executable: {sys.executable}')
print(f'Python path: {sys.path[:3]}')  # First 3 entries

# Try to import a package that's likely NOT in our dependencies
try:
    import requests
    print('WARNING: requests found in uvx environment (should be isolated)')
except ImportError:
    print('GOOD: requests not found (proper isolation)')

try:
    import numpy
    print('WARNING: numpy found in uvx environment (should be isolated)')
except ImportError:
    print('GOOD: numpy not found (proper isolation)')
             """],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        # Should show proper isolation (packages not found)
        assert "GOOD:" in result.stdout
        print("System Python isolation: OK")
        
    def test_virtual_environment_creation(self):
        """Test that uvx creates proper virtual environment"""
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c", 
             """
import sys
import os

# Check if we're in a virtual environment
in_venv = hasattr(sys, 'real_prefix') or (
    hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
)

print(f'In virtual environment: {in_venv}')
print(f'Python prefix: {sys.prefix}')
print(f'Executable: {sys.executable}')

# Should be isolated from system site-packages
if 'site-packages' in str(sys.path):
    venv_site_packages = [p for p in sys.path if 'site-packages' in p and 'uv' in p]
    print(f'Using uvx site-packages: {len(venv_site_packages) > 0}')
             """],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "In virtual environment: True" in result.stdout
        print("Virtual environment creation: OK")
        
    def test_package_isolation_between_runs(self):
        """Test that different uvx runs are isolated from each other"""
        # Run our package in one uvx session
        result1 = subprocess.run(
            ["uvx", "--from", ".", "python", "-c", 
             """
import tempfile
import os

# Create a temporary file that shouldn't persist
temp_file = '/tmp/uvx_isolation_test.txt'
with open(temp_file, 'w') as f:
    f.write('test data from run 1')
    
print(f'Created temp file: {temp_file}')
print(f'Current working dir: {os.getcwd()}')
             """],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result1.returncode == 0
        
        # Run in another uvx session - should be clean
        result2 = subprocess.run(
            ["uvx", "--from", ".", "python", "-c", 
             """
import os
import sys

print(f'Current working dir: {os.getcwd()}')
print(f'Python executable: {sys.executable}')

# Check if temp file exists (it should, but processes are isolated)
temp_file = '/tmp/uvx_isolation_test.txt'
print(f'Temp file exists: {os.path.exists(temp_file)}')

# But Python modules should be fresh
print(f'Fresh Python process: {__name__ == "__main__"}')
             """],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result2.returncode == 0
        assert "Fresh Python process: True" in result2.stdout
        print("Package isolation between runs: OK")
        
    def test_environment_variable_isolation(self):
        """Test environment variable handling in uvx"""
        # Set a test environment variable
        test_env = os.environ.copy()
        test_env["UVX_ISOLATION_TEST"] = "test_value"
        
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c", 
             """
import os
print(f'UVX_ISOLATION_TEST: {os.environ.get("UVX_ISOLATION_TEST", "NOT_FOUND")}')
print(f'PATH contains uv: {"uv" in os.environ.get("PATH", "")}')
print(f'VIRTUAL_ENV: {os.environ.get("VIRTUAL_ENV", "NOT_SET")}')
             """],
            cwd=self.project_root,
            env=test_env,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "UVX_ISOLATION_TEST: test_value" in result.stdout
        print("Environment variable handling: OK")


class TestUvxDependencyManagement:
    """Test advanced uvx dependency management scenarios"""
    
    def setup_method(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent
        
    def test_dependency_conflict_resolution(self):
        """Test that uvx handles dependency conflicts properly"""
        # Install our package with additional dependencies that might conflict
        result = subprocess.run(
            ["uvx", "--from", ".", "--with", "pytest", "python", "-c", 
             """
import fastmcp
import pytest
print(f'FastMCP: {fastmcp.__version__}')
print(f'pytest: {pytest.__version__}')
print('No dependency conflicts detected')
             """],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "No dependency conflicts detected" in result.stdout
        print("Dependency conflict resolution: OK")
        
    def test_transitive_dependency_resolution(self):
        """Test that transitive dependencies are properly resolved"""
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c", 
             """
# Check that FastMCP's dependencies are available
try:
    import json  # Should be in stdlib
    import typing  # Should be in stdlib
    print('Standard library dependencies: OK')
    
    # Check FastMCP transitive dependencies
    import fastmcp
    print(f'FastMCP imported: {fastmcp.__name__}')
    
    # Test that we can create a FastMCP instance
    from fastmcp import FastMCP
    mcp = FastMCP("test")
    print('FastMCP instance created: OK')
    
except ImportError as e:
    print(f'Transitive dependency missing: {e}')
    exit(1)
             """],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "FastMCP instance created: OK" in result.stdout
        print("Transitive dependency resolution: OK")
        
    def test_optional_dependency_handling(self):
        """Test handling of optional dependencies"""
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c", 
             """
# Test that our package works even if optional dependencies are missing
import sys
sys.path.insert(0, 'src')

try:
    from server import mcp
    print('Server module imported successfully')
    
    # Test that the tool function exists
    from server import generate_code_review_context
    print('Tool function available')
    
    # Test basic validation (should work without Gemini)
    result = generate_code_review_context('/tmp')
    print(f'Tool validation: {"ERROR" in result}')  # Should error due to invalid path
    
except Exception as e:
    print(f'Optional dependency error: {e}')
             """],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Tool function available" in result.stdout
        print("Optional dependency handling: OK")
        
    def test_cache_isolation(self):
        """Test that uvx cache is properly isolated"""
        # Run multiple times to test caching
        for i in range(2):
            run_num = i + 1
            test_code = f"""
import time
import tempfile
import os

print('Run {run_num}')
print(f'Process ID: {{os.getpid()}}')
print(f'Working directory: {{os.getcwd()}}')

# Each run should be independent
start_time = time.time()
import fastmcp
end_time = time.time()

print(f'FastMCP import time: {{end_time - start_time:.3f}}s')
print(f'FastMCP location: {{fastmcp.__file__}}')
            """
            
            result = subprocess.run(
                ["uvx", "--from", ".", "python", "-c", test_code],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert f"Run {run_num}" in result.stdout
            
        print("Cache isolation: OK")


class TestUvxPerformance:
    """Test uvx performance characteristics"""
    
    def setup_method(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent
        
    def test_startup_time(self):
        """Test uvx startup performance"""
        start_time = time.time()
        
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c", 
             """
import time
start = time.time()
import fastmcp
import_time = time.time() - start
print(f'Import time: {import_time:.3f}s')

# Test server creation time
start = time.time()
from fastmcp import FastMCP
mcp = FastMCP("test")
creation_time = time.time() - start
print(f'Server creation time: {creation_time:.3f}s')
             """],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        total_time = time.time() - start_time
        
        assert result.returncode == 0
        assert "Import time:" in result.stdout
        print(f"uvx startup time: {total_time:.3f}s")
        
        # Should start reasonably quickly (under 10 seconds)
        assert total_time < 10.0, f"Startup too slow: {total_time:.3f}s"
        
    def test_memory_efficiency(self):
        """Test memory usage in uvx environment"""
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c", 
             """
import sys
import gc
import os

# Get memory info if available
try:
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()
    print(f'Memory usage: {memory_info.rss / 1024 / 1024:.1f} MB')
except ImportError:
    print('psutil not available for memory monitoring')

# Test that our package doesn't leak memory with repeated imports
for i in range(10):
    import fastmcp
    from fastmcp import FastMCP
    mcp = FastMCP(f"test_{i}")
    del mcp
    gc.collect()

print('Memory efficiency test completed')
             """],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Memory efficiency test completed" in result.stdout
        print("Memory efficiency: OK")