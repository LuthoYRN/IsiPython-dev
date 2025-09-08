import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.append(str(Path(__file__).parent.parent.parent))
from app.models.saved_code import SavedCode

class TestSavedCodeValidation:
    """Test saved code data validation."""

    def test_validate_data_valid_input(self):
        """Test validation with valid title and code."""
        errors = SavedCode.validate_data("my_program.isi", "ukuba x == 5:")
        assert errors == {}

    def test_validate_data_missing_title(self):
        """Test validation fails when title is missing."""
        errors = SavedCode.validate_data("", "ukuba x == 5:")
        assert 'title' in errors
        assert errors['title'] == "Title is required"

    def test_validate_data_whitespace_title(self):
        """Test validation fails when title is only whitespace."""
        errors = SavedCode.validate_data("   ", "ukuba x == 5:")
        assert 'title' in errors
        assert errors['title'] == "Title is required"
    
    def test_validate_data_missing_isi_extension(self):
        """Test validation fails when title doesn't end with .isi."""
        errors = SavedCode.validate_data("my_program.py", "ukuba x == 5:")
        assert 'title' in errors
        assert errors['title'] == "Title must end with .isi extension"

    def test_validate_data_title_too_long(self):
        """Test validation fails when title is too long."""
        long_title = "a" * 252 + ".isi"  # 256 characters total
        errors = SavedCode.validate_data(long_title, "ukuba x == 5:")
        assert 'title' in errors
        assert errors['title'] == "Title must be 255 characters or less"
    
    def test_validate_data_title_only_extension(self):
        """Test validation fails when title is only .isi."""
        errors = SavedCode.validate_data(".isi", "ukuba x == 5:")
        assert 'title' in errors
        assert errors['title'] == "Title must have a name before .isi extension"
    
    def test_validate_data_missing_code(self):
        """Test validation fails when code is missing."""
        errors = SavedCode.validate_data("my_program.isi", "")
        assert 'code' in errors
        assert errors['code'] == "Code is required"

    def test_validate_data_whitespace_code(self):
        """Test validation fails when code is only whitespace."""
        errors = SavedCode.validate_data("my_program.isi", "   \n  \t  ")
        assert 'code' in errors
        assert errors['code'] == "Code is required"
    
    def test_validate_data_multiple_errors(self):
        """Test validation returns multiple errors."""
        errors = SavedCode.validate_data("", "")
        assert 'title' in errors
        assert 'code' in errors
        assert len(errors) == 2
    
    def test_validate_data_case_insensitive_extension(self):
        """Test validation accepts .isi extension in different cases."""
        errors1 = SavedCode.validate_data("program.ISI", "code")
        errors2 = SavedCode.validate_data("program.Isi", "code")
        assert errors1 == {}
        assert errors2 == {}
    
    def test_title_edge_cases(self):
        """Test various title edge cases."""
        # Test exactly at length limit
        title_255 = "a" * 251 + ".isi"  # Exactly 255 characters
        errors = SavedCode.validate_data(title_255, "code")
        assert errors == {}
        
        # Test one character over limit
        title_256 = "a" * 252 + ".isi"  # 256 characters
        errors = SavedCode.validate_data(title_256, "code")
        assert 'title' in errors

    def test_title_with_symbols(self):
        """Test titles with unicode characters."""
        unicode_title = "my_@_''name_.isi"  # Korean characters
        errors = SavedCode.validate_data(unicode_title, "print('hello')")
        assert errors == {}

