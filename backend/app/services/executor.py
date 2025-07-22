# app/services/executor.py
import subprocess
import os
import threading
import queue
import time
from typing import Optional, Dict, Any

from requests import session

class ExecutionSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.process: Optional[subprocess.Popen] = None
        self.input_queue = queue.Queue()
        self.output_lines = []
        self.error_lines = []
        self.is_waiting_for_input = False
        self.is_complete = False
        self.start_time = time.time()
        self.last_output_time = time.time()  
        self.output_thread = None              
        self.error_thread = None               
        self.stop_monitoring = False           
        
# Global dictionary to store active sessions
active_sessions: Dict[str, ExecutionSession] = {}

def execute_python(code: str, session_id: Optional[str] = None, 
                             user_input: Optional[str] = None,
                             prompts: Optional[list] = None) -> Dict[str, Any]:
    """
    Executor that can handle interactive input.
    """
    # Case 1: Continuing existing session with input
    if session_id and user_input is not None:
        return _continue_session_with_input(session_id, user_input)
    # Case 2: Check status of existing session
    elif session_id:
        return _get_session_status(session_id)
    else:
        # Case 3: Starting a new session
        return _start_new_execution(code)
    
def _start_output_monitoring(session: ExecutionSession):
    def monitor_stdout():
        print("[DEBUG] Stdout monitoring started")
        try:
            while session.process and session.process.poll() is None:
                # Try to read one line with a short timeout
                line = session.process.stdout.readline()
                if line:
                    clean_line = line.rstrip('\n')
                    session.output_lines.append(clean_line)
                    session.last_output_time = time.time()
                    print(f"[DEBUG] Captured stdout: '{clean_line}'")
                else:
                    time.sleep(0.05)  # Short sleep if no line
        except Exception as e:
            print(f"[DEBUG] Stdout error: {e}")
    
    def monitor_stderr():
        print("[DEBUG] Stderr monitoring started")
        try:
            while session.process and session.process.poll() is None:
                line = session.process.stderr.readline()
                if line:
                    clean_line = line.rstrip('\n')
                    session.error_lines.append(clean_line)
                    session.last_output_time = time.time()
                    print(f"[DEBUG] Captured stderr: '{clean_line}'")
                else:
                    time.sleep(0.05)
        except Exception as e:
            print(f"[DEBUG] Stderr error: {e}")
    
    # Start threads
    session.output_thread = threading.Thread(target=monitor_stdout, daemon=True)
    session.error_thread = threading.Thread(target=monitor_stderr, daemon=True)
    session.output_thread.start()
    session.error_thread.start()
    print("[DEBUG] Monitoring threads started")

