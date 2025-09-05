import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from app.services.transpiler import validate_isipython_only, _substitute_keywords, _add_debug_instrumentation,_convert_input_calls, transpile_code

# Validate isipython only tests
@pytest.mark.parametrize("python_keyword,isixhosa_equivalent", [
    ("import", "ngenisa"),
    ("if", "ukuba"),
    ("while", "ngelixa"),
    ("def", "chaza"),
    ("and", "kwaye"),
    ("or", "okanye"),
    ("not", "hayi"),
    ("True", "Inyaniso"),
    ("False", "Ubuxoki"),
    ("None", "Akukho"),
    ("class", "iklasi"),
    ("return", "buyisela"),
    ("break", "yekisa"),
    ("continue", "qhubeka"),
    ("try", "zama"),
    ("except", "ngaphandle"),
    ("finally", "ekugqibeleni"),
    ("for", "ngokulandelelana"),
    ("in", "ngaphakathi"),
    ("is", "ngu"),
    ("elif", "okanye_ukuba"),
    ("else", "enye"),
    ("pass", "dlula"),
    ("raise", "phakamisa"),
    ("with", "nge"),
    ("yield", "velisa"),
    ("global", "jikelele"),
    ("lambda", "umsebenzi"),
    ("nonlocal", "ingaphandle"),
    ("assert", "qinisekisa"),
    ("del", "cima"),
    ("from", "ukusuka"),
    ("as", "njenge"),
    ("async", "ngemva"),
    ("await", "linda")
])

def test_validate_isipython_only_all_keywords(python_keyword, isixhosa_equivalent):
    with pytest.raises(ValueError, match=f"Line 1: Please use isiXhosa keyword '{isixhosa_equivalent}' instead of Python keyword '{python_keyword}'"):
        validate_isipython_only(python_keyword)

# Test that comments are properly ignored during validation
def test_validate_isipython_only_ignores_comments():
    # These should NOT raise errors because keywords are in comments
    validate_isipython_only("x = 5  # this uses if keyword")
    validate_isipython_only("# def is a Python keyword")
    validate_isipython_only("ukuba x > 5:  # while this is valid")
    
def test_validate_isipython_only_mixed_code_and_comments():
    # Should catch Python keyword in code part, ignore in comment
    with pytest.raises(ValueError, match="Line 2: Please use isiXhosa keyword 'ukuba' instead of Python keyword 'if'"):
        validate_isipython_only("#def\n if x > 5:  # def is also a keyword")

@pytest.mark.parametrize("python_keyword,isixhosa_equivalent", [
    ("import", "ngenisa"),
    ("if", "ukuba"),
    ("while", "ngelixa"),
    ("def", "chaza"),
    ("and", "kwaye"),
    ("or", "okanye"),
    ("not", "hayi"),
    ("True", "Inyaniso"),
    ("False", "Ubuxoki"),
    ("None", "Akukho"),
    ("class", "iklasi"),
    ("return", "buyisela"),
    ("break", "yekisa"),
    ("continue", "qhubeka"),
    ("try", "zama"),
    ("except", "ngaphandle"),
    ("finally", "ekugqibeleni"),
    ("for", "ngokulandelelana"),
    ("in", "ngaphakathi"),
    ("is", "ngu"),
    ("elif", "okanye_ukuba"),
    ("else", "enye"),
    ("pass", "dlula"),
    ("raise", "phakamisa"),
    ("with", "nge"),
    ("yield", "velisa"),
    ("global", "jikelele"),
    ("lambda", "umsebenzi"),
    ("nonlocal", "ingaphandle"),
    ("assert", "qinisekisa"),
    ("del", "cima"),
    ("from", "ukusuka"),
    ("as", "njenge"),
    ("async", "ngemva"),
    ("await", "linda")
])
# keyword substitution tests
def test_substitute_keywords_all_keywords(python_keyword, isixhosa_equivalent):
    assert _substitute_keywords(isixhosa_equivalent)==python_keyword
# Word boundary tests
def test_substitute_keywords_word_boundaries():
    # Should NOT replace partial matches
    result = _substitute_keywords("ukuba_variable = 5")  # ukuba inside variable name
    assert "if_variable" not in result  # Should stay as ukuba_variable
    
    result = _substitute_keywords("my_ukuba_func()")  # ukuba in middle
    assert "my_if_func" not in result

