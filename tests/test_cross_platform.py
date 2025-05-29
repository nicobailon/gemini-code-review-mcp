"""
Cross-platform compatibility tests for MCP server
Tests platform-specific behaviors and path handling
"""

import os
import sys
import subprocess
import tempfile
import pytest
from pathlib import Path
import platform


class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility for MCP server"""
    
    def setup_method(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent
        self.current_platform = platform.system()
        
    def test_platform_detection(self):
        """Test that platform is correctly detected"""
        assert self.current_platform in ["Windows", "Darwin", "Linux"]
        print(f"Running on: {self.current_platform}")
        
    def test_python_version_compatibility(self):
        """Test that Python version meets requirements"""
        version_info = sys.version_info
        assert version_info >= (3, 8), f"Python 3.8+ required, got {version_info}"
        print(f"Python version: {sys.version}")
        
    def test_uvx_availability(self):
        """Test that uvx is available on the platform"""
        result = subprocess.run(
            ["uvx", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "uvx not available or not working"
        print(f"uvx version: {result.stdout.strip()}")
        
    def test_path_handling_cross_platform(self):
        """Test path handling works correctly across platforms"""
        # Create test paths
        test_paths = [
            "/tmp/test" if self.current_platform != "Windows" else "C:\\temp\\test",
            str(Path.home() / "test"),
            str(Path.cwd() / "test"),
        ]
        
        for test_path in test_paths:
            # Test absolute path detection
            result = subprocess.run(
                ["uvx", "--from", ".", "python", "-c", 
                 f"import os; print('Absolute:', os.path.isabs('{test_path}'))"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert "Absolute: True" in result.stdout
            
    def test_file_system_operations(self):
        """Test file system operations work across platforms"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test directory creation and file operations
            test_code = f"""
import os
from pathlib import Path

temp_path = Path('{temp_path}')
tasks_dir = temp_path / 'tasks'
tasks_dir.mkdir(exist_ok=True)

# Test file creation with different line endings
test_file = tasks_dir / 'test.md'
test_file.write_text('# Test\\n- Item 1\\n- Item 2\\n')

# Test file reading
content = test_file.read_text()
print('File operations successful')
print(f'Content length: {{len(content)}}')
"""
            
            result = subprocess.run(
                ["uvx", "--from", ".", "python", "-c", test_code],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert "File operations successful" in result.stdout
            
    def test_environment_variables(self):
        """Test environment variable handling across platforms"""
        test_env = os.environ.copy()
        test_env["TEST_VAR"] = "cross_platform_test"
        
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c", 
             "import os; print(f'TEST_VAR: {os.environ.get(\"TEST_VAR\", \"NOT_FOUND\")}')"],
            cwd=self.project_root,
            env=test_env,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "TEST_VAR: cross_platform_test" in result.stdout
        
    def test_subprocess_execution(self):
        """Test subprocess execution works correctly"""
        # Test basic subprocess functionality
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c", 
             "import subprocess; result = subprocess.run(['python', '--version'], capture_output=True, text=True); print('Subprocess:', result.returncode == 0)"],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Subprocess: True" in result.stdout
        
    def test_git_operations_cross_platform(self):
        """Test git operations work across platforms"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=temp_path, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_path)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_path)
            
            # Create and commit a file
            test_file = temp_path / "test.txt"
            test_file.write_text("test content")
            subprocess.run(["git", "add", "."], cwd=temp_path, capture_output=True)
            subprocess.run(["git", "commit", "-m", "test"], cwd=temp_path, capture_output=True)
            
            # Test git operations in our package
            test_code = f"""
import subprocess
import os
os.chdir('{temp_path}')

try:
    result = subprocess.run(['git', 'status'], capture_output=True, text=True)
    print('Git status success:', result.returncode == 0)
    
    result = subprocess.run(['git', 'log', '--oneline'], capture_output=True, text=True)
    print('Git log success:', result.returncode == 0)
    print('Has commits:', len(result.stdout.strip()) > 0)
except Exception as e:
    print(f'Git error: {{e}}')