def _start_new_execution(code: str) -> Dict[str, Any]:
    """Start a new execution session"""
    import uuid
    
    session_id = str(uuid.uuid4())
    session = ExecutionSession(session_id)
    
    temp_file = f"temp_{session_id}.py"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code)
        
        session.process = subprocess.Popen(
            ["python", temp_file],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        print(f"[DEBUG] Process started with PID: {session.process.pid}")
        
        _start_output_monitoring(session)
        active_sessions[session_id] = session
        
        time.sleep(0.5)  # Give it time to reach the input() call
        return _check_execution_status(session)
        
    except Exception as e:
        return {"output": None, "error": f"Failed to start execution: {str(e)}", "completed": True}
      
def _check_execution_status(session: ExecutionSession) -> Dict[str, Any]:
    """Check the current status of an execution session"""
    
    if not session.process:
        return {"output": None, "error": "Invalid session", "completed": True}
    
    # Check if process has finished
    return_code = session.process.poll()
    if return_code is not None:
        # Process completed - collect all remaining output
        return _finalize_session(session, return_code)
    
    # Check if we're waiting for input
    if _is_waiting_for_input(session):
        session.is_waiting_for_input = True
        prompt = _extract_input_prompt(session)
        return {
            "session_id": session.session_id,
            "waiting_for_input": True,
            "prompt": prompt,
            "output": "\n".join(session.output_lines) if session.output_lines else None
        }
    
    # Still running but not waiting for input yet
    # Return current output and keep session alive
    return {
        "session_id": session.session_id,
        "output": "\n".join(session.output_lines) if session.output_lines else None,
        "completed": False,
        "still_running": True
    }

def _is_waiting_for_input(session: ExecutionSession) -> bool:
    """
    Detect input waiting by process behavior rather than prompt capture
    """
    if not session.process or session.process.poll() is not None:
        return False
    
    current_time = time.time()
    time_since_start = current_time - session.start_time
    time_since_last_output = current_time - session.last_output_time
    
    print(f"[DEBUG] Time since start: {time_since_start:.2f}s, since last output: {time_since_last_output:.2f}s")
    print(f"[DEBUG] Output lines: {session.output_lines}")
    
    # Process needs to be running for a bit
    if time_since_start < 0.8:
        return False
    
    # Check if process appears to be blocked/idle
    # If we haven't gotten any output for a while, and the process is still running,
    # it's likely waiting for input
    
    # Case 1: We have some output already, but nothing recent
    if len(session.output_lines) > 0 and time_since_last_output > 1.0:
        print("[DEBUG] Detected: Has output but no recent activity - likely waiting for input")
        return True
    
    # Case 2: No output at all, but process has been running for a while
    # This happens when input() is the first statement
    if len(session.output_lines) == 0 and len(session.error_lines) == 0 and time_since_start > 1.5:
        print("[DEBUG] Detected: No output but process running - likely waiting for input")
        return True
    
    return False
 
def _extract_input_prompt(session: ExecutionSession) -> str:
    """Extract input prompt"""
    
    # If we have output lines, try to find a prompt-like line
    if session.output_lines:
        # Check the last few lines for something that looks like a prompt
        for line in reversed(session.output_lines[-3:]):  # Check last 3 lines
            line = line.strip()
            if line and (line.endswith('?') or 
                        'enter' in line.lower() or 'input' in line.lower()):
                return line
        
        # If no obvious prompt, return the last line
        return session.output_lines[-1].strip()

def _continue_session_with_input(session_id: str, user_input: str) -> Dict[str, Any]:
    """Continue an existing session by providing input"""
    if session_id not in active_sessions:
        return {"output": None, "error": "Session not found", "completed": True}
    
    session = active_sessions[session_id]
    
    if not session.process or session.process.poll() is not None:
        return {"output": None, "error": "Process is not running", "completed": True}
    
    try:
        # Write the input to the process
        session.process.stdin.write(user_input + '\n')
        session.process.stdin.flush()
        print(f"[DEBUG] Sent input to process: '{user_input}'")
        
        # Give the process time to handle the input and potentially produce more output
        time.sleep(0.5)
        
        # Check the new status
        return _check_execution_status(session)
        
    except Exception as e:
        return {"output": None, "error": f"Failed to send input: {str(e)}", "completed": True}

def _get_session_status(session_id: str) -> Dict[str, Any]:
    """Get the current status of an existing session"""
    if session_id not in active_sessions:
        return {"output": None, "error": "Session not found", "completed": True}
    
    session = active_sessions[session_id]
    return _check_execution_status(session)

def _finalize_session(session: ExecutionSession, return_code: int) -> Dict[str, Any]:
    """Finalize the session, collect all output and error, and mark as complete."""
    # Read any remaining output
    if session.process:
        try:
            # Read remaining stdout
            for line in session.process.stdout:
                session.output_lines.append(line.rstrip('\n'))
            # Read remaining stderr
            for line in session.process.stderr:
                session.error_lines.append(line.rstrip('\n'))
        except Exception:
            pass
        session.process.stdout.close()
        session.process.stderr.close()
        session.process.stdin.close()
    session.is_complete = True
    # Remove temp file if exists
    temp_file = f"temp_{session.session_id}.py"
    if os.path.exists(temp_file):
        try:
            os.remove(temp_file)
        except Exception:
            pass
    # Remove session from active_sessions
    if session.session_id in active_sessions:
        del active_sessions[session.session_id]
    return {
        "session_id": session.session_id,
        "output": "\n".join(session.output_lines) if session.output_lines else None,
        "error": "\n".join(session.error_lines) if session.error_lines else None,
        "completed": True,
    }