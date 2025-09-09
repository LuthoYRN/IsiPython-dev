import pytest
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch
import json

sys.path.append(str(Path(__file__).parent.parent.parent))
from app.models.challenge_submission import ChallengeSubmission

class TestChallengeSubmissionCreate:
    """Test challenge submission creation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.submission = ChallengeSubmission()
    
    def test_create_success(self):
        """Test successful submission creation."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase

        mock_submission_result = Mock()
        mock_submission_result.data = [{
            'id': 'submission-123',
            'challenge_id': 'challenge-456',
            'user_id': 'user-789',
            'code': "print('hello world')",
            'status': 'pending',
            'score': 0,
            'tests_passed': 0,
            'tests_total': 0
        }]

        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_submission_result

        result = self.submission.create('challenge-456', 'user-789', "print('hello world')")

        assert result["success"] is True
        assert result["data"]["id"] == "submission-123"
        assert result["data"]["code"] == "print('hello world')"
        assert result["data"]["status"] == "pending"
        assert result["data"]["tests_passed"] == 0
        assert result["data"]["tests_total"] == 0
    
    def test_create_failure(self):
        """Test creation when insertion fails."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Mock challenge not found
        mock_submission_result = Mock()
        mock_submission_result.data = []
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_submission_result

        code = "print('hello world')"
        result = self.submission.create('nonexistent-challenge', 'user-789', code)
        
        assert result["success"] is False
        assert result["error"] == "Failed to create submission"
      
    def test_create_database_error(self):
        """Test creation handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database error")
        
        code = "print('hello world')"
        result = self.submission.create('challenge-456', 'user-789', code)
        
        assert result["success"] is False
        assert "Database error" in result["error"]

