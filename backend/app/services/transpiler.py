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

def transpile_code(source_code: str, debug_mode: bool = False) -> str:
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
    
    if debug_mode:
        transpiled_code = _add_debug_instrumentation(transpiled_code)

    final_code = _convert_input_calls(transpiled_code,debug_mode=debug_mode)
    return final_code

def _substitute_keywords(line: str) -> str:
    """Helper: substitute keywords only in code, not comments."""
    for xhosa_kw, py_kw in KEYWORD_MAP.items():
        if py_kw is not None:
            line = re.sub(rf'\b{xhosa_kw}\b', py_kw, line)
    return line

def _convert_input_calls(code: str,debug_mode:bool =False) -> str:
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
            print_line = f'{indent_str}print({quote_char}>>>{prompt_text}{quote_char})'
            # Replace input("prompt") with input("") in the original line
            new_line = line.replace(f'input({quote_char}{prompt_text}{quote_char})', 'input("")')
            
            # Add both lines
            result_lines.append(print_line)
            result_lines.append(new_line)
        else:
            result_lines.append(line)

    if debug_mode:
        result_lines = [line.replace('debug_pause()', 'input("")') for line in result_lines]
    
    return '\n'.join(result_lines)

def _add_debug_instrumentation(code: str) -> str:
    """Add debug instrumentation to code for step-by-step execution"""
    lines = code.split('\n')
    instrumented = []
    line_number = 1
    
    for line in lines:
        original_line = line
        stripped_line = line.strip()
        
        # Skip empty lines and comments
        if not stripped_line or stripped_line.startswith('#'):
            instrumented.append(original_line)
            line_number+=1
            continue
        
        # Skip control structure keywords entirely - don't debug them
        is_control_structure = (
            stripped_line.endswith(':') and 
            any(stripped_line.rstrip(':').split()[0] in keyword for keyword in [
                'if', 'elif', 'else', 'try', 'except', 'finally', 
                'for', 'while', 'def', 'class', 'with'
            ])
        )
        
        if is_control_structure:
            instrumented.append(original_line)
            line_number+=1
            continue
        else:
            # Check if this line exits the current scope
            is_exit_statement = any(stripped_line.startswith(keyword) for keyword in [
                'return', 'break', 'continue', 'raise'
            ])
            
            indentation = len(line) - len(line.lstrip())
            indent_str = ' ' * indentation
            
            instrumented.append(f'{indent_str}print("D-D-D:LINE:{line_number}")')
            instrumented.append(original_line)
            
            # Only add debug pause if this line doesn't exit the scope
            if not is_exit_statement:
                instrumented.append(f'{indent_str}print("D-D-D:VARS:" + str({{k: v for k, v in locals().items() if not k.startswith("__") and type(v) in [int, float, str, bool, list, dict, type(None)]}}))')
                instrumented.append(f'{indent_str}print("D-D-D:STEP")')
                instrumented.append(f'{indent_str}debug_pause()')
        
        line_number += 1
    
    return '\n'.join(instrumented)