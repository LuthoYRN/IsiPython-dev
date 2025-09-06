import pytest
import sys
from pathlib import Path
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
import pytz

SOUTH_AFRICA_TZ = pytz.timezone('Africa/Johannesburg')

sys.path.append(str(Path(__file__).parent.parent.parent))
from app.models.quiz import Quiz

class TestQuizValidation:
    """Test quiz data validation."""
    
    def test_validate_data_valid_quiz(self):
        """Test validation with valid quiz data."""
        # Create a future date for due_date
        future_date = (datetime.now(SOUTH_AFRICA_TZ) + timedelta(days=7)).isoformat()
        
        valid_data = {
            'title': 'Test Quiz',
            'description': 'A test quiz for validation',
            'time_limit_minutes': 60,
            'due_date': future_date,
            'instructions': ['Read carefully', 'Choose the best answer']
        }
        
        errors = Quiz.validate_data(valid_data)
        assert errors == {}

    def test_validate_data_missing_title(self):
        """Test validation fails when title is missing."""
        future_date = (datetime.now(SOUTH_AFRICA_TZ) + timedelta(days=7)).isoformat()
        
        invalid_data = {
            'description': 'A test quiz',
            'due_date': future_date
        }
        
        errors = Quiz.validate_data(invalid_data)
        assert 'title' in errors
        assert errors['title'] == "Title is required"
    
    def test_validate_data_empty_title(self):
        """Test validation fails when title is empty."""
        future_date = (datetime.now(SOUTH_AFRICA_TZ) + timedelta(days=7)).isoformat()
        
        invalid_data = {
            'title': '   ',
            'due_date': future_date
        }
        
        errors = Quiz.validate_data(invalid_data)
        assert 'title' in errors
        assert errors['title'] == "Title is required"
    
    def test_validate_data_title_too_long(self):
        """Test validation fails when title exceeds 255 characters."""
        future_date = (datetime.now(SOUTH_AFRICA_TZ) + timedelta(days=7)).isoformat()
        
        invalid_data = {
            'title': 'a' * 256,
            'due_date': future_date
        }
        
        errors = Quiz.validate_data(invalid_data)
        assert 'title' in errors
        assert errors['title'] == "Title must be 255 characters or less"
    
    def test_validate_data_missing_due_date(self):
        """Test validation fails when due date is missing."""
        invalid_data = {
            'title': 'Test Quiz'
        }
        
        errors = Quiz.validate_data(invalid_data)
        assert 'due_date' in errors
        assert errors['due_date'] == "Due date is required"
    
    def test_validate_data_past_due_date(self):
        """Test validation fails when due date is in the past."""
        past_date = (datetime.now(SOUTH_AFRICA_TZ) - timedelta(days=1)).isoformat()
        
        invalid_data = {
            'title': 'Test Quiz',
            'due_date': past_date
        }
        
        errors = Quiz.validate_data(invalid_data)
        assert 'due_date' in errors
        assert errors['due_date'] == "Due date must be in the future"

    def test_validate_data_invalid_time_limit_zero(self):
        """Test validation fails with zero time limit."""
        future_date = (datetime.now(SOUTH_AFRICA_TZ) + timedelta(days=7)).isoformat()
        
        invalid_data = {
            'title': 'Test Quiz',
            'due_date': future_date,
            'time_limit_minutes': 0
        }
        
        errors = Quiz.validate_data(invalid_data)
        assert 'time_limit_minutes' in errors
        assert errors['time_limit_minutes'] == "Time limit must be greater than 0"

    def test_validate_data_invalid_time_limit_too_high(self):
        """Test validation fails with time limit over 6 hours."""
        future_date = (datetime.now(SOUTH_AFRICA_TZ) + timedelta(days=7)).isoformat()
            
        invalid_data = {
            'title': 'Test Quiz',
            'due_date': future_date,
            'time_limit_minutes': 400  # Over 6 hours (360 minutes)
        }
            
        errors = Quiz.validate_data(invalid_data)
        assert 'time_limit_minutes' in errors
        assert errors['time_limit_minutes'] == "Time limit cannot exceed 6 hours (360 minutes)"

    def test_validate_data_invalid_time_limit_type(self):
        """Test validation fails with non-numeric time limit."""
        future_date = (datetime.now(SOUTH_AFRICA_TZ) + timedelta(days=7)).isoformat()
        
        invalid_data = {
            'title': 'Test Quiz',
            'due_date': future_date,
            'time_limit_minutes': 'invalid'
        }
        
        errors = Quiz.validate_data(invalid_data)
        assert 'time_limit_minutes' in errors
        assert errors['time_limit_minutes'] == "Time limit must be a valid number"

    def test_validate_data_invalid_instructions_type(self):
        """Test validation fails with non-array instructions."""
        future_date = (datetime.now(SOUTH_AFRICA_TZ) + timedelta(days=7)).isoformat()
        
        invalid_data = {
            'title': 'Test Quiz',
            'due_date': future_date,
            'instructions': 'Not an array'
        }
        
        errors = Quiz.validate_data(invalid_data)
        assert 'instructions' in errors
        assert errors['instructions'] == "Instructions must be an array"

    def test_validate_data_invalid_status(self):
        """Test validation fails with invalid status."""
        future_date = (datetime.now(SOUTH_AFRICA_TZ) + timedelta(days=7)).isoformat()
        
        invalid_data = {
            'title': 'Test Quiz',
            'due_date': future_date,
            'instructions': 'Not an array',
            'status':'archived'
        }
        
        errors = Quiz.validate_data(invalid_data)
        assert 'status' in errors
        assert errors['status'] == "Status must be one of: draft, published"

    def test_validate_data_boundary_values(self):
        """Test validation with boundary values."""
        future_date = (datetime.now(SOUTH_AFRICA_TZ) + timedelta(days=7)).isoformat()
        
        boundary_data = {
            'title': 'a' * 255,  # Exactly 255 characters
            'due_date': future_date,
            'time_limit_minutes': 1,  # Minimum allowed value
            'instructions': []  # Empty array is valid
        }
        
        errors = Quiz.validate_data(boundary_data)
        assert errors == {}