class TestChallengeSubmissionUpdateResults:
    """Test updating submission results functionality."""
    def setup_method(self):
        """Set up test fixtures."""
        self.submission = ChallengeSubmission()
    
    @patch('app.models.challenge_submission.ChallengeSubmission.get_batch_challenge_statistics_rpc')
    @patch('app.models.challenge_submission.ChallengeSubmission.find_by_user')
    @patch('app.models.challenge_submission.ChallengeSubmission.find_by_user_and_challenge')
    @patch('app.models.challenge_submission.ChallengeSubmission.get_user_challenge_summary')
    def test_update_results_success(self,mock_user_challenge_summary, mock_find_by_user_challenge, mock_find_by_user, mock_batch_challenge_statistics_rpc):
        """Test successful results update."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        mock_find_by_user.cache_clear = Mock()
        mock_batch_challenge_statistics_rpc.cache_clear = Mock()
        mock_find_by_user_challenge.cache_clear = Mock()
        mock_user_challenge_summary.cache_clear = Mock()

        # Mock successful update
        scoring_result = {
            'score': 85,
            'tests_passed': 17,
            'tests_total': 20,
        }
        
        mock_result = Mock()
        mock_result.data = [{
            'id': 'submission-123',
            'score': 85,
            'percentage': 85.0,
            'tests_passed': 17,
            'tests_total': 20,
            'status': 'in_progress'
        }]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.submission.update_results('submission-123', scoring_result)
        
        assert result["success"] is True
        assert result["data"]["score"] == 85
        assert result["data"]["status"] == "in_progress"
        mock_batch_challenge_statistics_rpc.cache_clear.assert_called_once()
        mock_user_challenge_summary.cache_clear.assert_called_once()
        mock_find_by_user.cache_clear.assert_called_once()
        mock_find_by_user_challenge.cache_clear.assert_called_once()
    
    def test_update_results_failure(self):
        """Test update when submission fails."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Mock no submission found
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result
        
        scoring_result = {'score': 85}
        result = self.submission.update_results('nonexistent-id', scoring_result)
        
        assert result["success"] is False
        assert result["error"] == "Failed to update submission results"
    
    
    def test_update_results_database_error(self):
        """Test update handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database error")
        
        scoring_result = {'score': 85}
        result = self.submission.update_results('submission-123', scoring_result)
        
        assert result["success"] is False
        assert "Database error" in result["error"]

class TestChallengeSubmissionGetBestSubmission:
    """Test getting best submission functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.submission = ChallengeSubmission()

    def test_get_best_submission_success(self):
        """Test successful retrieval of best submission."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Mock successful query
        mock_result = Mock()
        mock_result.data = [{
            'id': 'submission-123',
            'score': 95,
            'status': 'in_progress',
            'submitted_at': '2024-01-15T10:30:00Z'
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
        
        result = self.submission.get_best_submission('user-789', 'challenge-456')
        
        assert result["success"] is True
        assert result["data"]["score"] == 95

    def test_get_best_submission_none_found(self):
        """Test get_best_submission when no submissions exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Mock no submissions found
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
        
        result = self.submission.get_best_submission('user-789', 'challenge-456')
        
        assert result["success"] is False
        assert result["error"] == "No submissions found"
    
    def test_get_best_submission_database_error(self):
        """Test get_best_submission handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database error")
        
        result = self.submission.get_best_submission('user-789', 'challenge-456')
        
        assert result["success"] is False
        assert "Database error" in result["error"]

class TestChallengeSubmissionFindByUser:
    """Test finding submissions by user."""

    def setup_method(self):
        """Set up test fixtures."""
        self.submission = ChallengeSubmission()

    def test_find_by_user_success(self):
        """Test successful retrieval of user submissions."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_result = Mock()
        mock_result.data = [
                {
                    'id': 'sub-1',
                    'challenge_id': 'challenge-1',
                    'score': 85,
                    'submitted_at': '2024-01-15T10:30:00Z'
                },
                {
                    'id': 'sub-2',
                    'challenge_id': 'challenge-2',
                    'score': 92,
                    'submitted_at': '2024-01-16T14:20:00Z'
                }
            ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
        result = self.submission.find_by_user('user-789')
        
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["score"] == 85
    
    def test_find_by_user_empty(self):
        """Test find_by_user when user has no submissions."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
        result = self.submission.find_by_user('user-789')
        
        assert result["success"] is True
        assert result["data"] == []

class TestChallengeSubmissionFindByChallenge:
    """Test finding submissions by challenge."""

    def setup_method(self):
        """Set up test fixtures."""
        self.submission = ChallengeSubmission()

    def test_find_by_challenge_success(self):
        """Test successful retrieval of user submissions."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_result = Mock()
        mock_result.data = [
                {
                    'id': 'sub-1',
                    'challenge_id': 'challenge-1',
                    'score': 85,
                    'submitted_at': '2024-01-15T10:30:00Z'
                },
                {
                    'id': 'sub-2',
                    'challenge_id': 'challenge-1',
                    'score': 92,
                    'submitted_at': '2024-01-16T14:20:00Z'
                }
            ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
        result = self.submission.find_by_challenge('challenge-1')
        
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["challenge_id"] == "challenge-1"
    
    def test_find_by_challenge_empty(self):
        """Test find_by_challenge when challenge has no submissions."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
        result = self.submission.find_by_challenge('challenge-1')
        
        assert result["success"] is True
        assert result["data"] == []

class TestChallengeSubmissionFindByUserChallenge:
    """Test finding submissions by user and challenge."""

    def setup_method(self):
        """Set up test fixtures."""
        self.submission = ChallengeSubmission()

    def test_find_by_user_and_challenge_success(self):
        """Test successful retrieval of submissions."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_result = Mock()
        mock_result.data = [
                {
                    'id': 'sub-1',
                    'user_id':'user-235',
                    'challenge_id': 'challenge-1',
                    'score': 85,
                    'submitted_at': '2024-01-15T10:30:00Z'
                },
                {
                    'id': 'sub-2',
                    'user_id':'user-235',
                    'challenge_id': 'challenge-1',
                    'score': 92,
                    'submitted_at': '2024-01-16T14:20:00Z'
                }
            ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
        result = self.submission.find_by_user_and_challenge('user-235','challenge-1')
        
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["user_id"] == "user-235"
        assert result["data"][0]["challenge_id"] == "challenge-1"
    
    def test_find_by_user_and_challenge_empty(self):
        """Test find_by_user_and_challenge when user has no submissions for challenge."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
        result = self.submission.find_by_user_and_challenge('user-235','challenge-1')
        
        assert result["success"] is True
        assert result["data"] == []

class TestChallengeSubmissionFindById:
    """Test finding submission by ID."""

    def setup_method(self):
        """Set up test fixtures."""
        self.submission = ChallengeSubmission()

    def test_find_by_id_success_with_user_filter(self):
        """Test successful retrieval by ID with user filter."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Mock successful query
        mock_result = Mock()
        mock_result.data = [{
            'id': 'submission-123',
            'challenge_id': 'challenge-456',
            'user_id': 'user-789',
            'score': 85,
            'code': "print('hello world')"
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.submission.find_by_id('submission-123', 'user-789')
        
        assert result["success"] is True
        assert result["data"]["id"] == "submission-123"
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.assert_called_once_with('user_id', 'user-789')

    def test_find_by_id_success_without_user_filter(self):
        """Test successful retrieval by ID without user filter."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Mock successful query
        mock_result = Mock()
        mock_result.data = [{
            'id': 'submission-123',
            'challenge_id': 'challenge-456',
            'score': 85
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.submission.find_by_id('submission-123')
        
        assert result["success"] is True
        assert result["data"]["id"] == "submission-123"
        mock_supabase.table.return_value.select.return_value.eq.assert_called_once_with('id','submission-123')
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.assert_not_called()
    
    def test_find_by_id_not_found(self):
        """Test find_by_id when submission doesn't exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Mock no submission found
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.submission.find_by_id('nonexistent-id')
        
        assert result["success"] is False
        assert result["error"] == "Submission not found or access denied"

class TestChallengeSubmissionGetUserchallengeSummary:
    """Test getting user challenge summary functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.submission = ChallengeSubmission()

    def test_get_user_challenge_summary_with_submissions(self):
        """Test summary when user has submissions."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase

        mock_submission = Mock()
        mock_submission.data = [{
            'status': 'passed',
            'submitted_at': '2024-01-16T14:20:00Z',
            'score': 85
        },
        {
            'status': 'in_progress',
            'submitted_at': '2024-01-16T14:20:00Z',
            'score': 80
        }
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = mock_submission
        
        result = self.submission.get_user_challenge_summary('user-789', 'challenge-456')
        result_b = self.submission.get_user_challenge_summary('user-789', 'challenge-456')
        assert result["success"] is True
        assert result["data"]["total_attempts"] == 2
        assert result["data"]["status"] == 'completed'
        assert result["data"]["best_score"] == 85
        assert result["data"]["has_passed"] is True
    
    def test_get_user_challenge_summary_with_submission_in_progress(self):
        """Test summary when user has submissions."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase

        mock_submission = Mock()
        mock_submission.data = [{
            'status': 'in_progress',
            'submitted_at': '2024-01-16T14:20:00Z',
            'score': 85
        },
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value= mock_submission
        
        result = self.submission.get_user_challenge_summary('user-789', 'challenge-456')
        
        assert result["success"] is True
        assert result["data"]["total_attempts"] == 1
        assert result["data"]["status"] == 'in_progress'
        assert result["data"]["best_score"] == 85
        assert result["data"]["has_passed"] is False

    def test_get_user_challenge_summary_with_no_submissions(self):
        """Test summary when user has no submissions."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase

        mock_submission = Mock()
        mock_submission.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = mock_submission
        
        result = self.submission.get_user_challenge_summary('user-789', 'challenge-456')
        
        assert result["success"] is True
        assert result["data"]["total_attempts"] == 0
        assert result["data"]["best_score"] == 0
        assert result["data"]["status"] == 'not_started'
        assert 'has_passed' not in result["data"]

class TestChallengeSubmissionGetBatchStatistics:
    """Test batch statistics functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.submission = ChallengeSubmission()

    def test_get_batch_statistics_success(self):
        """Test successful batch statistics retrieval."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Mock the RPC response 
        mock_batch_stats = Mock()
        mock_batch_stats.data = [
            {   
                "challenge_id": "challenge-1",
                "users_attempted": 25,
                "users_completed": 20,
                "pass_rate": 80.0,
                "total_submissions":100
            },
            {
                "challenge_id": "challenge-2",  
                "users_attempted": 30,
                "users_completed": 18,
                "pass_rate": 60.0,
                "total_submissions":100
            }
        ]
                
        mock_supabase.rpc.return_value.execute.return_value = mock_batch_stats
        
        challenge_ids = ["challenge-1", "challenge-2"]
        challenge_ids_str = json.dumps(challenge_ids, sort_keys=True)
        result = self.submission.get_batch_challenge_statistics_rpc(challenge_ids_str)
        
        assert result["success"] is True
        assert "challenge-1" in result["data"]
        assert "challenge-2" in result["data"]
        assert result["data"]["challenge-1"]["users_attempted"] == 25
        assert result["data"]["challenge-1"]["pass_rate"] == 80.0
        assert result["data"]["challenge-2"]["users_attempted"] == 30
        assert result["data"]["challenge-2"]["pass_rate"] == 60.0
    
    def test_get_batch_statistics_empty_challenges(self):
        """Test batch statistics with empty challenge list."""
        challenge_ids_str = json.dumps([], sort_keys=True)
        result = self.submission.get_batch_challenge_statistics_rpc(challenge_ids_str)
        assert result["success"] is True
        assert result["data"] == {}
    
    def test_get_batch_statistics_success_no_stats(self):
        """Test successful batch statistics retrieval with empty stats."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Mock the RPC response 
        mock_batch_stats = Mock()
        mock_batch_stats.data = []
                
        mock_supabase.rpc.return_value.execute.return_value = mock_batch_stats
        
        challenge_ids = ["challenge-1", "challenge-2"]
        challenge_ids_str = json.dumps(challenge_ids, sort_keys=True)
        result = self.submission.get_batch_challenge_statistics_rpc(challenge_ids_str)
        
        assert result["success"] is True
        assert "challenge-1" in result["data"]
        assert "challenge-2" in result["data"]
        assert result["data"]["challenge-1"]["users_attempted"] == 0
        assert result["data"]["challenge-1"]["pass_rate"] == 0
        assert result["data"]["challenge-2"]["users_attempted"] == 0
        assert result["data"]["challenge-2"]["pass_rate"] == 0
    
    def test_get_batch_statistics_rpc_failure(self):
        """Test batch statistics RPC failure handling."""
        # Mock RPC failure
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
                
        mock_supabase.rpc.return_value.execute.side_effect = Exception("RPC function not found")
        
        challenge_ids_str = json.dumps(["challenge-1"], sort_keys=True)
        result = self.submission.get_batch_challenge_statistics_rpc(challenge_ids_str)
        
        assert result["success"] is False
        assert "RPC function not found" in result["error"]

class TestChallengeSubmissionDelete:
    """Test submission deletion functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.submission = ChallengeSubmission()

    @patch('app.models.challenge_submission.ChallengeSubmission.get_batch_challenge_statistics_rpc')
    @patch('app.models.challenge_submission.ChallengeSubmission.find_by_user')
    @patch('app.models.challenge_submission.ChallengeSubmission.find_by_user_and_challenge')
    @patch('app.models.challenge_submission.ChallengeSubmission.get_user_challenge_summary')
    def test_delete_success(self,mock_user_challenge_summary, mock_find_by_user_challenge, mock_find_by_user, mock_batch_challenge_statistics_rpc):
        """Test successful deletion."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_find_by_user.cache_clear = Mock()
        mock_batch_challenge_statistics_rpc.cache_clear = Mock()
        mock_find_by_user_challenge.cache_clear = Mock()
        mock_user_challenge_summary.cache_clear = Mock()
        
        # Mock successful deletion
        mock_result = Mock()
        mock_result.data = [{'id': 'submission-123'}]
        mock_supabase.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result
        result = self.submission.delete('submission-123', 'user-789')
        
        assert result["success"] is True
        assert result["message"] == "Submission deleted successfully"
        mock_batch_challenge_statistics_rpc.cache_clear.assert_called_once()
        mock_user_challenge_summary.cache_clear.assert_called_once()
        mock_find_by_user.cache_clear.assert_called_once()
        mock_find_by_user_challenge.cache_clear.assert_called_once()
        mock_supabase.table.return_value.delete.return_value.eq.return_value.eq.assert_called_once_with("user_id","user-789")

    def test_delete_database_error(self):
        """Test deletion handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database error")
        
        result = self.submission.delete('submission-123', 'user-789')
        
        assert result["success"] is False
        assert "Database error" in result["error"]

class TestChallengeSubmissionSince:
    """Test published since functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.submission = ChallengeSubmission()

    def test_submissions_since_success(self):
        """Test successful return."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Create a test datetime
        since_date = datetime(2024, 1, 1, 10, 0, 0)
        
        mock_result = Mock()
        mock_result.data = [
            {'id': 'submission-123',
            'challenge_id': 'challenge-456',
            'user_id': 'user-789',
            'code': "print('hello world')",
            },
            {'id': 'submission-124',
            'challenge_id': 'challenge-456',
            'user_id': 'user-790',
            'code': "print('hello world')",
            }
        ]
        mock_supabase.table.return_value.select.return_value.gte.return_value.execute.return_value = mock_result
        
        result = self.submission.get_challenge_submissions_since(since_date)
        
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["id"] == "submission-123"
        assert result["data"][1]["id"] == "submission-124"

    def test_submissions_since_empty_result(self):
        """Test submissions since with no results."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        since_date = datetime(2024, 1, 1, 10, 0, 0)
        
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.gte.return_value.execute.return_value = mock_result
        
        result = self.submission.get_challenge_submissions_since(since_date)
        
        assert result["success"] is True
        assert len(result["data"]) == 0

class TestChallengeSubmissionCountSubmissions:
    """Test getting total submissions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.submission = ChallengeSubmission()

    def test_count_submissions_count_success(self):
        """Test successful retrieval of submissions."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Mock successful count query
        mock_result = Mock()
        mock_result.count = 150
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_result
        
        result = self.submission.count_submissions()
        
        assert result["success"] is True
        assert result["count"] == 150
    
    def test_count_submissions_count_none_result(self):
        """Test retrieval when count is None."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Mock result with None count
        mock_result = Mock()
        mock_result.count = None
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_result
        
        result = self.submission.count_submissions()
        
        assert result["success"] is True
        assert result["count"] == 0
    
    def test_count_submissions_database_error(self):
        """Test handling database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database connection failed")
        
        result = self.submission.count_submissions()
        
        assert result["success"] is False
        assert "Database connection failed" in result["error"]