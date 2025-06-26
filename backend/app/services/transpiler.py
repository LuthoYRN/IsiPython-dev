import re

KEYWORD_MAP = {
    "ubuxoki": "False",            # Means "falsehood"
    "inyaniso": "True",            # Means "truth"
    "akukho": "None",              # Means "nothing"
    "kwaye": "and",                # Logical AND
    "njenga": "as",                # Used in aliasing
    "qinisekisa": "assert",        # Ensure/verify
    "ngemva": "async", #??  
    "linda": "await",              # Wait
    "yekisa": "break",             # Stop/interrupt
    "iklasi": "class",             # Borrowed term
    "qhubeka": "continue",         # Continue
    "chaza": "def",                # Define
    "cima": "del",                 # Delete
    "okanye": "or",                
    "enye": "else",                # Another/else
    "ngaphandle": "except",        # Except for
    "ekugqibeleni": "finally",     # Finally
    "jikelele": "global",          # Global
    "ukuba": "if",                 # If
    "ngenisa": "import",          # Import
    "ku": "in",                    # In / of
    "phakathi": "in",             # Alternate for “inside”
    "umsebenzi": "lambda",         # Anonymous function
    "ingaphandle": "nonlocal",     # Opposite of local
    "hayi": "not",                 # Logical NOT
    "dlula": "pass",               # Pass through
    "phakamisa": "raise",          # Raise an error
    "buyisela": "return",          # Return / give back
    "zama": "try",                 # Attempt
    "ngexesha": "while",           # While
    "nge": "with",                 # With (context manager)
    "velisa": "yield",             # Produce/generate
    "ngokulandelelana": "for",     #for i in range()
    "ukusuka": "from",            #from x import y
    "ngu": "is",                #
    "okanye_ukuba": "elif"               # If using "okanye" for both `or` and `elif`, disambiguate during parsing
}

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