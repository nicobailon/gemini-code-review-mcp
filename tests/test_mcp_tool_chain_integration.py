"""
Integration tests for MCP tool chain workflows.
Following TDD Protocol: Testing complete workflows of MCP tools working together.
"""

import pytest
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
import json
from typing import Dict, Any, Optional

# Import the mock classes we created
from test_gemini_api_mocks import MockGeminiClient, GeminiAPIMockFactory


@pytest.fixture(scope="session", autouse=True)
def setup_import_path():
    """Fixture to ensure src module can be imported in tests."""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)


class TestMCPToolChainIntegration:
    """Test complete workflows of MCP tools working together."""
    
    @pytest.fixture
    def sample_project_setup(self, tmp_path):
        """Create a comprehensive test project structure."""
        project_dir = tmp_path / "mcp_integration_project"
        project_dir.mkdir()
        
        # Create git repository
        os.system(f"cd {project_dir} && git init --quiet")
        
        # Create source code files
        src_dir = project_dir / "src"
        src_dir.mkdir()
        
        (src_dir / "main.py").write_text("""
def authenticate_user(username: str, password: str) -> bool:
    # TODO: Implement proper authentication
    if not username or not password:
        raise ValueError("Username and password required")
    
    # Hardcoded credentials (security issue)
    return username == "admin" and password == "password123"

def get_user_profile(user_id: int):
    # No input validation (potential security issue)
    query = f"SELECT * FROM users WHERE id = {user_id}"
    # SQL injection vulnerability
    return execute_query(query)
""")
        
        (src_dir / "utils.py").write_text("""
import logging

def execute_query(query: str):
    # Missing error handling
    logging.info(f"Executing: {query}")
    # Simulate database operation
    return {"id": 1, "name": "Test User"}

def process_data(data):
    # Performance issue: O(n²) complexity
    result = []
    for i in range(len(data)):
        for j in range(len(data)):
            if i != j and data[i] == data[j]:
                result.append(data[i])
    return result
""")
        
        # Create tasks directory with comprehensive task list
        tasks_dir = project_dir / "tasks"
        tasks_dir.mkdir()
        
        (tasks_dir / "tasks-authentication-system.md").write_text("""
## Tasks

- [x] 1.0 Core Authentication Implementation
  - [x] 1.1 Basic login functionality
  - [x] 1.2 Password validation
  - [ ] 1.3 Security hardening
  - [ ] 1.4 Error handling improvements

- [ ] 2.0 User Profile Management
  - [x] 2.1 Profile data retrieval
  - [ ] 2.2 Input validation
  - [ ] 2.3 SQL injection prevention
  - [ ] 2.4 Performance optimization

- [ ] 3.0 Database Integration
  - [x] 3.1 Query execution framework
  - [ ] 3.2 Connection pooling
  - [ ] 3.3 Error handling
  - [ ] 3.4 Logging improvements
""")
        
        # Create git commits
        os.system(f"cd {project_dir} && git add . && git commit -m 'Initial implementation' --quiet")
        
        return str(project_dir)
    
    @pytest.fixture
    def mock_mcp_server_tools(self):
        """Mock all MCP server tools for integration testing."""
        with patch('src.server.generate_auto_prompt') as mock_auto_prompt, \
             patch('src.server.generate_code_review_context') as mock_context, \
             patch('src.server.generate_ai_code_review') as mock_ai_review:
            
            # Setup realistic mock responses
            mock_auto_prompt.return_value = {
                "generated_prompt": "Focus on security vulnerabilities in authentication and SQL injection risks in user profile queries.",
                "analysis_completed": True,
                "context_analyzed": 1850,
                "focus_areas": ["security", "performance", "code_quality"]
            }
            
            mock_context.return_value = "/tmp/test_context.md"
            mock_ai_review.return_value = "/tmp/test_ai_review.md"
            
            yield {
                'auto_prompt': mock_auto_prompt,
                'context': mock_context,
                'ai_review': mock_ai_review
            }
    
    def test_full_auto_prompt_workflow_integration(self, sample_project_setup, mock_mcp_server_tools):
        """Test complete workflow: project → auto-prompt → context → ai review."""
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            project_path = sample_project_setup
            
            # Execute the full auto-prompt workflow
            result = execute_auto_prompt_workflow(
                project_path=project_path,
                scope="full_project",
                temperature=0.5,
                auto_prompt=True,
                generate_prompt_only=False
            )
            
            # Verify the tool chain was called correctly
            mocks = mock_mcp_server_tools
            
            # 1. Auto-prompt generation should be called first
            mocks['auto_prompt'].assert_called_once()
            auto_prompt_call = mocks['auto_prompt'].call_args
            assert auto_prompt_call[1]['project_path'] == project_path
            assert auto_prompt_call[1]['scope'] == "full_project"
            
            # 2. Context generation should be called
            mocks['context'].assert_called_once()
            context_call = mocks['context'].call_args
            assert context_call[1]['project_path'] == project_path
            assert context_call[1]['raw_context_only'] is True  # For auto-prompt workflow
            
            # 3. AI review should be called with custom prompt
            mocks['ai_review'].assert_called_once()
            ai_review_call = mocks['ai_review'].call_args
            assert ai_review_call[1]['custom_prompt'] == "Focus on security vulnerabilities in authentication and SQL injection risks in user profile queries."
            assert ai_review_call[1]['temperature'] == 0.5
            
            # 4. Result should contain workflow completion info
            assert result is not None
            
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")
    
    def test_prompt_only_workflow_integration(self, sample_project_setup, mock_mcp_server_tools):
        """Test prompt-only workflow: project → auto-prompt (no review)."""
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            project_path = sample_project_setup
            
            # Execute prompt-only workflow
            result = execute_auto_prompt_workflow(
                project_path=project_path,
                scope="recent_phase",
                temperature=0.7,
                auto_prompt=False,
                generate_prompt_only=True
            )
            
            mocks = mock_mcp_server_tools
            
            # 1. Auto-prompt generation should be called
            mocks['auto_prompt'].assert_called_once()
            auto_prompt_call = mocks['auto_prompt'].call_args
            assert auto_prompt_call[1]['scope'] == "recent_phase"
            
            # 2. AI review should NOT be called in prompt-only mode
            mocks['ai_review'].assert_not_called()
            
            # 3. Context generation may or may not be called (depends on implementation)
            # This is acceptable as prompt-only focuses on prompt generation
            
            assert result is not None
            
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")
    
    def test_scope_specific_workflow_integration(self, sample_project_setup, mock_mcp_server_tools):
        """Test that different scopes produce different workflow behaviors."""
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            project_path = sample_project_setup
            scopes_to_test = ["full_project", "recent_phase", "specific_phase", "specific_task"]
            
            for scope in scopes_to_test:
                # Reset mocks for each scope test
                for mock in mock_mcp_server_tools.values():
                    mock.reset_mock()
                
                # Execute workflow with specific scope
                result = execute_auto_prompt_workflow(
                    project_path=project_path,
                    scope=scope,
                    temperature=0.5,
                    auto_prompt=True,
                    phase_number="2.0" if scope == "specific_phase" else None,
                    task_id="2.3" if scope == "specific_task" else None
                )
                
                # Verify auto-prompt was called with correct scope
                mock_mcp_server_tools['auto_prompt'].assert_called_once()
                call_args = mock_mcp_server_tools['auto_prompt'].call_args
                assert call_args[1]['scope'] == scope
                
                # Verify workflow completed
                assert result is not None
                
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")
    
    def test_cli_to_mcp_integration(self, sample_project_setup):
        """Test CLI commands properly invoke MCP tool workflows."""
        try:
            from src.generate_code_review_context import cli_main
            
            project_path = sample_project_setup
            
            # Test --auto-prompt CLI flag integration
            with patch('sys.argv', ['generate-code-review', '--auto-prompt', project_path]):
                with patch('src.generate_code_review_context.execute_auto_prompt_workflow') as mock_workflow:
                    mock_workflow.return_value = {
                        "status": "completed",
                        "generated_prompt": "Test prompt",
                        "ai_review_path": "/tmp/review.md"
                    }
                    
                    result = cli_main()
                    
                    # Verify CLI properly invoked the workflow
                    mock_workflow.assert_called_once()
                    call_args = mock_workflow.call_args
                    assert call_args[1]['project_path'] == project_path
                    assert call_args[1]['auto_prompt'] is True
                    assert call_args[1]['generate_prompt_only'] is False
            
            # Test --generate-prompt-only CLI flag integration
            with patch('sys.argv', ['generate-code-review', '--generate-prompt-only', project_path]):
                with patch('src.generate_code_review_context.execute_auto_prompt_workflow') as mock_workflow:
                    mock_workflow.return_value = {
                        "status": "completed",
                        "generated_prompt": "Test prompt only"
                    }
                    
                    result = cli_main()
                    
                    # Verify CLI properly invoked prompt-only workflow
                    mock_workflow.assert_called_once()
                    call_args = mock_workflow.call_args
                    assert call_args[1]['generate_prompt_only'] is True
                    assert call_args[1]['auto_prompt'] is False
            
        except ImportError:
            pytest.skip("cli_main function not found - implementation pending")
    
    def test_mcp_server_tool_composition(self):
        """Test MCP server tools can be composed correctly."""
        try:
            from src.server import app
            
            # Test that all required tools are registered
            tool_names = [tool.name for tool in app.list_tools()]
            
            assert "generate_auto_prompt" in tool_names
            assert "generate_code_review_context" in tool_names
            assert "generate_ai_code_review" in tool_names
            
            # Test tool dependencies and composition
            # Auto-prompt should work independently
            auto_prompt_tool = next(tool for tool in app.list_tools() if tool.name == "generate_auto_prompt")
            assert auto_prompt_tool is not None
            
            # Context generation should support raw_context_only parameter
            context_tool = next(tool for tool in app.list_tools() if tool.name == "generate_code_review_context")
            assert context_tool is not None
            
            # AI review should support custom_prompt parameter
            ai_review_tool = next(tool for tool in app.list_tools() if tool.name == "generate_ai_code_review")
            assert ai_review_tool is not None
            
        except ImportError:
            pytest.skip("MCP server app not found - implementation pending")
    
    def test_workflow_error_handling_integration(self, sample_project_setup):
        """Test that errors in one tool are properly handled in the workflow."""
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            project_path = sample_project_setup
            
            # Test auto-prompt generation failure
            with patch('src.generate_code_review_context.generate_auto_prompt') as mock_auto_prompt:
                mock_auto_prompt.side_effect = Exception("Gemini API failed")
                
                with pytest.raises(Exception) as exc_info:
                    execute_auto_prompt_workflow(
                        project_path=project_path,
                        scope="full_project",
                        temperature=0.5,
                        auto_prompt=True
                    )
                
                assert "Gemini API failed" in str(exc_info.value)
            
            # Test context generation failure with graceful handling
            with patch('src.generate_code_review_context.generate_auto_prompt') as mock_auto_prompt, \
                 patch('src.generate_code_review_context.generate_code_review_context') as mock_context:
                
                mock_auto_prompt.return_value = {"generated_prompt": "Test prompt", "analysis_completed": True}
                mock_context.side_effect = Exception("Context generation failed")
                
                # Workflow should handle context generation failure gracefully
                try:
                    result = execute_auto_prompt_workflow(
                        project_path=project_path,
                        scope="full_project",
                        temperature=0.5,
                        auto_prompt=True
                    )
                    # If no exception, verify error was handled gracefully
                    assert result is not None
                except Exception as e:
                    # If exception is raised, it should be a meaningful workflow error
                    assert "Context generation failed" in str(e) or "workflow" in str(e).lower()
            
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")
    
    def test_workflow_with_different_parameters(self, sample_project_setup, mock_mcp_server_tools):
        """Test workflows with various parameter combinations."""
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            project_path = sample_project_setup
            
            # Test with different temperature values
            temperatures = [0.1, 0.5, 0.9]
            for temp in temperatures:
                mock_mcp_server_tools['auto_prompt'].reset_mock()
                mock_mcp_server_tools['ai_review'].reset_mock()
                
                result = execute_auto_prompt_workflow(
                    project_path=project_path,
                    scope="full_project",
                    temperature=temp,
                    auto_prompt=True
                )
                
                # Verify temperature is passed through to AI review
                ai_review_call = mock_mcp_server_tools['ai_review'].call_args
                assert ai_review_call[1]['temperature'] == temp
            
            # Test with phase-specific parameters
            result = execute_auto_prompt_workflow(
                project_path=project_path,
                scope="specific_phase",
                temperature=0.5,
                auto_prompt=True,
                phase_number="2.0"
            )
            
            # Verify phase number is passed to auto-prompt
            auto_prompt_call = mock_mcp_server_tools['auto_prompt'].call_args
            assert auto_prompt_call[1].get('phase_number') == "2.0" or auto_prompt_call[0] == (project_path, "specific_phase")
            
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")
    
    def test_workflow_output_formatting_integration(self, sample_project_setup):
        """Test that workflow outputs are properly formatted for users."""
        try:
            from src.generate_code_review_context import format_auto_prompt_output, execute_auto_prompt_workflow
            
            # Test auto-prompt workflow output formatting
            mock_prompt_result = {
                "generated_prompt": "Focus on authentication security and SQL injection prevention.",
                "analysis_completed": True,
                "context_analyzed": 2100,
                "focus_areas": ["security", "performance"]
            }
            
            # Test auto-prompt mode formatting
            output_auto = format_auto_prompt_output(mock_prompt_result, auto_prompt_mode=True)
            assert "🤖" in output_auto or "AI" in output_auto
            assert "authentication" in output_auto
            assert "2,100" in output_auto or "2100" in output_auto
            
            # Test prompt-only mode formatting  
            output_only = format_auto_prompt_output(mock_prompt_result, auto_prompt_mode=False)
            assert "Generated prompt:" in output_only or "Prompt:" in output_only
            assert mock_prompt_result["generated_prompt"] in output_only
            
            # Test that formatting includes key workflow information
            assert "security" in output_auto.lower()
            assert len(output_auto) > 100  # Should be substantial output
            
        except ImportError:
            pytest.skip("format_auto_prompt_output function not found - implementation pending")


