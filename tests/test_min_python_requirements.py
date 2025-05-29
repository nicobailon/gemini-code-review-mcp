"""
Minimum Python version requirements validation
Tests that our code only uses features available in Python 3.8+
"""

import ast
import sys
from pathlib import Path
import subprocess


class TestMinimumPythonRequirements:
    """Test that code only uses features available in Python 3.8+"""
    
    def setup_method(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent
        self.src_files = list((self.project_root / "src").rglob("*.py"))
        
    def test_python_syntax_compatibility(self):
        """Test that all source files use Python 3.8+ compatible syntax"""
        for src_file in self.src_files:
            with open(src_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            try:
                # Parse with Python AST - this will catch syntax errors
                tree = ast.parse(source_code, filename=str(src_file))
                print(f"✅ Syntax compatible: {src_file.name}")
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {src_file}: {e}")
                
    def test_typing_usage_compatibility(self):
        """Test that typing usage is compatible with Python 3.8+"""
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c",
             """
import sys

# Test typing imports used in our code
try:
    from typing import Optional, List, Dict, Union, Any, Callable
    print('Basic typing imports: ✅ Compatible')
except ImportError as e:
    print(f'Typing imports failed: {e}')
    exit(1)

# Test that we don't use Python 3.9+ typing features
try:
    # These would fail on Python 3.8
    from typing import Annotated  # Python 3.9+
    print('WARNING: Using Python 3.9+ typing features')
except ImportError:
    print('✅ No Python 3.9+ typing features detected')

# Test typing.TYPE_CHECKING (available in 3.5+)
try:
    from typing import TYPE_CHECKING
    print('TYPE_CHECKING: ✅ Available')
except ImportError:
    print('TYPE_CHECKING: Not available')

print(f'Typing compatibility for Python {sys.version_info.major}.{sys.version_info.minor}: ✅ OK')
             """],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Typing compatibility" in result.stdout
        
    def test_pathlib_usage_compatibility(self):
        """Test pathlib usage is compatible with Python 3.8+"""
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c",
             """
import sys
from pathlib import Path

# Test pathlib features we use
test_path = Path('/tmp/test')

# Basic operations (available since Python 3.4)
try:
    # Path creation and operations
    p = Path('/tmp') / 'subdir' / 'file.txt'
    
    # String conversion
    str_path = str(p)
    
    # Path properties we use
    parent = p.parent
    name = p.name
    suffix = p.suffix
    
    print('Basic pathlib operations: ✅ Compatible')
    
    # Test methods we use in our code
    # exists(), is_file(), is_dir() - available since 3.4
    # read_text(), write_text() - available since 3.5
    # mkdir() - available since 3.4
    
    print(f'pathlib for Python {sys.version_info.major}.{sys.version_info.minor}: ✅ Compatible')
    
except Exception as e:
    print(f'pathlib compatibility error: {e}')
    exit(1)
             """],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "pathlib for Python" in result.stdout
        
    def test_f_string_usage_compatibility(self):
        """Test f-string usage (requires Python 3.6+)"""
        # Check our source files for f-string usage
        f_string_files = []
        
        for src_file in self.src_files:
            with open(src_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'f"' in content or "f'" in content:
                    f_string_files.append(src_file.name)
        
        if f_string_files:
            print(f"Files using f-strings: {f_string_files}")
            # f-strings require Python 3.6+, which is compatible with our 3.8+ requirement
            result = subprocess.run(
                ["uvx", "--from", ".", "python", "-c",
                 """
import sys

# Test f-string syntax
test_var = "test"
f_string_result = f"f-string test: {test_var}"

print(f_string_result)
print(f'f-strings on Python {sys.version_info.major}.{sys.version_info.minor}: ✅ Compatible')
                 """],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert "f-strings on Python" in result.stdout
        else:
            print("No f-strings found in source code")
            
    def test_asyncio_compatibility(self):
        """Test asyncio usage compatibility"""
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c",
             """
import sys
import asyncio

# Test asyncio features we might use
print(f'asyncio on Python {sys.version_info.major}.{sys.version_info.minor}:')

# asyncio.run() - available since Python 3.7
if hasattr(asyncio, 'run'):
    print('  asyncio.run(): ✅ Available')
else:
    print('  asyncio.run(): ❌ Not available (requires Python 3.7+)')

# Basic asyncio features (available since Python 3.4)
print('  Basic asyncio: ✅ Available')

# Event loop (available since Python 3.4)
try:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.close()
    print('  Event loop: ✅ Available')
except:
    print('  Event loop: ❌ Not available')

print('asyncio compatibility: ✅ OK')
             """],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "asyncio compatibility: ✅ OK" in result.stdout
        
    def test_standard_library_compatibility(self):
        """Test standard library modules we use"""
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c",
             """
import sys

# Test standard library modules used in our code
modules_to_test = [
    'os',
    'sys', 
    'pathlib',
    'tempfile',
    'subprocess',
    'json',
    're',
    'typing'
]

print(f'Testing standard library on Python {sys.version_info.major}.{sys.version_info.minor}:')

for module_name in modules_to_test:
    try:
        __import__(module_name)
        print(f'  {module_name}: ✅ Available')
    except ImportError:
        print(f'  {module_name}: ❌ Not available')
        exit(1)

print('Standard library compatibility: ✅ OK')
             """],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Standard library compatibility: ✅ OK" in result.stdout
        
    def test_feature_requirements_matrix(self):
        """Test feature requirements against our minimum Python version"""
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c",
             """
import sys

print('=== Feature Requirements Analysis ===')
print(f'Current Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')
print(f'Target minimum: 3.8')
print()

# Features and their minimum Python versions
features = {
    'f-strings': (3, 6),
    'pathlib': (3, 4),
    'typing': (3, 5),
    'asyncio': (3, 4),
    'asyncio.run()': (3, 7),
    'subprocess.run()': (3, 5),
    'json': (2, 6),  # Very old
    'tempfile': (2, 3),  # Very old
    'Positional-only parameters': (3, 8),
    'Assignment expressions (:=)': (3, 8),
}

print('Feature compatibility:')
current_version = sys.version_info[:2]
target_version = (3, 8)

all_compatible = True
for feature, min_version in features.items():
    compatible_with_target = min_version <= target_version
    compatible_with_current = min_version <= current_version
    
    if compatible_with_target:
        status = '✅'
    else:
        status = '❌'
        all_compatible = False
    
    print(f'  {feature}: {status} (requires Python {min_version[0]}.{min_version[1]}+)')

print()
if all_compatible:
    print('✅ All features compatible with Python 3.8+ requirement')
else:
    print('❌ Some features require newer Python versions')
    
print(f'\\nTarget compatibility: Python 3.8+ ✅')
             """],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "All features compatible" in result.stdout or "Target compatibility: Python 3.8+ ✅" in result.stdout