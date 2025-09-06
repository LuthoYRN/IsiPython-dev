import pytest
import sys
from pathlib import Path
from unittest.mock import patch, Mock

sys.path.append(str(Path(__file__).parent.parent.parent))
from app.models.challenge import Challenge

class TestChallengeValidation:
    """Test challenge data validation."""
    
    def test_validate_data_valid_challenge(self):
        """Test validation with valid challenge data."""
        valid_data = {
            'title': 'Test Challenge',
            'problem_statement': 'Solve this coding problem',
            'difficulty_level': 'Medium',
            'reward_points': 100,
            'estimated_time': 30
        }
        
        errors = Challenge.validate_data(valid_data)
        assert errors == {}
    
    def test_validate_data_missing_title(self):
        """Test validation fails when title is missing."""
        invalid_data = {
            'problem_statement': 'Solve this coding problem',
            'difficulty_level': 'Medium'
        }
        
        errors = Challenge.validate_data(invalid_data)
        assert 'title' in errors
        assert errors['title'] == "Title is required"
    
    def test_validate_data_empty_title(self):
        """Test validation fails when title is empty."""
        invalid_data = {
            'title': '   ',
            'problem_statement': 'Solve this coding problem',
            'difficulty_level': 'Medium'
        }
        
        errors = Challenge.validate_data(invalid_data)
        assert 'title' in errors
        assert errors['title'] == "Title is required"
    
    def test_validate_data_title_too_long(self):
        """Test validation fails when title exceeds 255 characters."""
        invalid_data = {
            'title': 'a' * 256,
            'problem_statement': 'Solve this coding problem',
            'difficulty_level': 'Medium'
        }
        
        errors = Challenge.validate_data(invalid_data)
        assert 'title' in errors
        assert errors['title'] == "Title must be 255 characters or less"
    
    def test_validate_data_missing_problem_statement(self):
        """Test validation fails when problem statement is missing."""
        invalid_data = {
            'title': 'Test Challenge',
            'difficulty_level': 'Medium'
        }
        
        errors = Challenge.validate_data(invalid_data)
        assert 'problem_statement' in errors
        assert errors['problem_statement'] == "Problem statement is required"

    def test_validate_data_invalid_difficulty(self):
        """Test validation fails with invalid difficulty level."""
        invalid_data = {
            'title': 'Test Challenge',
            'problem_statement': 'Solve this coding problem',
            'difficulty_level': 'Expert'
        }
        
        errors = Challenge.validate_data(invalid_data)
        assert 'difficulty_level' in errors
        assert "Difficulty must be one of: Easy, Medium, Hard" in errors['difficulty_level']

    def test_validate_data_negative_reward_points(self):
        """Test validation fails with negative reward points."""
        invalid_data = {
            'title': 'Test Challenge',
            'problem_statement': 'Solve this coding problem',
            'difficulty_level': 'Medium',
            'reward_points': -10
        }
        
        errors = Challenge.validate_data(invalid_data)
        assert 'reward_points' in errors
        assert errors['reward_points'] == "Reward points must be 0 or greater"

    def test_validate_data_invalid_reward_points_type(self):
        """Test validation fails with non-numeric reward points."""
        invalid_data = {
            'title': 'Test Challenge',
            'problem_statement': 'Solve this coding problem',
            'difficulty_level': 'Medium',
            'reward_points': 'invalid'
        }
        
        errors = Challenge.validate_data(invalid_data)
        assert 'reward_points' in errors
        assert errors['reward_points'] == "Reward points must be a valid number"

    def test_validate_data_zero_estimated_time(self):
        """Test validation fails with zero estimated time."""
        invalid_data = {
            'title': 'Test Challenge',
            'problem_statement': 'Solve this coding problem',
            'difficulty_level': 'Medium',
            'estimated_time': 0
        }
        
        errors = Challenge.validate_data(invalid_data)
        assert 'estimated_time' in errors
        assert errors['estimated_time'] == "Estimated time must be greater than 0"

    def test_validate_data_invalid_status(self):
        """Test validation fails with invalid status."""
        invalid_data = {
            'title': 'Test Challenge',
            'problem_statement': 'Solve this coding problem',
            'difficulty_level': 'Medium',
            'status': 'invalid_status'
        }
        
        errors = Challenge.validate_data(invalid_data)
        assert 'status' in errors
        assert "Status must be one of: draft, published" in errors['status']
    
    def test_validate_data_boundary_values(self):
        """Test validation with boundary values."""
        boundary_data = {
            'title': 'a' * 255,  # Exactly 255 characters
            'problem_statement': 'Valid problem statement',
            'difficulty_level': 'Easy',
            'reward_points': 0,  # Minimum allowed value
            'estimated_time': 1  # Minimum allowed value
        }
        
        errors = Challenge.validate_data(boundary_data)
        assert errors == {}