def test_substitute_keywords_case_sensitivity():
    # Test if your keywords are case sensitive
    result = _substitute_keywords("UKUBA x > 5:")
    assert "IF x > 5:" not in result  # Should not replace uppercase
    assert "UKUBA x > 5:"==result
    result = _substitute_keywords("Ukuba x > 5:")
    assert "If x > 5:" not in result  # Should not replace capitalized
    assert result == "Ukuba x > 5:"

# Multiple keywords in one line
def test_substitute_keywords_multiple_in_line():
    result = _substitute_keywords("ukuba x > 5 kwaye y < 10:")
    assert "if x > 5 and y < 10:" == result

# String literal preservation
def test_substitute_keywords_in_strings():
    # Keywords inside strings should NOT be replaced
    result = _substitute_keywords('print("ukuba this kwaye that")')
    assert 'print("ukuba this kwaye that")' == result  # Should stay unchanged
    
    result = _substitute_keywords("message = 'ukuba test'")
    assert "message = 'ukuba test'" == result

# Empty and whitespace
def test_substitute_keywords_empty_line():
    assert _substitute_keywords("") == ""
    assert _substitute_keywords("   ") == "   "
    assert _substitute_keywords("\t\n") == "\t\n"

# Special characters and punctuation
def test_substitute_keywords_with_punctuation():
    result = _substitute_keywords("ukuba(x > 5):")
    assert "if(x > 5):" == result
    
    result = _substitute_keywords("ukuba:x>5")
    assert "if:x>5" == result

# Repeated keywords
def test_substitute_keywords_repeated():
    result = _substitute_keywords("ukuba ukuba_var kwaye ukuba:")
    assert "if ukuba_var and if:" == result  # Only standalone ukuba replaced
    
# Complex nested scenarios
def test_substitute_keywords_complex_line():
    complex_line = "ukuba x > 5 kwaye ngu True: buyisela Inyaniso"
    result = _substitute_keywords(complex_line)
    expected = "if x > 5 and is True: return True"
    assert expected == result

# Large input handling
def test_substitute_keywords_long_line():
    long_line = "ukuba " * 1000 + "x > 5:"
    result = _substitute_keywords(long_line)
    assert result.startswith("if " * 1000)

# debug instrumentation tests
def test_add_debug_instrumentation_basic():
    """Test basic debug instrumentation on simple code."""
    code = "x = 5\nprint(x)"
    line_mapping = {1: 1, 2: 2}
    
    result, new_mapping = _add_debug_instrumentation(code, line_mapping)
    
    # Should contain debug markers
    assert "D-D-D:LINE:1" in result
    assert "D-D-D:LINE:2" in result
    assert "D-D-D:VARS:" in result
    assert "D-D-D:STEP" in result
    assert "debug_pause()" in result
    
    # Original code should still be there
    assert "x = 5" in result
    assert "print(x)" in result

def test_add_debug_instrumentation_skips_control_structures():
    """Test that control structures are not instrumented."""
    code = "x=6\nif x > 5:\n    print('big')\nelse:\n    print('small')"
    line_mapping = {1: 1, 2: 2, 3: 3, 4: 4,5:5}
    
    result, new_mapping = _add_debug_instrumentation(code, line_mapping)
    
    # Control structures should not have debug instrumentation
    if_index = result.index("if x > 5:")
    else_index = result.index("else:")
    assert if_index>=0
    assert else_index>=0
    assert "D-D-D:LINE 2:" not in result # No debug for the if line itself
    assert result[if_index+len("if x > 5:"):].find("D-D-D:LINE 3:") # Next debug should be for line 3
    assert "D-D-D:LINE 4:" not in result # No debug for the else line itself
    assert result[else_index+len("else:"):].find("D-D-D:LINE 5:") # Next debug should be for line 5

def test_add_debug_instrumentation_preserves_indentation():
    """Test that debug lines match the indentation of instrumented code."""
    code = "if True:\n    x = 5\n    print(x)"
    line_mapping = {1: 1, 2: 2, 3: 3}
    
    result, new_mapping = _add_debug_instrumentation(code, line_mapping)
    
    lines = result.split('\n')
    
    # Find debug lines for indented code
    debug_lines = [line for line in lines if "D-D-D:" in line and line.startswith("    ")]
    
    # Should have debug lines with proper indentation (4 spaces)
    assert len(debug_lines) > 0
    assert all(line.startswith("    ") for line in debug_lines)

