
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, Mock

sys.path.append(str(Path(__file__).parent.parent.parent))
from app.models.challenge_testcase import ChallengeTestCase

class TestChallengeTestCaseValidation:
    """Test challenge test case data validation."""
    
    def test_validate_data_valid_test_case(self):
        """Test validation with valid test case data."""
        valid_data = {
            'expected_output': 'Hello World',
            'input_data': ['input1', 'input2'],
            'points_weight': 10,
            'is_hidden': False,
            'is_example': True,
            'explanation': 'This test case checks basic output'
        }
        
        errors = ChallengeTestCase.validate_data(valid_data)
        assert errors == {}
    
    def test_validate_data_missing_expected_output(self):
        """Test validation fails when expected output is missing."""
        invalid_data = {
            'input_data': ['input1'],
            'points_weight': 10,
            'is_hidden': False,
            'is_example': True
        }
        
        errors = ChallengeTestCase.validate_data(invalid_data)
        assert 'expected_output' in errors
        assert errors['expected_output'] == "Expected output is required"
    
    def test_validate_data_empty_expected_output(self):
        """Test validation fails when expected output is empty."""
        invalid_data = {
            'expected_output': '   ',
            'input_data': ['input1'],
            'points_weight': 10,
            'is_hidden': False,
            'is_example': True
        }
        
        errors = ChallengeTestCase.validate_data(invalid_data)
        assert 'expected_output' in errors
        assert errors['expected_output'] == "Expected output is required"
    
    def test_validate_data_invalid_input_data_type(self):
        """Test validation fails when input data is not an array."""
        invalid_data = {
            'expected_output': 'Hello World',
            'input_data': 'not an array',
            'points_weight': 10,
            'is_hidden': False,
            'is_example': True
        }
        
        errors = ChallengeTestCase.validate_data(invalid_data)
        assert 'input_data' in errors
        assert errors['input_data'] == "Input data must be an array"

    def test_validate_data_negative_points_weight(self):
        """Test validation fails with negative points weight."""
        invalid_data = {
            'expected_output': 'Hello World',
            'input_data': ['input1'],
            'points_weight': -5,
            'is_hidden': False,
            'is_example': True
        }
        
        errors = ChallengeTestCase.validate_data(invalid_data)
        assert 'points_weight' in errors
        assert errors['points_weight'] == "Points weight must be 0 or greater"

    def test_validate_data_invalid_points_weight_type(self):
        """Test validation fails with non-numeric points weight."""
        invalid_data = {
            'expected_output': 'Hello World',
            'input_data': ['input1'],
            'points_weight': 'invalid',
            'is_hidden': False,
            'is_example': True
        }
        
        errors = ChallengeTestCase.validate_data(invalid_data)
        assert 'points_weight' in errors
        assert errors['points_weight'] == "Points weight must be a valid number"
    
    def test_validate_data_missing_boolean_fields(self):
        """Test validation fails when required boolean fields are missing."""
        invalid_data = {
            'expected_output': 'Hello World',
            'input_data': ['input1'],
            'points_weight': 10
            # Missing is_hidden and is_example
        }
        
        errors = ChallengeTestCase.validate_data(invalid_data)
        assert 'is_hidden' in errors
        assert 'is_example' in errors
        assert errors['is_hidden'] == "Is Hidden is required"
        assert errors['is_example'] == "Is Example is required"
    
    def test_validate_data_invalid_boolean_types(self):
        """Test validation fails when boolean fields are not boolean."""
        invalid_data = {
            'expected_output': 'Hello World',
            'input_data': ['input1'],
            'points_weight': 10,
            'is_hidden': 'not_boolean',
            'is_example': 1
        }
        
        errors = ChallengeTestCase.validate_data(invalid_data)
        assert 'is_hidden' in errors
        assert 'is_example' in errors
        assert errors['is_hidden'] == "Is Hidden must be true or false"
        assert errors['is_example'] == "Is Example must be true or false"

    def test_validate_data_both_hidden_and_example_true(self):
        """Test validation fails when both hidden and example are true."""
        invalid_data = {
            'expected_output': 'Hello World',
            'input_data': ['input1'],
            'points_weight': 10,
            'is_hidden': True,
            'is_example': True
        }
        
        errors = ChallengeTestCase.validate_data(invalid_data)
        assert 'both_true' in errors
        assert errors['both_true'] == "Test case cannot be both hidden and an example"
    
    def test_validate_data_boundary_values(self):
        """Test validation with boundary values."""
        boundary_data = {
            'expected_output': 'Output',
            'input_data': [],  # Empty array is valid
            'points_weight': 0,  # Minimum allowed value
            'is_hidden': False,
            'is_example': False
        }
        
        errors = ChallengeTestCase.validate_data(boundary_data)
        assert errors == {}

