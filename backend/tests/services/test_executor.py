import pytest
import sys
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import time
import threading

sys.path.append(str(Path(__file__).parent.parent.parent))
from app.services.executor import execute_python, kill_session, active_sessions, ExecutionSession

class TestBasicExecution:
    """Test basic code execution functionality."""
    
    @patch('app.services.executor.subprocess.Popen')
    def test_simple_code_execution(self, mock_popen):
        """Test executing simple Python code."""
        # Mock process with proper file-like objects
        mock_process = Mock()
        mock_process.poll.return_value = 0  # Process completed
        
        # Mock stdout and stderr as file-like objects
        mock_stdout = Mock()
        mock_stdout.readline.return_value = ""
        mock_stdout.__iter__ = Mock(return_value=iter([]))  # For iteration in finalize
        mock_stdout.close = Mock()
        
        mock_stderr = Mock()  
        mock_stderr.readline.return_value = ""
        mock_stderr.__iter__ = Mock(return_value=iter([]))
        mock_stderr.close = Mock()
        
        mock_stdin = Mock()
        mock_stdin.close = Mock()
        
        mock_process.stdout = mock_stdout
        mock_process.stderr = mock_stderr
        mock_process.stdin = mock_stdin
        mock_process.pid = 12345
        
        mock_popen.return_value = mock_process
        
        with patch('builtins.open', create=True) as mock_open, \
            patch('os.path.exists', return_value=True), \
            patch('os.remove') as mock_remove:
            
            result = execute_python(
                original_code="print('hello')",
                transpiled_code="print('hello')",
                line_mapping={1: 1}
            )
        
        assert result["completed"] is True
        assert "error" not in result or result["error"] is None

    @patch('app.services.executor.subprocess.Popen')
    def test_code_with_error(self, mock_popen):
        """Test executing code that produces an error."""
        mock_process = Mock()
        mock_process.poll.return_value = 1  # Process FAILED (non-zero exit)
        
        # Mock stderr with error message
        mock_stderr = Mock()
        mock_stderr.readline.return_value = ""
        mock_stderr.__iter__ = Mock(return_value=iter(["NameError: name 'x' is not defined"]))
        mock_stderr.close = Mock()
        
        # Empty stdout
        mock_stdout = Mock()
        mock_stdout.readline.return_value = ""
        mock_stdout.__iter__ = Mock(return_value=iter([]))
        mock_stdout.close = Mock()
        
        mock_stdin = Mock()
        mock_stdin.close = Mock()
        
        mock_process.stdout = mock_stdout
        mock_process.stderr = mock_stderr
        mock_process.stdin = mock_stdin
        mock_process.pid = 12345
        
        mock_popen.return_value = mock_process
        
        with patch('builtins.open', create=True), \
            patch('os.path.exists', return_value=True), \
            patch('os.remove'):
            
            result = execute_python(
                original_code="print(x)",
                transpiled_code="print(x)",
                line_mapping={1: 1}
            )
        
        assert result["completed"] is True
        assert "error" in result
        assert result["error"] is not None
    
class TestSessionManagement:
    """Test session creation and management."""
    
    def setup_method(self):
        """Clear active sessions before each test."""
        active_sessions.clear()

    def test_execution_session_creation(self):
            """Test ExecutionSession object creation."""
            session = ExecutionSession("test_session")
            
            assert session.session_id == "test_session"
            assert session.process is None
            assert session.output_lines == []
            assert session.error_lines == []
            assert session.is_waiting_for_input is False
            assert session.is_complete is False
   
    def test_session_activity_tracking(self):
        """Test session activity timestamp updates."""
        session = ExecutionSession("test_session")
        original_time = session.last_activity
        
        time.sleep(0.1)
        session.update_activity()   
        assert session.last_activity > original_time
    
    def test_output_line_limiting(self):
        """Test that output lines are limited to prevent memory issues."""
        session = ExecutionSession("test_session")
        
        # Add more lines than the limit
        for i in range(150):
            session.add_output_line(f"Line {i}")
        
        assert len(session.output_lines) <= session.max_output_lines
        assert f"Line {149}" in session.output_lines  # Latest lines kept