"""
            
            result = subprocess.run(
                ["uvx", "--from", ".", "python", "-c", test_code],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert "Git status success: True" in result.stdout
            
    def test_mcp_server_startup_cross_platform(self):
        """Test MCP server starts correctly on the platform"""
        # Test basic server startup
        cmd = ["uvx", "--from", ".", "ai-dev-tasks-mcp"]
        
        process = subprocess.Popen(
            cmd,
            cwd=self.project_root,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            # Give server time to start
            import time
            time.sleep(1)
            
            # Check if server is running
            if process.poll() is None:
                # Server is running - send test message
                process.stdin.write('{"jsonrpc":"2.0","id":1,"method":"ping"}\n')
                process.stdin.flush()
                time.sleep(0.5)
                
                # Server should still be running
                assert process.poll() is None, "Server should remain running"
                
            process.terminate()
            stdout, stderr = process.communicate(timeout=3)
            
            # Check for platform-specific startup issues
            if process.returncode == 1 and stderr:
                pytest.fail(f"Server failed to start on {self.current_platform}: {stderr}")
                
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            
    def test_unicode_handling(self):
        """Test Unicode and special character handling"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test content with Unicode characters
            unicode_content = """# Test PRD with Unicode 
            
## Requirements 
- Support émojis: 🚀 ✅ ❌
- Handle accents: café, résumé, naïve
- Process symbols: ← → ↑ ↓ ∞ ≠ ≤ ≥
- Asian characters: 你好 こんにちは 안녕하세요
"""
            
            tasks_dir = temp_path / "tasks"
            tasks_dir.mkdir()
            (tasks_dir / "prd-unicode.md").write_text(unicode_content, encoding="utf-8")
            (tasks_dir / "tasks-prd-unicode.md").write_text("## Tasks\n- [ ] 1.0 Unicode test", encoding="utf-8")
            
            # Test our server can handle Unicode paths and content
            test_code = f"""
import sys
sys.path.insert(0, 'src')
from generate_code_review_context import main as generate_review

try:
    output = generate_review(
        project_path='{temp_path}',
        enable_gemini_review=False
    )
    print('Unicode handling successful')
    print(f'Output file: {{output}}')
    
    # Verify content can be read
    with open(output, 'r', encoding='utf-8') as f:
        content = f.read()
        print('Content length:', len(content))
        print('Has unicode:', any(ord(c) > 127 for c in content))
        
except Exception as e:
    print(f'Unicode error: {{e}}')
"""
            
            result = subprocess.run(
                ["uvx", "--from", ".", "python", "-c", test_code],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            assert result.returncode == 0
            assert "Unicode handling successful" in result.stdout
            
    def test_large_file_handling(self):
        """Test handling of large files and directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a project with many files
            tasks_dir = temp_path / "tasks"
            tasks_dir.mkdir()
            
            # Create larger content
            large_content = "# Large PRD\n\n" + "\n".join([
                f"## Section {i}\nContent for section {i} with detailed requirements and specifications."
                for i in range(100)
            ])
            
            (tasks_dir / "prd-large.md").write_text(large_content)
            (tasks_dir / "tasks-prd-large.md").write_text("## Tasks\n" + "\n".join([
                f"- [ ] {i}.0 Task {i}" for i in range(50)
            ]))
            
            # Create many source files
            src_dir = temp_path / "src"
            src_dir.mkdir()
            for i in range(20):
                (src_dir / f"file_{i}.py").write_text(f"# File {i}\nprint('hello from file {i}')")
                
            # Test performance and memory handling
            test_code = f"""
import sys
import time
sys.path.insert(0, 'src')
from generate_code_review_context import main as generate_review

start_time = time.time()
try:
    output = generate_review(
        project_path='{temp_path}',
        enable_gemini_review=False
    )
    end_time = time.time()
    
    print('Large file handling successful')
    print(f'Processing time: {{end_time - start_time:.2f}} seconds')
    
    # Check output size
    with open(output, 'r') as f:
        content = f.read()
        print(f'Output size: {{len(content)}} characters')
        
except Exception as e:
    print(f'Large file error: {{e}}')
"""
            
            result = subprocess.run(
                ["uvx", "--from", ".", "python", "-c", test_code],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert "Large file handling successful" in result.stdout


class TestPlatformSpecificFeatures:
    """Test platform-specific features and edge cases"""
    
    def test_line_ending_handling(self):
        """Test handling of different line endings (CRLF vs LF)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            tasks_dir = temp_path / "tasks"
            tasks_dir.mkdir()
            
            # Test different line endings
            if platform.system() == "Windows":
                line_ending = "\r\n"
            else:
                line_ending = "\n"
                
            content = f"# Test PRD{line_ending}## Requirements{line_ending}- Requirement 1{line_ending}- Requirement 2{line_ending}"
            
            (tasks_dir / "prd-lineend.md").write_text(content, newline='')
            (tasks_dir / "tasks-prd-lineend.md").write_text(f"## Tasks{line_ending}- [ ] 1.0 Test task{line_ending}", newline='')
            
            # Test processing
            result = subprocess.run(
                ["uvx", "--from", ".", "python", "-c", 
                 f"import sys; sys.path.insert(0, 'src'); from generate_code_review_context import main; "
                 f"output = main('{temp_path}', enable_gemini_review=False); print('Success:', output is not None)"],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert "Success: True" in result.stdout
            
    def test_permission_handling(self):
        """Test file permission handling across platforms"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test file creation with different permissions
            test_file = temp_path / "test.txt"
            test_file.write_text("test content")
            
            if platform.system() != "Windows":
                # Unix-like systems - test permission changes
                os.chmod(test_file, 0o644)
                
            # Test reading permissions
            result = subprocess.run(
                ["uvx", "--from", ".", "python", "-c", 
                 f"import os; print('Readable:', os.access('{test_file}', os.R_OK))"],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert "Readable: True" in result.stdout
            
    def test_package_metadata_cross_platform(self):
        """Test package metadata is correct across platforms"""
        result = subprocess.run(
            ["uvx", "--from", ".", "python", "-c", 
             "import sys; sys.path.insert(0, 'src'); import server; print('FastMCP server imported successfully')"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "FastMCP server imported successfully" in result.stdout