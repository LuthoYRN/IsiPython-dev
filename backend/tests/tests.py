import requests
import json

BASE_URL = "http://localhost:5000/api/code"

TEST_CASES = {
    # IMPORT/FROM ERRORS
    1: {
        "name": "Incomplete Import Statement",
        "category": "Import Errors",
        "code": """ukusuka math ngenisa 
x = 5
print(x)"""
    },
    2: {
        "name": "Missing Import Module",
        "category": "Import Errors", 
        "code": """ngenisa 
x = 5
print(x)"""
    },
    3: {
        "name": "Valid Import",
        "category": "Import Errors",
        "code": """ukusuka math ngenisa sqrt
x = sqrt(16)
print(x)"""
    },
    
    # SYNTAX ERRORS
    4: {
        "name": "Missing Colon in If Statement",
        "category": "Syntax Errors",
        "code": """x = 5
ukuba x > 3
    print("Greater than 3")"""
    },
    5: {
        "name": "Unclosed String",
        "category": "Syntax Errors",
        "code": """x = "Hello World
print(x)"""
    },
    6: {
        "name": "Missing Parentheses in Function Call",
        "category": "Syntax Errors",
        "code": """x = 5
print x"""
    },
    7: {
        "name": "Missing Parentheses in Function Definition",
        "category": "Syntax Errors",
        "code": """chaza my_function:
    print("Hello")"""
    },
    
    # INDENTATION ERRORS
    8: {
        "name": "Missing Indentation After If",
        "category": "Indentation Errors",
        "code": """x = 5
ukuba x > 3:
print("Greater")"""
    },
    9: {
        "name": "Inconsistent Indentation",
        "category": "Indentation Errors",
        "code": """x = 5
ukuba x > 3:
    print("Line 1")
  print("Line 2")"""
    },
    
    # NAME ERRORS
    10: {
        "name": "Undefined Variable",
        "category": "Name Errors",
        "code": """x = 5
y = z + 10
print(y)"""
    },
    11: {
        "name": "Typo in Variable Name",
        "category": "Name Errors",
        "code": """my_variable = 10
print(my_varible)"""
    },
    
    # CONTROL STRUCTURE ERRORS
    12: {
        "name": "Else Without If",
        "category": "Control Structure Errors",
        "code": """x = 5
enye:
    print("This won't work")"""
    },
    13: {
        "name": "Missing Condition in While",
        "category": "Control Structure Errors",
        "code": """ngelixa:
    print("Infinite?")"""
    },
    14: {
        "name": "Valid If-Else Structure",
        "category": "Control Structure Errors",
        "code": """x = 5
ukuba x > 3:
    print("Greater than 3")
enye:
    print("Not greater than 3")"""
    },
    
    # FUNCTION DEFINITION ERRORS
    15: {
        "name": "Function Definition Without Colon",
        "category": "Function Errors",
        "code": """chaza my_function()
    print("Hello")"""
    },
    16: {
        "name": "Invalid Function Name",
        "category": "Function Errors",
        "code": """chaza 123function():
    print("Invalid name")"""
    },
    17: {
        "name": "Valid Function Definition",
        "category": "Function Errors",
        "code": """chaza greet():
    print("Hello from function!")

greet()"""
    },
    
    # TYPE ERRORS
    18: {
        "name": "String + Integer Error",
        "category": "Type Errors",
        "code": """name = "Age: "
age = 25
result = name + age
print(result)"""
    },
    19: {
        "name": "Division by Zero",
        "category": "Type Errors",
        "code": """x = 10
y = 0
result = x / y
print(result)"""
    },
    
    # LOOP ERRORS
    20: {
        "name": "Invalid For Loop Syntax",
        "category": "Loop Errors",
        "code": """ngokulandelelana i ngaphakathi range(5)
    print(i)"""
    },
    21: {
        "name": "Valid For Loop",
        "category": "Loop Errors",
        "code": """ngokulandelelana i ngaphakathi range(5):
    print(i)"""
    },
    22: {
        "name": "Valid While Loop",
        "category": "Loop Errors",
        "code": """count = 0
ngelixa count < 3:
    print(count)
    count = count + 1"""
    },
    
    # BOOLEAN AND LOGICAL ERRORS
    23: {
        "name": "Valid Boolean Operations",
        "category": "Boolean Errors",
        "code": """x = inyaniso
y = ubuxoki
result = x kwaye y
print(result)"""
    },
    24: {
        "name": "Invalid Boolean Comparison",
        "category": "Boolean Errors",
        "code": """x = 5
ukuba x ngu inyaniso:
    print("This is wrong")"""
    },
    
    # WORKING PROGRAMS
    25: {
        "name": "Complete Working Program",
        "category": "Working Programs",
        "code": """# IsiPython program that works
ukusuka math ngenisa sqrt

chaza calculate_hypotenuse(a, b):
    result = sqrt(a*a + b*b)
    buyisela result

x = 3
y = 4
hypotenuse = calculate_hypotenuse(x, y)

ukuba hypotenuse > 5:
    print("Hypotenuse is greater than 5")
enye:
    print("Hypotenuse is 5 or less")

print("The answer is:", hypotenuse)"""
    },
    26: {
        "name": "Simple Calculator",
        "category": "Working Programs",
        "code": """# Simple calculator
chaza add(a, b):
    buyisela a + b

chaza multiply(a, b):
    buyisela a * b

num1 = 10
num2 = 5

sum_result = add(num1, num2)
product_result = multiply(num1, num2)

print("Sum:", sum_result)
print("Product:", product_result)"""
    },
    27: {
        "name": "Taking input test",
        "category": "Input",
        "code": """ngenisa time
num1 = eval(input("Enter a number: "))#zyi
#input
num2 = eval(input("Enter another number "))
ukuba num1 > num2:
    print(num1, "is greater than", num2)
okanye_ukuba num1 < num2:
    print(num1, "is less than", num2)
enye:
    y = int(input("Enter a number to compare with both: "))#zyi
    ukuba y > num1 kwaye y > num2:
        print(y, "is greater than both", num1, "and", num2)
    okanye_ukuba y < num1 kwaye y < num2:
        print(y, "is less than both", num1, "and", num2)
    enye:
        print(y, "is equal to both numbers")
"""
    }, 
28: {
        "name": "Partial working code",
        "category": "Partial Working Code",
        "code": """
ngokulandelelana i ngaphakathi range(5):
    print(i)
i = None
print(i+1)
"""},
29: {
    "name": "While True without break",
    "category": "Infinite Loop",
    "code": """
ngelixa Inyaniso:
    print("This")
"""
},
30: {
    "name": "Counter never increments",
    "category": "Infinite Loop", 
    "code": """
i = 0
ngelixa i < 10:
    print("Count is:", i)
"""
},
31: {
    "name": "Wrong increment direction",
    "category": "Infinite Loop",
    "code": """
x = 10
ngelixa x > 0:
    print("Counting down:", x)
    x = x + 1"""
},
32: {
    "name": "Nested infinite loops",
    "category": "Infinite Loop",
    "code": """
i = 0
ngelixa i < 5:
    j = 0
    ngelixa j < 3:
        print(i, j)
    i = i + 1"""
},
33: {
    "name": "Condition never changes",
    "category": "Infinite Loop",
    "code": """
ready = Ubuxoki
ngelixa hayi ready:
    print("Waiting...")
"""
},
34: {
    "name": "Infinite recursion",
    "category": "Infinite Loop", 
    "code": """
chaza countdown(n):
    print(n)
    countdown(n - 1)

countdown(5)"""
}
,
35: {
    "name": "For loop with crazy range",
    "category": "Infinite Loop",
    "code": """
ngokulandelelana i ngaphakathi range(1, 100000000):
    print("Processing:", i)
"""
},
36: {
    "name": "Infinite loop with break in wrong place",
    "category": "Infinite Loop",
    "code": """
count = 0
ngelixa Inyaniso:
    print("Running...")
    ukuba count == 10:
        yekisa
"""
},
37: {
    "name": "String processing infinite loop",
    "category": "Infinite Loop", 
    "code": """
text = "hello world"
ngelixa len(text) > 0:
    print("Processing:", text)
    text = text + "!"
"""
},
38: {
    "name": "Mathematical infinite loop",
    "category": "Infinite Loop",
    "code": """
num = 4
ngelixa num % 2 == 0:  # num is even
    print("Number is even:", num)
    num = num * 2
"""
},
39: {
    "name": "Infinite loop with multiple conditions",
    "category": "Infinite Loop",
    "code": """
a = 5
b = 3
ngelixa a > 0 okanye b > 0:
    print("Both positive")
    a = a - 1
"""
},
40: {
    "name": "Complex slow computation",
    "category": "Slow Code",
    "code": """
total = 0
ngokulandelelana i ngaphakathi range(1000000):
    ngokulandelelana j ngaphakathi range(1000):
        total = total + (i * j)
print("Total:", total)"""
},
41: {
    "name": "Slow algorithm - bubble sort",
    "category": "Slow Code",
    "code": """
numbers = list(range(10000, 0, -1))  # Large reverse list
ngokulandelelana i ngaphakathi range(len(numbers)):
    ngokulandelelana j ngaphakathi range(len(numbers) - 1):
        ukuba numbers[j] > numbers[j + 1]:
            temp = numbers[j]
            numbers[j] = numbers[j + 1] 
            numbers[j + 1] = temp
print("Sorted!")"""
}
,
42: {
        "name": "Edge case for input/infinite loop detection",
        "category": "Input/Infinite loop",
        "code": """
ngokulandelelana i ngaphakathi range(100000):
    print(i) 
"""},
43: {
        "name": "Edge case for input/infinite loop detection",
        "category": "Input/Infinite loop",
        "code": """
ngokulandelelana i ngaphakathi range(100000):
    dlula 
"""},
}

