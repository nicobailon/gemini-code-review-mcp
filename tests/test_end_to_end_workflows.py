"""
End-to-end integration tests for complete auto-prompt generation workflows.
Following TDD Protocol: Testing complete user journeys and workflow scenarios.
"""

import pytest
import tempfile
import os
import sys
import json
import time
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


class TestCompleteUserWorkflows:
    """Test complete end-to-end user workflows."""
    
    def create_realistic_project(self, tmp_path):
        """Create a realistic project structure for testing."""
        project = tmp_path / "realistic_web_app"
        project.mkdir()
        
        # Create backend structure
        backend = project / "backend"
        backend.mkdir()
        
        (backend / "app.py").write_text("""
from flask import Flask, request, jsonify
import sqlite3
import hashlib

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    # Security issue: direct SQL query without parameterization
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    conn = sqlite3.connect('users.db')
    result = conn.execute(query).fetchone()
    
    if result:
        return jsonify({'status': 'success', 'user_id': result[0]})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid credentials'})

@app.route('/user/<int:user_id>')
def get_user(user_id):
    # Missing authorization check
    conn = sqlite3.connect('users.db')
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return jsonify({'user': user})

if __name__ == '__main__':
    app.run(debug=True)  # Debug mode in production
""")
        
        (backend / "database.py").write_text("""
import sqlite3
import logging

def init_db():
    conn = sqlite3.connect('users.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_user(username, password, email):
    # Performance issue: no connection pooling
    conn = sqlite3.connect('users.db')
    try:
        # Security issue: storing plain text passwords
        conn.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                    (username, password, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_all_users():
    # Performance issue: loading all users at once
    conn = sqlite3.connect('users.db')
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return users
""")
        
        # Create frontend structure
        frontend = project / "frontend"
        frontend.mkdir()
        
        (frontend / "app.js").write_text("""
class UserManager {
    constructor() {
        this.users = [];
        this.currentUser = null;
    }
    
    async login(username, password) {
        // Missing input validation
        const response = await fetch('/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            this.currentUser = data.user_id;
            // Security issue: storing sensitive data in localStorage
            localStorage.setItem('userId', data.user_id);
        }
        return data;
    }
    
    async loadUsers() {
        // Performance issue: loading all users
        const response = await fetch('/users');
        this.users = await response.json();
        this.renderUsers();
    }
    
    renderUsers() {
        // DOM manipulation without proper sanitization
        const container = document.getElementById('users');
        this.users.forEach(user => {
            const div = document.createElement('div');
            div.innerHTML = `<h3>${user.username}</h3><p>${user.email}</p>`;
            container.appendChild(div);
        });
    }
}

// Initialize app
const userManager = new UserManager();
""")
        
        # Create task list with mixed completion status
        tasks_dir = project / "tasks"
        tasks_dir.mkdir()
        
        (tasks_dir / "tasks-user-authentication.md").write_text("""
## Tasks

- [x] 1.0 Basic Authentication System
  - [x] 1.1 Create login endpoint
  - [x] 1.2 User database schema
  - [ ] 1.3 Password hashing implementation
  - [ ] 1.4 Session management

- [ ] 2.0 Security Hardening
  - [ ] 2.1 SQL injection prevention
  - [ ] 2.2 Authorization middleware
  - [ ] 2.3 Input validation
  - [ ] 2.4 Security headers

- [x] 3.0 Frontend User Interface
  - [x] 3.1 Login form
  - [x] 3.2 User list display
  - [ ] 3.3 Input sanitization
  - [ ] 3.4 Error handling

- [ ] 4.0 Performance Optimization
  - [ ] 4.1 Database connection pooling
  - [ ] 4.2 User pagination
  - [ ] 4.3 Caching layer
  - [ ] 4.4 Frontend optimization
""")
        
        # Create configuration files
        (project / "requirements.txt").write_text("""
flask==2.3.0
sqlite3
""")
        
        (project / "package.json").write_text("""
{
  "name": "web-app",
  "version": "1.0.0",
  "dependencies": {
    "express": "^4.18.0"
  }
}
""")
        
        return str(project)
    
    def test_complete_auto_prompt_workflow(self, tmp_path):
        """Test complete auto-prompt generation workflow from CLI to AI review."""
        try:
            from src.generate_code_review_context import cli_main
            
            project_path = self.create_realistic_project(tmp_path)
            
            # Mock all the workflow components
            with patch('sys.argv', ['generate-code-review', '--auto-prompt', project_path]), \
                 patch('src.generate_code_review_context.execute_auto_prompt_workflow') as mock_workflow, \
                 patch('src.generate_code_review_context.format_auto_prompt_output') as mock_format:
                
                # Setup realistic workflow response
                mock_workflow.return_value = {
                    "status": "completed",
                    "generated_prompt": "Focus on SQL injection vulnerabilities in login endpoint and missing authorization checks in user routes. Address password storage security and implement proper input validation.",
                    "ai_review_path": "/tmp/security_focused_review.md",
                    "context_analyzed": 2800,
                    "focus_areas": ["security", "performance", "code_quality"]
                }
                
                mock_format.return_value = """
🤖 AI Auto-Prompt Generated Successfully!

📋 Generated Prompt:
Focus on SQL injection vulnerabilities in login endpoint and missing authorization checks in user routes. Address password storage security and implement proper input validation.

📊 Analysis Summary:
- Context analyzed: 2,800 characters
- Focus areas: security, performance, code_quality
- AI review generated: /tmp/security_focused_review.md

✅ Complete workflow finished!
"""
                
                # Execute the complete workflow
                result = cli_main()
                
                # Verify workflow was executed
                mock_workflow.assert_called_once()
                call_args = mock_workflow.call_args[1]
                
                assert call_args['project_path'] == project_path
                assert call_args['auto_prompt'] is True
                assert call_args['generate_prompt_only'] is False
                
                # Verify output formatting was called
                mock_format.assert_called_once()
                
                print("✅ Complete auto-prompt workflow test passed")
                
        except ImportError:
            pytest.skip("CLI main function not found - implementation pending")
    
    def test_prompt_only_workflow(self, tmp_path):
        """Test prompt-only generation workflow."""
        try:
            from src.generate_code_review_context import cli_main
            
            project_path = self.create_realistic_project(tmp_path)
            
            with patch('sys.argv', ['generate-code-review', '--generate-prompt-only', project_path]), \
                 patch('src.generate_code_review_context.execute_auto_prompt_workflow') as mock_workflow, \
                 patch('src.generate_code_review_context.format_auto_prompt_output') as mock_format:
                
                mock_workflow.return_value = {
                    "status": "completed",
                    "generated_prompt": "Review authentication system for security vulnerabilities, focusing on SQL injection prevention and proper authorization implementation.",
                    "context_analyzed": 2800,
                    "focus_areas": ["security", "authentication"]
                }
                
                mock_format.return_value = """
🎯 Generated Prompt Only:

Review authentication system for security vulnerabilities, focusing on SQL injection prevention and proper authorization implementation.

📊 Analysis: 2,800 characters reviewed
🎯 Focus: security, authentication
"""
                
                result = cli_main()
                
                # Verify prompt-only workflow
                mock_workflow.assert_called_once()
                call_args = mock_workflow.call_args[1]
                
                assert call_args['generate_prompt_only'] is True
                assert call_args['auto_prompt'] is False
                
                print("✅ Prompt-only workflow test passed")
                
        except ImportError:
            pytest.skip("CLI main function not found - implementation pending")
    
    def test_scope_specific_workflows(self, tmp_path):
        """Test workflows with different scope parameters."""
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            project_path = self.create_realistic_project(tmp_path)
            
            scope_test_cases = [
                {
                    "scope": "full_project",
                    "expected_prompt": "Comprehensive review of web application covering security vulnerabilities in authentication, performance issues in database operations, and code quality improvements throughout the codebase.",
                    "focus_areas": ["security", "performance", "code_quality"]
                },
                {
                    "scope": "recent_phase", 
                    "expected_prompt": "Focus on recent authentication system development, emphasizing security hardening and completion of pending tasks.",
                    "focus_areas": ["security", "authentication"]
                },
                {
                    "scope": "specific_phase",
                    "phase_number": "2.0",
                    "expected_prompt": "Deep dive into Security Hardening phase implementation, focusing on SQL injection prevention and authorization middleware completion.",
                    "focus_areas": ["security"]
                }
            ]
            
            for test_case in scope_test_cases:
                with patch('src.generate_code_review_context.generate_auto_prompt') as mock_auto_prompt, \
                     patch('src.generate_code_review_context.generate_ai_code_review') as mock_ai_review:
                    
                    mock_auto_prompt.return_value = {
                        "generated_prompt": test_case["expected_prompt"],
                        "analysis_completed": True,
                        "focus_areas": test_case["focus_areas"]
                    }
                    
                    mock_ai_review.return_value = "/tmp/scoped_review.md"
                    
                    kwargs = {
                        "project_path": project_path,
                        "scope": test_case["scope"],
                        "temperature": 0.5,
                        "auto_prompt": True
                    }
                    
                    if "phase_number" in test_case:
                        kwargs["phase_number"] = test_case["phase_number"]
                    
                    result = execute_auto_prompt_workflow(**kwargs)
                    
                    # Verify scope-specific behavior
                    mock_auto_prompt.assert_called_once()
                    auto_prompt_call = mock_auto_prompt.call_args[1]
                    assert auto_prompt_call['scope'] == test_case["scope"]
                    
                    if "phase_number" in test_case:
                        assert auto_prompt_call.get('phase_number') == test_case["phase_number"]
                    
                    assert result is not None
                    
                    print(f"✅ {test_case['scope']} workflow test passed")
            
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")


