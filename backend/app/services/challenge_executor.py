# app/services/challenge_executor.py
from app.services.transpiler import transpile_code
from app.services.errors import translate_error
from app.models.challenge_testcase import challenge_test_case_model
from app.models.challenge_submission import challenge_submission_model
from app.models.challenge_progress import user_challenge_progress_model
import subprocess
import os

def execute_challenge_submission(challenge_id: str, user_id: str, user_code: str) -> dict:
    """
    Execute user's IsiXhosa code against challenge test cases
    Runs the full program and provides input through stdin
    """
    
    try:
        # STEP 1: Create submission record
        submission_result = challenge_submission_model.create(challenge_id, user_id, user_code)
        if not submission_result["success"]:
            return {"success": False, "error": submission_result["error"]}
        
        submission_id = submission_result["data"]["id"]
        
        # STEP 2: Get test cases for this challenge
        test_cases_result = challenge_test_case_model.find_by_challenge(challenge_id)
        if not test_cases_result["success"]:
            return {"success": False, "error": "Failed to load test cases"}
        
        test_cases = test_cases_result["data"]
        if not test_cases:
            return {"success": False, "error": "No test cases found for this challenge"}
        
        # STEP 3: Try to transpile the code first
        try:
            python_code, line_mapping = transpile_code(user_code,challenge_mode=True) #challenge_mode
        except ValueError as e:
            challenge_submission_model.update_results(submission_id, {'status': "error"})
            user_challenge_progress_model.update_progress(user_id, challenge_id, {
                'submission_id': submission_id,
                'status': 'error',
            }
            )
            result = {
                "success": False,
                "english_error":str(e),
            }
            result['validation_error'] = translate_error(str(e))
            return (result)
        # STEP 4: Execute against each test case
        visible_results = []
        hidden_results = []
        total_score = 0
        tests_passed = 0
        tests_total = len(test_cases)
        
        for test_case in test_cases:
            result = _execute_single_test(python_code, line_mapping, test_case)
            
            if result["status"] == "passed":
                tests_passed += 1
                total_score += test_case["points_weight"]
            
            # Separate visible vs hidden results
            if test_case.get("is_hidden", False):
                hidden_results.append(result)
            else:
                test_result = {
                    "input_data": test_case["input_data"],
                    "expected_output": test_case["expected_output"],
                    "actual_output": result["actual_output"],
                    "status": result["status"],
                    "explanation": test_case.get("explanation")
                }
                
                # Include error information if there was one
                if result.get("error_message"):
                    test_result["error_message"] = result["error_message"]
                    test_result["english_error"] = result["english_error"]
                
                visible_results.append(test_result)
        
        # STEP 5: Determine overall status
        overall_status = "passed" if tests_passed == tests_total else "failed"
        
        # STEP 6: Update submission with results
        submission_update = {
            'status': overall_status,
            'score': total_score,
            'tests_passed': tests_passed,
            'tests_total': tests_total
        }
        
        challenge_submission_model.update_results(submission_id, submission_update)
        
        # STEP 7: Update user progress
        user_challenge_progress_model.update_progress(
            user_id, challenge_id, {
                'submission_id': submission_id,
                'status': overall_status,
                'score': total_score
            }
        )
        
        return {
            "success": True,
            "submission_id": submission_id,
            "status": overall_status,
            "score": total_score,
            "tests_passed": tests_passed,
            "tests_total": tests_total,
            "test_results": {
                "visible_tests": visible_results,
                "hidden_tests": {
                    "total": len(hidden_results),
                    "passed": len([r for r in hidden_results if r["status"] == "passed"]),
                    "failed": len([r for r in hidden_results if r["status"] == "failed"]),
                }
            }
        }
        
    except Exception as e:
        return {"success": False, "error": f"Execution failed: {str(e)}"}

def _execute_single_test(python_code: str, line_mapping: dict, test_case: dict) -> dict:
    """
    Execute code against a single test case by running the full program
    and providing input through stdin. Returns partial output even on errors.
    """
    try:
        test_input_data = test_case["input_data"]
        expected_output = test_case["expected_output"].strip()
        
        # Create input string for the program
        input_string = "\n".join(str(item) for item in test_input_data) + "\n"
        
        # Execute the program with input provided via stdin
        result = _run_with_input(python_code, input_string, line_mapping)
        
        if result.get("error"):
            error_msg = result.get("error", "Unknown error")
            english_error = result.get("english_error","Unkown error")
            partial_output = result.get("output", "")
            
            if error_msg.startswith("[Timeout]"):
                return {
                    "status": "failed",
                    "actual_output": partial_output,
                    "error_message": "Ikhowudi yakho ithathe ixesha elide kakhulu",
                    "english_error": "Code took too long to execute"
                }
            else:
                return {
                    "status": "failed", 
                    "actual_output": partial_output,
                    "error_message": error_msg,
                    "english_error":english_error
                }
        
        actual_output = (result.get("output") or "").strip()
        
        # Compare outputs
        if actual_output == expected_output:
            return {
                "status": "passed",
                "actual_output": actual_output
            }
        else:
            return {
                "status": "failed",
                "actual_output": actual_output
            }
            
    except Exception as e:
        return {
            "status": "failed",
            "actual_output": "",
            "error_message": f"Test execution error: {str(e)}"
        }

def _run_with_input(python_code: str, input_data: str, line_mapping: dict) -> dict:
    """
    Run Python code with input provided via stdin
    Returns both partial output and error information for better debugging
    """
    import uuid
    
    session_id = str(uuid.uuid4())
    temp_file = f"temp_{session_id}.py"
    
    try:
        # Write code to temporary file
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(python_code)
        
        # Run the code with input provided
        process = subprocess.Popen(
            ["python", temp_file],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Provide input and get output
        stdout, stderr = process.communicate(input=input_data,timeout=10)
        
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        if stderr:
            # Translate error using error translator
            error_msg = translate_error(stderr, line_mapping)
            return {
                "output": stdout.strip() if stdout else "",  # Return partial output
                "error": error_msg,
                "english_error":stderr,
                "completed": True
            }
        
        return {
            "output": stdout,
            "error": None,
            "completed": True
        }
        
    except subprocess.TimeoutExpired:     
        process.kill()
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        return {
            "output": "",
            "error": "[Timeout]",
            "completed": True
        }
        
    except Exception as e:
        # Clean up on any error
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        return {
            "output": "",
            "error": str(e),
            "completed": True,
        }