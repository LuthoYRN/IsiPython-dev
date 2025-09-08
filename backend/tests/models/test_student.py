import pytest
import sys
from pathlib import Path
from unittest.mock import Mock
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))
from app.models.student import Student

class TestStudentGetStudentCount:
    """Test getting total student count."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.student = Student()

    def test_get_student_count_success(self):
        """Test successful retrieval of student count."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.student.supabase = mock_supabase
        
        # Mock successful count query
        mock_result = Mock()
        mock_result.count = 150
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_result
        
        result = self.student.get_student_count()
        
        assert result["success"] is True
        assert result["count"] == 150
    
    def test_get_student_count_none_result(self):
        """Test retrieval when count is None."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.student.supabase = mock_supabase
        
        # Mock result with None count
        mock_result = Mock()
        mock_result.count = None
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_result
        
        result = self.student.get_student_count()
        
        assert result["success"] is True
        assert result["count"] == 0
    
    def test_get_student_count_database_error(self):
        """Test handling database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.student.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database connection failed")
        
        result = self.student.get_student_count()
        
        assert result["success"] is False
        assert "Database connection failed" in result["error"]

class TestStudentGetStudentsAddedSince:
    """Test getting students added since a specific date."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.student = Student()

    def test_get_students_added_since_success(self):
        """Test successful retrieval of students added since date."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.student.supabase = mock_supabase
        
        # Mock successful count query
        mock_result = Mock()
        mock_result.count = 25
        mock_supabase.table.return_value.select.return_value.gte.return_value.execute.return_value = mock_result
        
        since_date = datetime(2024, 1, 1, 12, 0, 0)
        result = self.student.get_students_added_since(since_date)
        
        assert result["success"] is True
        assert result["count"] == 25
        mock_supabase.table.return_value.select.return_value.gte.assert_called_with(
            'created_at', since_date.isoformat()
        )

    def test_get_students_added_since_none_result(self):
        """Test retrieval when count is None."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.student.supabase = mock_supabase
        
        # Mock result with None count
        mock_result = Mock()
        mock_result.count = None
        mock_supabase.table.return_value.select.return_value.gte.return_value.execute.return_value = mock_result
        
        since_date = datetime(2024, 1, 1)
        result = self.student.get_students_added_since(since_date)
        
        assert result["success"] is True
        assert result["count"] == 0
    
    def test_get_students_added_since_database_error(self):
        """Test handling database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.student.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database timeout")
        
        since_date = datetime(2024, 1, 1)
        result = self.student.get_students_added_since(since_date)
        
        assert result["success"] is False
        assert "Database timeout" in result["error"]

class TestStudentDelete:
    """Test student deletion functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.student = Student()

    def test_delete_student_success(self):
        """Test successful student deletion."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.student.supabase = mock_supabase
        
        # Mock successful deletion
        mock_result = Mock()
        mock_result.data = [{'id': 'user-123'}] 
        mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.student.delete('user-123')
        
        assert result["success"] is True
        assert result["message"] == "Student deleted successfully"
  
    def test_delete_student_database_error(self):
        """Test handling database errors during deletion."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.student.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Foreign key constraint violation")
        
        result = self.student.delete('user-123')
        
        assert result["success"] is False
        assert "Foreign key constraint violation" in result["error"]