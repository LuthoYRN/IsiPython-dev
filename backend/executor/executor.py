import subprocess

def run_transpiled_file(file_path: str) -> tuple[str, str]:
    """
    Executes a Python file and captures stdout and stderr.
    Returns (stdout, stderr).
    """
    try:
        result = subprocess.run(
            ["python", file_path],
            capture_output=True,
            text=True,
            timeout=10  # prevent infinite loops
        )
        return result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        return "", "Execution timed out"

    except Exception as e:
        return "", f"Unexpected error: {str(e)}"