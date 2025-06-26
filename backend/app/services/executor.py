import subprocess,os

def execute_python(code: str) -> tuple[str, str]:
    """
    Executes a Python file and captures stdout and stderr.
    Returns (stdout, stderr).
    """
    temp_file = "temp.py"
    try:
        with open("temp.py", "w", encoding="utf-8") as f:
            f.write(code)

        result = subprocess.run(
            ["python", temp_file],
            capture_output=True,
            text=True,
            timeout=10  # prevent infinite loops
        )
        return result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        return "", "Execution timed out"

    except Exception as e:
        return "", f"Unexpected error: {str(e)}"
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)