def list_tests():
    """Display all available tests"""
    print("\n" + "="*70)
    print("AVAILABLE ISIPYTHON TESTS")
    print("="*70)
    
    current_category = ""
    for test_id, test_data in TEST_CASES.items():
        if test_data["category"] != current_category:
            current_category = test_data["category"]
            print(f"\n{current_category}:")
            print("-" * 40)
        
        print(f"  {test_id:2d}. {test_data['name']}")
    
    print(f"\n{'='*70}")
    print(f"Total: {len(TEST_CASES)} test cases")

def run_test(test_id):
    """Run a test that simulates real program execution flow"""
    if test_id not in TEST_CASES:
        print(f"Test {test_id} not found!")
        return
    
    test_data = TEST_CASES[test_id]
    
    print(f"\n{'='*70}")
    print(f"TEST {test_id}: {test_data['name']}")
    print(f"Category: {test_data['category']}")
    print(f"{'='*70}")
    print(f"Code:")
    print(f"{'-'*30}")
    print(test_data['code'])
    print(f"{'-'*30}")
    print(f"\nProgram Output:")
    print(f"{'-'*30}")
    
    # Track all output and errors separately
    all_output = []
    all_errors = []
    
    try:
        response = requests.post(BASE_URL, json={"code": test_data['code']})
        result = response.json()
        
        session_id = result.get('session_id')
        
        # Main execution loop
        while not result.get('completed'):
            
            # Show any new output immediately (like a real program)
            if result.get('output'):
                # Only show new output (not repeated)
                current_output = result['output']
                if current_output not in all_output:
                    # Print just the new lines
                    if all_output:
                        # Find what's new since last time
                        last_output = all_output[-1] if all_output else ""
                        if current_output.startswith(last_output):
                            new_part = current_output[len(last_output):].lstrip('\n')
                            if new_part:
                                print(new_part)
                    else:
                        print(current_output)
                    all_output.append(current_output)
            
            if result.get('waiting_for_input'):
                # Show prompt and get input (just like a real program)
                user_input = input()  # No extra text, just like real input()
                
                # Send the input
                response = requests.post(BASE_URL, json={
                    "session_id": session_id,
                    "input": user_input
                })
                result = response.json()
                
            elif result.get('still_running'):
                import time
                time.sleep(0.5)  # Shorter polling for more responsive feel
                
                # Poll for status
                response = requests.post(BASE_URL, json={
                    "session_id": session_id
                })
                result = response.json()
                
            else:
                # Something unexpected
                break
            
            # Collect any errors (but don't show them yet)
            if result.get('error'):
                all_errors.append(result['error'])
        
        # Show final output if there's any new content
        if result.get('output'):
            current_output = result['output']
            if not all_output or current_output != all_output[-1]:
                if all_output:
                    last_output = all_output[-1] if all_output else ""
                    if current_output.startswith(last_output):
                        new_part = current_output[len(last_output):].lstrip('\n')
                        if new_part:
                            print(new_part)
                else:
                    print(current_output)
        
        print(f"\n{'-'*30}")
        
        # Show errors at the bottom (like real programs)
        if result.get('error') or all_errors:
            print("Errors:")
            if result.get('error'):
                print(result['error'])
            for error in all_errors:
                if error != result.get('error'):  # Avoid duplicates
                    print(error)
            
    except KeyboardInterrupt:
        print("\n\nProgram interrupted")
    except Exception as e:
        print(f"\nError running test: {e}")

# Helper functions for easy testing
def test(test_id):
    """Shorthand for run_test"""
    run_test(test_id)

def tests():
    """Shorthand for list_tests"""
    list_tests()

# Usage examples and help
def help_usage():
    print("""
🔧 IsiPython Test Suite Usage:
    
    list_tests()                    # Show all available tests
    run_test(5)                     # Run test number 5
    test(5)                         # Shorthand for run_test(5)
    tests()                         # Shorthand for list_tests()
    
Examples:
    >>> tests()                     # See all tests
    >>> test(1)                     # Run incomplete import test
    >>> test(25)                    # Run complete working program
    """)

if __name__ == "__main__":
    help_usage()
    list_tests()