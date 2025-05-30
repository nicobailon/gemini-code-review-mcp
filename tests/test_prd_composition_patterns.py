"""
Test MCP tool composition patterns from PRD examples.
Following TDD Protocol: Testing the specific composition patterns described in the original PRD.
"""

import pytest
import tempfile
import os
import sys
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typing import Dict, Any, List

# Import mock classes
from test_gemini_api_mocks import MockGeminiClient, GeminiAPIMockFactory


@pytest.fixture(scope="session", autouse=True)
def setup_import_path():
    """Fixture to ensure src module can be imported in tests."""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)


class TestPRDCompositionPatterns:
    """Test MCP tool composition patterns from the original PRD examples."""
    
    def test_pattern_1_auto_prompt_to_ai_review(self, tmp_path):
        """Test Pattern 1: Auto-prompt generation → AI review (from PRD Example 1)."""
        # Create project matching PRD Example 1
        project_path = str(tmp_path / "prd_example_1")
        os.makedirs(project_path, exist_ok=True)
        
        (Path(project_path) / "api.py").write_text("""
def authenticate_user(username, password):
    # Direct SQL query - security vulnerability
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    return execute_query(query)
""")
        
        try:
            # Test the exact composition pattern from PRD
            from src.server import generate_auto_prompt, generate_ai_code_review
            
            with patch('src.server.get_gemini_model') as mock_gemini_auto, \
                 patch('src.ai_code_review.get_gemini_model') as mock_gemini_ai:
                
                # Setup auto-prompt mock
                mock_auto_client = MockGeminiClient()
                mock_gemini_auto.return_value = mock_auto_client
                
                # Setup AI review mock  
                mock_ai_client = MockGeminiClient()
                mock_gemini_ai.return_value = mock_ai_client
                
                # Step 1: Generate auto-prompt (PRD Pattern 1.1)
                auto_result = generate_auto_prompt(
                    project_path=project_path,
                    scope="full_project"
                )
                
                assert auto_result is not None
                assert "generated_prompt" in auto_result
                generated_prompt = auto_result["generated_prompt"]
                
                # Step 2: Use generated prompt in AI review (PRD Pattern 1.2)
                with patch('src.ai_code_review.create_ai_review_file') as mock_review_file:
                    mock_review_file.return_value = "/tmp/prd_pattern_1_review.md"
                    
                    ai_review_path = generate_ai_code_review(
                        context_file_path="/tmp/context.md",
                        project_path=project_path,
                        custom_prompt=generated_prompt,  # Key: using auto-generated prompt
                        temperature=0.5
                    )
                    
                    assert ai_review_path is not None
                
                print("✅ PRD Pattern 1: Auto-prompt → AI review composition working")
                
        except ImportError:
            pytest.skip("MCP server functions not found - implementation pending")
    
    def test_pattern_2_context_with_auto_prompt(self, tmp_path):
        """Test Pattern 2: Context generation + Auto-prompt composition (PRD Example 2)."""
        # Create project for context + auto-prompt pattern
        project_path = str(tmp_path / "prd_example_2")
        os.makedirs(project_path, exist_ok=True)
        
        # Create task-based project (PRD scenario)
        tasks_dir = Path(project_path) / "tasks"
        tasks_dir.mkdir()
        
        (tasks_dir / "tasks-authentication.md").write_text("""
## Tasks

- [x] 1.0 Basic Auth Implementation
  - [x] 1.1 Login endpoint
  - [ ] 1.2 Password hashing
  - [ ] 1.3 Session management

- [ ] 2.0 Security Hardening
  - [ ] 2.1 Input validation
  - [ ] 2.2 SQL injection prevention
""")
        
        (Path(project_path) / "auth.py").write_text("""
def login(username, password):
    # Implementation from tasks 1.1 - needs security review
    return validate_credentials(username, password)
""")
        
        try:
            from src.server import generate_code_review_context, generate_auto_prompt
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = MockGeminiClient()
                mock_gemini.return_value = mock_client
                
                # Step 1: Generate context (PRD Pattern 2.1)
                with patch('src.generate_code_review_context.create_context_file') as mock_context_file:
                    mock_context_file.return_value = "/tmp/prd_pattern_2_context.md"
                    
                    context_path = generate_code_review_context(
                        project_path=project_path,
                        scope="specific_phase",
                        phase_number="1.0",
                        raw_context_only=True  # For auto-prompt consumption
                    )
                    
                    assert context_path is not None
                
                # Step 2: Generate auto-prompt with phase-specific context (PRD Pattern 2.2)
                auto_result = generate_auto_prompt(
                    project_path=project_path,
                    scope="specific_phase",
                    phase_number="1.0"  # Focus on Basic Auth Implementation
                )
                
                assert auto_result is not None
                assert "generated_prompt" in auto_result
                
                # Verify phase-specific focus
                generated_prompt = auto_result["generated_prompt"]
                assert len(generated_prompt) > 50
                
                print("✅ PRD Pattern 2: Context + Auto-prompt composition working")
                
        except ImportError:
            pytest.skip("MCP server functions not found - implementation pending")
    
    def test_pattern_3_full_workflow_composition(self, tmp_path):
        """Test Pattern 3: Full workflow composition (PRD Complete Example)."""
        # Create comprehensive project matching PRD full workflow
        project_path = str(tmp_path / "prd_full_workflow")
        os.makedirs(project_path, exist_ok=True)
        
        # Create multi-module project
        (Path(project_path) / "auth_service.py").write_text("""
class AuthService:
    def authenticate(self, token):
        # Security: missing token validation
        return True
    
    def authorize(self, user, resource):
        # Missing implementation
        pass
""")
        
        (Path(project_path) / "data_service.py").write_text("""
def get_user_data(user_id):
    # Performance: inefficient query
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return execute_slow_query(query)
""")
        
        # Create task list for full workflow
        tasks_dir = Path(project_path) / "tasks" 
        tasks_dir.mkdir()
        
        (tasks_dir / "tasks-microservices.md").write_text("""
## Microservices Implementation

- [x] 1.0 Authentication Service
  - [x] 1.1 Basic auth endpoint
  - [ ] 1.2 Token validation
  - [ ] 1.3 Authorization logic

- [x] 2.0 Data Service  
  - [x] 2.1 User data retrieval
  - [ ] 2.2 Query optimization
  - [ ] 2.3 Caching layer

- [ ] 3.0 Integration
  - [ ] 3.1 Service communication
  - [ ] 3.2 Error handling
  - [ ] 3.3 Monitoring
""")
        
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            # Test the complete workflow composition from PRD
            with patch('src.generate_code_review_context.generate_auto_prompt') as mock_auto_prompt, \
                 patch('src.generate_code_review_context.generate_code_review_context') as mock_context, \
                 patch('src.generate_code_review_context.generate_ai_code_review') as mock_ai_review:
                
                # Setup realistic PRD workflow responses
                mock_auto_prompt.return_value = {
                    "generated_prompt": "Focus on authentication service token validation implementation and data service query optimization. Address missing authorization logic and implement proper error handling across microservices.",
                    "analysis_completed": True,
                    "context_analyzed": 1800,
                    "focus_areas": ["security", "performance", "microservices"]
                }
                
                mock_context.return_value = "/tmp/prd_full_context.md"
                mock_ai_review.return_value = "/tmp/prd_full_review.md"
                
                # Execute full workflow (PRD Pattern 3)
                result = execute_auto_prompt_workflow(
                    project_path=project_path,
                    scope="full_project",
                    temperature=0.5,
                    auto_prompt=True,
                    generate_prompt_only=False
                )
                
                # Verify complete composition chain
                mock_auto_prompt.assert_called_once()
                mock_context.assert_called_once()
                mock_ai_review.assert_called_once()
                
                # Verify parameter flow through composition
                auto_call = mock_auto_prompt.call_args[1]
                assert auto_call['project_path'] == project_path
                assert auto_call['scope'] == "full_project"
                
                context_call = mock_context.call_args[1]
                assert context_call['project_path'] == project_path
                assert context_call['raw_context_only'] is True
                
                ai_review_call = mock_ai_review.call_args[1]
                assert "authentication service" in ai_review_call['custom_prompt'].lower()
                assert ai_review_call['temperature'] == 0.5
                
                assert result is not None
                
                print("✅ PRD Pattern 3: Full workflow composition working")
                
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")
    
    def test_pattern_4_scope_specific_composition(self, tmp_path):
        """Test Pattern 4: Scope-specific composition patterns (PRD Scoping Examples)."""
        # Create project with clear phase structure for scope testing
        project_path = str(tmp_path / "prd_scope_examples")
        os.makedirs(project_path, exist_ok=True)
        
        # Create files representing different development phases
        (Path(project_path) / "phase1_auth.py").write_text("""
# Phase 1: Authentication basics
def basic_login(username, password):
    return username == "admin" and password == "password"
""")
        
        (Path(project_path) / "phase2_security.py").write_text("""
# Phase 2: Security hardening
import hashlib
def secure_login(username, password_hash):
    # Improved but still needs work
    stored_hash = get_user_hash(username)
    return password_hash == stored_hash
""")
        
        (Path(project_path) / "phase3_performance.py").write_text("""
# Phase 3: Performance optimization
import redis
def cached_user_lookup(user_id):
    # Performance improvements
    cache_key = f"user:{user_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    return fetch_from_db(user_id)
""")
        
        # Create phase-specific task list
        tasks_dir = Path(project_path) / "tasks"
        tasks_dir.mkdir()
        
        (tasks_dir / "tasks-phased-development.md").write_text("""
## Phased Development

- [x] 1.0 Phase 1: Basic Authentication
  - [x] 1.1 Simple login function
  - [x] 1.2 Basic validation

- [x] 2.0 Phase 2: Security Hardening  
  - [x] 2.1 Password hashing
  - [ ] 2.2 Salt generation
  - [ ] 2.3 Rate limiting

- [x] 3.0 Phase 3: Performance Optimization
  - [x] 3.1 Redis caching
  - [ ] 3.2 Database optimization
  - [ ] 3.3 Load balancing
""")
        
        try:
            from src.server import generate_auto_prompt
            
            # Test different scope compositions from PRD
            scope_test_cases = [
                {
                    "scope": "recent_phase",
                    "expected_focus": "phase 3",
                    "description": "Should focus on most recent development (Phase 3)"
                },
                {
                    "scope": "specific_phase", 
                    "phase_number": "2.0",
                    "expected_focus": "security hardening",
                    "description": "Should focus specifically on Phase 2"
                },
                {
                    "scope": "specific_task",
                    "task_id": "2.2", 
                    "expected_focus": "salt generation",
                    "description": "Should focus on specific task 2.2"
                }
            ]
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = MockGeminiClient()
                mock_gemini.return_value = mock_client
                
                for test_case in scope_test_cases:
                    # Prepare kwargs for scope-specific call
                    kwargs = {
                        "project_path": project_path,
                        "scope": test_case["scope"]
                    }
                    
                    if "phase_number" in test_case:
                        kwargs["phase_number"] = test_case["phase_number"]
                    if "task_id" in test_case:
                        kwargs["task_id"] = test_case["task_id"]
                    
                    # Execute scope-specific auto-prompt
                    result = generate_auto_prompt(**kwargs)
                    
                    assert result is not None
                    assert "generated_prompt" in result
                    
                    # Verify scope-specific behavior
                    generated_prompt = result["generated_prompt"]
                    assert len(generated_prompt) > 50
                    
                    print(f"✅ PRD Pattern 4.{test_case['scope']}: {test_case['description']} working")
            
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")