class TestQuizCreate:
    """Test quiz creation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.quiz = Quiz()

    @patch('app.models.quiz.clear_quiz_dependent_caches')
    @patch('app.models.quiz.Quiz.find_by_id')
    @patch('app.models.quiz.Quiz._check_title_uniqueness')
    @patch('app.models.quiz.Quiz._get_unique_slug')
    def test_create_quiz_success(self, mock_get_slug, mock_check_title, 
                                 mock_find_by_id, mock_clear_cache):
        """Test successful quiz creation."""
        # Setup mocks
        mock_check_title.return_value = True
        mock_get_slug.return_value = "test-quiz"
        mock_find_by_id.cache_clear = Mock()
        
        # Mock the supabase instance
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        
        # Mock successful database insertion
        mock_result = Mock()
        mock_result.data = [{
            'id': 'test-id',
            'title': 'Test Quiz',
            'slug': 'test-quiz',
            'status': 'draft',
            'time_limit_minutes': 60
        }]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
        
        future_date = (datetime.now(SOUTH_AFRICA_TZ) + timedelta(days=7)).isoformat()
        quiz_data = {
            'title': 'Test Quiz',
            'description': 'A test quiz',
            'due_date': future_date,
            'time_limit_minutes': 60
        }
        
        result = self.quiz.create(quiz_data)
        
        assert result["success"] is True
        assert result["data"]["title"] == "Test Quiz"
        assert result["data"]["slug"] == "test-quiz"
        mock_find_by_id.cache_clear.assert_called_once()
        mock_clear_cache.assert_called_once()
    
    @patch('app.models.quiz.Quiz._check_title_uniqueness')
    def test_create_quiz_duplicate_title(self, mock_check_title):
        """Test quiz creation fails with duplicate title."""
        mock_check_title.return_value = False
        
        future_date = (datetime.now(SOUTH_AFRICA_TZ) + timedelta(days=7)).isoformat()
        quiz_data = {
            'title': 'Existing Title',
            'due_date': future_date
        }
        
        result = self.quiz.create(quiz_data)
        
        assert result["success"] is False
        assert result["errors"]["title"] == "A quiz with this title already exists"

    def test_create_quiz_validation_errors(self):
        """Test quiz creation fails with validation errors."""
        invalid_data = {
            'title': '',  # Invalid title
            'time_limit_minutes': 0  # Invalid time limit
        }
        
        result = self.quiz.create(invalid_data)
        
        assert result["success"] is False
        assert "errors" in result
        assert len(result["errors"]) > 0

    @patch('app.models.quiz.Quiz._check_title_uniqueness')
    @patch('app.models.quiz.Quiz._get_unique_slug')
    def test_create_quiz_database_failure(self, mock_get_slug, mock_check_title):
        """Test quiz creation handles database failures."""
        mock_check_title.return_value = True
        mock_get_slug.return_value = "test-quiz"
        
        # Mock the supabase instance
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        
        # Mock database failure
        mock_result = Mock()
        mock_result.data = None
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
        
        future_date = (datetime.now(SOUTH_AFRICA_TZ) + timedelta(days=7)).isoformat()
        quiz_data = {
            'title': 'Test Quiz',
            'due_date': future_date
        }
        
        result = self.quiz.create(quiz_data)
        
        assert result["success"] is False
        assert result["error"] == "Failed to create quiz"

class TestQuizFindById:
    """Test quiz retrieval by ID."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.quiz = Quiz()

    def test_find_by_id_success(self):
        """Test successful quiz retrieval by ID."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        
        mock_quiz = [{
            'id': 'test-id',
            'title': 'Test Quiz',
            'status': 'published',
            'time_limit_minutes': 60
        }]
        
        mock_result = Mock()
        mock_result.data = mock_quiz
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.quiz.find_by_id('test-id')
        
        assert result["success"] is True
        assert result["data"]["title"] == "Test Quiz"
        assert result["data"]["id"] == "test-id"

    def test_find_by_id_not_found(self):
        """Test quiz retrieval when quiz doesn't exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.quiz.find_by_id('nonexistent-id')
        
        assert result["success"] is False
        assert result["error"] == "Quiz not found"
    
    @patch('app.models.quiz.clear_quiz_dependent_caches')
    def test_find_by_id_database_error(self, mock_clear_cache):
        """Test find_by_id handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database connection failed")
        
        result = self.quiz.find_by_id('test-id')
        
        assert result["success"] is False
        assert "Database connection failed" in result["error"]
        mock_clear_cache.assert_called_once()

class TestQuizFindAll:
    """Test quiz list retrieval."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.quiz = Quiz()

    def test_find_all_no_filters(self):
        """Test retrieving all quizzes without filters."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        
        mock_quizzes = [
            {'id': '1', 'title': 'Quiz 1', 'status': 'published'},
            {'id': '2', 'title': 'Quiz 2', 'status': 'draft'}
        ]
        
        mock_result = Mock()
        mock_result.data = mock_quizzes
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = mock_result
        
        result = self.quiz.find_all()
        
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["title"] == "Quiz 1"
    
    def test_find_all_with_status_filter(self):
        """Test retrieving quizzes with status filter."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        
        mock_quizzes = [
            {'id': '1', 'title': 'Published Quiz', 'status': 'published'}
        ]
        
        mock_result = Mock()
        mock_result.data = mock_quizzes
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_result
        
        result = self.quiz.find_all({'status': 'published'})
        
        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["status"] == "published"
    
    def test_find_all_empty_result(self):
        """Test find_all when no quizzes exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = mock_result
        
        result = self.quiz.find_all()
        
        assert result["success"] is True
        assert result["data"] == []
        assert len(result["data"]) == 0

class TestQuizUpdate:
    """Test quiz update functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.quiz = Quiz()

    @patch('app.models.quiz.clear_quiz_dependent_caches')
    @patch('app.models.quiz.Quiz.find_by_id')
    @patch('app.models.quiz.Quiz._check_title_uniqueness')
    @patch('app.models.quiz.Quiz._get_unique_slug')
    def test_update_quiz_success(self, mock_get_slug, mock_check_title, 
                                 mock_find_by_id, mock_clear_cache):
        """Test successful quiz update."""
        # Mock the supabase instance and cache clear method
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        mock_check_title.return_value = True
        mock_get_slug.return_value = "updated-quiz"
        mock_find_by_id.cache_clear = Mock()
        
        mock_updated_quiz = {
            'id': 'test-id',
            'title': 'Updated Quiz',
            'status': 'published',
            'time_limit_minutes': 90
        }
        
        mock_result = Mock()
        mock_result.data = [mock_updated_quiz]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result
        
        future_date = (datetime.now(SOUTH_AFRICA_TZ) + timedelta(days=7)).isoformat()
        updates = {
            'title': 'Updated Quiz',
            'time_limit_minutes': 90,
            'due_date': future_date
        }
        
        result = self.quiz.update('test-id', updates)
        
        assert result["success"] is True
        assert result["data"]["title"] == "Updated Quiz"
        assert result["data"]["time_limit_minutes"] == 90
        mock_clear_cache.assert_called_once()
        mock_find_by_id.cache_clear.assert_called_once()

    def test_update_quiz_validation_errors(self):
        """Test quiz update fails with validation errors."""
        invalid_updates = {
            'title': '',  # Invalid title
            'time_limit_minutes': 0  # Invalid time limit
        }
        
        result = self.quiz.update('test-id', invalid_updates)
        
        assert result["success"] is False
        assert "errors" in result
        assert 'title' in result["errors"]
        assert 'time_limit_minutes' in result["errors"]
    
    @patch('app.models.quiz.Quiz._check_title_uniqueness')
    def test_update_quiz_title_exists(self, mock_check_title):
        """Test quiz update when title already exists."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        mock_check_title.return_value = False
        
        future_date = (datetime.now(SOUTH_AFRICA_TZ) + timedelta(days=7)).isoformat()
        updates = {
            'title': 'Overlapping Title',
            'due_date': future_date
        }
        
        result = self.quiz.update('test-id', updates)
        
        assert result["success"] is False
        assert 'title' in result["errors"]
        assert result['errors']['title'] == "A quiz with this title already exists"

    @patch('app.models.quiz.Quiz._get_unique_slug')
    @patch('app.models.quiz.Quiz._check_title_uniqueness')
    def test_update_quiz_not_found(self, mock_check_title, mock_get_slug):
        """Test quiz update when quiz doesn't exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        mock_check_title.return_value = True
        mock_get_slug.return_value = "title"
        
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result
        
        future_date = (datetime.now(SOUTH_AFRICA_TZ) + timedelta(days=7)).isoformat()
        updates = {
            'title': 'Title',
            'due_date': future_date
        }
        
        result = self.quiz.update('nonexistent-id', updates)
        
        assert result["success"] is False
        assert result["error"] == "Failed to update quiz or quiz not found"