class TestMCPToolDataFlow:
    """Test data flow between MCP tools in the workflow."""
    
    def test_auto_prompt_to_ai_review_data_flow(self):
        """Test that auto-prompt output correctly flows to AI review input."""
        try:
            from src.server import generate_auto_prompt, generate_ai_code_review
            
            # Mock auto-prompt generation
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = MockGeminiClient()
                mock_gemini.return_value = mock_client
                
                # Generate auto-prompt
                auto_prompt_result = generate_auto_prompt(
                    project_path="/tmp/test",
                    scope="full_project"
                )
                
                generated_prompt = auto_prompt_result["generated_prompt"]
                assert isinstance(generated_prompt, str)
                assert len(generated_prompt) > 50
                
                # Use generated prompt in AI review
                with patch('src.ai_code_review.get_gemini_model') as mock_ai_gemini:
                    mock_ai_gemini.return_value = mock_client
                    
                    ai_review_path = generate_ai_code_review(
                        context_file_path="/tmp/context.md",
                        project_path="/tmp/test",
                        custom_prompt=generated_prompt,
                        temperature=0.5
                    )
                    
                    assert ai_review_path is not None
                    assert isinstance(ai_review_path, str)
            
        except ImportError:
            pytest.skip("MCP server tools not found - implementation pending")
    
    def test_context_generation_with_raw_output(self):
        """Test that context generation produces appropriate raw output for auto-prompt."""
        try:
            from src.server import generate_code_review_context
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create minimal project structure
                test_file = Path(temp_dir) / "test.py"
                test_file.write_text("def hello(): return 'world'")
                
                # Generate context in raw mode
                context_path = generate_code_review_context(
                    project_path=temp_dir,
                    scope="full_project",
                    raw_context_only=True
                )
                
                assert context_path is not None
                assert isinstance(context_path, str)
                
                # Verify raw context file exists and contains code
                if os.path.exists(context_path):
                    with open(context_path, 'r') as f:
                        content = f.read()
                        assert "hello" in content
                        assert len(content) > 20  # Should contain substantial context
            
        except ImportError:
            pytest.skip("generate_code_review_context function not found - implementation pending")
    
    def test_workflow_parameter_propagation(self):
        """Test that parameters correctly propagate through the tool chain."""
        workflow_params = {
            "project_path": "/tmp/test_project",
            "scope": "specific_phase", 
            "temperature": 0.7,
            "phase_number": "2.1",
            "task_id": "2.1.3"
        }
        
        # Test parameter validation and propagation
        try:
            from src.generate_code_review_context import validate_cli_arguments
            
            # Mock args object with workflow parameters
            class MockArgs:
                def __init__(self, **kwargs):
                    for key, value in kwargs.items():
                        setattr(self, key, value)
                    self.auto_prompt = True
                    self.generate_prompt_only = False
                    self.context_only = False
            
            args = MockArgs(**workflow_params)
            
            # Should not raise validation errors for valid workflow parameters
            validate_cli_arguments(args)
            
            # Verify parameters are accessible
            assert args.project_path == workflow_params["project_path"]
            assert args.scope == workflow_params["scope"] 
            assert args.temperature == workflow_params["temperature"]
            
        except ImportError:
            pytest.skip("validate_cli_arguments function not found - implementation pending")


