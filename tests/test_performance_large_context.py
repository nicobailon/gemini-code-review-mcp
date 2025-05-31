"""
Performance tests for large context handling in auto-prompt generation system.
Following TDD Protocol: Testing performance characteristics and scalability.
"""

import pytest
import tempfile
import os
import sys
import time
import psutil
import threading
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
from typing import Dict, Any, List, Optional
import gc

# Import mock classes
from test_gemini_api_mocks import MockGeminiClient, GeminiAPIMockFactory


@pytest.fixture(scope="session", autouse=True)
def setup_import_path():
    """Fixture to ensure src module can be imported in tests."""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)


class PerformanceMonitor:
    """Utility class for monitoring performance metrics."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.peak_memory = None
        
    def start(self):
        """Start performance monitoring."""
        gc.collect()  # Clean up before measurement
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.start_memory
        
    def update_peak_memory(self):
        """Update peak memory usage."""
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
    
    def stop(self):
        """Stop performance monitoring."""
        self.end_time = time.time()
        self.end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
    @property
    def execution_time(self):
        """Get execution time in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def memory_delta(self):
        """Get memory usage delta in MB."""
        if self.start_memory and self.end_memory:
            return self.end_memory - self.start_memory
        return None
    
    @property
    def peak_memory_delta(self):
        """Get peak memory usage delta in MB."""
        if self.start_memory and self.peak_memory:
            return self.peak_memory - self.start_memory
        return None


@pytest.fixture
def performance_monitor():
    """Pytest fixture providing performance monitoring."""
    return PerformanceMonitor()