class TestQuizDelete:
    """Test quiz deletion functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.quiz = Quiz()

    @patch('app.models.quiz.Quiz.find_by_id')
    @patch('app.models.quiz.clear_quiz_dependent_caches')
    def test_delete_quiz_success(self, mock_clear_cache, mock_find_by_id):
        """Test successful quiz deletion."""
        # Mock the supabase instance and cache clear method
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        mock_find_by_id.cache_clear = Mock()
        
        mock_result = Mock()
        mock_result.data = [{'id': 'test-id'}]
        mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.quiz.delete('test-id')
        
        assert result["success"] is True
        assert result["message"] == "Quiz deleted successfully"
        mock_clear_cache.assert_called_once()
        mock_find_by_id.cache_clear.assert_called_once()

    @patch('app.models.quiz.Quiz.find_by_id')
    @patch('app.models.quiz.clear_quiz_dependent_caches')
    def test_delete_quiz_not_found(self, mock_clear_cache, mock_find_by_id):
        """Test quiz deletion when quiz doesn't exist."""
        # Mock the supabase instance and cache clear method
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        mock_find_by_id.cache_clear = Mock()
        
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.quiz.delete('nonexistent-id')
        
        assert result["success"] is False  
        assert result["error"] == "quiz not found OR Failed to delete quiz"
        mock_clear_cache.assert_not_called()
        mock_find_by_id.cache_clear.assert_not_called()

