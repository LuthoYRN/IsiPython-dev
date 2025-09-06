import pytest
import sys
import subprocess
from pathlib import Path
from unittest.mock import patch, Mock

sys.path.append(str(Path(__file__).parent.parent.parent))
from app.services.challenge_executor import _run_with_input, _execute_single_test,execute_challenge_submission

class TestRunWithInput:
    """Test the _run_with_input function - core subprocess execution."""
    @patch('app.services.challenge_executor.subprocess.Popen')
    def test_successful_execution(self,mock_popen):
        """"Test successful code execution with output."""
        mock_process = Mock()
        mock_process.communicate.return_value = ("Hello World","")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        with patch("builtins.open",create=True),\
             patch("os.path.exists",return_value=True),\
             patch("os.remove"):

            result = _run_with_input("print'('Hello World')","test_input\n",{1:1})
        
        assert result["output"] == "Hello World"
        assert result["error"] is None
        assert result["completed"] == True
    
    @patch('app.services.challenge_executor.subprocess.Popen')
    def test_runtime_error(self,mock_popen):
        """"Test code that produces a runtime error."""
        mock_process = Mock()
        mock_process.communicate.return_value = ("", "NameError: name 'x' is not defined")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        with patch("builtins.open",create=True),\
             patch("os.path.exists",return_value = True),\
             patch("os.remove"),\
             patch("app.services.challenge_executor.translate_error") as mock_translate:
            
            mock_translate.return_value = "Igama elithi 'x' alichazwanga"

            result = _run_with_input("print(x)","input\n",{1:1})
        
        assert "error" in result
        assert result["error"] == "Igama elithi 'x' alichazwanga"
        assert result["english_error"] == "NameError: name 'x' is not defined"
        assert result["completed"] is True
    
    @patch('app.services.challenge_executor.subprocess.Popen')
    def test_timeout_handling(self, mock_popen):
        """Test timeout on long-running code."""
        mock_process = Mock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired("python", 10)
        mock_process.kill = Mock()
        mock_popen.return_value = mock_process

        with patch("builtins.open",create=True),\
             patch("os.path.exists",return_value = True),\
             patch("os.remove"):
            
            result = _run_with_input("while True: pass", "input\n", {1: 1})
        
        assert "error" in result
        assert result["output"]==""
        assert result["error"]=="[Timeout]"
        assert result["completed"] == True
        mock_process.kill.assert_called_once()
    