class TestChallengeCreate:
    """Test challenge creation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.challenge = Challenge()

    @patch('app.models.challenge.clear_challenge_dependent_caches')
    @patch('app.models.challenge.Challenge.find_by_id')
    @patch('app.models.challenge.Challenge._check_title_uniqueness')
    @patch('app.models.challenge.Challenge._get_unique_slug')
    def test_create_challenge_success(self, mock_get_slug, mock_check_title, 
                                      mock_find_by_id,mock_clear_cache):
        """Test successful challenge creation."""
        # Setup mocks
        mock_supabase = Mock()
        self.challenge.supabase = mock_supabase
        mock_check_title.return_value = True
        mock_get_slug.return_value = "test-challenge"
        mock_find_by_id.cache_clear = Mock()
        
        # Mock successful database insertion
        mock_result = Mock()
        mock_result.data = [{
            'id': 'test-id',
            'title': 'Test Challenge',
            'slug': 'test-challenge',
            'status': 'draft',
            'reward_points': 100
        }]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
        
        challenge_data = {
            'title': 'Test Challenge',
            'problem_statement': 'Solve this problem',
            'difficulty_level': 'Medium',
            'reward_points': 100
        }
        
        result = self.challenge.create(challenge_data)
        
        assert result["success"] is True
        assert result["data"]["title"] == "Test Challenge"
        assert result["data"]["slug"] == "test-challenge"
        mock_find_by_id.cache_clear.assert_called_once()
        mock_clear_cache.assert_called_once()
    
    @patch('app.models.challenge.Challenge._check_title_uniqueness')
    def test_create_challenge_duplicate_title(self, mock_check_title):
        """Test challenge creation fails with duplicate title."""
        mock_check_title.return_value = False
        
        challenge_data = {
            'title': 'Existing Title',
            'problem_statement': 'Solve this problem',
            'difficulty_level': 'Medium',
            'reward_points': 100
        }
        
        result = self.challenge.create(challenge_data)

        assert result["success"] is False
        assert result["errors"]["title"] == "A challenge with this title already exists" 

    def test_create_challenge_validation_errors(self):
        """Test challenge creation fails with validation errors."""
        invalid_data = {
            'title': '',  # Invalid title
            'difficulty_level': 'Invalid'  # Invalid difficulty
        }
        
        result = self.challenge.create(invalid_data)

        assert result["success"] is False
        assert len(result["errors"]) > 0
    
    @patch('app.models.challenge.Challenge._check_title_uniqueness')
    @patch('app.models.challenge.Challenge._get_unique_slug')
    def test_create_challenge_database_failure(self, mock_get_slug, mock_check_title):
        """Test challenge creation handles database failures."""
        mock_check_title.return_value = True
        mock_get_slug.return_value = "test-challenge"
        
        # Mock the supabase instance
        mock_supabase = Mock()
        self.challenge.supabase = mock_supabase
        
        # Mock database failure
        mock_result = Mock()
        mock_result.data = None
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
        
        challenge_data = {
            'title': 'Test Challenge',
            'problem_statement': 'Solve this problem',
            'difficulty_level': 'Medium'
        }
        
        result = self.challenge.create(challenge_data)
        
        assert result["success"] is False
        assert result["error"] == "Failed to create challenge"

class TestChallengeFindById:
    """Test challenge retrieval by ID."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.challenge = Challenge()

    def test_find_by_id_success(self):
        """Test successful challenge retrieval by ID."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.challenge.supabase = mock_supabase
        
        mock_challenge = [{
            'id': 'test-id',
            'title': 'Test Challenge',
            'status': 'published',
            'difficulty_level': 'Medium'
        }]
        
        mock_result = Mock()
        mock_result.data = mock_challenge
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.challenge.find_by_id('test-id')
        
        assert result["success"] is True
        assert result["data"]["title"] == "Test Challenge"
        assert result["data"]["id"] == "test-id"

    def test_find_by_id_not_found(self):
        """Test challenge retrieval when challenge doesn't exist."""
        
        mock_supabase = Mock()
        self.challenge.supabase = mock_supabase
        
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.challenge.find_by_id('nonexistent-id')
        
        assert result["success"] is False
        assert result["error"] == "Challenge not found"
    
    @patch('app.models.challenge.clear_challenge_dependent_caches')
    def test_find_by_id_database_error(self, mock_clear_cache):
        """Test find_by_id handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.challenge.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database connection failed")
        result = self.challenge.find_by_id('test-id')
        
        assert result["success"] is False
        assert "Database connection failed" in result["error"]
        mock_clear_cache.assert_called_once()

    
class TestChallengeFindAll:
    """Test challenge list retrieval."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.challenge = Challenge()

    def test_find_all_no_filters(self):
        """Test retrieving all challenges without filters."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.challenge.supabase = mock_supabase
        
        mock_challenges = [
            {'id': '1', 'title': 'Challenge 1', 'status': 'published'},
            {'id': '2', 'title': 'Challenge 2', 'status': 'draft'}
        ]
        
        mock_result = Mock()
        mock_result.data = mock_challenges
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = mock_result
        
        result = self.challenge.find_all()
        
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["title"] == "Challenge 1"
    
    def test_find_all_with_status_filter(self):
        """Test retrieving challenges with status filter."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.challenge.supabase = mock_supabase
        
        mock_challenges = [
            {'id': '1', 'title': 'Published Challenge', 'status': 'published'}
        ]
        
        mock_result = Mock()
        mock_result.data = mock_challenges
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_result
        
        result = self.challenge.find_all({'status': 'published'})
        
        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["status"] == "published"
    
    def test_find_all_empty_result(self):
        """Test find_all when no challenges exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.challenge.supabase = mock_supabase
        
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = mock_result
        
        result = self.challenge.find_all()
        
        assert result["success"] is True
        assert result["data"] == []
        assert len(result["data"]) == 0

class TestChallengeUpdate:
    """Test challenge update functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.challenge = Challenge()

    @patch('app.models.challenge.clear_challenge_dependent_caches')
    @patch('app.models.challenge.Challenge.find_by_id')
    @patch('app.models.challenge.Challenge._check_title_uniqueness')
    @patch('app.models.challenge.Challenge._get_unique_slug')
    def test_update_challenge_success(self, mock_get_slug, mock_check_title, mock_find_by_id , mock_clear_cache):
        """Test successful challenge update."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.challenge.supabase = mock_supabase
        mock_check_title.return_value = True
        mock_get_slug.return_value = "updated-challenge"
        mock_find_by_id.cache_clear = Mock()
        mock_updated_challenge = {
            'id': 'test-id',
            'title': 'Updated Challenge',
            'status': 'published',
            'difficulty_level': 'Hard'
        }
        
        mock_result = Mock()
        mock_result.data = [mock_updated_challenge]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result
        
        updates = {
            'title': 'Updated Challenge',
            'difficulty_level': 'Hard',
            'problem_statement': 'Solve this coding problem',
        }
        
        result = self.challenge.update('test-id', updates)
        
        assert result["success"] is True
        assert result["data"]["title"] == "Updated Challenge"
        assert result["data"]["difficulty_level"] == "Hard"
        mock_clear_cache.assert_called_once()
        mock_find_by_id.cache_clear.assert_called_once()
    
    def test_update_challenge_validation_errors(self):
        """Test challenge update fails with validation errors."""
        invalid_updates = {
            'title': '',  # Invalid title
            'difficulty_level': 'Invalid'  # Invalid difficulty
            #missing problem statement
        }
        
        result = self.challenge.update('test-id', invalid_updates)
        
        assert result["success"] is False
        assert "errors" in result
        assert 'title' in result["errors"]
        assert 'difficulty_level' in result["errors"]
        assert 'problem_statement' in result["errors"]
    
    @patch('app.models.challenge.Challenge._check_title_uniqueness')
    def test_update_challenge_title_exists(self, mock_check_title):
        """Test challenge update when challenge doesn't exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.challenge.supabase = mock_supabase
        mock_check_title.return_value = False 
        updates = {'title': 'Overlapping Title',
                   'difficulty_level': 'Hard',
                   'problem_statement': 'Solve this coding problem'
                }
        
        result = self.challenge.update('test-id', updates)
        
        assert result["success"] is False
        assert 'title' in result["errors"]
        assert result['errors']['title'] == "A challenge with this title already exists"

    @patch('app.models.challenge.Challenge._get_unique_slug')
    @patch('app.models.challenge.Challenge._check_title_uniqueness')
    def test_update_challenge_not_found(self, mock_check_title, mock_get_slug):
        """Test challenge update when challenge doesn't exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.challenge.supabase = mock_supabase
        mock_check_title.return_value = True
        mock_get_slug.return_value = "title"
        
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result
        
        updates = {'title': 'Title',
                   'difficulty_level': 'Hard',
                   'problem_statement': 'Solve this coding problem'
                }
        
        result = self.challenge.update('nonexistent-id', updates)
        
        assert result["success"] is False
        assert result["error"] == "Failed to update challenge or challenge not found"

class TestChallengeDelete:
    """Test challenge deletion functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.challenge = Challenge()

    @patch('app.models.challenge.Challenge.find_by_id')
    @patch('app.models.challenge.clear_challenge_dependent_caches')
    def test_delete_challenge_success(self, mock_clear_cache, mock_find_by_id):
        """Test successful challenge deletion."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.challenge.supabase = mock_supabase
        
        mock_result = Mock()
        mock_result.data = [{'id': 'test-id'}]
        mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_result
        mock_find_by_id.cache_clear = Mock()
        result = self.challenge.delete('test-id')
        
        assert result["success"] is True
        assert result["message"] == "Challenge deleted successfully"
        mock_clear_cache.assert_called_once()
        mock_find_by_id.cache_clear.assert_called_once()
    
    @patch('app.models.challenge.Challenge.find_by_id')
    @patch('app.models.challenge.clear_challenge_dependent_caches')
    def test_delete_challenge_not_found(self, mock_clear_cache, mock_find_by_id):
        """Test challenge deletion when challenge doesn't exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.challenge.supabase = mock_supabase
        
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_result
        mock_find_by_id.cache_clear = Mock()
        result = self.challenge.delete('nonexistent-id')
        
        assert result["success"] is False
        assert result["error"] == "Failed to delete or challenge not found"
        mock_clear_cache.assert_not_called()
        mock_find_by_id.cache_clear.assert_not_called()

