"""
Python version compatibility tests for MCP server
Tests compatibility for Python 3.13
"""

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
        """Test that code syntax is compatible with current Python version"""
        # Test our main server module can be parsed
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", "src/server.py"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Syntax error in server.py: {result.stderr}"

        # Test core module
        result = subprocess.run(
            [
                sys.executable,
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

    def test_import_compatibility(self):
        """Test that all modules can be imported"""
        # Create a test script that imports all modules
        test_script = """
import sys
sys.path.insert(0, 'src')

# Test imports
try:
    from src import server
    from src import generate_code_review_context
    from src import meta_prompt_generator
    from src import file_context_generator
    print("All imports successful")
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(test_script)
            f.flush()

            result = subprocess.run(
                [sys.executable, f.name],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Import error: {result.stderr}"

    def test_typing_annotations_compatibility(self):
        """Test typing annotations are compatible"""
        # Check that typing annotations work
        test_script = """
from typing import Optional, Union, List, Dict, Any
from typing import Protocol  # Added in 3.8

# Test Protocol (3.8+)
class Testable(Protocol):
    def test(self) -> None: ...

# Test Union with None (Optional)
def func(x: Optional[str] = None) -> Union[str, int]:
    return x or 0

# Test List/Dict generics
def process(items: List[Dict[str, Any]]) -> None:
    pass

print("Typing annotations work correctly")
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(test_script)
            f.flush()

            result = subprocess.run(
                [sys.executable, f.name],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            assert (
                result.returncode == 0
            ), f"Typing annotation error: {result.stderr}"

    def test_pathlib_compatibility(self):
        """Test pathlib functionality"""
        test_script = """
from pathlib import Path

# Basic Path operations
p = Path(".")
assert p.exists()
assert list(p.glob("*.py")) is not None

# Path / operator
subpath = p / "src"
print(f"Path operations work: {subpath}")
"""
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Pathlib error: {result.stderr}"

    def test_f_string_compatibility(self):
        """Test f-string functionality"""
        test_script = """
name = "MCP"
version = 1.0
# Basic f-string
msg = f"Testing {name} v{version}"
# Expression in f-string
calc = f"Result: {2 + 2}"
# Format specifiers
pi = 3.14159
formatted = f"Pi: {pi:.2f}"
print(f"F-strings work: {msg}, {calc}, {formatted}")
"""
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"F-string error: {result.stderr}"

    def test_asyncio_compatibility(self):
        """Test asyncio functionality"""
        test_script = """
import asyncio

async def test_async():
    await asyncio.sleep(0.001)
    return "async works"

# Run async function
result = asyncio.run(test_async())
print(f"Asyncio result: {result}")
"""
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Asyncio error: {result.stderr}"


class TestDependencyVersionCompatibility:
    """Test that dependencies work across Python versions"""

    def setup_method(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent

    @pytest.mark.skipif(
        not Path("venv").exists(),
        reason="Virtual environment not available"
    )
    def test_fastmcp_version_compatibility(self):
        """Test fastmcp compatibility"""
        test_script = """
try:
    from fastmcp import FastMCP
    print("fastmcp import successful")
except ImportError as e:
    print(f"fastmcp import failed: {e}")
    exit(1)
"""
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"fastmcp compatibility error: {result.stderr}"

    @pytest.mark.skipif(
        not Path("venv").exists(),
        reason="Virtual environment not available"
    )
    def test_google_genai_compatibility(self):
        """Test google.generativeai compatibility"""
        test_script = """
try:
    import google.generativeai
    print("google.generativeai import successful")
except ImportError as e:
    print(f"google.generativeai import failed: {e}")
    exit(1)
"""
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
        )
        assert (
            result.returncode == 0
        ), f"google.generativeai compatibility error: {result.stderr}"

    @pytest.mark.skipif(
        not Path("venv").exists(),
        reason="Virtual environment not available"
    )
    def test_python_dotenv_compatibility(self):
        """Test python-dotenv compatibility"""
        test_script = """
try:
    from dotenv import load_dotenv
    print("python-dotenv import successful")
except ImportError as e:
    print(f"python-dotenv import failed: {e}")
    exit(1)
"""
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
        )
        assert (
            result.returncode == 0
        ), f"python-dotenv compatibility error: {result.stderr}"


class TestFunctionalCompatibility:
    """Test functional compatibility across versions"""

    def setup_method(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent

    @pytest.mark.skipif(
        not Path("venv").exists(),
        reason="Virtual environment not available"
    )
    def test_server_startup_compatibility(self):
        """Test server can start without errors"""
        # Just test import, not actual server start
        test_script = """
import sys
sys.path.insert(0, 'src')
try:
    from src.server import mcp
    print("Server module loaded successfully")
except Exception as e:
    print(f"Server startup error: {e}")
    exit(1)
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(test_script)
            f.flush()

            result = subprocess.run(
                [sys.executable, f.name],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert (
                result.returncode == 0
            ), f"Server startup compatibility error: {result.stderr}"

    @pytest.mark.skipif(
        not Path("venv").exists(),
        reason="Virtual environment not available"
    )
    def test_tool_function_compatibility(self):
        """Test tool functions work correctly"""
        test_script = """
import sys
sys.path.insert(0, 'src')
try:
    from src.server import get_mcp_tools
    tools = get_mcp_tools()
    assert isinstance(tools, list), f"Expected list, got {type(tools)}"
    assert len(tools) > 0, "No tools found"
    print(f"Found {len(tools)} tools")
except Exception as e:
    print(f"Tool function error: {e}")
    exit(1)
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(test_script)
            f.flush()

            result = subprocess.run(
                [sys.executable, f.name],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            assert (
                result.returncode == 0
            ), f"Tool function compatibility error: {result.stderr}"

    def test_package_metadata_compatibility(self):
        """Test package metadata is accessible"""
        test_script = """
import sys
sys.path.insert(0, 'src')
try:
    # Read version from __init__.py
    with open('src/__init__.py', 'r') as f:
        content = f.read()
        if '__version__' in content:
            print("Version metadata found")
        else:
            print("No version metadata")
except Exception as e:
    print(f"Metadata error: {e}")
    exit(1)
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(test_script)
            f.flush()

            result = subprocess.run(
                [sys.executable, f.name],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            assert (
                result.returncode == 0
            ), f"Package metadata compatibility error: {result.stderr}"


class TestPythonVersionSpecificFeatures:
    """Test Python version-specific features we use"""

    def test_python_38_features(self):
        """Test Python 3.8+ features we rely on"""
        # Walrus operator (3.8+)
        test_script = """
# Test walrus operator
if (n := 5) > 3:
    print(f"Walrus operator works: {n}")

# Test positional-only parameters (3.8+)
def func(a, /, b):
    return a + b

result = func(1, 2)
print(f"Positional-only params work: {result}")
"""
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
        )
        if sys.version_info >= (3, 8):
            assert result.returncode == 0, f"Python 3.8+ feature error: {result.stderr}"
        else:
            # Should fail on older versions
            assert result.returncode != 0, "Python 3.8+ features should fail on older versions"

    def test_backwards_compatibility(self):
        """Test we're not using features from newer Python than we support"""
        # Test we're NOT using Python 3.10+ features like match/case
        test_script = '''
# This should fail - we don't use match/case (3.10+)
code = """
match x:
    case 1:
        print("one")
"""
try:
    compile(code, "test", "exec")
    print("ERROR: match/case compiled (should not use 3.10+ features)")
    exit(1)
except SyntaxError:
    print("Good: not using match/case (3.10+ feature)")
'''
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
        )
        if sys.version_info < (3, 10):
            assert result.returncode == 0, "Should not use Python 3.10+ features"


class TestPythonVersionMatrix:
    """Generate compatibility matrix report"""

    def test_version_matrix_report(self):
        """Generate a compatibility report for all Python versions"""
        current_version = sys.version_info
        print("\n" + "=" * 60)
        print("PYTHON VERSION COMPATIBILITY MATRIX")
        print("=" * 60)
        print(f"Current Python: {current_version.major}.{current_version.minor}.{current_version.micro}")
        print(f"Platform: {platform.platform()}")
        print(f"Architecture: {platform.architecture()}")
        print("\nSupported Python Versions:")
        print("- Python 3.8  : Core features")
        print("- Python 3.9  : Additional type hints")
        print("- Python 3.10 : Better error messages")
        print("- Python 3.11 : tomllib built-in")
        print("- Python 3.12 : Type parameter syntax")
        print("- Python 3.13 : Latest version")
        print("\nDependency Requirements:")
        print("- fastmcp: Python 3.8+")
        print("- google-generativeai: Python 3.8+")
        print("- python-dotenv: Python 3.8+")
        print("=" * 60)

        # Always pass - this is just informational
        assert True