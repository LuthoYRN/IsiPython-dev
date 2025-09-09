
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))
from app.models.quiz_progress import UserQuizProgress

class TestQuizProgressGetOrCreateProgress:
    """Test get or create progress functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.progress = UserQuizProgress()

    def test_get_or_create_progress_existing(self):
        """Test getting existing progress record."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        
        # Mock existing progress found
        mock_result = Mock()
        mock_result.data = [{
            'id': 'progress-123',
            'user_id': 'user-456',
            'quiz_id': 'quiz-789',
            'best_score': 85,
            'best_percentage': 85.0,
            'attempts_count': 2,
            'status': 'completed'
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.progress.get_or_create_progress('user-456', 'quiz-789')
        
        assert result["success"] is True
        assert result["data"]["best_score"] == 85
        assert result["data"]["attempts_count"] == 2

    @patch('app.models.quiz_progress.UserQuizProgress.get_quizzes_with_progress')
    @patch('app.models.quiz_progress.UserQuizProgress.get_user_all_progress')
    def test_get_or_create_progress_create_new(self,mock_user_all_progress,mock_quizzes_with_progress):
        """Test creating new progress record when none exists."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        mock_quizzes_with_progress.cache_clear = Mock()
        mock_user_all_progress.cache_clear = Mock()
        # Mock no existing progress found
        mock_select_result = Mock()
        mock_select_result.data = []
        
        # Mock successful creation
        mock_insert_result = Mock()
        mock_insert_result.data = [{
            'id': 'progress-new',
            'user_id': 'user-456',
            'quiz_id': 'quiz-789',
            'best_score': 0,
            'best_percentage': 0.0,
            'attempts_count': 0,
            'status': 'not_started'
        }]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_select_result
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_result
        
        result = self.progress.get_or_create_progress('user-456', 'quiz-789')
        
        assert result["success"] is True
        assert result["data"]["best_score"] == 0
        assert result["data"]["status"] == "not_started"
        mock_user_all_progress.cache_clear.assert_called_once()
        mock_quizzes_with_progress.cache_clear.assert_called_once()
    
    def test_get_or_create_progress_fail(self):
        """Test get_or_create_progress failure to create."""
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        mock_existing = Mock()
        mock_existing.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_existing
        
        mock_insert_result = Mock()
        mock_insert_result.data = []
        
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_result
        
        result = self.progress.get_or_create_progress('user-456', 'quiz-789')
        
        assert result["success"] is False
        assert result["error"] ==  "Failed to create progress record"

    def test_get_or_create_progress_database_error(self):
        """Test get_or_create_progress handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database error")
        
        result = self.progress.get_or_create_progress('user-456', 'quiz-789')
        
        assert result["success"] is False
        assert "Database error" in result["error"]
    
class TestQuizProgressUpdateProgress:
    """Test updating user progress."""

    def setup_method(self):
        """Set up test fixtures."""
        self.progress = UserQuizProgress()

    @patch('app.models.quiz_progress.UserQuizProgress.get_or_create_progress')
    @patch('app.models.quiz_progress.UserQuizProgress.get_quizzes_with_progress')
    @patch('app.models.quiz_progress.UserQuizProgress.get_user_all_progress')
    def test_update_progress_success(self, mock_all_progress, mock_quizzes_progress,mock_get_or_create_progress):
        """Test successful progress update."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase

        # Mock cache clearing
        mock_all_progress.cache_clear = Mock()
        mock_quizzes_progress.cache_clear = Mock()
        mock_get_or_create_progress.return_value = {
            "success":True,
            "data":{
                'id': 'progress-123',
                'user_id': 'user-456',
                'quiz_id': 'quiz-789',
                'best_score': 85,
                'best_percentage': 85.0,
                'attempts_count': 2,
                'status': 'completed',
                'completed_at':'2024-01-15T10:30:00Z'
            }
        }
        mock_result = Mock()
        mock_result.data = [{ 
                'id': 'progress-124',
                'user_id': 'user-456',
                'quiz_id': 'quiz-789',
                'best_score': 85,
                'best_percentage': 85.0,
                'status': 'completed',
                'completed_at':'2024-01-15T10:30:00Z'
            }]
        mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        progress_update = {
            "submission_id": "sub-123",
            "score": 85,
            "percentage": 85.0,
            "status": "completed"
        }

        result = self.progress.update_progress('user-456', 'quiz-789', progress_update)

        assert result["success"] is True
        assert result["data"]["best_score"] == 85
        assert result["data"]["status"] == "completed"
        mock_supabase.table.return_value.update.assert_called_once_with({'attempts_count':3,
                                                                         'last_attempt_at': 'now()',
                                                                         'status': 'completed'})
        mock_all_progress.cache_clear.assert_called_once()
        mock_quizzes_progress.cache_clear.assert_called_once()

    @patch('app.models.quiz_progress.UserQuizProgress.get_or_create_progress')
    @patch('app.models.quiz_progress.UserQuizProgress.get_quizzes_with_progress')
    @patch('app.models.quiz_progress.UserQuizProgress.get_user_all_progress')
    def test_update_progress_success_new_best(self, mock_all_progress, mock_quizzes_progress,mock_get_or_create_progress):
        """Test successful progress update with new best submission."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase

        # Mock cache clearing
        mock_all_progress.cache_clear = Mock()
        mock_quizzes_progress.cache_clear = Mock()
        mock_get_or_create_progress.return_value = {
            "success":True,
            "data":{
                'id': 'progress-123',
                'user_id': 'user-456',
                'quiz_id': 'quiz-789',
                'best_score': 85,
                'best_percentage': 85.0,
                'attempts_count': 3,
                'status': 'completed',
                'completed_at':'2024-01-15T10:30:00Z'
            }
        }
        mock_result = Mock()
        mock_result.data = [{ 
                'id': 'progress-124',
                'user_id': 'user-456',
                'quiz_id': 'quiz-789',
                'best_score': 90,
                'best_percentage': 90.0,
                'status': 'completed',
                'completed_at':'2024-01-16T10:30:00Z'
            }]
        mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        progress_update = {
            "submission_id": "sub-125",
            "score": 90,
            "percentage": 90.0,
            "status": "completed"
        }

        result = self.progress.update_progress('user-456', 'quiz-789', progress_update)

        assert result["success"] is True
        assert result["data"]["best_score"] == 90
        assert result["data"]["status"] == "completed"
        mock_supabase.table.return_value.update.assert_called_once_with({'attempts_count':4,
                                                                          'best_percentage': 90.0,
                                                                          'best_score': 90.0,
                                                                          'best_submission_id': 'sub-125',
                                                                          'completed_at': 'now()',
                                                                          'last_attempt_at': 'now()',
                                                                          'status': 'completed'})
        mock_all_progress.cache_clear.assert_called_once()
        mock_quizzes_progress.cache_clear.assert_called_once()     

    @patch('app.models.quiz_progress.UserQuizProgress.get_or_create_progress')
    def test_update_progress_fail_to_update(self,mock_get_or_create_progress):
        """Test update progress handles failure to update."""
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        mock_get_or_create_progress.return_value = {
            "success":True,
            "data":{
                'id': 'progress-123',
                'user_id': 'user-456',
                'quiz_id': 'quiz-789',
                'best_score': 85,
                'best_percentage': 85.0,
                'attempts_count': 2,
                'status': 'completed',
                'completed_at':'2024-01-15T10:30:00Z'
            }
        }
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        progress_update = {
            "submission_id": "sub-123",
            "score": 85,
            "percentage": 85.0,
            "status": "completed"
        }

        result = self.progress.update_progress('user-456', 'quiz-789', progress_update)

        assert result["success"] is False
        assert result["error"] == "Failed to update progress"

    @patch('app.models.quiz_progress.UserQuizProgress.get_or_create_progress')
    def test_update_progress_database_error(self,mock_get_or_create_progress):
        """Test update progress handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        mock_get_or_create_progress.return_value = {
            "success":True,
            "data":{
                'id': 'progress-123',
                'user_id': 'user-456',
                'quiz_id': 'quiz-789',
                'best_score': 85,
                'best_percentage': 85.0,
                'attempts_count': 2,
                'status': 'completed',
                'completed_at':'2024-01-15T10:30:00Z'
            }
        }
        mock_supabase.table.side_effect = Exception("Database error")

        progress_update = {
            "submission_id": "sub-123",
            "score": 85,
            "percentage": 85.0,
            "status": "completed"
        }

        result = self.progress.update_progress('user-456', 'quiz-789', progress_update)

        assert result["success"] is False
        assert "Database error" in result["error"]
    
    @patch('app.models.quiz_progress.UserQuizProgress.get_or_create_progress')
    def test_update_progress_get_or_create_progress_fail(self,mock_get_or_create_progress):
        """Test update progress when get_or_create progress fails."""
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        mock_get_or_create_progress.return_value = {
            "success":False,
            "error":"user_id not found"
        }
        progress_update = {
            "submission_id": "sub-123",
            "score": 85,
            "percentage": 85.0,
            "status": "completed"
        }

        result = self.progress.update_progress('user-456', 'quiz-789', progress_update)

        assert result["success"] is False
        assert result["error"] == "user_id not found"
    
class TestQuizProgressGetUserProgress:
    """Test getting specific user progress functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.progress = UserQuizProgress()

    def test_get_user_progress_found(self):
        """Test getting user progress when record exists."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        
        # Mock progress found
        mock_result = Mock()
        mock_result.data = [{
            'id': 'progress-123',
            'user_id': 'user-456',
            'quiz_id': 'quiz-789',
            'best_score': 92,
            'best_percentage': 92.0,
            'attempts_count': 3,
            'status': 'completed',
            'completed_at': '2024-01-15T10:30:00Z',
            'last_attempt_at': '2024-01-15T10:30:00Z',
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.progress.get_user_progress('user-456', 'quiz-789')
        
        assert result["success"] is True
        assert result["data"]["best_score"] == 92
        assert result["data"]["attempts_count"] == 3
        assert result["data"]["status"] == "completed"

    def test_get_user_progress_not_found(self):
        """Test getting user progress when no record exists."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        
        # Mock no progress found
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.progress.get_user_progress('user-456', 'quiz-789')
        
        assert result["success"] is True
        assert result["data"]["best_score"] == 0
        assert result["data"]["attempts_count"] == 0
        assert result["data"]["status"] == "not_started"

    def test_get_user_progress_database_error(self):
        """Test get_user_progress handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database connection failed")
        
        result = self.progress.get_user_progress('user-456', 'quiz-789')
        assert result["success"] is False
        assert "Database connection failed" in result["error"]

class TestQuizProgressGetUserAllProgress:
    """Test getting all user progress."""

    def setup_method(self):
        """Set up test fixtures."""
        self.progress = UserQuizProgress()

    def test_get_user_all_progress_success(self):
        """Test successful retrieval of all user progress."""
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase

        mock_result = Mock()
        mock_result.data = [
                {
                    "quiz_id": "quiz-1",
                    "best_score": 85,
                    "best_percentage": 85.0,
                    "attempts_count": 2,
                    "status": "completed",
                    "last_attempt_date": "2024-01-15T10:30:00Z"
                },
                {
                    "quiz_id": "quiz-2",
                    "best_score": 92,
                    "best_percentage": 92.0,
                    "attempts_count": 1,
                    "status": "completed", 
                    "last_attempt_date": "2024-01-16T14:20:00Z"
                }
            ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        result = self.progress.get_user_all_progress('user-123')

        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["attempts_count"] == 2
        assert result["data"][1]["best_percentage"] == 92.0

    def test_get_user_all_progress_empty(self):
        """Test all progress when user has no progress."""
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase

        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        result = self.progress.get_user_all_progress('user-123')

        assert result["success"] is True
        assert result["data"] == []

class TestQuizProgressGetUserProgressSince:
    """Test getting user progress since a date."""

    def setup_method(self):
        """Set up test fixtures."""
        self.progress = UserQuizProgress()

    def test_get_user_progress_since_success(self):
        """Test successful retrieval of progress since date."""
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        mock_result = Mock()
        mock_result.data = [
                {
                    "quiz_id": "quiz-1",
                    "status": "completed",
                    "score": 85,
                    "completion_date": "2024-01-15T10:30:00Z"
                },
                {
                    "quiz_id": "quiz-2", 
                    "status": "completed",
                    "score": 92,
                    "completion_date": "2024-01-16T14:20:00Z"
                }
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value = mock_result

        since_date = datetime(2024, 1, 10)
        result = self.progress.get_user_progress_since('user-123', since_date)

        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["status"] == "completed"
 
    def test_get_user_progress_since_no_recent_progress(self):
        """Test progress since date when no recent progress.""" 
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value = mock_result

        since_date = datetime(2024, 1, 20)
        result = self.progress.get_user_progress_since('user-123', since_date)

        assert result["success"] is True
        assert result["data"] == []

class TestQuizProgressGetQuizzesWithProgress:
    """Test getting quizzes with user progress."""

    def setup_method(self):
        """Set up test fixtures."""
        self.progress = UserQuizProgress()

    def test_get_quizzes_with_progress_success_with_user_id(self):
        """Test successful retrieval of quizzes with progress."""
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        mock_quizzes = Mock()
        mock_progress = Mock()
        mock_quizzes.data =  [
                {
                    "id": "quiz-1",
                    "title": "Python Basics",
                    "total_points": 100
                },
                {
                    "id": "quiz-2", 
                    "title": "Advanced Python",
                    "total_points": 150
                }
            ]
        mock_progress.data =  [
                {
                    "quiz_id": "quiz-1",
                    "best_score": 85,
                    "best_percentage": 85.0,
                    "attempts_count": 2,
                    "status": "completed"
                }
            ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_quizzes
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_progress

        result = self.progress.get_quizzes_with_progress('user-123')

        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["user_progress"]["best_score"] == 85
        assert result["data"][0]["user_progress"]["status"] == "completed"
        assert result["data"][1]["user_progress"]["status"] == "not_started"
    
    def test_get_quizzes_with_progress_success_no_user_id(self):
        """Test successful retrieval of quizzes with no user progress."""
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        mock_quizzes = Mock()
        mock_quizzes.data =  [
                {
                    "id": "quiz-1",
                    "title": "Python Basics",
                    "total_points": 100
                },
                {
                    "id": "quiz-2", 
                    "title": "Advanced Python",
                    "total_points": 150
                }
            ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_quizzes

        result = self.progress.get_quizzes_with_progress()

        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["id"] == "quiz-1"
        assert "user_progress" not in result["data"][0]

    def test_get_quizzes_with_progress_no_quizzes(self):
        """Test quizzes with progress when no quizzes exist."""
        # Mock empty response
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        mock_quizzes = Mock()
        mock_quizzes.data =  []
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_quizzes
       
        result = self.progress.get_quizzes_with_progress('user-123')

        assert result["success"] is True
        assert result["data"] == []
    
    def test_get_quizzes_with_progress_with_default_progress(self):
        """Test successful retrieval of quizzes with default progress when there is no user progress."""
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        mock_quizzes = Mock()
        mock_progress = Mock()
        mock_quizzes.data =  [
                {
                    "id": "quiz-1",
                    "title": "Python Basics",
                    "total_points": 100
                },
                {
                    "id": "quiz-2", 
                    "title": "Advanced Python",
                    "total_points": 150
                }
            ]
        mock_progress.data =  []
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_quizzes
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_progress

        result = self.progress.get_quizzes_with_progress('user-123')

        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["user_progress"]["best_score"] == 0
        assert result["data"][0]["user_progress"]["status"] == "not_started"
        assert result["data"][1]["user_progress"]["status"] == "not_started"

class TestQuizProgressGetUserDashboardStats:
    """Test getting user dashboard statistics."""

    def setup_method(self):
        """Set up test fixtures."""
        self.progress = UserQuizProgress()

    @patch('app.models.quiz_progress.UserQuizProgress.get_user_all_progress')
    def test_get_user_dashboard_stats_success(self, mock_all_progress):
        mock_all_progress.return_value = {
            "success":True,
            "data":[
                {
                    "quiz_id": "quiz-1",
                    "best_score": 85,
                    "best_percentage": 85.0,
                    "attempts_count": 2,
                    "status": "completed",
                    "last_attempt_date": "2024-01-15T10:30:00Z"
                },
                {
                    "quiz_id": "quiz-2",
                    "best_score": 92,
                    "best_percentage": 92.0,
                    "attempts_count": 1,
                    "status": "completed", 
                    "last_attempt_date": "2024-01-16T14:20:00Z"
                }]
        }
        result = self.progress.get_user_dashboard_stats('user-123')
        assert result["success"] is True
        assert result["data"]["completed_quizzes"] == 2
        assert result["data"]["average_score"] == 88.5
    
    @patch('app.models.quiz_progress.UserQuizProgress.get_user_all_progress')
    def test_get_user_dashboard_stats_no_progress(self, mock_all_progress):
        """Test dashboard stats for user with no progress."""
        mock_all_progress.return_value = {
            "success":True,
            "data":[]
        }
        result = self.progress.get_user_dashboard_stats('user-123')
        assert result["success"] is True
        assert result["data"]["completed_quizzes"] == 0
        assert result["data"]["average_score"] == 0
    
    @patch('app.models.quiz_progress.UserQuizProgress.get_user_all_progress')
    def test_get_user_dashboard_stats_error(self, mock_all_progress):
        """Test dashboard stats error handling."""
        mock_all_progress.return_value = {
          "success": False,
           "error": "Database connection failed"
        }
        result = self.progress.get_user_dashboard_stats('user-123')
        assert result["success"] is False
        assert "Database connection failed" in result["error"]

class TestQuizProgressGetLeaderboard:
    """Test getting leaderboard functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.progress = UserQuizProgress()

    def test_get_leaderboard_quiz_specific(self):
        """Test leaderboard for specific quiz."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase

        # Mock quiz-specific leaderboard data
        mock_progress_result = Mock()
        mock_progress_result.data = [
            {
                'user_id': 'user-1',
                'profiles':{
                    'first_name': 'John',
                    'last_name': 'Doe',
                },
                'best_score': 95,
                'best_percentage': 95.0,
                'attempts_count': 1,
                'completed_at':"2024-01-15T10:30:00Z"
            },
            {
                'user_id': 'user-2', 
                'profiles':{
                    'first_name': 'Jane', 
                    'last_name': 'Smith'
                },
                'best_score': 88,
                'best_percentage': 88.0,
                'attempts_count': 2,
                'completed_at':"2024-01-15T10:30:00Z"
            }
        ]

        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.order.return_value.limit.return_value.execute.return_value = mock_progress_result

        result = self.progress.get_leaderboard('quiz-123', limit=10)

        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["rank"] == 1
        assert result["data"][0]["best_percentage"] == 95
        assert result["data"][0]["full_name"] == "John Doe"

    @patch('app.models.quiz_progress.UserQuizProgress.get_global_leaderboard')
    def test_get_leaderboard_global(self,mock_get_global_leaderboard):
        """Test global leaderboard."""

        # Mock global leaderboard RPC response
        mock_get_global_leaderboard.return_value ={
            "success":True,
            "data":[
                {
                    'user_id': 'user-1',
                    'full_name': 'John Doe',
                    'average_score': 90.5,
                    'quiz_count': 5,
                    'total_points': 452
                },
                {
                    'user_id': 'user-2',
                    'full_name': 'Jane Smith', 
                    'average_score': 85.2,
                    'quiz_count': 4,
                    'total_points': 341
                }
            ]
        } 

        result = self.progress.get_leaderboard()

        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["average_score"] == 90.5

    def test_get_leaderboard_no_progress(self):
        """Test leaderboard with empty progress."""
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        mock_progress_result = Mock()
        mock_progress_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.order.return_value.limit.return_value.execute.return_value = mock_progress_result


        result = self.progress.get_leaderboard('quiz-123')

        assert result["success"] is True
        assert result["data"] == []

    def test_get_leaderboard_database_error(self):
        """Test leaderboard handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database error")

        result = self.progress.get_leaderboard('quiz-123')

        assert result["success"] is False
        assert "Database error" in result["error"]

class TestQuizProgressGetGlobalLeaderboard:
    """Test getting global leaderboard functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.progress = UserQuizProgress()

    def test_get_global_leaderboard_success(self):
        """Test successful global leaderboard retrieval."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase

        # Mock RPC response
        mock_rpc_result = Mock()
        mock_rpc_result.data = [
            {
                'user_id': 'user-1',
                'full_name': 'Alice Johnson',
                'average_score': 92.5,
                'quiz_count': 8,
            },
            {
                'user_id': 'user-2',
                'full_name': 'Bob Wilson',
                'average_score': 87.3,
                'quiz_count': 6,
            }
        ]
        mock_supabase.rpc.return_value.execute.return_value = mock_rpc_result

        result = self.progress.get_global_leaderboard(limit=25)

        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["average_score"] == 92.5
        mock_supabase.rpc.assert_called_with('get_global_quiz_leaderboard', {'limit_count': 25})

    def test_get_global_leaderboard_rpc_error(self):
        """Test global leaderboard handles RPC errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.progress.supabase = mock_supabase
        mock_supabase.rpc.side_effect = Exception("RPC function not found")

        result = self.progress.get_global_leaderboard()

        assert result["success"] is False
        assert "RPC function not found" in result["error"]

class TestQuizProgressGetUserGlobalRank:
    """Test getting user's global rank."""

    def setup_method(self):
        """Set up test fixtures."""
        self.progress = UserQuizProgress()

    @patch('app.models.quiz_progress.UserQuizProgress.get_global_leaderboard')
    def test_get_user_global_rank_found(self, mock_global_leaderboard):
        """Test user global rank when user is found."""
        # Mock global leaderboard
        mock_global_leaderboard.return_value = {
            "success": True,
            "data": [
                {
                    'user_id': 'user-1',
                    'full_name': 'Alice Johnson',
                    'average_score': 92.5
                },
                {
                    'user_id': 'user-123',  # Target user
                    'full_name': 'John Doe',
                    'average_score': 88.2
                },
                {
                    'user_id': 'user-3',
                    'full_name': 'Bob Wilson', 
                    'average_score': 85.7
                }
            ]
        }

        result = self.progress.get_user_global_rank('user-123')

        assert result["success"] is True
        assert result["data"]["rank"] == 2  # Second place
        assert result["data"]["total_users"] == 3
        assert result["data"]["user_stats"]["full_name"] == "John Doe"
        assert result["data"]["user_stats"]["average_score"] == 88.2

    @patch('app.models.quiz_progress.UserQuizProgress.get_global_leaderboard')
    def test_get_user_global_rank_not_found(self, mock_global_leaderboard):
        """Test user global rank when user is not found."""
        # Mock global leaderboard without target user
        mock_global_leaderboard.return_value = {
            "success": True,
            "data": [
                {
                    'user_id': 'user-1',
                    'full_name': 'Alice Johnson',
                    'average_score': 92.5
                },
                {
                    'user_id': 'user-2',
                    'full_name': 'Bob Wilson',
                    'average_score': 85.7
                }
            ]
        }

        result = self.progress.get_user_global_rank('user-999')

        assert result["success"] is True
        assert result["data"]["rank"] is None
        assert result["data"]["total_users"] == 2
   
    @patch('app.models.quiz_progress.UserQuizProgress.get_global_leaderboard')
    def test_get_user_global_rank_leaderboard_error(self, mock_global_leaderboard):
        """Test user global rank when leaderboard fails."""
        # Mock leaderboard error
        mock_global_leaderboard.return_value = {
            "success": False,
            "error": "Database connection failed"
        }

        result = self.progress.get_user_global_rank('user-123')

        assert result["success"] is False
        assert "Database connection failed" in result["error"]