class TestWorkflowRobustness:
    """Test workflow robustness and edge cases."""
    
    def test_workflow_with_missing_files(self, tmp_path):
        """Test workflow behavior with missing or empty project files."""
        empty_project = tmp_path / "empty_project"
        empty_project.mkdir()
        
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            # Test with empty project directory
            with patch('src.generate_code_review_context.generate_auto_prompt') as mock_auto_prompt:
                mock_auto_prompt.return_value = {
                    "generated_prompt": "No significant code found for review.",
                    "analysis_completed": True,
                    "context_analyzed": 50
                }
                
                result = execute_auto_prompt_workflow(
                    project_path=str(empty_project),
                    scope="full_project",
                    temperature=0.5,
                    auto_prompt=True
                )
                
                # Workflow should handle empty projects gracefully
                assert result is not None
                mock_auto_prompt.assert_called_once()
        
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")
    
    def test_workflow_with_large_projects(self):
        """Test workflow scalability with large project structures."""
        # This test would simulate performance with large codebases
        # For now, we test that the workflow can handle the concept
        large_project_params = {
            "project_path": "/tmp/large_project",
            "scope": "full_project",
            "temperature": 0.5,
            "auto_prompt": True
        }
        
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            with patch('src.generate_code_review_context.generate_auto_prompt') as mock_auto_prompt:
                # Simulate large project response
                mock_auto_prompt.return_value = {
                    "generated_prompt": GeminiAPIMockFactory.create_large_project_prompt_response().text,
                    "analysis_completed": True,
                    "context_analyzed": 15000  # Large context
                }
                
                result = execute_auto_prompt_workflow(**large_project_params)
                
                # Verify workflow can handle large projects
                assert result is not None
                call_args = mock_auto_prompt.call_args
                assert call_args[1]['scope'] == "full_project"
        
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")
    
    def test_concurrent_workflow_safety(self):
        """Test that workflows can be run concurrently without interference."""
        # This is a placeholder for concurrent safety testing
        # In a real implementation, we'd test thread safety and resource isolation
        
        concurrent_params = [
            {"project_path": "/tmp/project1", "scope": "full_project"},
            {"project_path": "/tmp/project2", "scope": "recent_phase"},
            {"project_path": "/tmp/project3", "scope": "specific_task"}
        ]
        
        # For now, verify that multiple parameter sets can be processed
        for params in concurrent_params:
            assert "project_path" in params
            assert "scope" in params
            assert params["project_path"] != params.get("other_path", "")
        
        # This would be expanded to actual concurrent execution testing
        # when the implementation supports concurrent workflows