class TestInteractiveExecution:
    """Test interactive execution with input/output."""
    
    def setup_method(self):
        active_sessions.clear()
    
    @patch('app.services.executor.subprocess.Popen')
    def test_session_with_input_prompt(self, mock_popen):
        """Test session waiting for user input."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Still running
        mock_process.stdout.readline.side_effect = [">>>Enter name: ", ""]
        mock_process.stderr.readline.return_value = ""
        mock_popen.return_value = mock_process
        
        # Start new session
        with patch('builtins.open', create=True), \
            patch('os.path.exists', return_value=True), \
            patch('os.remove'):
        
            result = execute_python(
                original_code="name = input('Enter name: ')",
                transpiled_code="name = input('Enter name: ')",
                line_mapping={1: 1}
            )
        
        assert "session_id" in result
        assert result.get("waiting_for_input") is True
    
    def test_continue_session_with_input(self):
        """Test providing input to existing session."""
        # Create a mock session
        session = ExecutionSession("test_session")
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.stdin = Mock()
        session.process = mock_process
        active_sessions["test_session"] = session

        with patch('builtins.open', create=True), \
            patch('os.path.exists', return_value=True), \
            patch('os.remove'):
        
            result = execute_python(
                session_id="test_session",
                user_input="John"
            )
            
        # Should call stdin.write with the input
        mock_process.stdin.write.assert_called_with("John\n")
        mock_process.stdin.flush.assert_called_once()

class TestSessionLifecycle:
    """Test complete session lifecycle."""
    
    def setup_method(self):
        active_sessions.clear()
    
    def test_kill_session_success(self):
        """Test successfully killing a session."""
        # Create mock session
        session = ExecutionSession("test_session")
        mock_process = Mock()
        mock_process.poll.return_value = None  # Still running
        session.process = mock_process
        active_sessions["test_session"] = session
        
        with patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove:
            
            result = kill_session("test_session")
            
            assert result["message"] == "Session killed successfully"
            assert result["session_id"] == "test_session"
            mock_process.kill.assert_called_once()
            assert "test_session" not in active_sessions
    
    def test_kill_nonexistent_session(self):
        """Test killing a session that doesn't exist."""
        result = kill_session("nonexistent_session")
        
        assert result[0]["error"] == "Session not found"
        assert result[1] == 404

class TestErrorHandling:
    """Test various error scenarios."""
    @patch('app.services.executor.subprocess.Popen')
    def test_subprocess_creation_failure(self, mock_popen):
        """Test handling subprocess creation failure."""
        mock_popen.side_effect = OSError("Permission denied")
        
        with patch('builtins.open', create=True):
            result = execute_python(
                original_code="print('test')",
                transpiled_code="print('test')",
                line_mapping={1: 1}
            )
        
        assert result["completed"] is True
        assert "error" in result
        assert "Failed to start execution" in result["error"]
    
    def test_invalid_session_continuation(self):
        """Test continuing with invalid session ID."""
        result = execute_python(
            session_id="invalid_session",
            user_input="test"
        )
        
        assert result["completed"] is True
        assert result["error"] == "Session not found"

class TestDebugMode:
    """Test debug mode functionality."""
    
    def setup_method(self):
        active_sessions.clear()
    
    @patch('app.services.executor._is_waiting_for_debug_step')
    @patch('app.services.executor._parse_debug_output')
    @patch('app.services.executor.subprocess.Popen')
    def test_debug_step_detection(self, mock_popen, mock_parse, mock_debug_waiting):
        """Test detection of debug step waiting."""
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        
        mock_debug_waiting.return_value = True
        mock_parse.return_value = {"line": 2, "variables": {"x": 5}}
        
        # Create session manually to control the test
        session = ExecutionSession("debug_session")
        session.process = mock_process
        session.output_lines = ["D-D-D:LINE:2", "D-D-D:VARS:{'x': 5}", "D-D-D:STEP"]
        active_sessions["debug_session"] = session
        
        with patch('builtins.open', create=True), \
            patch('os.path.exists', return_value=True), \
            patch('os.remove'):
            
            result = execute_python(session_id="debug_session")
        
        assert result.get("waiting_for_debug_step") is True
        assert result.get("waiting_for_input") is False
        assert result.get("current_line") == 2
        assert result.get("variables") == {"x": 5}

class TestFileManagement:
    """Test temporary file creation and cleanup."""
    
    @patch('builtins.open', create=True)
    @patch('app.services.executor.subprocess.Popen')
    def test_temp_file_creation(self, mock_popen, mock_open):
        """Test that temporary files are created correctly."""
        mock_process = Mock()
        mock_process.poll.return_value = 0
        mock_process.stdout = []
        mock_process.stderr = []
        mock_popen.return_value = mock_process
        
        execute_python(
            original_code="print('test')",
            transpiled_code="print('test')",
            line_mapping={1: 1}
        )
        
        # Verify file was opened for writing
        mock_open.assert_called()
        # Get the call arguments
        call_args = mock_open.call_args
        filename = call_args[0][0]
        mode = call_args[0][1]
        
        assert filename.startswith("temp_")
        assert filename.endswith(".py")
        assert mode == "w"

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_code_execution(self):
        """Test executing empty code."""
        result = execute_python(
            original_code="",
            transpiled_code="",
            line_mapping={1:1}
        )
        
        # Should handle gracefully
        assert isinstance(result, dict)
        assert "completed" in result and result["completed"]==True and result["error"]==None and result["output"]=='' 