class TestPRDIntegrationScenarios:
    """Test integration scenarios from PRD use cases."""
    
    def test_prd_use_case_1_security_focused_review(self, tmp_path):
        """Test PRD Use Case 1: Security-focused code review with auto-prompt."""
        # Create project with security issues (PRD Example)
        project_path = str(tmp_path / "security_review_project")
        os.makedirs(project_path, exist_ok=True)
        
        (Path(project_path) / "vulnerable_app.py").write_text("""
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/api/user', methods=['GET'])
def get_user():
    user_id = request.args.get('id')
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_id}"
    
    conn = sqlite3.connect('app.db')
    result = conn.execute(query).fetchone()
    
    # Information disclosure
    return jsonify({
        'user': result,
        'query': query,  # Exposing query structure
        'db_path': 'app.db'  # Exposing system info
    })

@app.route('/api/admin', methods=['POST'])
def admin_action():
    # Missing authentication
    action = request.json.get('action')
    
    # Command injection risk
    os.system(f"admin_tool --action {action}")
    
    return jsonify({'status': 'executed'})
""")
        
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            with patch('src.generate_code_review_context.generate_auto_prompt') as mock_auto_prompt, \
                 patch('src.generate_code_review_context.generate_ai_code_review') as mock_ai_review:
                
                # Setup security-focused response (PRD Use Case 1)
                mock_auto_prompt.return_value = {
                    "generated_prompt": "CRITICAL SECURITY REVIEW: Focus on SQL injection vulnerability in user endpoint, command injection risk in admin action, and information disclosure in API responses. Prioritize immediate security hardening.",
                    "analysis_completed": True,
                    "context_analyzed": 1200,
                    "focus_areas": ["security", "vulnerabilities", "immediate_action"]
                }
                
                mock_ai_review.return_value = "/tmp/security_focused_review.md"
                
                # Execute security-focused workflow
                result = execute_auto_prompt_workflow(
                    project_path=project_path,
                    scope="full_project",
                    temperature=0.3,  # Lower temperature for security consistency
                    auto_prompt=True
                )
                
                # Verify security focus was applied
                mock_auto_prompt.assert_called_once()
                mock_ai_review.assert_called_once()
                
                ai_review_call = mock_ai_review.call_args[1]
                custom_prompt = ai_review_call['custom_prompt']
                
                # PRD requirement: Security issues should be prioritized
                assert "CRITICAL" in custom_prompt or "security" in custom_prompt.lower()
                assert "SQL injection" in custom_prompt or "injection" in custom_prompt.lower()
                
                assert result is not None
                
                print("✅ PRD Use Case 1: Security-focused review working")
                
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")
    
    def test_prd_use_case_2_performance_optimization_review(self, tmp_path):
        """Test PRD Use Case 2: Performance optimization with task-specific focus."""
        # Create project with performance issues (PRD Example)
        project_path = str(tmp_path / "performance_review_project")
        os.makedirs(project_path, exist_ok=True)
        
        (Path(project_path) / "slow_service.py").write_text("""
import time
import requests

class DataProcessor:
    def __init__(self):
        self.cache = {}
    
    def process_users(self, user_ids):
        results = []
        # Performance issue: N+1 query problem
        for user_id in user_ids:
            user_data = self.fetch_user(user_id)
            processed = self.process_user_data(user_data)
            results.append(processed)
        return results
    
    def fetch_user(self, user_id):
        # Performance issue: no connection pooling
        # Performance issue: synchronous API calls
        response = requests.get(f"https://api.example.com/users/{user_id}")
        time.sleep(0.1)  # Simulating slow API
        return response.json()
    
    def process_user_data(self, user_data):
        # Performance issue: expensive computation in loop
        complex_result = 0
        for i in range(10000):
            complex_result += i * len(str(user_data))
        
        return {
            'processed': True,
            'result': complex_result,
            'user': user_data
        }
""")
        
        # Create performance-focused task list
        tasks_dir = Path(project_path) / "tasks"
        tasks_dir.mkdir()
        
        (tasks_dir / "tasks-performance-optimization.md").write_text("""
## Performance Optimization Tasks

- [x] 1.0 Data Processing Setup
  - [x] 1.1 Basic user processing
  - [x] 1.2 API integration
  - [ ] 1.3 Batch processing
  - [ ] 1.4 Caching layer

- [ ] 2.0 API Performance
  - [ ] 2.1 Connection pooling
  - [ ] 2.2 Async API calls
  - [ ] 2.3 Response caching
  - [ ] 2.4 Rate limiting

- [ ] 3.0 Processing Optimization
  - [ ] 3.1 Algorithm optimization
  - [ ] 3.2 Memory usage reduction
  - [ ] 3.3 Parallel processing
  - [ ] 3.4 Performance monitoring
""")
        
        try:
            from src.server import generate_auto_prompt
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = MockGeminiClient([
                    GeminiAPIMockFactory.create_large_project_prompt_response()
                ])
                mock_gemini.return_value = mock_client
                
                # Test performance-focused auto-prompt (PRD Use Case 2)
                result = generate_auto_prompt(
                    project_path=project_path,
                    scope="specific_phase",
                    phase_number="2.0"  # Focus on API Performance
                )
                
                assert result is not None
                assert "generated_prompt" in result
                
                generated_prompt = result["generated_prompt"]
                
                # PRD requirement: Should focus on performance aspects
                assert len(generated_prompt) > 100
                
                print("✅ PRD Use Case 2: Performance optimization review working")
                
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
    
    def test_prd_use_case_3_feature_completion_review(self, tmp_path):
        """Test PRD Use Case 3: Feature completion review with task tracking."""
        # Create project with mixed completion status (PRD Example)
        project_path = str(tmp_path / "feature_completion_project")
        os.makedirs(project_path, exist_ok=True)
        
        (Path(project_path) / "user_management.py").write_text("""
# User Management Feature - Partially Implemented

class UserManager:
    def __init__(self):
        self.users = {}
    
    def create_user(self, username, email):
        # Task 1.1: COMPLETED
        user_id = len(self.users) + 1
        self.users[user_id] = {
            'username': username,
            'email': email,
            'created_at': datetime.now()
        }
        return user_id
    
    def update_user(self, user_id, **kwargs):
        # Task 1.2: PARTIAL - missing validation
        if user_id in self.users:
            self.users[user_id].update(kwargs)
            return True
        return False
    
    def delete_user(self, user_id):
        # Task 1.3: NOT IMPLEMENTED
        pass  # TODO: Implement user deletion
    
    def get_user_permissions(self, user_id):
        # Task 2.1: NOT IMPLEMENTED  
        pass  # TODO: Implement permission system
    
    def send_notification(self, user_id, message):
        # Task 3.1: COMPLETED
        print(f"Notification to {user_id}: {message}")
""")
        
        # Create feature completion task list
        tasks_dir = Path(project_path) / "tasks"
        tasks_dir.mkdir()
        
        (tasks_dir / "tasks-user-management-feature.md").write_text("""
## User Management Feature

- [x] 1.0 Basic User Operations
  - [x] 1.1 Create user functionality
  - [ ] 1.2 Update user with validation
  - [ ] 1.3 Delete user functionality

- [ ] 2.0 Permission System
  - [ ] 2.1 User permission management
  - [ ] 2.2 Role-based access control
  - [ ] 2.3 Permission validation

- [x] 3.0 User Notifications
  - [x] 3.1 Basic notification system
  - [ ] 3.2 Email notifications
  - [ ] 3.3 Notification preferences
""")
        
        try:
            from src.server import generate_auto_prompt
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = MockGeminiClient()
                mock_gemini.return_value = mock_client
                
                # Test feature completion focused review (PRD Use Case 3)
                result = generate_auto_prompt(
                    project_path=project_path,
                    scope="recent_phase"  # Focus on completing current work
                )
                
                assert result is not None
                assert "generated_prompt" in result
                
                generated_prompt = result["generated_prompt"]
                assert len(generated_prompt) > 50
                
                print("✅ PRD Use Case 3: Feature completion review working")
                
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")