class TestLargeProjectPerformance:
    """Test performance with large project structures."""
    
    def create_large_project(self, tmp_path, num_files=100, file_size_kb=50):
        """Create a large test project with many files."""
        large_project = tmp_path / "large_performance_project"
        large_project.mkdir()
        
        # Create multiple directories
        for dir_idx in range(10):
            dir_path = large_project / f"module_{dir_idx:02d}"
            dir_path.mkdir()
            
            # Create files in each directory
            for file_idx in range(num_files // 10):
                file_content = f"""
# Module {dir_idx} File {file_idx}
import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any, Union

class LargeClass{dir_idx}{file_idx}:
    \"\"\"
    This is a large class designed to test performance with substantial codebases.
    It contains multiple methods and complex logic to simulate real-world scenarios.
    \"\"\"
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data = {{}}
        self.cache = {{}}
        self.logger = logging.getLogger(__name__)
        
    def process_data(self, input_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        \"\"\"Process large amounts of data with complex transformations.\"\"\"
        results = []
        for item in input_data:
            processed_item = self._transform_item(item)
            if self._validate_item(processed_item):
                results.append(processed_item)
        return results
    
    def _transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Transform individual data items.\"\"\"
        transformed = {{}}
        for key, value in item.items():
            if isinstance(value, str):
                transformed[key] = value.upper()
            elif isinstance(value, (int, float)):
                transformed[key] = value * 2
            elif isinstance(value, list):
                transformed[key] = [self._process_list_item(v) for v in value]
            else:
                transformed[key] = value
        return transformed
    
    def _validate_item(self, item: Dict[str, Any]) -> bool:
        \"\"\"Validate processed items.\"\"\"
        required_fields = ['id', 'name', 'type']
        return all(field in item for field in required_fields)
    
    def _process_list_item(self, item: Any) -> Any:
        \"\"\"Process individual list items.\"\"\"
        if isinstance(item, str):
            return item.strip().lower()
        return item
    
    def bulk_operation(self, operation_type: str, data: List[Any]) -> Dict[str, Any]:
        \"\"\"Perform bulk operations on large datasets.\"\"\"
        start_time = time.time()
        
        if operation_type == 'aggregate':
            result = self._aggregate_data(data)
        elif operation_type == 'filter':
            result = self._filter_data(data)
        elif operation_type == 'transform':
            result = self._batch_transform(data)
        else:
            raise ValueError(f"Unknown operation type: {{operation_type}}")
        
        end_time = time.time()
        
        return {{
            'result': result,
            'execution_time': end_time - start_time,
            'processed_items': len(data)
        }}
    
    def _aggregate_data(self, data: List[Any]) -> Dict[str, Any]:
        \"\"\"Aggregate large datasets.\"\"\"
        aggregations = {{
            'count': len(data),
            'numeric_sum': sum(item for item in data if isinstance(item, (int, float))),
            'string_count': sum(1 for item in data if isinstance(item, str)),
            'unique_types': len(set(type(item).__name__ for item in data))
        }}
        return aggregations
    
    def _filter_data(self, data: List[Any]) -> List[Any]:
        \"\"\"Filter large datasets based on complex criteria.\"\"\"
        filtered = []
        for item in data:
            if self._complex_filter_condition(item):
                filtered.append(item)
        return filtered
    
    def _complex_filter_condition(self, item: Any) -> bool:
        \"\"\"Complex filtering logic.\"\"\"
        if isinstance(item, dict):
            return len(item) > 2 and 'id' in item
        elif isinstance(item, str):
            return len(item) > 5 and item.isalnum()
        elif isinstance(item, (int, float)):
            return item > 0 and item < 1000000
        return False
    
    def _batch_transform(self, data: List[Any]) -> List[Any]:
        \"\"\"Transform data in batches for efficiency.\"\"\"
        batch_size = 100
        transformed = []
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_result = [self._single_transform(item) for item in batch]
            transformed.extend(batch_result)
        
        return transformed
    
    def _single_transform(self, item: Any) -> Any:
        \"\"\"Single item transformation.\"\"\"
        if isinstance(item, dict):
            return {{k: str(v).upper() for k, v in item.items()}}
        elif isinstance(item, str):
            return item.upper()[:50]  # Truncate long strings
        elif isinstance(item, (int, float)):
            return item ** 0.5  # Square root transformation
        return str(item)

# Additional performance-testing code
def performance_critical_function():
    \"\"\"Function designed to test performance characteristics.\"\"\"
    large_data = list(range(10000))
    processed = [x * 2 + 1 for x in large_data if x % 2 == 0]
    return sum(processed)

""" + "# " + "Large comment block " * 100  # Add substantial content
                
                file_path = dir_path / f"large_file_{file_idx:03d}.py"
                file_path.write_text(file_content)
        
        # Create task files to test task parsing performance
        tasks_dir = large_project / "tasks"
        tasks_dir.mkdir()
        
        large_task_content = """
## Tasks

""" + "\n".join([
            f"- [ ] {i}.0 Performance Test Task {i}\n" + 
            "\n".join([f"  - [ ] {i}.{j} Subtask {i}.{j} with detailed description and implementation notes"
                      for j in range(1, 11)])  # 10 subtasks each
            for i in range(1, 21)  # 20 main tasks
        ])
        
        (tasks_dir / "tasks-performance-test.md").write_text(large_task_content)
        
        return str(large_project)
    
    def test_large_project_auto_prompt_performance(self, tmp_path, performance_monitor):
        """Test auto-prompt generation performance with large projects."""
        try:
            from src.server import generate_meta_prompt
            
            # Create large project (500 files, ~25MB total)
            large_project_path = self.create_large_project(tmp_path, num_files=500, file_size_kb=50)
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = MockGeminiClient()
                mock_gemini.return_value = mock_client
                
                performance_monitor.start()
                
                result = generate_meta_prompt(
                    project_path=large_project_path,
                    scope="full_project"
                )
                
                performance_monitor.stop()
                
                # Performance assertions
                assert performance_monitor.execution_time < 30.0, \
                    f"Auto-prompt generation took too long: {performance_monitor.execution_time}s"
                
                assert performance_monitor.peak_memory_delta < 200, \
                    f"Memory usage too high: {performance_monitor.peak_memory_delta}MB"
                
                # Verify result quality despite large project
                assert result is not None
                assert "generated_prompt" in result
                assert len(result["generated_prompt"]) > 100
                
                print(f"✅ Large project performance: {performance_monitor.execution_time:.2f}s, "
                      f"Memory: {performance_monitor.peak_memory_delta:.1f}MB")
                
        except ImportError:
            pytest.skip("generate_meta_prompt function not found - implementation pending")
    
    def test_context_generation_performance_large_codebase(self, tmp_path, performance_monitor):
        """Test context generation performance with large codebases."""
        try:
            from src.server import generate_code_review_context
            
            # Create very large project (1000 files)
            large_project_path = self.create_large_project(tmp_path, num_files=1000, file_size_kb=30)
            
            performance_monitor.start()
            
            with patch('src.generate_code_review_context.create_context_file') as mock_create:
                mock_create.return_value = "/tmp/large_context.md"
                
                context_path = generate_code_review_context(
                    project_path=large_project_path,
                    scope="full_project",
                    raw_context_only=True
                )
                
                performance_monitor.stop()
                
                # Performance requirements for large codebases
                assert performance_monitor.execution_time < 45.0, \
                    f"Context generation took too long: {performance_monitor.execution_time}s"
                
                assert performance_monitor.peak_memory_delta < 300, \
                    f"Memory usage too high: {performance_monitor.peak_memory_delta}MB"
                
                assert context_path is not None
                
                print(f"✅ Large context performance: {performance_monitor.execution_time:.2f}s, "
                      f"Memory: {performance_monitor.peak_memory_delta:.1f}MB")
                
        except ImportError:
            pytest.skip("generate_code_review_context function not found - implementation pending")


class TestMemoryEfficiency:
    """Test memory efficiency and resource management."""
    
    def test_memory_usage_with_multiple_requests(self, tmp_path, performance_monitor):
        """Test memory usage with multiple concurrent auto-prompt requests."""
        try:
            from src.server import generate_meta_prompt
            
            # Create moderate-sized project
            project_path = self.create_medium_project(tmp_path)
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = MockGeminiClient()
                mock_gemini.return_value = mock_client
                
                performance_monitor.start()
                
                # Simulate multiple requests
                results = []
                for i in range(10):
                    performance_monitor.update_peak_memory()
                    result = generate_meta_prompt(
                        project_path=project_path,
                        scope="full_project"
                    )
                    results.append(result)
                    
                    # Force garbage collection between requests
                    gc.collect()
                
                performance_monitor.stop()
                
                # Memory should not grow significantly with multiple requests
                assert performance_monitor.peak_memory_delta < 150, \
                    f"Memory leaked during multiple requests: {performance_monitor.peak_memory_delta}MB"
                
                # All requests should succeed
                assert len(results) == 10
                for result in results:
                    assert result is not None
                    assert "generated_prompt" in result
                
                print(f"✅ Multiple requests memory efficiency: "
                      f"Peak delta: {performance_monitor.peak_memory_delta:.1f}MB")
                
        except ImportError:
            pytest.skip("generate_meta_prompt function not found - implementation pending")
    
    def create_medium_project(self, tmp_path):
        """Create a medium-sized test project."""
        project = tmp_path / "medium_project"
        project.mkdir()
        
        # Create moderate number of files
        for i in range(50):
            file_content = f"""
def function_{i}():
    \"\"\"Function {i} for performance testing.\"\"\"
    data = [{{
        'id': j,
        'value': j * 2,
        'name': f'item_{{j}}'
    }} for j in range(100)]
    
    return sum(item['value'] for item in data)

class Class{i}:
    def __init__(self):
        self.data = list(range(1000))
    
    def process(self):
        return [x for x in self.data if x % 2 == 0]
"""
            (project / f"module_{i}.py").write_text(file_content)
        
        return str(project)
    
    def test_memory_cleanup_after_errors(self, tmp_path, performance_monitor):
        """Test that memory is properly cleaned up after errors."""
        try:
            from src.server import generate_meta_prompt
            
            project_path = self.create_medium_project(tmp_path)
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = Mock()
                mock_client.generate_content.side_effect = Exception("Simulated API error")
                mock_gemini.return_value = mock_client
                
                performance_monitor.start()
                
                # Cause multiple errors
                for i in range(5):
                    try:
                        generate_meta_prompt(
                            project_path=project_path,
                            scope="full_project"
                        )
                    except Exception:
                        pass  # Expected to fail
                    
                    performance_monitor.update_peak_memory()
                    gc.collect()
                
                performance_monitor.stop()
                
                # Memory should not accumulate despite errors
                assert performance_monitor.peak_memory_delta < 100, \
                    f"Memory leaked during error handling: {performance_monitor.peak_memory_delta}MB"
                
                print(f"✅ Error cleanup memory efficiency: "
                      f"Peak delta: {performance_monitor.peak_memory_delta:.1f}MB")
                
        except ImportError:
            pytest.skip("generate_meta_prompt function not found - implementation pending")


class TestScalabilityLimits:
    """Test system behavior at scalability limits."""
    
    def test_extremely_large_single_file(self, tmp_path, performance_monitor):
        """Test handling of extremely large single files."""
        try:
            from src.server import generate_meta_prompt
            
            extreme_project = tmp_path / "extreme_file_project"
            extreme_project.mkdir()
            
            # Create a very large file (5MB)
            large_content = "# Large file header\n" + "print('line')\n" * 250000
            (extreme_project / "enormous_file.py").write_text(large_content)
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = MockGeminiClient([
                    GeminiAPIMockFactory.create_large_project_prompt_response()
                ])
                mock_gemini.return_value = mock_client
                
                performance_monitor.start()
                
                result = generate_meta_prompt(
                    project_path=str(extreme_project),
                    scope="full_project"
                )
                
                performance_monitor.stop()
                
                # Should handle large files without excessive memory usage
                assert performance_monitor.execution_time < 60.0, \
                    f"Large file processing took too long: {performance_monitor.execution_time}s"
                
                assert performance_monitor.peak_memory_delta < 500, \
                    f"Large file used too much memory: {performance_monitor.peak_memory_delta}MB"
                
                assert result is not None
                assert "generated_prompt" in result
                
                print(f"✅ Extreme file performance: {performance_monitor.execution_time:.2f}s, "
                      f"Memory: {performance_monitor.peak_memory_delta:.1f}MB")
                
        except ImportError:
            pytest.skip("generate_meta_prompt function not found - implementation pending")
    
    def test_deep_directory_structure_performance(self, tmp_path, performance_monitor):
        """Test performance with very deep directory structures."""
        try:
            from src.server import generate_meta_prompt
            
            # Create deep directory structure (30 levels deep)
            deep_project = tmp_path / "deep_structure_project"
            current_path = deep_project
            
            for level in range(30):
                current_path = current_path / f"level_{level:02d}"
                current_path.mkdir(parents=True, exist_ok=True)
                
                # Add a file at each level
                (current_path / f"file_level_{level}.py").write_text(f"""
def function_at_level_{level}():
    \"\"\"Function at directory level {level}.\"\"\"
    return "level_{level}"

class Level{level}Class:
    def __init__(self):
        self.level = {level}
        self.data = list(range(100))
""")
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = MockGeminiClient()
                mock_gemini.return_value = mock_client
                
                performance_monitor.start()
                
                result = generate_meta_prompt(
                    project_path=str(deep_project),
                    scope="full_project"
                )
                
                performance_monitor.stop()
                
                # Should handle deep structures efficiently
                assert performance_monitor.execution_time < 20.0, \
                    f"Deep structure processing took too long: {performance_monitor.execution_time}s"
                
                assert result is not None
                assert "generated_prompt" in result
                
                print(f"✅ Deep structure performance: {performance_monitor.execution_time:.2f}s")
                
        except ImportError:
            pytest.skip("generate_meta_prompt function not found - implementation pending")


class TestConcurrentPerformance:
    """Test performance under concurrent load."""
    
    def test_concurrent_auto_prompt_requests(self, tmp_path, performance_monitor):
        """Test handling of concurrent auto-prompt requests."""
        try:
            from src.server import generate_meta_prompt
            
            project_path = str(tmp_path / "concurrent_test_project")
            os.makedirs(project_path, exist_ok=True)
            
            # Create a small test project
            (Path(project_path) / "test.py").write_text("def test(): return 'concurrent'")
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = MockGeminiClient()
                mock_gemini.return_value = mock_client
                
                results = []
                errors = []
                threads = []
                
                def worker(worker_id):
                    """Worker function for concurrent testing."""
                    try:
                        result = generate_meta_prompt(
                            project_path=project_path,
                            scope="full_project"
                        )
                        results.append((worker_id, result))
                    except Exception as e:
                        errors.append((worker_id, e))
                
                performance_monitor.start()
                
                # Start multiple concurrent requests
                for i in range(5):
                    thread = threading.Thread(target=worker, args=(i,))
                    threads.append(thread)
                    thread.start()
                
                # Wait for all threads to complete
                for thread in threads:
                    thread.join(timeout=30)  # 30 second timeout
                
                performance_monitor.stop()
                
                # Verify concurrent execution
                assert len(results) >= 3, f"Too few successful concurrent requests: {len(results)}"
                assert len(errors) <= 2, f"Too many concurrent errors: {len(errors)}"
                
                # Performance should be reasonable even with concurrency
                assert performance_monitor.execution_time < 45.0, \
                    f"Concurrent execution took too long: {performance_monitor.execution_time}s"
                
                print(f"✅ Concurrent performance: {len(results)} successful, "
                      f"{len(errors)} errors, {performance_monitor.execution_time:.2f}s")
                
        except ImportError:
            pytest.skip("generate_meta_prompt function not found - implementation pending")
    
    def test_workflow_performance_under_load(self, tmp_path, performance_monitor):
        """Test complete workflow performance under simulated load."""
        try:
            from src.generate_code_review_context import execute_auto_prompt_workflow
            
            project_path = str(tmp_path / "workflow_load_test")
            os.makedirs(project_path, exist_ok=True)
            
            # Create test files
            for i in range(20):
                (Path(project_path) / f"module_{i}.py").write_text(f"""
def function_{i}():
    return {i} * 2

class Module{i}:
    def process(self):
        return [x for x in range(100) if x % {i + 1} == 0]
""")
            
            workflow_results = []
            
            def workflow_worker(worker_id):
                """Worker for workflow testing."""
                try:
                    with patch('src.generate_code_review_context.generate_meta_prompt') as mock_auto, \
                         patch('src.generate_code_review_context.generate_ai_code_review') as mock_ai:
                        
                        mock_auto.return_value = {
                            "generated_prompt": f"Workflow test prompt {worker_id}",
                            "analysis_completed": True
                        }
                        mock_ai.return_value = f"/tmp/review_{worker_id}.md"
                        
                        result = execute_auto_prompt_workflow(
                            project_path=project_path,
                            scope="full_project",
                            temperature=0.5,
                            auto_prompt=True
                        )
                        workflow_results.append((worker_id, result))
                        
                except Exception as e:
                    workflow_results.append((worker_id, f"Error: {e}"))
            
            performance_monitor.start()
            
            # Simulate load with multiple workflow requests
            threads = []
            for i in range(3):
                thread = threading.Thread(target=workflow_worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join(timeout=45)
            
            performance_monitor.stop()
            
            # Verify workflow performance under load
            successful_workflows = [r for r in workflow_results if not str(r[1]).startswith("Error")]
            assert len(successful_workflows) >= 2, \
                f"Too few successful workflows under load: {len(successful_workflows)}"
            
            assert performance_monitor.execution_time < 60.0, \
                f"Workflow load test took too long: {performance_monitor.execution_time}s"
            
            print(f"✅ Workflow load performance: {len(successful_workflows)} successful workflows, "
                  f"{performance_monitor.execution_time:.2f}s")
            
        except ImportError:
            pytest.skip("execute_auto_prompt_workflow function not found - implementation pending")


class TestPerformanceRegression:
    """Test for performance regressions and baseline benchmarks."""
    
    def test_baseline_performance_benchmark(self, tmp_path, performance_monitor):
        """Establish baseline performance benchmarks."""
        try:
            from src.server import generate_meta_prompt
            
            # Create standardized test project
            benchmark_project = tmp_path / "benchmark_project"
            benchmark_project.mkdir()
            
            # Standard project with 100 files, ~10MB total
            for i in range(100):
                content = f"""
# Benchmark File {i}
import os
import sys
import json
from typing import Dict, List, Any

def benchmark_function_{i}(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    \"\"\"Benchmark function {i} for performance testing.\"\"\"
    processed = []
    for item in data:
        if 'id' in item and isinstance(item['id'], int):
            processed.append({{
                'id': item['id'],
                'processed': True,
                'value': item.get('value', 0) * 2
            }})
    
    return {{
        'processed_count': len(processed),
        'total_value': sum(item['value'] for item in processed),
        'function_id': {i}
    }}

class BenchmarkClass{i}:
    def __init__(self):
        self.data = list(range(1000))
        self.config = {{'setting_{j}': j for j in range(50)}}
    
    def process_benchmark(self):
        return [x ** 2 for x in self.data if x % 10 == 0]
""" + "# " + "Padding comment " * 50  # Standard padding
                
                (benchmark_project / f"benchmark_{i:03d}.py").write_text(content)
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = MockGeminiClient([
                    GeminiAPIMockFactory.create_successful_prompt_generation_response()
                ])
                mock_gemini.return_value = mock_client
                
                performance_monitor.start()
                
                result = generate_meta_prompt(
                    project_path=str(benchmark_project),
                    scope="full_project"
                )
                
                performance_monitor.stop()
                
                # Baseline performance requirements
                baseline_time = 15.0  # seconds
                baseline_memory = 100  # MB
                
                assert performance_monitor.execution_time < baseline_time, \
                    f"Performance regression: {performance_monitor.execution_time:.2f}s > {baseline_time}s baseline"
                
                assert performance_monitor.peak_memory_delta < baseline_memory, \
                    f"Memory regression: {performance_monitor.peak_memory_delta:.1f}MB > {baseline_memory}MB baseline"
                
                assert result is not None
                assert "generated_prompt" in result
                assert len(result["generated_prompt"]) > 200  # Substantial prompt
                
                # Store benchmark results for future comparison
                benchmark_results = {
                    "execution_time": performance_monitor.execution_time,
                    "peak_memory_delta": performance_monitor.peak_memory_delta,
                    "memory_delta": performance_monitor.memory_delta,
                    "project_files": 100,
                    "project_size_estimate": "~10MB"
                }
                
                print(f"✅ Baseline benchmark: {performance_monitor.execution_time:.2f}s, "
                      f"Memory: {performance_monitor.peak_memory_delta:.1f}MB")
                
                # This could be saved to a file for regression testing
                return benchmark_results
                
        except ImportError:
            pytest.skip("generate_meta_prompt function not found - implementation pending")
    
    def test_performance_with_different_scopes(self, tmp_path, performance_monitor):
        """Test performance across different scope parameters."""
        try:
            from src.server import generate_meta_prompt
            
            project_path = str(tmp_path / "scope_perf_project")
            os.makedirs(project_path, exist_ok=True)
            
            # Create moderate test project
            for i in range(50):
                (Path(project_path) / f"file_{i}.py").write_text(f"""
def scope_test_function_{i}():
    return {i} * 3

class ScopeTest{i}:
    def method(self):
        return list(range({i * 10}))
""")
            
            scopes = ["full_project", "recent_phase", "specific_phase", "specific_task"]
            scope_performance = {}
            
            with patch('src.server.get_gemini_model') as mock_gemini:
                mock_client = MockGeminiClient()
                mock_gemini.return_value = mock_client
                
                for scope in scopes:
                    performance_monitor.start()
                    
                    result = generate_meta_prompt(
                        project_path=project_path,
                        scope=scope
                    )
                    
                    performance_monitor.stop()
                    
                    scope_performance[scope] = {
                        "time": performance_monitor.execution_time,
                        "memory": performance_monitor.peak_memory_delta
                    }
                    
                    assert result is not None
                    assert "generated_prompt" in result
                    
                    # Each scope should complete within reasonable time
                    assert performance_monitor.execution_time < 20.0, \
                        f"Scope {scope} took too long: {performance_monitor.execution_time}s"
            
            # Verify scope performance characteristics
            full_project_time = scope_performance["full_project"]["time"]
            for scope in ["recent_phase", "specific_phase", "specific_task"]:
                scope_time = scope_performance[scope]["time"]
                # Narrower scopes should generally be faster or similar
                assert scope_time <= full_project_time * 1.5, \
                    f"Scope {scope} should not be much slower than full_project"
            
            print(f"✅ Scope performance: " + 
                  ", ".join([f"{scope}: {perf['time']:.2f}s" 
                           for scope, perf in scope_performance.items()]))
            
        except ImportError:
            pytest.skip("generate_meta_prompt function not found - implementation pending")