class TestChallengeTestCaseCreate:
    """Test test case creation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_case = ChallengeTestCase()

    @patch('app.models.challenge_testcase.ChallengeTestCase.find_by_challenge')
    def test_create_test_case_success(self,mock_find_by_challenge):
        """Test successful test case creation."""

        mock_supabase = Mock()
        self.test_case.supabase = mock_supabase
        mock_find_by_challenge.cache_clear = Mock()

        mock_challenge_result = Mock()
        mock_challenge_result.data = [{'id': 'challenge-id', 'reward_points': 100}]

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_challenge_result

        mock_insert_result = Mock()
        mock_insert_result.data = [
            {
            'id': 'test-case-id',
            'challenge_id': 'challenge-id',
            'expected_output': 'Hello World',
            'input_data': ['input1'],
            'points_weight': 10,
            'is_hidden': False,
            'is_example': True
            }
        ]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_result

        test_case_data = {
            'expected_output': 'Hello World',
            'input_data': ['input1'],
            'points_weight': 10,
            'is_hidden': False,
            'is_example': True
        }
        result = self.test_case.create('challenge-id',test_case_data)
        assert result['success'] is True
        assert result["data"]["id"] == "test-case-id"
        assert result["data"]["expected_output"] == "Hello World"
        assert result["data"]["challenge_id"] == "challenge-id"
        mock_find_by_challenge.cache_clear.assert_called_once()
    
    def test_create_test_case_validation_errors(self):
        """Test test case creation fails with validation errors."""
        invalid_data = {
            'expected_output': '',  # Invalid
            'input_data': 'not_array',  # Invalid
            'is_hidden': 'not_boolean'  # Invalid
        }
        
        result = self.test_case.create('challenge-id', invalid_data)
        
        assert result["success"] is False
        assert "errors" in result
        assert len(result["errors"]) > 0
    
    def test_create_test_case_challenge_not_found(self):
        """Test test case creation fails when challenge doesn't exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.test_case.supabase = mock_supabase
        
        # Mock challenge not found
        mock_challenge_result = Mock()
        mock_challenge_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_challenge_result
        
        test_case_data = {
            'expected_output': 'Hello World',
            'input_data': ['input1'],
            'points_weight': 10,
            'is_hidden': False,
            'is_example': True
        }
        
        result = self.test_case.create('nonexistent-challenge', test_case_data)
        
        assert result["success"] is False
        assert result["error"] == "Challenge not found"

    def test_create_test_case_database_failure(self):
        """Test test case creation handles database failures."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.test_case.supabase = mock_supabase
        
        # Mock challenge exists
        mock_challenge_result = Mock()
        mock_challenge_result.data = [{'id': 'challenge-id'}]
        
        # Mock database failure on insert
        mock_insert_result = Mock()
        mock_insert_result.data = None
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_challenge_result
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_result
        
        test_case_data = {
            'expected_output': 'Hello World',
            'input_data': ['input1'],
            'points_weight': 10,
            'is_hidden': False,
            'is_example': True
        }
        
        result = self.test_case.create('challenge-id', test_case_data)
        
        assert result["success"] is False
        assert result["error"] == "Failed to create test case"

class TestChallengeTestCaseFindByChallenge:
    """Test finding test cases by challenge."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_case = ChallengeTestCase()

    def test_find_by_challenge_success(self):
        """Test successful retrieval of test cases by challenge."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.test_case.supabase = mock_supabase
        
        mock_test_cases = [
            {
                'id': 'test-case-1',
                'challenge_id': 'challenge-id',
                'expected_output': 'Output 1',
                'is_hidden': False,
                'is_example': True
            },
            {
                'id': 'test-case-2',
                'challenge_id': 'challenge-id',
                'expected_output': 'Output 2',
                'is_hidden': True,
                'is_example': False
            }
        ]
        
        mock_result = Mock()
        mock_result.data = mock_test_cases
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_result
        
        result = self.test_case.find_by_challenge('challenge-id')
        
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["expected_output"] == "Output 1"
        assert result["data"][1]["expected_output"] == "Output 2"
    
    def test_find_by_challenge_empty_result(self):
        """Test find_by_challenge when no test cases exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.test_case.supabase = mock_supabase
        
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_result
        
        result = self.test_case.find_by_challenge('challenge-id')
        
        assert result["success"] is True
        assert result["data"] == []
    
    def test_find_by_challenge_database_error(self):
        """Test find_by_challenge handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.test_case.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database error")
        
        result = self.test_case.find_by_challenge('challenge-id')
        
        assert result["success"] is False
        assert "Database error" in result["error"]

class TestChallengeTestCaseFindById:
    """Test finding test case by ID."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_case = ChallengeTestCase()

    def test_find_by_id_success(self):
        """Test successful retrieval of test case by ID."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.test_case.supabase = mock_supabase
        
        mock_test_case = [{
            'id': 'test-case-id',
            'challenge_id': 'challenge-id',
            'expected_output': 'Hello World',
            'points_weight': 10
        }]
        
        mock_result = Mock()
        mock_result.data = mock_test_case
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.test_case.find_by_id('test-case-id')
        
        assert result["success"] is True
        assert result["data"]["id"] == "test-case-id"
        assert result["data"]["expected_output"] == "Hello World"
    
    def test_find_by_id_not_found(self):
        """Test find_by_id when test case doesn't exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.test_case.supabase = mock_supabase
        
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.test_case.find_by_id('nonexistent-id')
        
        assert result["success"] is False
        assert result["error"] == "Test case not found"

    def test_find_by_id_database_error(self):
        """Test find_by_id handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.test_case.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database error")
        
        result = self.test_case.find_by_id('test-case-id')
        
        assert result["success"] is False
        assert "Database error" in result["error"]

class TestChallengeTestCaseUpdate:
    """Test test case update functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_case = ChallengeTestCase()
 
    @patch('app.models.challenge_testcase.ChallengeTestCase.find_by_challenge')
    def test_update_test_case_success(self,mock_find_by_challenge):
        """Test successful test case update."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.test_case.supabase = mock_supabase
        mock_find_by_challenge.cache_clear = Mock()

        
        mock_updated_test_case = {
            'id': 'test-case-id',
            'expected_output': 'Updated Output',
            'points_weight': 15,
            'is_hidden': True
        }
        
        mock_result = Mock()
        mock_result.data = [mock_updated_test_case]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result
        
        updates = {
            'expected_output': 'Updated Output',
            'points_weight': 15,
            'is_hidden': True,
            'is_example': False
        }
        
        result = self.test_case.update('test-case-id', updates)
        
        assert result["success"] is True
        assert result["data"]["expected_output"] == "Updated Output"
        assert result["data"]["points_weight"] == 15
        mock_find_by_challenge.cache_clear.assert_called_once()

    def test_update_test_case_validation_errors(self):
        """Test test case update fails with validation errors."""
        invalid_updates = {
            'expected_output': '',  # Invalid
            'points_weight': -5,  # Invalid
            'is_hidden': 'not_boolean'  # Invalid
        }
        
        result = self.test_case.update('test-case-id', invalid_updates)
        
        assert result["success"] is False
        assert "errors" in result
        assert 'expected_output' in result["errors"]
        assert 'points_weight' in result["errors"]
        assert 'is_hidden' in result["errors"]

    def test_update_test_case_not_found(self):
        """Test test case update when test case doesn't exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.test_case.supabase = mock_supabase
        
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result
        
        updates = {
            'expected_output': 'Updated Output',
            'is_hidden': False,
            'is_example': True
        }
        
        result = self.test_case.update('nonexistent-id', updates)
        
        assert result["success"] is False
        assert result["error"] == "Failed to update test case or test case not found"