class TestExecuteSingleTest:
    """Test the _execute_single_test function - test case logic."""
    @patch('app.services.challenge_executor._run_with_input')
    def test_passing_test_case(self, mock_run):
        """Test a test case that passes."""
        mock_run.return_value = {"output": "Expected Output"}

        test_case = {"expected_output":"Expected Output",
                     "input_data": []
                    }
        
        result = _execute_single_test("print('Expected Output')",{1:1},test_case)

        assert result["status"] == "passed"
        assert result["actual_output"] == "Expected Output"
    
    @patch('app.services.challenge_executor._run_with_input')  
    def test_failing_test_case(self, mock_run):
        """Test a test case that fails due to output mismatch."""
        mock_run.return_value = {"output": "Wrong Output"}

        test_case = {"expected_output":"Expected Output",
                     "input_data": []
                     }
        result = _execute_single_test("print('Wrong Output')",{1:1},test_case)

        assert result["status"] == "failed"
        assert result["actual_output"] == "Wrong Output"

    @patch('app.services.challenge_executor._run_with_input')
    def test_runtime_error_handling(self, mock_run):
        """Test handling when code produces runtime error."""
        mock_run.return_value = {
            "output": "",
            "error": "Igama elithi 'x' alikachazwa",
            "english_error": "NameError: name 'x' is not defined",
            "completed":True
        }

        test_case = {"expected_output":"Expected Output",
                     "input_data": []
                     }
        result = _execute_single_test("print(x)",{1:1},test_case)

        assert result["status"] == "failed"
        assert result["english_error"] == "NameError: name 'x' is not defined"
        assert result["error_message"] == "Igama elithi 'x' alikachazwa"
        assert result["actual_output"] == ""
    
    @patch('app.services.challenge_executor._run_with_input')
    def test_timeout_error_handling(self, mock_run):
        """Test handling when code times out."""
        mock_run.return_value = {
            "output": "",
            "error": "[Timeout]",
            "completed":True
        }

        test_case = {"expected_output":"Expected Output",
                     "input_data": []
                     }
        result = _execute_single_test("while True: pass",{1:1},test_case)

        assert result["status"] == "failed"
        assert result["english_error"] == "Code took too long to execute"
        assert result["error_message"] == "Ikhowudi yakho ithathe ixesha elide kakhulu"
        assert result["actual_output"] == ""
    
    @patch('app.services.challenge_executor._run_with_input')
    def test_input_data_formatting(self, mock_run):
        """Test that input data is formatted correctly."""
        mock_run.return_value = {"output": "result"}
        
        test_case = {
            "input_data": ["first", "second", "third"],
            "expected_output": "result",
        }
        
        _execute_single_test("code", {}, test_case)
        
        # Verify input was formatted correctly
        expected_input = "first\nsecond\nthird\n"
        mock_run.assert_called_with("code", expected_input, {})

    @patch('app.services.challenge_executor._run_with_input')
    def test_output_stripping(self, mock_run):
        """Test that whitespace is right stripped from test case output and code output."""
        mock_run.return_value = {"output": "Expected Output   \n"}
        
        test_case_a = {
            "input_data": ["5"],
            "expected_output": "Expected Output"
        }
        test_case_b = {
            "input_data": ["5"],
            "expected_output": "Expected Output "#space at the end should be stripped
        }

        test_case_c = {
            "input_data": ["5"],
            "expected_output": "    Expected Output "#space should not be stripped
        }
        result_a = _execute_single_test("code", {}, test_case_a)
        result_b = _execute_single_test("code", {}, test_case_b)
        result_c = _execute_single_test("code", {}, test_case_c)
        
        assert result_a["status"] == "passed"  # Should pass after stripping
        assert result_a["actual_output"] == "Expected Output"

        assert result_b["status"] == "passed"
        assert result_b["actual_output"] == "Expected Output"

        assert result_c["status"] == "failed"
        assert result_c["actual_output"] == "Expected Output"
    
    @patch('app.services.challenge_executor._run_with_input')
    def test_multiline_output_with_stripping(self, mock_run):
        """Test handling of multiline output."""
        mock_run.return_value = {"output": "Line 1  \nLine 2    \nLine 3    "}
        
        test_case = {
            "input_data": ["3"],
            "expected_output": "Line 1 \nLine 2 \nLine 3 ",
        }
        
        result = _execute_single_test("for i in range(3): print(f'Line {i+1}')", {1:1}, test_case)
        
        assert result["status"] == "passed"
        assert result["actual_output"] == "Line 1\nLine 2\nLine 3"

    @patch('app.services.challenge_executor._run_with_input')
    def test_multiline_output_mismatch(self, mock_run):
        """Test multiline output that doesn't match expected."""
        mock_run.return_value = {"output": "Line 1\nWrong Line\nLine 3"}
        
        test_case = {
            "input_data": ["3"],
            "expected_output": "Line 1\nLine 2\nLine 3"
        }
        
        result = _execute_single_test("code", {}, test_case)
        
        assert result["status"] == "failed"
        assert result["actual_output"] == "Line 1\nWrong Line\nLine 3"