class TestQuizUpdateTotals:
    """Test quiz totals update functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.quiz = Quiz()

    @patch('app.models.quiz.Quiz.find_by_id')
    def test_update_totals_success(self,mock_find_by_id):
        """Test successful totals update."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        self.quiz.find_by_id.cache_clear = Mock()
        mock_find_by_id.cache_clear = Mock()
        
        # Mock questions query
        mock_questions = [
            {'points_weight': 5},
            {'points_weight': 10},
            {'points_weight': 5}
        ]
        
        mock_questions_result = Mock()
        mock_questions_result.data = mock_questions
        
        # Mock quiz update
        mock_updated_quiz = {
            'id': 'test-id',
            'total_questions': 3,
            'total_points': 20
        }
        
        mock_update_result = Mock()
        mock_update_result.data = [mock_updated_quiz]
        
        # Setup the mock chain
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_questions_result
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_result
        
        result = self.quiz.update_totals('test-id')
        
        assert result["success"] is True
        assert result["data"]["total_questions"] == 3
        assert result["data"]["total_points"] == 20
        mock_find_by_id.cache_clear.assert_called_once()
    
class TestQuizHelperMethods:
    """Test quiz helper methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.quiz = Quiz()

    def test_check_title_uniqueness_unique(self):
        """Test title uniqueness check with unique title."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.quiz._check_title_uniqueness("Unique Title")
        
        assert result is True

    def test_check_title_uniqueness_duplicate(self):
        """Test title uniqueness check with duplicate title."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        
        mock_result = Mock()
        mock_result.data = [{'id': 'existing-id', 'title': 'Existing Title'}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.quiz._check_title_uniqueness("Existing Title")
        
        assert result is False

    def test_generate_slug_basic(self):
        """Test basic slug generation."""
        result = self.quiz.generate_slug("Hello World Quiz")
        assert result == "hello-world-quiz"

    def test_generate_slug_special_characters(self):
        """Test slug generation with special characters."""
        result = self.quiz.generate_slug("Python & JavaScript: Advanced!")
        assert result == "python-javascript-advanced"

    def test_generate_slug_with_numbers(self):
        """Test slug generation preserves numbers."""
        result = self.quiz.generate_slug("Quiz 123 Test")
        assert result == "quiz-123-test"

    def test_get_unique_slug_first_attempt(self):
        """Test getting unique slug on first attempt."""
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.quiz._get_unique_slug("Test Title")
        
        assert result == "test-title"

    def test_get_unique_slug_with_collision(self):
        """Test getting unique slug when collision occurs."""
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        
        mock_result = Mock()
        mock_result.data = [{'id': 'existing-id'}]
        mock_result_second = Mock()
        mock_result_second.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [mock_result, mock_result_second]
        
        result = self.quiz._get_unique_slug("Test Title")
        
        assert result == "test-title-2"


class TestQuizPublishedSince:
    """Test published since functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.quiz = Quiz()

    def test_published_since_success(self):
        """Test successful return."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        
        # Create a test datetime
        since_date = datetime(2024, 1, 1, 10, 0, 0)
        
        mock_result = Mock()
        mock_result.data = [
            {'id': '1', 'title': 'Quiz 1', 'status': 'published'},
            {'id': '2', 'title': 'Quiz 2', 'status': 'published'}
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value = mock_result
        
        result = self.quiz.get_quizzes_published_since(since_date)
        
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["status"] == "published"
        assert result["data"][1]["status"] == "published"

    def test_published_since_empty_result(self):
        """Test published since with no results."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.quiz.supabase = mock_supabase
        
        since_date = datetime(2024, 1, 1, 10, 0, 0)
        
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value = mock_result
        
        result = self.quiz.get_quizzes_published_since(since_date)
        
        assert result["success"] is True
        assert len(result["data"]) == 0