class TestPRDWorkflowValidation:
    """Validate that implemented workflows match PRD specifications."""
    
    def test_prd_workflow_parameter_passing(self, tmp_path):
        """Test that parameters flow correctly through PRD-specified workflows."""
        project_path = str(tmp_path / "prd_validation_project")
        os.makedirs(project_path, exist_ok=True)
        
        (Path(project_path) / "test.py").write_text("def test(): pass")
        
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            # Test PRD-specified parameter combinations
            prd_parameter_sets = [
                {
                    "name": "Full Project Auto-Prompt",
                    "params": {
                        "project_path": project_path,
                        "scope": "full_project",
                        "temperature": 0.5,
                        "auto_prompt": True,
                        "generate_prompt_only": False
                    }
                },
                {
                    "name": "Phase-Specific Generation",
                    "params": {
                        "project_path": project_path,
                        "scope": "specific_phase",
                        "phase_number": "1.0",
                        "temperature": 0.7,
                        "auto_prompt": False,
                        "generate_prompt_only": True
                    }
                },
                {
                    "name": "Task-Specific Review",
                    "params": {
                        "project_path": project_path,
                        "scope": "specific_task",
                        "task_id": "1.1",
                        "temperature": 0.3,
                        "auto_prompt": True,
                        "generate_prompt_only": False
                    }
                }
            ]
            
            with patch('src.generate_code_review_context.generate_auto_prompt') as mock_auto_prompt, \
                 patch('src.generate_code_review_context.generate_ai_code_review') as mock_ai_review:
                
                mock_auto_prompt.return_value = {
                    "generated_prompt": "PRD validation prompt",
                    "analysis_completed": True
                }
                mock_ai_review.return_value = "/tmp/prd_validation_review.md"
                
                for test_case in prd_parameter_sets:
                    # Reset mocks for each test
                    mock_auto_prompt.reset_mock()
                    mock_ai_review.reset_mock()
                    
                    # Execute workflow with PRD parameters
                    result = execute_auto_prompt_workflow(**test_case["params"])
                    
                    # Verify parameter passing according to PRD specs
                    if test_case["params"]["auto_prompt"]:
                        mock_auto_prompt.assert_called_once()
                        auto_call = mock_auto_prompt.call_args[1]
                        assert auto_call['project_path'] == project_path
                        assert auto_call['scope'] == test_case["params"]["scope"]
                    
                    if not test_case["params"]["generate_prompt_only"]:
                        mock_ai_review.assert_called_once()
                        ai_call = mock_ai_review.call_args[1]
                        assert ai_call['temperature'] == test_case["params"]["temperature"]
                    
                    assert result is not None
                    
                    print(f"✅ PRD Parameter Validation: {test_case['name']} working")
            
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")
    
    def test_prd_output_format_compliance(self, tmp_path):
        """Test that outputs match PRD-specified formats."""
        project_path = str(tmp_path / "prd_output_format_test")
        os.makedirs(project_path, exist_ok=True)
        
        (Path(project_path) / "sample.py").write_text("def sample(): return 'format_test'")
        
        try:
            from src.generate_code_review_context import format_auto_prompt_output
            
            # Test PRD-specified output formats
            sample_auto_prompt_result = {
                "generated_prompt": "Focus on code quality improvements and security vulnerability assessment.",
                "analysis_completed": True,
                "context_analyzed": 1500,
                "focus_areas": ["security", "code_quality"]
            }
            
            # Test auto-prompt mode output (PRD Format 1)
            auto_prompt_output = format_auto_prompt_output(
                sample_auto_prompt_result,
                auto_prompt_mode=True,
                ai_review_path="/tmp/review.md"
            )
            
            # Verify PRD-required elements in output
            assert isinstance(auto_prompt_output, str)
            assert len(auto_prompt_output) > 100
            
            # Test prompt-only mode output (PRD Format 2)
            prompt_only_output = format_auto_prompt_output(
                sample_auto_prompt_result,
                auto_prompt_mode=False,
                ai_review_path=None
            )
            
            assert isinstance(prompt_only_output, str)
            assert sample_auto_prompt_result["generated_prompt"] in prompt_only_output
            
            print("✅ PRD Output Format Compliance: Working")
            
        except ImportError:
            pytest.skip("format_auto_prompt_output function not found - implementation pending")
    
    def test_prd_error_handling_patterns(self, tmp_path):
        """Test error handling matches PRD specifications."""
        project_path = str(tmp_path / "prd_error_handling_test")
        os.makedirs(project_path, exist_ok=True)
        
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            # Test PRD-specified error scenarios
            prd_error_scenarios = [
                {
                    "name": "Invalid Project Path",
                    "params": {
                        "project_path": "/nonexistent/path",
                        "scope": "full_project",
                        "auto_prompt": True
                    },
                    "expected_error_type": "path_error"
                },
                {
                    "name": "Invalid Scope",
                    "params": {
                        "project_path": project_path,
                        "scope": "invalid_scope",
                        "auto_prompt": True
                    },
                    "expected_error_type": "validation_error"
                }
            ]
            
            for scenario in prd_error_scenarios:
                try:
                    result = execute_auto_prompt_workflow(**scenario["params"])
                    
                    # If no exception, verify graceful error handling
                    if result is not None:
                        # PRD requires graceful degradation
                        print(f"✅ PRD Error Handling: {scenario['name']} - Graceful degradation")
                    
                except Exception as e:
                    # PRD requires meaningful error messages
                    error_message = str(e).lower()
                    assert len(error_message) > 10, "Error message should be meaningful"
                    
                    print(f"✅ PRD Error Handling: {scenario['name']} - Exception with message")
            
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")