class TestExecuteChallengeSubmission:
    """Test the main execute_challenge_submission function."""
    
    @patch('app.services.challenge_executor.challenge_test_case_model')
    @patch('app.services.challenge_executor.challenge_submission_model') 
    @patch('app.services.challenge_executor.user_challenge_progress_model')
    @patch('app.services.challenge_executor.transpile_code')
    @patch('app.services.challenge_executor._execute_single_test')
    def test_successful_submission_all_pass(self, mock_execute_test, mock_transpile, 
                                          mock_progress, mock_submission, mock_test_case):
        """Test successful submission with all tests passing."""
        # Mock database calls
        mock_submission.create.return_value = {"success": True, "data": {"id": "sub123"}}
        mock_submission.update_results.return_value = {"success": True}
        mock_test_case.find_by_challenge.return_value = {
            "success": True, 
            "data": [
                {
                    "input_data": [], 
                    "expected_output": "Hello World!", 
                    "points_weight": 10, 
                    "is_hidden": False,
                    "is_example":True
                },
                {
                    "input_data": [], 
                    "expected_output": "Hello World!", 
                    "points_weight": 10, 
                    "is_hidden": True,
                    "is_example":False
                }
            ]
        }
        
        # Mock transpilation
        mock_transpile.return_value = ('print("Hello World!")', {1: 1})
        
        # Mock test execution
        mock_execute_test.return_value = {"status": "passed", "actual_output": "Hello World!"}
        
        result = execute_challenge_submission("challenge123", "user456", 'print("Hello World!")')
        
        assert result["success"] is True
        assert result["submission_id"] == "sub123"
        assert result["status"] == "passed"
        assert result["tests_passed"] == 2
        assert result["tests_total"] == 2
        assert result["score"] == 20
        assert "hidden_tests" in result["test_results"]
        assert "visible_tests" in result["test_results"]
        assert len(result["test_results"]["visible_tests"])==1
        visible_test = result["test_results"]["visible_tests"][0]
        assert visible_test["status"] == "passed"
        assert visible_test["actual_output"] == "Hello World!"
        assert visible_test["explanation"] == None
        assert result["test_results"]["hidden_tests"]["total"]==1
        assert result["test_results"]["hidden_tests"]["passed"]==1
        assert result["test_results"]["hidden_tests"]["failed"]==0
        
    @patch('app.services.challenge_executor.challenge_test_case_model')
    @patch('app.services.challenge_executor.challenge_submission_model') 
    @patch('app.services.challenge_executor.user_challenge_progress_model')
    @patch('app.services.challenge_executor.transpile_code')
    @patch('app.services.challenge_executor._execute_single_test')
    def test_submission_partial_success(self, mock_execute_test, mock_transpile, 
                                    mock_progress, mock_submission, mock_test_case):
        """Test submission with some passing and some failing tests."""
        # Mock database calls
        mock_submission.create.return_value = {"success": True, "data": {"id": "sub123"}}
        mock_submission.update_results.return_value = {"success": True}
        mock_test_case.find_by_challenge.return_value = {
            "success": True, 
            "data": [
                {
                    "input_data": ["5"], 
                    "expected_output": "5", 
                    "points_weight": 10, 
                    "is_hidden": False,
                    "is_example": True,
                    "explanation": "Print the input number"
                },
                {
                    "input_data": ["10"], 
                    "expected_output": "10", 
                    "points_weight": 15, 
                    "is_hidden": True,
                    "is_example": False
                }
            ]
        }
        
        # Mock transpilation
        mock_transpile.return_value = ("print(input())", {1: 1})
        
        # Mock test execution - first passes, second fails
        mock_execute_test.side_effect = [
            {"status": "passed", "actual_output": "5"},
            {"status": "failed", "actual_output": "-1"}
        ]
        
        result = execute_challenge_submission("challenge123", "user456", "code")
        
        assert result["success"] is True
        assert result["submission_id"] == "sub123"
        assert result["status"] == "failed"  # Overall status is failed
        assert result["tests_passed"] == 1
        assert result["tests_total"] == 2
        assert result["score"] == 10  # Only first test's points (10)
        
        # Check visible test results
        assert len(result["test_results"]["visible_tests"]) == 1
        visible_test = result["test_results"]["visible_tests"][0]
        assert visible_test["status"] == "passed"
        assert visible_test["actual_output"] == "5"
        assert visible_test["explanation"] == "Print the input number"
        
        # Check hidden test results
        assert result["test_results"]["hidden_tests"]["total"] == 1
        assert result["test_results"]["hidden_tests"]["passed"] == 0
        assert result["test_results"]["hidden_tests"]["failed"] == 1
    
    @patch('app.services.challenge_executor.challenge_test_case_model')
    @patch('app.services.challenge_executor.challenge_submission_model') 
    @patch('app.services.challenge_executor.user_challenge_progress_model')
    @patch('app.services.challenge_executor.transpile_code')
    @patch('app.services.challenge_executor._execute_single_test')
    def test_submission_with_error(self, mock_execute_test, mock_transpile, 
                                mock_progress, mock_submission, mock_test_case):
        """Test submission where tests fail with error message."""
        # Mock database calls
        mock_submission.create.return_value = {"success": True, "data": {"id": "sub123"}}
        mock_submission.update_results.return_value = {"success": True}
        mock_test_case.find_by_challenge.return_value = {
            "success": True, 
            "data": [
                {
                    "input_data": ["5"], 
                    "expected_output": "5", 
                    "points_weight": 10, 
                    "is_hidden": False,  
                    "is_example": True,
                    "explanation": "Print the input number"
                },
                {
                    "input_data": ["10"], 
                    "expected_output": "10", 
                    "points_weight": 15, 
                    "is_hidden": True,  
                    "is_example": False
                }
            ]
        }
        
        # Mock transpilation
        mock_transpile.return_value = ("print(x)", {1: 1})
        
        # Mock test execution - visible test fails with error, hidden test passes
        mock_execute_test.return_value = {"status": "failed",
                                          "actual_output": "",
                                          "error_message": "Igama 'x' alichazwanga",  # isiXhosa error
                                          "english_error": "NameError: name 'x' is not defined"  # English error
                                        }
        
        result = execute_challenge_submission("challenge123", "user456", "print(x)")
        
        assert result["success"] is True
        assert result["status"] == "failed"  # Overall failed
        assert result["tests_passed"] == 0
        assert result["score"] == 0
        
        # Check visible test includes error information
        assert len(result["test_results"]["visible_tests"]) == 1
        visible_test = result["test_results"]["visible_tests"][0]
        assert visible_test["status"] == "failed"
        assert visible_test["actual_output"] == ""
        assert visible_test["error_message"] == "Igama 'x' alichazwanga"  
        assert visible_test["english_error"] == "NameError: name 'x' is not defined"  
        
        # Check hidden test results
        assert result["test_results"]["hidden_tests"]["total"] == 1
        assert result["test_results"]["hidden_tests"]["passed"] == 0
        assert result["test_results"]["hidden_tests"]["failed"] == 1

    @patch('app.services.challenge_executor.challenge_test_case_model')
    @patch('app.services.challenge_executor.challenge_submission_model') 
    @patch('app.services.challenge_executor.user_challenge_progress_model')
    @patch('app.services.challenge_executor.transpile_code')
    @patch('app.services.challenge_executor.translate_error')
    def test_submission_with_failing_transpilation(self, mock_translate_error,mock_transpile,
                                mock_progress, mock_submission, mock_test_case):
        """Test submission where code fails transpilation."""
        # Mock database calls
        mock_submission.create.return_value = {"success": True, "data": {"id": "sub123"}}
        mock_submission.update_results.return_value = {"success": True}
        mock_test_case.find_by_challenge.return_value = {
            "success": True, 
            "data": [
                {
                    "input_data": ["5"], 
                    "expected_output": "5", 
                    "points_weight": 10, 
                    "is_hidden": False,  
                    "is_example": True
                },
                {
                    "input_data": ["0"], 
                    "expected_output": "", 
                    "points_weight": 25, 
                    "is_hidden": True,  
                    "is_example": False
                }
            ]
        }
        
        # Mock transpilation
        mock_transpile.side_effect = ValueError("Line 1: Please use isiXhosa keyword 'ukusuka' instead of Python keyword 'from'")
        mock_translate_error.return_value = "Sebenzisa 'ukusuka' hayi u 'import'"
        # Mock test execution - visible test fails with error, hidden test passes
        result = execute_challenge_submission("challenge123", "user456", "from math import sqrt\nval = eval(input(''))\nprint(25/val)")
        
        assert result["success"] is False
        assert result["validation_error"] == "Sebenzisa 'ukusuka' hayi u 'import'"
        assert result["english_error"] == "Line 1: Please use isiXhosa keyword 'ukusuka' instead of Python keyword 'from'"