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
        "code": """ngexesha:
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
        "code": """ngokulandelelana i ku range(5)
    print(i)"""
    },
    21: {
        "name": "Valid For Loop",
        "category": "Loop Errors",
        "code": """ngokulandelelana i ku range(5):
    print(i)"""
    },
    22: {
        "name": "Valid While Loop",
        "category": "Loop Errors",
        "code": """count = 0
ngexesha count < 3:
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
    }
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
    """Run a specific test by its ID"""
    if test_id not in TEST_CASES:
        print(f"Test {test_id} not found!")
        print("Use list_tests() to see available tests.")
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
    
    try:
        response = requests.post(BASE_URL, json={"code": test_data['code']})
        result = response.json()
        
        if result.get('error'):
            print(f"ERROR:\n{result['error']}")
        if result.get('output'):
            print(f"OUTPUT:\n{result['output']}")
        if not result.get('error') and not result.get('output'):
            print("SUCCESS: No output, no errors")
            
    except Exception as e:
        print(f"REQUEST FAILED: {e}")
    
    print(f"{'='*70}")

def run_tests_by_category(category):
    """Run all tests in a specific category"""
    matching_tests = [test_id for test_id, test_data in TEST_CASES.items() 
                     if test_data['category'].lower() == category.lower()]
    
    if not matching_tests:
        print(f"No tests found for category: {category}")
        return
    
    print(f"\nRunning all tests in category: {category}")
    for test_id in matching_tests:
        run_test(test_id)
        input("\nPress Enter to continue to next test...")

def get_categories():
    """Get list of all test categories"""
    categories = list(set(test_data['category'] for test_data in TEST_CASES.values()))
    return sorted(categories)

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
    
    run_tests_by_category("Syntax Errors")  # Run all syntax error tests
    get_categories()                # List all test categories
    
Examples:
    >>> tests()                     # See all tests
    >>> test(1)                     # Run incomplete import test
    >>> test(25)                    # Run complete working program
    """)

if __name__ == "__main__":
    help_usage()
    list_tests()