def test_add_debug_instrumentation_skips_empty_lines():
    """Test that empty lines and comments are skipped."""
    code = "x = 5\n\n# This is a comment\ny = 10"
    line_mapping = {1: 1, 2: 2, 3: 3, 4: 4}
    
    result, new_mapping = _add_debug_instrumentation(code, line_mapping)
    
    # Should still contain empty line and comment
    assert "\n\n" in result and "# This is a comment" in result
    
    # Should have debug instrumentation for x = 5 and y = 10 only
    debug_line_markers = result.count("D-D-D:LINE:")
    assert "D-D-D:LINE:2" not in result
    assert "D-D-D:LINE:3" not in result
    assert debug_line_markers == 2  # Only for x = 5 and y = 10

def test_add_debug_instrumentation_exit_statements():
    """Test that exit statements (return, break, continue, raise) don't get pause."""
    code = "def test():\n    x = 5\n    return x"
    line_mapping = {1: 1, 2: 2, 3: 3}
    
    result, new_mapping = _add_debug_instrumentation(code, line_mapping)
    
    lines = result.split('\n')
    
    # Find the return line and lines after it
    return_line_idx = None
    for i, line in enumerate(lines):
        if "return x" in line:
            return_line_idx = i
            break
    
    assert return_line_idx is not None
    assert "D-D-D:LINE:1" not in lines # No debug for the def line
    # Should not have debug_pause() after return statement
    remaining_lines = lines[return_line_idx + 1:]
    has_debug_pause_after_return = any("debug_pause()" in line for line in remaining_lines)
    assert not has_debug_pause_after_return

def test_add_debug_instrumentation_line_mapping_accuracy():
    """Test that line mapping is correctly updated."""
    code = "x = 5\ny = 10"
    line_mapping = {1: 1, 2: 2}
    
    result, new_mapping = _add_debug_instrumentation(code, line_mapping)
    
    # New mapping should map all new lines back to original lines
    assert isinstance(new_mapping, dict)
    assert len(new_mapping) > len(line_mapping)  # More lines after instrumentation
    
    # All values in new_mapping should be valid original line numbers
    original_lines = set(line_mapping.values())
    mapped_lines = set(new_mapping.values())
    assert mapped_lines.issubset(original_lines)
    #check mappings
    assert new_mapping[1]==1 #DEBUG LINE 
    assert new_mapping[2]==1 #original line
    assert new_mapping[3]==1 #DEBUG VARS
    assert new_mapping[4]==1 #DEBUG STEP
    assert new_mapping[5]==1 #debug pause
    assert new_mapping[6]==2 #DEBUG LINE 
    assert new_mapping[7]==2 #original line
    assert new_mapping[8]==2 #DEBUG VARS
    assert new_mapping[9]==2 #DEBUG STEP
    assert new_mapping[10]==2 #debug pause

def test_add_debug_instrumentation_empty_code():
    """Test debug instrumentation on empty code."""
    code = ""
    line_mapping = {1:1}
    
    result, new_mapping = _add_debug_instrumentation(code, line_mapping)
    
    assert result == ""
    assert new_mapping == {1:1}

def test_add_debug_instrumentation_variables_tracking():
    """Test that variables are tracked in debug output."""
    code = "x = 5\ny = x + 1"
    line_mapping = {1: 1, 2: 2}
    
    result, new_mapping = _add_debug_instrumentation(code, line_mapping)
    
    # Should have variables tracking
    assert "D-D-D:VARS:" in result
    
    # Should track locals() with filtering
    assert "locals().items()" in result
    assert "not k.startswith(\"__\")" in result

# input call substitution tests
# normal execution
def test_convert_input_calls_normal_mode():
    """Test input conversion in normal mode."""
    code = 'name = input("Enter your name: ")'
    line_mapping = {1: 1}
    
    result, new_mapping = _convert_input_calls(code, line_mapping)
    
    # Should convert to print + input
    assert 'print(">>>Enter your name: ")' in result
    assert 'name = input("")' in result
    
    # Should have two lines now
    lines = result.split('\n')
    assert len(lines) == 2
    assert new_mapping[2] ==1

def test_convert_input_calls_single_quotes():
    """Test input conversion with single quotes."""
    code = "age = input('Enter your age: ')"
    line_mapping = {1: 1}
    
    result, new_mapping = _convert_input_calls(code, line_mapping)
    
    # Should convert to print + input with single quotes
    assert "print('>>>Enter your age: ')" in result
    assert 'age = input("")' in result
    assert new_mapping[2] ==1

