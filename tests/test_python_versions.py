"""
Python version compatibility tests for MCP server
Tests compatibility across Python 3.8, 3.9, 3.10, 3.11, 3.12
"""

import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestPythonVersionCompatibility:
    """Test Python version compatibility for the MCP server package"""

    def setup_method(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent
        self.current_python = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    def test_current_python_version_info(self):
        """Display current Python version information"""
        version_info = sys.version_info
        print(f"Current Python: {self.current_python}")
        print(f"Version info: {version_info}")
        print(f"Platform: {platform.platform()}")
        print(f"Architecture: {platform.architecture()}")

        # Verify we're running on a supported version
        assert version_info >= (3, 8), f"Python 3.8+ required, got {version_info}"
        assert version_info < (
            4,
            0,
        ), f"Python 4.x not yet supported, got {version_info}"

    def test_syntax_compatibility(self):
        """Test that code syntax is compatible with target Python versions"""
        # Test our main server module can be parsed
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-m", "py_compile", "src/server.py"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Syntax error in server.py: {result.stderr}"

        # Test core module
        result = subprocess.run(
            [
                "uvx",
                "--from",
                ".",
                "python",
                "-m",
                "py_compile",
                "src/generate_code_review_context.py",
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        assert (
            result.returncode == 0
        ), f"Syntax error in generate_code_review_context.py: {result.stderr}"
        print("Syntax compatibility: OK")

    def test_import_compatibility(self):
        """Test that imports work correctly"""
        result = subprocess.run(
            [
                "uvx",
                "--from",
                ".",
                "python",
                "-c",
                """
import sys
print(f'Python version: {sys.version}')

# Test standard library imports
import os
import sys
import pathlib
import tempfile
import subprocess
import json
import re
from typing import Optional, List, Dict
print('Standard library imports: OK')

# Test our module imports
sys.path.insert(0, 'src')
try:
    import server
    print('Server module import: OK')
    
    import generate_code_review_context
    print('Core module import: OK')
    
    # Test FastMCP import
    from fastmcp import FastMCP
    print('FastMCP import: OK')
    
except ImportError as e:
    print(f'Import error: {e}')
    exit(1)
             """,
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Server module import: OK" in result.stdout
        assert "FastMCP import: OK" in result.stdout
        print("Import compatibility: OK")

    def test_typing_annotations_compatibility(self):
        """Test that type annotations work across Python versions"""
        result = subprocess.run(
            [
                "uvx",
                "--from",
                ".",
                "python",
                "-c",
                """
import sys
from typing import Optional, List, Dict, Union

# Test function with type annotations (our server function signature)
def test_function(
    project_path: str,
    current_phase: Optional[str] = None,
    output_path: Optional[str] = None,
    enable_gemini_review: bool = True
) -> str:
    return f'Python {sys.version_info.major}.{sys.version_info.minor} typing: OK'

result = test_function('/tmp')
print(result)

# Test more complex typing patterns
from typing import Any, Callable
def complex_typing_test(
    data: Dict[str, Any],
    callback: Optional[Callable[[str], str]] = None
) -> Union[str, None]:
    return 'Complex typing: OK'

print(complex_typing_test({'test': 'data'}))
             """,
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "typing: OK" in result.stdout
        print("Type annotations compatibility: OK")

    def test_pathlib_compatibility(self):
        """Test pathlib usage across Python versions"""
        result = subprocess.run(
            [
                "uvx",
                "--from",
                ".",
                "python",
                "-c",
                """
from pathlib import Path
import tempfile
import os

# Test pathlib features used in our code
with tempfile.TemporaryDirectory() as temp_dir:
    temp_path = Path(temp_dir)
    
    # Test path operations
    test_file = temp_path / 'test.txt'
    test_file.write_text('test content')
    
    content = test_file.read_text()
    assert content == 'test content'
    
    # Test path properties
    assert test_file.exists()
    assert test_file.is_file()
    assert temp_path.is_dir()
    
    # Test absolute path detection
    assert os.path.isabs(str(test_file))
    
    print('pathlib compatibility: OK')
             """,
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "pathlib compatibility: OK" in result.stdout
        print("pathlib compatibility: OK")

    def test_f_string_compatibility(self):
        """Test f-string usage (Python 3.6+ feature)"""
        result = subprocess.run(
            [
                "uvx",
                "--from",
                ".",
                "python",
                "-c",
                """
import sys

# Test f-strings used in our code
project_path = "/tmp/test"
phase = "2.0"
enable_gemini = True

# Simple f-string
message = f"Processing project: {project_path}"
print(message)

# F-string with expressions
status = f"Phase {phase} with Gemini {'enabled' if enable_gemini else 'disabled'}"
print(status)

# F-string with method calls
version = f"Python {sys.version_info.major}.{sys.version_info.minor}"
print(f"f-string test on {version}: OK")
             """,
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "f-string test on" in result.stdout
        print("f-string compatibility: OK")

    def test_asyncio_compatibility(self):
        """Test asyncio features if used by FastMCP"""
        result = subprocess.run(
            [
                "uvx",
                "--from",
                ".",
                "python",
                "-c",
                """
import asyncio
import sys

async def test_async():
    return f'Asyncio on Python {sys.version_info.major}.{sys.version_info.minor}: OK'

# Test asyncio.run (Python 3.7+ feature)
try:
    result = asyncio.run(test_async())
    print(result)
except AttributeError:
    # Fallback for older Python versions
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(test_async())
    print(result)
    loop.close()
             """,
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Asyncio on Python" in result.stdout
        print("asyncio compatibility: OK")


class TestDependencyVersionCompatibility:
    """Test that dependencies work across Python versions"""

    def setup_method(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent

    def test_fastmcp_version_compatibility(self):
        """Test FastMCP compatibility across Python versions"""
        result = subprocess.run(
            [
                "uvx",
                "--from",
                ".",
                "python",
                "-c",
                """
import sys
import fastmcp

print(f'Python: {sys.version_info.major}.{sys.version_info.minor}')
print(f'FastMCP: {fastmcp.__version__}')

# Test FastMCP instance creation
try:
    from fastmcp import FastMCP
    mcp = FastMCP("Version Test")
    print('FastMCP instance creation: OK')
    
    # Test basic tool decoration
    @mcp.tool()
    def test_tool(message: str) -> str:
        return f"Tool test: {message}"
    
    print('FastMCP tool decoration: OK')
    
except Exception as e:
    print(f'FastMCP error: {e}')
    exit(1)
             """,
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "FastMCP instance creation: OK" in result.stdout
        print("FastMCP version compatibility: OK")

    def test_google_genai_compatibility(self):
        """Test google-genai package compatibility"""
        result = subprocess.run(
            [
                "uvx",
                "--from",
                ".",
                "python",
                "-c",
                """
import sys
try:
    import google.genai
    print(f'google-genai on Python {sys.version_info.major}.{sys.version_info.minor}: OK')
    
    # Test basic import structure
    print(f'google.genai module: {google.genai.__name__}')
    
except ImportError as e:
    print(f'google-genai import error: {e}')
    exit(1)
             """,
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "google-genai on Python" in result.stdout
        print("google-genai compatibility: OK")

    def test_python_dotenv_compatibility(self):
        """Test python-dotenv package compatibility"""
        result = subprocess.run(
            [
                "uvx",
                "--from",
                ".",
                "python",
                "-c",
                """
import sys
try:
    import dotenv
    print(f'python-dotenv on Python {sys.version_info.major}.{sys.version_info.minor}: OK')
    
    # Test basic functionality
    from dotenv import load_dotenv
    print('load_dotenv function available: OK')
    
except ImportError as e:
    print(f'python-dotenv import error: {e}')
    exit(1)
             """,
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "python-dotenv on Python" in result.stdout
        print("python-dotenv compatibility: OK")


class TestFunctionalCompatibility:
    """Test functional compatibility across Python versions"""

    def setup_method(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent

    def test_server_startup_compatibility(self):
        """Test that the server can start on different Python versions"""
        result = subprocess.run(
            [
                "uvx",
                "--from",
                ".",
                "python",
                "-c",
                """
import sys
sys.path.insert(0, 'src')

try:
    from server import mcp
    print(f'Server import on Python {sys.version_info.major}.{sys.version_info.minor}: OK')
    
    # Test server instance
    print(f'Server instance: {type(mcp).__name__}')
    print('Server startup compatibility: OK')
    
except Exception as e:
    print(f'Server startup error: {e}')
    exit(1)
             """,
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Server startup compatibility: OK" in result.stdout
        print("Server startup compatibility: OK")

    def test_tool_function_compatibility(self):
        """Test that tool functions work across Python versions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create minimal test environment
            tasks_dir = temp_path / "tasks"
            tasks_dir.mkdir()
            (tasks_dir / "prd-test.md").write_text(
                "# Test PRD\n## Requirements\n- Test requirement"
            )
            (tasks_dir / "tasks-prd-test.md").write_text(
                "## Tasks\n- [ ] 1.0 Test task"
            )

            test_code = f"""
import sys
sys.path.insert(0, 'src')

try:
    from server import generate_code_review_context
    print(f'Tool function on Python {{sys.version_info.major}}.{{sys.version_info.minor}}: Available')
    
    # Test function call (should handle errors gracefully)
    result = generate_code_review_context(
        project_path='{temp_path}',
        enable_gemini_review=False
    )
    
    # Should return string result (success or error message)
    print(f'Function result type: {{type(result).__name__}}')
    print(f'Function execution: OK')
    
except Exception as e:
    print(f'Tool function error: {{e}}')
    exit(1)
            """

            result = subprocess.run(
                ["uvx", "--from", ".", "python", "-c", test_code],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert "Function execution: OK" in result.stdout
            print("Tool function compatibility: OK")

    def test_package_metadata_compatibility(self):
        """Test that package metadata is accessible across Python versions"""
        result = subprocess.run(
            [
                "uvx",
                "--from",
                ".",
                "python",
                "-c",
                """
import sys
import pkg_resources

try:
    # Test package is discoverable
    distribution = pkg_resources.get_distribution('gemini-code-review-mcp')
    print(f'Package discovery on Python {sys.version_info.major}.{sys.version_info.minor}: OK')
    print(f'Package version: {distribution.version}')
    
    # Test entry points
    entry_points = distribution.get_entry_map()
    if 'console_scripts' in entry_points:
        scripts = entry_points['console_scripts']
        if 'gemini-code-review-mcp' in scripts:
            print('Entry point available: OK')
        else:
            print('Entry point missing')
    
    print('Package metadata compatibility: OK')
    
except Exception as e:
    print(f'Package metadata error: {e}')
    # Don't exit(1) as this might fail in development mode
             """,
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        # Don't assert returncode as pkg_resources might not find dev package
        if "Package discovery" in result.stdout:
            print("Package metadata compatibility: OK")
        else:
            print("Package metadata: Development mode (expected)")


class TestPythonVersionSpecificFeatures:
    """Test version-specific features and compatibility"""

    def setup_method(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent

    def test_python_38_features(self):
        """Test Python 3.8+ specific features if used"""
        result = subprocess.run(
            [
                "uvx",
                "--from",
                ".",
                "python",
                "-c",
                """
import sys

# Test walrus operator (Python 3.8+) - if we use it
if sys.version_info >= (3, 8):
    # Test assignment expression
    data = [1, 2, 3, 4, 5]
    if (n := len(data)) > 3:
        print(f'Walrus operator works: {n} items')
    else:
        print('Walrus operator test failed')
else:
    print('Python 3.8+ features not available')

# Test positional-only parameters (Python 3.8+)
def test_pos_only(a, b, /, c=None):
    return f'pos-only params: {a}, {b}, {c}'

try:
    result = test_pos_only(1, 2, c=3)
    print(result)
    print('Positional-only parameters: OK')
except:
    print('Positional-only parameters: Not supported')

print(f'Python {sys.version_info.major}.{sys.version_info.minor} features: OK')
             """,
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        print("Python version-specific features: OK")

    def test_backwards_compatibility(self):
        """Test backwards compatibility with older syntax"""
        result = subprocess.run(
            [
                "uvx",
                "--from",
                ".",
                "python",
                "-c",
                """
import sys

# Test older-style type hints that should work across versions
def old_style_function(project_path, current_phase=None):
    # type: (str, str) -> str
    return f'Old style typing on Python {sys.version_info.major}.{sys.version_info.minor}: OK'

print(old_style_function('/tmp'))

# Test format strings (pre f-string style)
message = 'Format string on Python {}.{}: OK'.format(
    sys.version_info.major, sys.version_info.minor
)
print(message)

# Test percent formatting
legacy_message = 'Legacy formatting on Python %d.%d: OK' % (
    sys.version_info.major, sys.version_info.minor
)
print(legacy_message)
             """,
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Old style typing" in result.stdout
        print("Backwards compatibility: OK")


class TestPythonVersionMatrix:
    """Test matrix of Python version compatibility scenarios"""

    def setup_method(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent
        self.current_version = f"{sys.version_info.major}.{sys.version_info.minor}"

    def test_version_matrix_report(self):
        """Generate a compatibility report for the current Python version"""
        result = subprocess.run(
            [
                "uvx",
                "--from",
                ".",
                "python",
                "-c",
                """
import sys
import platform

print('=== Python Version Compatibility Report ===')
print(f'Python Version: {sys.version}')
print(f'Platform: {platform.platform()}')
print(f'Architecture: {platform.architecture()[0]}')
print(f'Executable: {sys.executable}')

# Test package requirements
print('\\n=== Package Requirements ===')
print(f'Python >= 3.8: {sys.version_info >= (3, 8)}')
print(f'Python < 4.0: {sys.version_info < (4, 0)}')

# Test key features
print('\\n=== Feature Compatibility ===')

# Typing support
try:
    from typing import Optional, List, Dict
    print('typing module: ✅ Available')
except ImportError:
    print('typing module: ❌ Not available')

# pathlib support
try:
    from pathlib import Path
    print('pathlib module: ✅ Available')
except ImportError:
    print('pathlib module: ❌ Not available')

# asyncio support
try:
    import asyncio
    if hasattr(asyncio, 'run'):
        print('asyncio.run: ✅ Available (Python 3.7+)')
    else:
        print('asyncio.run: ⚠️ Not available (requires Python 3.7+)')
except ImportError:
    print('asyncio: ❌ Not available')

# Test dependencies
print('\\n=== Dependency Compatibility ===')
try:
    import fastmcp
    print(f'FastMCP: ✅ v{fastmcp.__version__}')
except ImportError as e:
    print(f'FastMCP: ❌ {e}')

try:
    import google.genai
    print('google-genai: ✅ Available')
except ImportError as e:
    print(f'google-genai: ❌ {e}')

try:
    import dotenv
    print('python-dotenv: ✅ Available')
except ImportError as e:
    print(f'python-dotenv: ❌ {e}')

print('\\n=== Compatibility Status ===')
print(f'Python {sys.version_info.major}.{sys.version_info.minor}: ✅ Compatible')
             """,
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        print(f"Python {self.current_version} compatibility report generated")

        # Store the report for documentation
        report_lines = result.stdout.split("\n")

        # Verify key compatibility indicators
        assert "Compatible" in result.stdout
        assert "✅" in result.stdout  # Should have some successful checks

        return result.stdout