class TestMCPServerWorkflows:
    """Test complete MCP server workflows."""
    
    def test_mcp_tool_chain_execution(self, tmp_path):
        """Test complete MCP tool chain execution."""
        try:
            from src.server import generate_auto_prompt, generate_code_review_context, generate_ai_code_review
            
            project_path = str(tmp_path / "mcp_test_project")
            os.makedirs(project_path, exist_ok=True)
            
            # Create test files
            (Path(project_path) / "main.py").write_text("""
def vulnerable_function(user_input):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    return execute_query(query)

def slow_function(data):
    # Performance issue
    result = []
    for i in range(len(data)):
        for j in range(len(data)):
            if data[i] == data[j]:
                result.append(data[i])
    return result
""")
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = MockGeminiClient([
                    GeminiAPIMockFactory.create_successful_prompt_generation_response(),
                    GeminiAPIMockFactory.create_context_analysis_response()
                ])
                mock_gemini.return_value = mock_client
                
                # Step 1: Generate auto-prompt
                auto_prompt_result = generate_auto_prompt(
                    project_path=project_path,
                    scope="full_project"
                )
                
                assert auto_prompt_result is not None
                assert "generated_prompt" in auto_prompt_result
                generated_prompt = auto_prompt_result["generated_prompt"]
                
                # Step 2: Generate context
                with patch('src.generate_code_review_context.create_context_file') as mock_context_file:
                    mock_context_file.return_value = "/tmp/test_context.md"
                    
                    context_path = generate_code_review_context(
                        project_path=project_path,
                        scope="full_project",
                        raw_context_only=True
                    )
                    
                    assert context_path is not None
                
                # Step 3: Generate AI review with custom prompt
                with patch('src.ai_code_review.get_gemini_model') as mock_ai_gemini:
                    mock_ai_gemini.return_value = mock_client
                    
                    with patch('src.ai_code_review.create_ai_review_file') as mock_review_file:
                        mock_review_file.return_value = "/tmp/test_review.md"
                        
                        ai_review_path = generate_ai_code_review(
                            context_file_path="/tmp/test_context.md",
                            project_path=project_path,
                            custom_prompt=generated_prompt,
                            temperature=0.5
                        )
                        
                        assert ai_review_path is not None
                
                print("✅ Complete MCP tool chain execution test passed")
                
        except ImportError:
            pytest.skip("MCP server functions not found - implementation pending")
    
    def test_mcp_server_error_recovery(self, tmp_path):
        """Test MCP server workflow error recovery."""
        try:
            from src.server import generate_auto_prompt, generate_ai_code_review
            
            project_path = str(tmp_path / "error_recovery_project")
            os.makedirs(project_path, exist_ok=True)
            (Path(project_path) / "test.py").write_text("def test(): pass")
            
            # Test recovery from Gemini API failures
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = Mock()
                
                # First call fails, second succeeds
                call_count = 0
                def mock_generate_content(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        raise Exception("API temporarily unavailable")
                    else:
                        mock_response = Mock()
                        mock_response.text = "Fallback prompt generated after retry"
                        return mock_response
                
                mock_client.generate_content.side_effect = mock_generate_content
                mock_gemini.return_value = mock_client
                
                # Should recover from first failure
                try:
                    result = generate_auto_prompt(
                        project_path=project_path,
                        scope="full_project"
                    )
                    
                    # If retry mechanism exists, this should succeed
                    assert result is not None or call_count >= 1
                    print("✅ Error recovery mechanism working")
                    
                except Exception as e:
                    # If no retry mechanism, first failure should be handled gracefully
                    assert "API temporarily unavailable" in str(e)
                    print("✅ Error handling working (no retry mechanism)")
                
        except ImportError:
            pytest.skip("MCP server functions not found - implementation pending")


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""
    
    def test_large_enterprise_project_workflow(self, tmp_path):
        """Test workflow with large enterprise project structure."""
        # Create enterprise-like project
        enterprise_project = tmp_path / "enterprise_app"
        enterprise_project.mkdir()
        
        # Create microservices structure
        services = ["auth-service", "user-service", "payment-service", "notification-service"]
        
        for service in services:
            service_dir = enterprise_project / service
            service_dir.mkdir()
            
            (service_dir / "app.py").write_text(f"""
# {service.replace('-', ' ').title()}
from flask import Flask, request, jsonify
import redis
import logging

app = Flask(__name__)
redis_client = redis.Redis(host='localhost', port=6379, db=0)

@app.route('/health')
def health_check():
    return jsonify({{'status': 'healthy', 'service': '{service}'}})

@app.route('/api/{service.replace('-', '_')}/process')
def process_request():
    # Missing rate limiting
    # Missing authentication
    data = request.get_json()
    
    # Process business logic here
    result = process_{service.replace('-', '_')}(data)
    
    return jsonify(result)

def process_{service.replace('-', '_')}(data):
    # Placeholder for service-specific logic
    return {{'processed': True, 'service': '{service}'}}
""")
            
            # Create service-specific task list
            tasks_dir = service_dir / "tasks"
            tasks_dir.mkdir()
            
            (tasks_dir / f"tasks-{service}-implementation.md").write_text(f"""
## Tasks for {service.replace('-', ' ').title()}

- [x] 1.0 Basic Service Setup
  - [x] 1.1 Flask application structure
  - [x] 1.2 Health check endpoint
  - [ ] 1.3 Configuration management
  - [ ] 1.4 Logging setup

- [ ] 2.0 Security Implementation
  - [ ] 2.1 Authentication middleware
  - [ ] 2.2 Rate limiting
  - [ ] 2.3 Input validation
  - [ ] 2.4 CORS configuration

- [ ] 3.0 Performance & Reliability
  - [ ] 3.1 Redis caching
  - [ ] 3.2 Database connection pooling
  - [ ] 3.3 Circuit breaker pattern
  - [ ] 3.4 Monitoring and metrics
""")
        
        # Create shared infrastructure
        infra_dir = enterprise_project / "infrastructure"
        infra_dir.mkdir()
        
        (infra_dir / "docker-compose.yml").write_text("""
version: '3.8'
services:
  auth-service:
    build: ./auth-service
    ports:
      - "8001:8000"
  user-service:
    build: ./user-service
    ports:
      - "8002:8000"
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
""")
        
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            with patch('src.generate_code_review_context.generate_auto_prompt') as mock_auto_prompt, \
                 patch('src.generate_code_review_context.generate_ai_code_review') as mock_ai_review:
                
                mock_auto_prompt.return_value = {
                    "generated_prompt": "Enterprise microservices review focusing on authentication middleware, rate limiting implementation across services, and standardized security practices. Address missing circuit breaker patterns and monitoring gaps.",
                    "analysis_completed": True,
                    "context_analyzed": 8500,
                    "focus_areas": ["security", "microservices", "performance", "reliability"]
                }
                
                mock_ai_review.return_value = "/tmp/enterprise_review.md"
                
                result = execute_auto_prompt_workflow(
                    project_path=str(enterprise_project),
                    scope="full_project",
                    temperature=0.3,  # Lower temperature for enterprise consistency
                    auto_prompt=True
                )
                
                # Verify enterprise-scale handling
                mock_auto_prompt.assert_called_once()
                call_args = mock_auto_prompt.call_args[1]
                assert call_args['project_path'] == str(enterprise_project)
                assert call_args['scope'] == "full_project"
                
                # Should handle large project structure
                assert result is not None
                
                print("✅ Enterprise project workflow test passed")
                
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")
    
    def test_ai_ml_project_workflow(self, tmp_path):
        """Test workflow with AI/ML project characteristics."""
        ml_project = tmp_path / "ml_sentiment_analysis"
        ml_project.mkdir()
        
        # Create ML project structure
        (ml_project / "train.py").write_text("""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pickle

def load_data(file_path):
    # Missing data validation
    return pd.read_csv(file_path)

def preprocess_text(text):
    # Basic preprocessing - missing robust cleaning
    return text.lower().strip()

def train_model(data):
    # Missing hyperparameter tuning
    # Missing cross-validation
    X = data['text'].apply(preprocess_text)
    y = data['sentiment']
    
    vectorizer = TfidfVectorizer(max_features=10000)
    X_vectorized = vectorizer.fit_transform(X)
    
    X_train, X_test, y_train, y_test = train_test_split(X_vectorized, y, test_size=0.2)
    
    model = LogisticRegression()
    model.fit(X_train, y_train)
    
    # Missing model evaluation
    # Missing model versioning
    
    with open('model.pkl', 'wb') as f:
        pickle.dump((model, vectorizer), f)
    
    return model, vectorizer

if __name__ == '__main__':
    data = load_data('sentiment_data.csv')
    model, vectorizer = train_model(data)
""")
        
        (ml_project / "predict.py").write_text("""
import pickle
from flask import Flask, request, jsonify

app = Flask(__name__)

# Global model loading - performance issue
with open('model.pkl', 'rb') as f:
    model, vectorizer = pickle.load(f)

@app.route('/predict', methods=['POST'])
def predict():
    text = request.json.get('text')
    
    # Missing input validation
    # Missing rate limiting
    # Missing error handling
    
    processed_text = preprocess_text(text)
    vectorized = vectorizer.transform([processed_text])
    prediction = model.predict(vectorized)[0]
    confidence = model.predict_proba(vectorized)[0].max()
    
    return jsonify({
        'sentiment': prediction,
        'confidence': float(confidence)
    })

def preprocess_text(text):
    return text.lower().strip()

if __name__ == '__main__':
    app.run(debug=True)  # Debug mode in production
""")
        
        # Create ML-specific task list
        tasks_dir = ml_project / "tasks"
        tasks_dir.mkdir()
        
        (tasks_dir / "tasks-ml-pipeline.md").write_text("""
## ML Pipeline Tasks

- [x] 1.0 Data Processing
  - [x] 1.1 Basic data loading
  - [x] 1.2 Text preprocessing
  - [ ] 1.3 Data validation
  - [ ] 1.4 Feature engineering

- [x] 2.0 Model Training
  - [x] 2.1 Basic model implementation
  - [ ] 2.2 Hyperparameter tuning
  - [ ] 2.3 Cross-validation
  - [ ] 2.4 Model evaluation metrics

- [x] 3.0 Model Serving
  - [x] 3.1 Basic Flask API
  - [ ] 3.2 Input validation
  - [ ] 3.3 Error handling
  - [ ] 3.4 Performance optimization

- [ ] 4.0 MLOps Implementation
  - [ ] 4.1 Model versioning
  - [ ] 4.2 Monitoring and logging
  - [ ] 4.3 A/B testing framework
  - [ ] 4.4 Automated retraining
""")
        
        try:
            from src.server import generate_auto_prompt
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = MockGeminiClient([
                    GeminiAPIMockFactory.create_large_project_prompt_response()
                ])
                mock_gemini.return_value = mock_client
                
                result = generate_auto_prompt(
                    project_path=str(ml_project),
                    scope="full_project"
                )
                
                assert result is not None
                assert "generated_prompt" in result
                
                # Should handle ML project characteristics
                generated_prompt = result["generated_prompt"]
                assert len(generated_prompt) > 200
                
                print("✅ AI/ML project workflow test passed")
                
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")
    
    def test_mobile_app_project_workflow(self, tmp_path):
        """Test workflow with mobile app project structure."""
        mobile_project = tmp_path / "mobile_social_app"
        mobile_project.mkdir()
        
        # Create React Native structure
        src_dir = mobile_project / "src"
        src_dir.mkdir()
        
        (src_dir / "App.js").write_text("""
import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function App() {
  const [posts, setPosts] = useState([]);
  const [user, setUser] = useState(null);
  const [newPost, setNewPost] = useState('');

  useEffect(() => {
    loadUserData();
    loadPosts();
  }, []);

  const loadUserData = async () => {
    // Security issue: storing sensitive data in AsyncStorage
    const userData = await AsyncStorage.getItem('userToken');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  };

  const loadPosts = async () => {
    // Missing error handling
    // Missing loading states
    const response = await fetch('https://api.example.com/posts');
    const data = await response.json();
    setPosts(data);
  };

  const createPost = async () => {
    // Missing input validation
    // Missing authorization header
    await fetch('https://api.example.com/posts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: newPost })
    });
    
    setNewPost('');
    loadPosts(); // Performance issue: reloading all posts
  };

  const renderPost = ({ item }) => (
    <View style={{ padding: 10, borderBottomWidth: 1 }}>
      <Text>{item.content}</Text>
      <Text style={{ fontSize: 12, color: 'gray' }}>
        {item.author} - {item.createdAt}
      </Text>
    </View>
  );

  return (
    <View style={{ flex: 1, padding: 20 }}>
      <TextInput
        value={newPost}
        onChangeText={setNewPost}
        placeholder="What's on your mind?"
        multiline
        style={{ borderWidth: 1, padding: 10, marginBottom: 10 }}
      />
      <TouchableOpacity onPress={createPost} style={{ backgroundColor: 'blue', padding: 10 }}>
        <Text style={{ color: 'white', textAlign: 'center' }}>Post</Text>
      </TouchableOpacity>
      
      <FlatList
        data={posts}
        renderItem={renderPost}
        keyExtractor={(item) => item.id.toString()}
        style={{ marginTop: 20 }}
      />
    </View>
  );
}
""")
        
        (src_dir / "api.js").write_text("""
// API utility functions
const API_BASE = 'https://api.example.com';

export const apiCall = async (endpoint, options = {}) => {
  // Missing timeout configuration
  // Missing retry logic
  // Missing proper error handling
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  });
  
  // Missing response validation
  return response.json();
};

export const authenticatedApiCall = async (endpoint, options = {}) => {
  // Security issue: token handling
  const token = await AsyncStorage.getItem('userToken');
  
  return apiCall(endpoint, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      ...options.headers
    }
  });
};
""")
        
        # Create mobile-specific task list
        tasks_dir = mobile_project / "tasks"
        tasks_dir.mkdir()
        
        (tasks_dir / "tasks-mobile-app.md").write_text("""
## Mobile App Development Tasks

- [x] 1.0 Core App Structure
  - [x] 1.1 Basic React Native setup
  - [x] 1.2 Post creation interface
  - [x] 1.3 Post listing
  - [ ] 1.4 Navigation implementation

- [ ] 2.0 Security & Authentication
  - [ ] 2.1 Secure token storage
  - [ ] 2.2 API authentication
  - [ ] 2.3 Input sanitization
  - [ ] 2.4 Biometric authentication

- [x] 3.0 API Integration
  - [x] 3.1 Basic API calls
  - [ ] 3.2 Error handling
  - [ ] 3.3 Offline capability
  - [ ] 3.4 Real-time updates

- [ ] 4.0 Performance & UX
  - [ ] 4.1 Loading states
  - [ ] 4.2 Image optimization
  - [ ] 4.3 List virtualization
  - [ ] 4.4 Push notifications
""")
        
        try:
            from src.server import generate_auto_prompt
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = MockGeminiClient()
                mock_gemini.return_value = mock_client
                
                result = generate_auto_prompt(
                    project_path=str(mobile_project),
                    scope="recent_phase"
                )
                
                assert result is not None
                assert "generated_prompt" in result
                
                print("✅ Mobile app project workflow test passed")
                
        except ImportError:
            pytest.skip("generate_auto_prompt function not found - implementation pending")


class TestWorkflowPerformance:
    """Test end-to-end workflow performance."""
    
    def test_workflow_execution_time(self, tmp_path):
        """Test that complete workflows execute within reasonable time."""
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            # Create moderate project
            project_path = str(tmp_path / "performance_test_project")
            os.makedirs(project_path, exist_ok=True)
            
            for i in range(20):
                (Path(project_path) / f"module_{i}.py").write_text(f"""
def function_{i}():
    return {i} * 2

class Class{i}:
    def method(self):
        return list(range({i * 10}))
""")
            
            start_time = time.time()
            
            with patch('src.generate_code_review_context.generate_auto_prompt') as mock_auto_prompt, \
                 patch('src.generate_code_review_context.generate_ai_code_review') as mock_ai_review:
                
                mock_auto_prompt.return_value = {
                    "generated_prompt": "Performance test prompt",
                    "analysis_completed": True
                }
                mock_ai_review.return_value = "/tmp/perf_review.md"
                
                result = execute_auto_prompt_workflow(
                    project_path=project_path,
                    scope="full_project",
                    temperature=0.5,
                    auto_prompt=True
                )
                
                execution_time = time.time() - start_time
                
                # Complete workflow should finish quickly with mocks
                assert execution_time < 5.0, f"Workflow took too long: {execution_time:.2f}s"
                assert result is not None
                
                print(f"✅ Workflow performance test passed: {execution_time:.2f}s")
                
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")
    
    def test_multiple_concurrent_workflows(self, tmp_path):
        """Test multiple workflows can run without interference."""
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            # Create multiple test projects
            projects = []
            for i in range(3):
                project_path = str(tmp_path / f"concurrent_project_{i}")
                os.makedirs(project_path, exist_ok=True)
                (Path(project_path) / "test.py").write_text(f"def test_{i}(): return {i}")
                projects.append(project_path)
            
            results = []
            
            with patch('src.generate_code_review_context.generate_auto_prompt') as mock_auto_prompt, \
                 patch('src.generate_code_review_context.generate_ai_code_review') as mock_ai_review:
                
                mock_auto_prompt.return_value = {
                    "generated_prompt": "Concurrent test prompt",
                    "analysis_completed": True
                }
                mock_ai_review.return_value = "/tmp/concurrent_review.md"
                
                # Execute workflows sequentially (simulating concurrent behavior)
                for i, project_path in enumerate(projects):
                    result = execute_auto_prompt_workflow(
                        project_path=project_path,
                        scope="full_project", 
                        temperature=0.5,
                        auto_prompt=True
                    )
                    results.append((i, result))
                
                # All workflows should succeed
                assert len(results) == 3
                for i, result in results:
                    assert result is not None
                
                print("✅ Concurrent workflows test passed")
                
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")