def test_convert_input_calls_preserves_indentation():
    """Test that input conversion preserves indentation."""
    code = "if True:\n    name = input('Enter name: ')"
    line_mapping = {1: 1, 2: 2}
    
    result, new_mapping = _convert_input_calls(code, line_mapping)
    
    lines = result.split('\n')
    # Should have indented print and input
    assert any(line.startswith("    print('>>>Enter name: ')") for line in lines)
    assert any(line.startswith('    name = input("")') for line in lines)

def test_convert_input_calls_no_input():
    """Test code with no input calls remains unchanged."""
    code = "x = 5\nprint('hello')"
    line_mapping = {1: 1, 2: 2}
    
    result, new_mapping = _convert_input_calls(code, line_mapping)
    
    # Should remain exactly the same
    assert result == code
    assert new_mapping == line_mapping

def test_convert_input_calls_multiple_inputs():
    """Test multiple input calls in same code."""
    code = 'name = input("Name: ")\nage = input("Age: ")'
    line_mapping = {1: 1, 2: 2}
    
    result, new_mapping = _convert_input_calls(code, line_mapping)
    
    # Should convert both
    assert 'print(">>>Name: ")' in result
    assert 'print(">>>Age: ")' in result
    assert 'name = input("")' in result
    assert 'age = input("")' in result

# debug mode
def test_convert_input_calls_debug_mode():
    """Test input conversion in debug mode."""
    code = 'name = input("Enter name: ")\nx=5\ndebug_pause()'
    line_mapping = {1: 1}
    
    result, new_mapping = _convert_input_calls(code, line_mapping, debug_mode=True)
    
    # In debug mode, debug_pause() should be replaced with input("")
    assert 'print(">>>Enter name: ")' in result
    assert 'name = input("")' in result
    assert 'debug_pause()' not in result
    input_count = result.count('input("")')
    assert input_count == 2
   
# challenge mode
def test_convert_input_calls_challenge_mode():
    """Test input conversion in challenge mode."""
    code = 'name = input("Enter name: ")'
    line_mapping = {1: 1}
    
    result, new_mapping = _convert_input_calls(code, line_mapping, challenge_mode=True)
    
    # In challenge mode, should not add >>> prefix
    assert 'print("Enter name: ")' in result  # No >>> prefix
    assert 'name = input("")' in result

def test_convert_input_calls_line_mapping_accuracy():
    """Test that line mapping is correctly updated."""
    code = 'name = input("Enter name: ")\nprint(name)'
    line_mapping = {1: 1, 2: 2}
    
    result, new_mapping = _convert_input_calls(code, line_mapping)
    
    # Should have more lines after conversion
    original_lines = len(code.split('\n'))
    result_lines = len(result.split('\n'))
    assert result_lines > original_lines
    
    # All mapped values should reference original lines
    original_line_nums = set(line_mapping.values())
    mapped_line_nums = set(new_mapping.values())
    assert mapped_line_nums.issubset(original_line_nums)
    assert new_mapping[1]==1 #padded print
    assert new_mapping[2]==1 #input
    assert new_mapping[3]==2 #different line

def test_convert_input_calls_empty_prompt():
    """Test input with empty prompt."""
    code = 'name = input("")'
    line_mapping = {1: 1}
    
    result, new_mapping = _convert_input_calls(code, line_mapping)
    
    # Should still convert
    assert 'print(">>>")' in result
    assert 'name = input("")' in result

#transpile code
def test_transpile_code_basic_functionality():
    """Test basic transpile_code functionality."""
    code = "ukuba x > 5:\n    print('big')"
    
    result, line_mapping = transpile_code(code)
    
    # Should convert keywords
    assert "if x > 5:" in result
    assert "print('big')" in result
    
    # Should have line mapping
    assert isinstance(line_mapping, dict)
    assert len(line_mapping) >= 2

def test_transpile_code_with_input_calls():
    """Test transpile_code with input conversion."""
    code = 'name = input("Enter name: ")\nprint(name)'
    
    result, line_mapping = transpile_code(code)
    
    # Should convert input calls
    assert 'print(">>>Enter name: ")' in result
    assert 'name = input("")' in result
    assert 'print(name)' in result

def test_transpile_code_debug_mode():
    """Test transpile_code with debug mode enabled."""
    code = "x = 5\nprint(x)"
    
    result, line_mapping = transpile_code(code, debug_mode=True)
    
    # Should have debug instrumentation
    assert "D-D-D:LINE:" in result
    assert "D-D-D:VARS:" in result
    assert "D-D-D:STEP" in result
    assert "debug_pause()" not in result  # Should be replaced with input("")
    assert 'input("")' in result