class TestChallengeTestCaseDeleteByChallenge:
    """Test deleting test cases by challenge."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_case = ChallengeTestCase()

    @patch('app.models.challenge_testcase.ChallengeTestCase.find_by_challenge')
    def test_delete_by_challenge_success(self,mock_find_by_challenge):
        """Test successful deletion of test cases by challenge."""
        # Mock the supabase instance
        mock_supabase = Mock()
        mock_find_by_challenge.cache_clear = Mock()
        self.test_case.supabase = mock_supabase
        self.test_case.find_by_challenge.cache_clear = Mock()
        
        mock_result = Mock()
        mock_result.data = [{'id': 'test-case-1'}, {'id': 'test-case-2'}]
        mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.test_case.delete_by_challenge('challenge-id')
        
        assert result["success"] is True
        assert result["message"] == "All test cases deleted successfully"
        mock_find_by_challenge.cache_clear.assert_called_once()

    def test_delete_by_challenge_database_error(self):
        """Test delete_by_challenge handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.test_case.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database error")
        
        result = self.test_case.delete_by_challenge('challenge-id')
        
        assert result["success"] is False
        assert "Database error" in result["error"]

class TestChallengeTestCaseValidateWeightsSum:
    """Test weights sum validation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_case = ChallengeTestCase()

    def test_validate_weights_sum_valid(self):
        """Test weights sum validation when weights match reward points."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.test_case.supabase = mock_supabase
        
        # Mock challenge data
        mock_challenge_result = Mock()
        mock_challenge_result.data = [{'reward_points': 100}]
        
        # Mock test cases data that sum to 100
        mock_test_cases_result = Mock()
        mock_test_cases_result.data = [
            {'points_weight': 50},
            {'points_weight': 30},
            {'points_weight': 20}
        ]
        
        # Setup mock chain
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            mock_challenge_result,
            mock_test_cases_result
        ]
        
        result = self.test_case.validate_weights_sum('challenge-id')
        
        assert result["success"] is True
        assert result["data"]["is_valid"] is True
        assert result["data"]["total_weight"] == 100
        assert result["data"]["reward_points"] == 100
        assert result["data"]["difference"] == 0
    
    def test_validate_weights_sum_invalid(self):
        """Test weights sum validation when weights don't match reward points."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.test_case.supabase = mock_supabase
        
        # Mock challenge data
        mock_challenge_result = Mock()
        mock_challenge_result.data = [{'reward_points': 100}]
        
        # Mock test cases data that sum to 80 (not 100)
        mock_test_cases_result = Mock()
        mock_test_cases_result.data = [
            {'points_weight': 50},
            {'points_weight': 30}
        ]
        
        # Setup mock chain
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            mock_challenge_result,
            mock_test_cases_result
        ]
        
        result = self.test_case.validate_weights_sum('challenge-id')
        
        assert result["success"] is True
        assert result["data"]["is_valid"] is False
        assert result["data"]["total_weight"] == 80
        assert result["data"]["reward_points"] == 100
        assert result["data"]["difference"] == -20

    def test_validate_weights_sum_challenge_not_found(self):
        """Test weights sum validation when challenge doesn't exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.test_case.supabase = mock_supabase
        
        # Mock challenge not found
        mock_challenge_result = Mock()
        mock_challenge_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_challenge_result
        
        result = self.test_case.validate_weights_sum('nonexistent-challenge')
        
        assert result["success"] is False
        assert result["error"] == "Challenge not found"

    def test_validate_weights_sum_no_test_cases(self):
        """Test weights sum validation with no test cases."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.test_case.supabase = mock_supabase
        
        # Mock challenge data
        mock_challenge_result = Mock()
        mock_challenge_result.data = [{'reward_points': 100}]
        
        # Mock empty test cases
        mock_test_cases_result = Mock()
        mock_test_cases_result.data = []
        
        # Setup mock chain
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            mock_challenge_result,
            mock_test_cases_result
        ]
        
        result = self.test_case.validate_weights_sum('challenge-id')
        
        assert result["success"] is True
        assert result["data"]["is_valid"] is False  # 0 != 100
        assert result["data"]["total_weight"] == 0
        assert result["data"]["reward_points"] == 100
        assert result["data"]["difference"] == -100