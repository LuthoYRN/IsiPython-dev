# app/services/executor.py
import subprocess
import os
import ast
import threading
import time
from typing import Optional, Dict, Any

class ExecutionSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.process: Optional[subprocess.Popen] = None
        self.current_prompt = ""
        self.output_lines = []
        self.error_lines = []
        self.is_waiting_for_input = False
        self.is_complete = False
        self.last_activity = time.time()  # Track last user interaction
        self.max_output_lines = 100  # Limit output buffer
        self.output_thread = None              
        self.error_thread = None        
        self.code = ""        
        self.line_mapping = {}  # Store line mapping for error translation
    
    def update_activity(self):
        """Update the last activity timestamp"""
        self.last_activity = time.time()
    
    def add_output_line(self, line: str):
        """Add output line with limit enforcement"""
        self.output_lines.append(line)
        if len(self.output_lines) > self.max_output_lines:
            # Keep only the last N lines
            self.output_lines = self.output_lines[-self.max_output_lines:]
        
# Global dictionary to store active sessions
active_sessions: Dict[str, ExecutionSession] = {}

def execute_python(original_code: str = "", transpiled_code: str = "", line_mapping: dict = None,
                   session_id: Optional[str] = None, user_input: Optional[str] = None) -> Dict[str, Any]:
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
        return _start_new_execution(original_code, transpiled_code, line_mapping or {})
    
def _start_output_monitoring(session: ExecutionSession):
    def monitor_stdout():
        print("[DEBUG] Stdout monitoring started")
        try:
            while session.process and session.process.poll() is None:
                # Try to read one line with a short timeout
                line = session.process.stdout.readline()
                if line:
                    clean_line = line.rstrip('\n')
                    if line.startswith(">>>"): #for input prompts
                        clean_line = clean_line[3:]
                        session.current_prompt = clean_line
                    session.add_output_line(clean_line)
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

def _start_new_execution(original_code: str, transpiled_code: str, line_mapping: dict) -> Dict[str, Any]:
    """Start a new execution session"""
    import uuid
    
    session_id = str(uuid.uuid4())
    session = ExecutionSession(session_id)
    session.code = original_code
    session.line_mapping = line_mapping
    
    temp_file = f"temp_{session_id}.py"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(transpiled_code)
        
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
    
    if _is_waiting_for_debug_step(session):
        debug_info = _parse_debug_output(session.output_lines)
        return {
            "session_id": session.session_id,
            "waiting_for_debug_step": True,
            "waiting_for_input": False,
            "current_line": debug_info.get("line"),
            "variables": debug_info.get("variables", {}),
            "output": _filter_program_output(session.output_lines)
        }
    
    # Check if we're waiting for input
    if _is_waiting_for_input(session):
        session.is_waiting_for_input = True
        result = {
            "session_id": session.session_id,
            "waiting_for_input": True,
            "prompt": session.current_prompt,
            "output": _filter_program_output(session.output_lines)
        }
        if _is_in_debug_mode(session):
            debug_info = _parse_debug_output(session.output_lines)
            current_line = debug_info.get("line")
            if current_line:
                result["current_line"] = current_line
        return result
    # Check for infinite loop
    if _detect_infinite_loop(session):
        return _handle_infinite_loop(session)
    # Still running but not waiting for input yet
    # Return current output and keep session alive
    return {
        "session_id": session.session_id,
        "output": _filter_program_output(session.output_lines),
        "completed": False,
        "still_running": True
    }

def _is_in_debug_mode(session: ExecutionSession) -> bool:
    """Check if the session is running in debug mode by looking for debug markers in output"""
    for line in session.output_lines:
        if line.startswith("D-D-D:"):
            return True
    return False

def _is_waiting_for_input(session: ExecutionSession) -> bool:
    if not session.process or session.process.poll() is not None:
        return False
    
    if session.current_prompt and session.output_lines[-1]==session.current_prompt:
        print(f"[DEBUG] Detected input prompt: {session.current_prompt}")
        return True
  
    return False

def _is_waiting_for_debug_step(session: ExecutionSession) -> bool:
    """Check if we're at a debug pause (D-D-D:STEP)"""
    if len(session.output_lines) >= 1:
        last_line = session.output_lines[-1]
        if last_line == "D-D-D:STEP":
            return True
    return False

def _parse_debug_output(output_lines):
    """Extract debug info from recent output"""
    debug_info = {}
    
    # Look for debug markers in recent output, starting from most recent
    for line in reversed(output_lines[-10:]):
        # Get the most recent line number (first one we encounter going backwards)
        if "line" not in debug_info and line.startswith("D-D-D:LINE:"):
            debug_info["line"] = int(line.split(":")[2])
        
        # Get the most recent variables (first one we encounter going backwards)  
        elif "variables" not in debug_info and line.startswith("D-D-D:VARS:"):
            try:
                var_string = line[11:]  # Remove "D-D-D:VARS:"
                debug_info["variables"] = ast.literal_eval(var_string)
            except:
                debug_info["variables"] = {}
        
        # Stop when we have both pieces of info
        if "line" in debug_info and "variables" in debug_info:
            break
                
    return debug_info

def _filter_program_output(output_lines):
    """Filter out debug markers, return only actual program output"""
    filtered = []
    for line in output_lines:
        if not line.startswith("D-D-D:"):
            filtered.append(line)
    return "\n".join(filtered)

def _detect_infinite_loop(session: ExecutionSession) -> bool:
    """Only called when we're NOT waiting for input"""
    time_running = time.time() - session.last_activity
    
    if time_running > 10:  # 10 seconds without activity
        print(f"[DEBUG] Long running/slow/possible infinite loop detected: {time_running:.1f}s")
        return True
    
    return False

def _handle_infinite_loop(session: ExecutionSession) -> Dict[str, Any]:
    """Handle long running code/ possible infinite loop by killing process and cleaning up"""
    print(f"[DEBUG] Killing potential infinite loop/long running process PID: {session.process.pid}")
    
    # Kill the process
    kill_session(session.session_id)
    return {
        "session_id": session.session_id,
        "output": _filter_program_output(session.output_lines),
        "error": "[Timeout]",
        "code": session.code,
        "completed": True
    }

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
        session.update_activity()
        session.current_prompt = ""
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

def _finalize_session(session: ExecutionSession) -> Dict[str, Any]:
    """Finalize the session, collect all output and error, and mark as complete."""
    # Read any remaining output
    if session.process:
        try:
            # Read remaining stdout
            for line in session.process.stdout:
                session.add_output_line(line.rstrip('\n'))
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
        "output": _filter_program_output(session.output_lines),
        "error": "\n".join(session.error_lines) if session.error_lines else None,
        "line_mapping": session.line_mapping,
        "completed": True,
    }

def kill_session(session_id) ->Dict[str, Any]:
    """Kill a running execution session"""
    if session_id not in active_sessions:
        return ({"error": "Session not found"}), 404
        
    session = active_sessions[session_id]
        
    # Kill the process if it's running
    if session.process and session.process.poll() is None:
        session.process.kill()
            
    # Clean up temp file
    temp_file = f"temp_{session_id}.py"
    if os.path.exists(temp_file):
        os.remove(temp_file)
            
    # Remove from active sessions
    del active_sessions[session_id]
    return ({
            "message": "Session killed successfully",
            "session_id": session_id
        })