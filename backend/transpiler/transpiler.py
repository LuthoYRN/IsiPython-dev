import re
from keyword_map import KEYWORD_MAP

def transpile_code(source_code: str) -> str:
    """Transpile IsiPython code into valid Python code, ignoring comments."""
    lines = source_code.splitlines()
    result = []

    for line in lines:
        # Separate code from comment
        if "#" in line:
            code_part, comment_part = line.split("#", 1)
            code_transpiled = _substitute_keywords(code_part)
            result.append(f"{code_transpiled}#{comment_part}")
        else:
            result.append(_substitute_keywords(line))

    return "\n".join(result)

def _substitute_keywords(line: str) -> str:
    """Helper: substitute keywords only in code, not comments."""
    for xhosa_kw, py_kw in KEYWORD_MAP.items():
        if py_kw is not None:
            line = re.sub(rf'\b{xhosa_kw}\b', py_kw, line)
    return line