class TestSavedCodeCreate:
    """Test saved code creation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.saved_code = SavedCode()

    @patch('app.models.saved_code.SavedCode._get_unique_title')
    def test_create_success(self, mock_get_unique_title):
        """Test successful code creation."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        # Mock unique title generation
        mock_get_unique_title.return_value = "my_program.isi"
        
        # Mock successful insertion
        mock_result = Mock()
        mock_result.data = [{
            'id': 'code-123',
            'title': 'my_program.isi',
            'code': 'ukuba x == 5:\n    print("Hello")',
            'user_id': 'user-456'
        }]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
        
        result = self.saved_code.create("my_program.isi", "ukuba x == 5:\n    print(\"Hello\")", "user-456")
        
        assert result["success"] is True
        assert result["data"]["id"] == "code-123"
        assert result["data"]["title"] == "my_program.isi"
        mock_get_unique_title.assert_called_once_with("my_program.isi", "user-456")
    
    def test_create_validation_errors(self):
        """Test creation fails with validation errors."""
        result = self.saved_code.create("", "", "user-456")
        
        assert result["success"] is False
        assert "errors" in result
        assert "title" in result["errors"]
        assert "code" in result["errors"]

    @patch('app.models.saved_code.SavedCode._get_unique_title')
    def test_create_database_failure(self, mock_get_unique_title):
        """Test creation handles database failures."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        mock_get_unique_title.return_value = "my_program.isi"
        
        # Mock database failure
        mock_result = Mock()
        mock_result.data = None
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
        
        result = self.saved_code.create("my_program.isi", "ukuba x == 5:", "user-456")
        
        assert result["success"] is False
        assert result["error"] == "Failed to save code"

class TestSavedCodeGetUniqueTitle:
    """Test unique title generation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.saved_code = SavedCode()

    def test_get_unique_title_no_existing_files(self):
        """Test unique title when no files exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        # Mock no existing files
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        title = self.saved_code._get_unique_title("my_program.isi", "user-456")
        
        assert title == "my_program.isi"

    def test_get_unique_title_with_existing_file(self):
        """Test unique title when file already exists."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        # Mock existing file
        mock_result = Mock()
        mock_result.data = [{'title': 'my_program.isi'}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        title = self.saved_code._get_unique_title("my_program.isi", "user-456")
        
        assert title == "my_program(1).isi"
    
    def test_get_unique_title_with_multiple_existing_files(self):
        """Test unique title with multiple existing numbered files."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        # Mock multiple existing files
        mock_result = Mock()
        mock_result.data = [
            {'title': 'my_program.isi'},
            {'title': 'my_program(1).isi'},
            {'title': 'my_program(2).isi'}
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        title = self.saved_code._get_unique_title("my_program.isi", "user-456")
        
        assert title == "my_program(3).isi"
    
    def test_get_unique_title_removes_existing_number(self):
        """Test unique title removes existing number from input."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        # Mock existing file with base name
        mock_result = Mock()
        mock_result.data = [{'title': 'my_program.isi'}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        # Input already has a number that should be removed
        title = self.saved_code._get_unique_title("my_program(5).isi", "user-456")
        
        assert title == "my_program(1).isi"
    
    def test_get_unique_title_with_different_existing_file(self):
        """Test unique title if user has existing file with different title."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        # Mock existing file
        mock_result = Mock()
        mock_result.data = [
            {'title': 'other_file.isi'}  # Different file
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        title = self.saved_code._get_unique_title("my_program.isi", "user-456")
        
        assert title == "my_program.isi"  
    
    def test_get_unique_title_gaps_in_numbering(self):
        """Test unique title finds next number even with gaps."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        # Mock existing files with gaps in numbering
        mock_result = Mock()
        mock_result.data = [
            {'title': 'my_program.isi'},
            {'title': 'my_program(1).isi'},
            {'title': 'my_program(5).isi'},  # Gap in numbering
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        title = self.saved_code._get_unique_title("my_program.isi", "user-456")
        
        assert title == "my_program(6).isi" 

class TestSavedCodeFindByUser:
    """Test finding saved code by user."""

    def setup_method(self):
        """Set up test fixtures."""
        self.saved_code = SavedCode()

    def test_find_by_user_success(self):
        """Test successful retrieval of user's saved code."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        # Mock successful query
        mock_result = Mock()
        mock_result.data = [
            {
                'id': 'code-1',
                'title': 'program1.isi',
                'code': 'ukuba x == 5:',
                'user_id': 'user-456'
            },
            {
                'id': 'code-2',
                'title': 'program2.isi',
                'code': 'ukuba y = 10',
                'user_id': 'user-456'
            }
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_result
        
        result = self.saved_code.find_by_user("user-456")
        
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["title"] == "program1.isi"
    
    def test_find_by_user_empty_result(self):
        """Test find_by_user when user has no saved code."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        # Mock empty result
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_result
        
        result = self.saved_code.find_by_user("user-456")
        
        assert result["success"] is True
        assert result["data"] == []
    
    def test_find_by_user_database_error(self):
        """Test find_by_user handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database error")
        
        result = self.saved_code.find_by_user("user-456")
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
class TestSavedCodeFindById:
    """Test finding saved code by ID."""

    def setup_method(self):
        """Set up test fixtures."""
        self.saved_code = SavedCode()

    def test_find_by_id_success_with_user_filter(self):
        """Test successful retrieval by ID with user filter."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        # Mock successful query
        mock_result = Mock()
        mock_result.data = [{
            'id': 'code-123',
            'title': 'my_program.isi',
            'code': 'ukuba x == 5:',
            'user_id': 'user-456'
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.saved_code.find_by_id("code-123", "user-456")
        
        assert result["success"] is True
        assert result["data"]["id"] == "code-123"
        mock_supabase.table.return_value.select.return_value.eq.assert_called_once_with('id','code-123')
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.assert_called_once_with('user_id','user-456')
    
    def test_find_by_id_success_without_user_filter(self):
        """Test successful retrieval by ID without user filter."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        # Mock successful query
        mock_result = Mock()
        mock_result.data = [{
            'id': 'code-123',
            'title': 'my_program.isi',
            'code': 'ukuba x == 5:',
            'user_id': 'user-456'
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.saved_code.find_by_id("code-123")
        
        assert result["success"] is True
        assert result["data"]["id"] == "code-123"
        mock_supabase.table.return_value.select.return_value.eq.assert_called_once_with('id','code-123')
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.assert_not_called()

    def test_find_by_id_not_found(self):
        """Test find_by_id when code doesn't exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        # Mock empty result
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.saved_code.find_by_id("nonexistent-id")
        
        assert result["success"] is False
        assert result["error"] == "Code not found or access denied"
    
    def test_find_by_id_database_error(self):
        """Test find_by_id handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database error")
        
        result = self.saved_code.find_by_id("code-123")
        
        assert result["success"] is False
        assert "Database error" in result["error"]

class TestSavedCodeUpdate:
    """Test saved code update functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.saved_code = SavedCode()

    @patch('app.models.saved_code.SavedCode._get_unique_title')
    def test_update_success_with_title_change(self, mock_get_unique_title):
        """Test successful update with title change."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        # Mock unique title generation
        mock_get_unique_title.return_value = "new_program(1).isi"
        
        # Mock current file query
        mock_current_result = Mock()
        mock_current_result.data = [{'title': 'old_program.isi'}]
        
        # Mock update query
        mock_update_result = Mock()
        mock_update_result.data = [{
            'id': 'code-123',
            'title': 'new_program(1).isi',
            'code': 'updated code',
            'user_id': 'user-456'
        }]
        
        # Set up mock chain
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_current_result
        mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_update_result
        
        result = self.saved_code.update("code-123", "user-456", title="new_program.isi", code="updated code")
        
        assert result["success"] is True
        assert result["data"]["title"] == "new_program(1).isi"
        mock_get_unique_title.assert_called_once_with("new_program.isi", "user-456")
    
    @patch('app.models.saved_code.SavedCode._get_unique_title')
    def test_update_success_without_title_change(self, mock_get_unique_title):
        """Test successful update without title change."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        # Mock current file query - same title
        mock_current_result = Mock()
        mock_current_result.data = [{'title': 'my_program.isi'}]
        
        # Mock update query
        mock_update_result = Mock()
        mock_update_result.data = [{
            'id': 'code-123',
            'title': 'my_program.isi',
            'code': 'updated code',
            'user_id': 'user-456'
        }]
        
        # Set up mock chain
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_current_result
        mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_update_result
        
        result = self.saved_code.update("code-123", "user-456", title="my_program.isi", code="updated code")
        
        assert result["success"] is True
        assert result["data"]["code"] == "updated code"
        mock_get_unique_title.assert_not_called()
    
    @patch('app.models.saved_code.SavedCode._get_unique_title')
    def test_update_success_with_code_only(self, mock_get_unique_title):
        """Test successful update with only code change."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        mock_current_result = Mock()
        mock_current_result.data = [{'title': 'my_program.isi'}]
        
        # Mock update query
        mock_update_result = Mock()
        mock_update_result.data = [{
            'id': 'code-123',
            'title': 'my_program.isi',
            'code': 'updated code',
            'user_id': 'user-456'
        }]
        
        # Set up mock chain
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_current_result
        mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_update_result
        
        result = self.saved_code.update("code-123", "user-456", code="updated code")
        
        assert result["success"] is True
        assert result["data"]["code"] == "updated code"
        mock_get_unique_title.assert_not_called()
    
    @patch('app.models.saved_code.SavedCode._get_unique_title')
    def test_update_success_with_title_only(self, mock_get_unique_title):
        """Test successful update with only title change."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        mock_current_result = Mock()
        mock_current_result.data = [{'title': 'my_program.isi'}]
        
        mock_get_unique_title.return_value = "updated.isi"
        # Mock update query
        mock_update_result = Mock()
        mock_update_result.data = [{
            'id': 'code-123',
            'title': 'updated.isi',
            'code': 'updated code',
            'user_id': 'user-456'
        }]
        
        # Set up mock chain
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_current_result
        mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_update_result
        
        result = self.saved_code.update("code-123", "user-456", title="updated.isi")
        
        assert result["success"] is True
        assert result["data"]["title"] == "updated.isi"
        mock_get_unique_title.assert_called_once()
        
    def test_update_no_valid_fields(self):
        """Test update with no valid fields."""
        result = self.saved_code.update("code-123", "user-456", invalid_field="value")
        
        assert result["success"] is False
        assert result["error"] == "No valid fields to update"

    def test_update_validation_errors(self):
        """Test update fails with validation errors."""
        result = self.saved_code.update("code-123", "user-456", title="", code="")
        
        assert result["success"] is False
        assert "errors" in result

    def test_update_file_not_found(self):
        """Test update when file doesn't exist or access denied."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        # Mock file not found
        mock_current_result = Mock()
        mock_current_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_current_result
        
        result = self.saved_code.update("code-123", "user-456", title="new_title.isi")
        
        assert result["success"] is False
        assert result["error"] == "File not found or access denied"

    @patch('app.models.saved_code.SavedCode._get_unique_title')
    def test_update_database_failure(self, mock_unique_title):
        """Test update handles database failures."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        # Mock current file exists
        mock_current_result = Mock()
        mock_current_result.data = [{'title': 'old_title.isi'}]
        
        # Mock update failure
        mock_update_result = Mock()
        mock_update_result.data = []
        mock_unique_title.return_value = "new_title.isi"
        
        # Set up mock chain
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_current_result
        mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_update_result
        
        result = self.saved_code.update("code-123", "user-456", title="new_title.isi")
        
        assert result["success"] is False
        assert result["error"] == "Failed to update or access denied"

class TestSavedCodeDelete:
    """Test saved code deletion functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.saved_code = SavedCode()

    def test_delete_success(self):
        """Test successful deletion."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        
        # Mock successful deletion
        mock_result = Mock()
        mock_result.data = [{'id': 'code-123'}]
        mock_supabase.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.saved_code.delete("code-123", "user-456")
        
        assert result["success"] is True
        assert result["message"] == "Code deleted successfully"

    def test_delete_database_error(self):
        """Test deletion handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.saved_code.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database error")
        
        result = self.saved_code.delete("code-123", "user-456")
        
        assert result["success"] is False
        assert "Database error" in result["error"]