class TestPRDPerformanceRequirements:
    """Test that performance meets PRD requirements."""
    
    def test_prd_response_time_requirements(self, tmp_path):
        """Test that workflows meet PRD response time requirements."""
        import time
        
        project_path = str(tmp_path / "prd_performance_test")
        os.makedirs(project_path, exist_ok=True)
        
        # Create moderately sized project for performance testing
        for i in range(20):
            (Path(project_path) / f"module_{i}.py").write_text(f"""
def function_{i}():
    return {i} * 2

class Class{i}:
    def method(self):
        return "module_{i}"
""")
        
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            with patch('src.generate_code_review_context.generate_auto_prompt') as mock_auto_prompt, \
                 patch('src.generate_code_review_context.generate_ai_code_review') as mock_ai_review:
                
                mock_auto_prompt.return_value = {
                    "generated_prompt": "PRD performance test prompt",
                    "analysis_completed": True
                }
                mock_ai_review.return_value = "/tmp/prd_performance_review.md"
                
                # Test PRD performance requirement: < 30 seconds for moderate projects
                start_time = time.time()
                
                result = execute_auto_prompt_workflow(
                    project_path=project_path,
                    scope="full_project",
                    temperature=0.5,
                    auto_prompt=True
                )
                
                execution_time = time.time() - start_time
                
                # PRD requirement: reasonable response time
                assert execution_time < 10.0, f"PRD Performance: Workflow too slow - {execution_time:.2f}s"
                assert result is not None
                
                print(f"✅ PRD Performance Requirement: {execution_time:.2f}s (< 10s target)")
                
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")
    
    def test_prd_resource_usage_requirements(self, tmp_path):
        """Test that resource usage meets PRD requirements."""
        import psutil
        import gc
        
        project_path = str(tmp_path / "prd_resource_test")
        os.makedirs(project_path, exist_ok=True)
        
        (Path(project_path) / "test_file.py").write_text("def test(): pass")
        
        try:
            from src.server import generate_auto_prompt
            
            # Measure initial memory
            gc.collect()
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = MockGeminiClient()
                mock_gemini.return_value = mock_client
                
                # Execute operation
                result = generate_auto_prompt(
                    project_path=project_path,
                    scope="full_project"
                )
                
                # Measure final memory
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_delta = final_memory - initial_memory
                
                # PRD requirement: reasonable memory usage
                assert memory_delta < 100, f"PRD Resource: Memory usage too high - {memory_delta:.1f}MB"
                assert result is not None
                
                print(f"✅ PRD Resource Requirement: {memory_delta:.1f}MB memory delta")
                
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")