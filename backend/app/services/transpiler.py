import re

KEYWORD_MAP = {
    "Ubuxoki": "False",            # Means "falsehood"
    "Inyaniso": "True",            # Means "truth"
    "Akukho": "None",              # Means "nothing"
    "kwaye": "and",                # Logical AND
    "njenge": "as",                # Used in aliasing
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
    "ngaphakathi": "in",             # In
    "umsebenzi": "lambda",         # Anonymous function
    "ingaphandle": "nonlocal",     # Opposite of local
    "hayi": "not",                 # Logical NOT
    "dlula": "pass",               # Pass through
    "phakamisa": "raise",          # Raise an error
    "buyisela": "return",          # Return / give back
    "zama": "try",                 # Attempt
    "ngelixa": "while",           # While
    "nge": "with",                 # With (context manager)
    "velisa": "yield",             # Produce/generate
    "ngokulandelelana": "for",     #for i in range()
    "ukusuka": "from",            #from x import y
    "ngu": "is",                #
    "okanye_ukuba": "elif"               # If using "okanye" for both `or` and `elif`, disambiguate during parsing
}

def transpile_code(source_code: str, debug_mode: bool = False) -> tuple[str, dict]:
    """
    Transpile IsiPython code into valid Python code, ignoring comments.
    Returns tuple of (transpiled_code, line_mapping)
    """
    lines = source_code.splitlines()
    result = []
    line_mapping = {}  # Maps transpiled_line_num -> original_line_num

    current_output_line = 1
    
    for original_line_num, line in enumerate(lines, 1):
        # Separate code from comment
        if "#" in line:
            code_part, comment_part = line.split("#", 1)
            code_transpiled = _substitute_keywords(code_part)
            transpiled_line = f"{code_transpiled}#{comment_part}"
        else:
            transpiled_line = _substitute_keywords(line)
        
        result.append(transpiled_line)
        line_mapping[current_output_line] = original_line_num
        current_output_line += 1

    transpiled_code = "\n".join(result)
    
    if debug_mode:
        transpiled_code, debug_mapping = _add_debug_instrumentation(transpiled_code, line_mapping)
        line_mapping = debug_mapping

    final_code, input_mapping = _convert_input_calls(transpiled_code, line_mapping, debug_mode=debug_mode)
    
    return final_code, input_mapping

def _substitute_keywords(line: str) -> str:
    """Helper: substitute keywords only in code, not comments."""
    for xhosa_kw, py_kw in KEYWORD_MAP.items():
        if py_kw is not None:
            line = re.sub(rf'\b{xhosa_kw}\b', py_kw, line)
    return line

def _convert_input_calls(code: str, existing_mapping: dict, debug_mode: bool = False) -> tuple[str, dict]:
    """
    Convert input("prompt") calls to print("prompt") + input("")
    Preserves indentation and handles complex cases
    Returns updated code and line mapping
    """
    import re
    
    lines = code.split('\n')
    result_lines = []
    new_mapping = {}
    current_output_line = 1
    
    for line_num, line in enumerate(lines, 1):
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
            
            # Add print line (maps to same original line as the input line)
            result_lines.append(print_line)
            original_line = existing_mapping.get(line_num, line_num)
            new_mapping[current_output_line] = original_line
            current_output_line += 1
            
            # Add modified input line
            result_lines.append(new_line)
            new_mapping[current_output_line] = original_line
            current_output_line += 1
        else:
            result_lines.append(line)
            # Preserve existing mapping
            original_line = existing_mapping.get(line_num, line_num)
            new_mapping[current_output_line] = original_line
            current_output_line += 1

    if debug_mode:
        result_lines = [line.replace('debug_pause()', 'input("")') for line in result_lines]
    
    return '\n'.join(result_lines), new_mapping

def _add_debug_instrumentation(code: str, existing_mapping: dict) -> tuple[str, dict]:
    """
    Add debug instrumentation to code for step-by-step execution
    Returns updated code and line mapping
    """
    lines = code.split('\n')
    instrumented = []
    new_mapping = {}
    current_output_line = 1
    
    for line_num, line in enumerate(lines, 1):
        original_line = line
        stripped_line = line.strip()
        
        # Skip empty lines and comments
        if not stripped_line or stripped_line.startswith('#'):
            instrumented.append(original_line)
            # Preserve mapping for empty/comment lines
            original_source_line = existing_mapping.get(line_num, line_num)
            new_mapping[current_output_line] = original_source_line
            current_output_line += 1
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
            original_source_line = existing_mapping.get(line_num, line_num)
            new_mapping[current_output_line] = original_source_line
            current_output_line += 1
            continue
        else:
            # Check if this line exits the current scope
            is_exit_statement = any(stripped_line.startswith(keyword) for keyword in [
                'return', 'break', 'continue', 'raise'
            ])
            
            indentation = len(line) - len(line.lstrip())
            indent_str = ' ' * indentation
            
            # Get original source line number
            original_source_line = existing_mapping.get(line_num, line_num)
            
            # Add debug line info
            instrumented.append(f'{indent_str}print("D-D-D:LINE:{original_source_line}")')
            new_mapping[current_output_line] = original_source_line
            current_output_line += 1
            
            # Add original line
            instrumented.append(original_line)
            new_mapping[current_output_line] = original_source_line
            current_output_line += 1
            
            # Only add debug pause if this line doesn't exit the scope
            if not is_exit_statement:
                instrumented.append(f'{indent_str}print("D-D-D:VARS:" + str({{k: v for k, v in locals().items() if not k.startswith("__") and type(v) in [int, float, str, bool, list, dict, type(None)]}}))')
                new_mapping[current_output_line] = original_source_line
                current_output_line += 1
                
                instrumented.append(f'{indent_str}print("D-D-D:STEP")')
                new_mapping[current_output_line] = original_source_line
                current_output_line += 1
                
                instrumented.append(f'{indent_str}debug_pause()')
                new_mapping[current_output_line] = original_source_line
                current_output_line += 1
    
    return '\n'.join(instrumented), new_mapping