class TestChallengeHelperMethods:
    """Test challenge helper methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.challenge = Challenge()

    def test_check_title_uniqueness_unique(self):
        """Test title uniqueness check with unique title."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.challenge.supabase = mock_supabase
        
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.challenge._check_title_uniqueness("Unique Title")
        
        assert result is True

    def test_check_title_uniqueness_duplicate(self):
        """Test title uniqueness check with duplicate title."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.challenge.supabase = mock_supabase
        
        mock_result = Mock()
        mock_result.data = [{'id': 'existing-id', 'title': 'Existing Title'}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.challenge._check_title_uniqueness("Existing Title")
        
        assert result is False

    def test_generate_slug_basic(self):
        """Test basic slug generation."""
        result = self.challenge.generate_slug("Hello World Challenge")
        assert result == "hello-world-challenge"

    def test_generate_slug_special_characters(self):
        """Test slug generation with special characters."""
        result = self.challenge.generate_slug("C++ & Python: Advanced!")
        assert result == "c-python-advanced"

    def test_generate_slug_with_numbers(self):
        """Test slug generation preserves numbers."""
        result = self.challenge.generate_slug("Challenge 123 Test")
        assert result == "challenge-123-test"

    def test_get_unique_slug_first_attempt(self):
        """Test getting unique slug on first attempt."""
        mock_supabase = Mock()
        self.challenge.supabase = mock_supabase
        
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        result = self.challenge._get_unique_slug("Test Title")
        
        assert result == "test-title"
    
    def test_get_unique_slug_with_collision(self):
        """Test getting unique slug when collision occurs."""
        mock_supabase = Mock()
        self.challenge.supabase = mock_supabase
        
        mock_result = Mock()
        mock_result.data = [{'id': 'existing-id'}]
        mock_result_second = Mock()
        mock_result_second.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [mock_result,mock_result_second]

        result = self.challenge._get_unique_slug("Test Title")
        
        assert result == "test-title-2"