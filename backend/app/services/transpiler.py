import re

KEYWORD_MAP = {
    "Ubuxoki": "False",            # Means "falsehood"
    "Inyaniso": "True",            # Means "truth"
    "Akukho": "None",              # Means "nothing"
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

    transpiled_code = "\n".join(result)
    final_code = _convert_input_calls(transpiled_code)
    return final_code

def _substitute_keywords(line: str) -> str:
    """Helper: substitute keywords only in code, not comments."""
    for xhosa_kw, py_kw in KEYWORD_MAP.items():
        if py_kw is not None:
            line = re.sub(rf'\b{xhosa_kw}\b', py_kw, line)
    return line

def _convert_input_calls(code: str) -> str:
    """
    Convert input("prompt") calls to print("prompt") + input("")
    Preserves indentation and handles complex cases
    """
    import re
    
    lines = code.split('\n')
    result_lines = []
    
    for line in lines:
        # Check if this line contains input() with a prompt
        input_match = re.search(r'input\s*\(\s*(["\'])(.*?)\1\s*\)', line)
        
        if input_match:
            quote_char = input_match.group(1)
            prompt_text = input_match.group(2)
            
            # Get the indentation of the current line
            indentation = len(line) - len(line.lstrip())
            indent_str = line[:indentation]
            
            # Create the print statement with same indentation
            print_line = f'{indent_str}print({quote_char}{prompt_text}{quote_char})'
            # Replace input("prompt") with input("") in the original line
            new_line = line.replace(f'input({quote_char}{prompt_text}{quote_char})', 'input("")')
            
            # Add both lines
            result_lines.append(print_line)
            result_lines.append(new_line)
        else:
            result_lines.append(line)
    
    return '\n'.join(result_lines)