def test_transpile_code_challenge_mode():
    """Test transpile_code with challenge mode enabled."""
    code = 'name = input("Enter name: ")'
    
    result, line_mapping = transpile_code(code, challenge_mode=True)
    
    # Should convert input without >>> prefix
    assert 'print("Enter name: ")' in result
    assert '>>>' not in result

def test_transpile_code_validation_error():
    """Test that validation errors are properly raised."""
    code = "import os"  # Python keyword
    
    with pytest.raises(ValueError, match="Line 1: Please use isiXhosa keyword 'ngenisa' instead of Python keyword 'import'"):
        transpile_code(code)

def test_transpile_code_complex_integration():
    """Test complex code with multiple features."""
    code = '''ukuba x > 5:
    name = input("Enter name: ")
    print(name)
enye:
    print("small")'''
    
    result, line_mapping = transpile_code(code)
    
    # Should convert keywords
    assert "if x > 5:" in result
    assert "else:" in result
    
    # Should convert input
    assert 'print(">>>Enter name: ")' in result
    assert 'name = input("")' in result
    
    # Should preserve other statements
    assert 'print(name)' in result
    assert 'print("small")' in result

def test_transpile_code_comments_preserved():
    """Test that comments are preserved during transpilation."""
    code = "ukuba x > 5:  # Check if big\n    print('big')  # Print result"
    
    result, line_mapping = transpile_code(code)
    
    # Should convert keywords but preserve comments
    assert "if x > 5:  # Check if big" in result
    assert "print('big')  # Print result" in result
    
def test_transpile_code_string_literals_preserved():
    """Test that keywords in strings are not converted."""
    code = 'print("ukuba this kwaye that")'
    
    result, line_mapping = transpile_code(code)
    
    # Keywords in strings should remain unchanged
    assert 'print("ukuba this kwaye that")' in result

def test_transpile_code_empty_input():
    """Test transpile_code with empty input."""
    result, line_mapping = transpile_code("")
    
    assert result == ""
    assert line_mapping == {1:1}

def test_transpile_code_line_mapping_accuracy():
    """Test that line mapping accurately tracks original lines."""
    code = "ukuba x > 5:\n    print('big')\n    y = 10"
    
    result, line_mapping = transpile_code(code)
    
    # All mapped lines should reference valid original line numbers
    original_line_count = len(code.split('\n'))
    mapped_original_lines = set(line_mapping.values())
    
    assert all(1 <= line_num <= original_line_count for line_num in mapped_original_lines)

def test_transpile_code_debug_mode_line_mapping():
    """Test line mapping accuracy in debug mode."""
    code = "x = 5\nprint(x)"
    
    result, line_mapping = transpile_code(code, debug_mode=True)
    
    # Should have more output lines than input lines due to debug instrumentation
    input_lines = len(code.split('\n'))
    output_lines = len(result.split('\n'))
    
    assert output_lines > input_lines
    assert len(line_mapping) == output_lines
    
    # All mapped lines should still reference original lines (1 or 2)
    mapped_lines = set(line_mapping.values())
    assert mapped_lines.issubset({1, 2})

def test_transpile_code_all_modes_integration():
    """Test transpile_code with all processing modes combined."""
    code = 'ukuba x > 5:\n    name = input("Enter: ")\nenye:\n    print("small")'

    # Test different mode combinations
    normal_result, _ = transpile_code(code)
    debug_result, _ = transpile_code(code, debug_mode=True)
    challenge_result, _ = transpile_code(code, challenge_mode=True)
    both_result, _ = transpile_code(code, debug_mode=True, challenge_mode=True)
    
    # All should convert keywords
    for result in [normal_result, debug_result, challenge_result, both_result]:
        assert "if x > 5:" in result
        assert "else:" in result
    
    # Normal and debug should have >>>
    assert ">>>Enter:" in normal_result
    assert ">>>Enter:" in debug_result
    
    # Challenge modes should not have >>>
    assert ">>>Enter:" not in challenge_result
    assert ">>>Enter:" not in both_result
    
    # Debug modes should have debug instrumentation
    assert "D-D-D:" in debug_result
    assert "D-D-D:" in both_result
    assert "D-D-D:" not in normal_result
    assert "D-D-D:" not in challenge_result