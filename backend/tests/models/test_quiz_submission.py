import pytest
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch
import json

sys.path.append(str(Path(__file__).parent.parent.parent))
from app.models.quiz_submission import QuizSubmission

class TestQuizSubmissionCreate:
    """Test quiz submission creation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.submission = QuizSubmission()
    
    def test_create_success(self):
        """Test successful submission creation."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_quiz_result = Mock()
        mock_quiz_result.data = [{'time_limit_minutes': 30}]

        mock_questions_result = Mock()
        mock_questions_result.data = [
            {'id': 'q1'},
            {'id': 'q2'},
            {'id': 'q3'}
        ]
        
        mock_submission_result = Mock()
        mock_submission_result.data = [{
            'id': 'submission-123',
            'quiz_id': 'quiz-456',
            'user_id': 'user-789',
            'answers': {'q1': 'A', 'q2': 'B', 'q3': 'C'},
            'status': 'submitted',
        }]

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [mock_quiz_result,mock_questions_result]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_submission_result

        answers = {'q1': 'A', 'q2': 'B', 'q3': 'C'}
        result = self.submission.create('quiz-456', 'user-789', answers)

        assert result["success"] is True
        assert result["data"]["id"] == "submission-123"
        assert result["data"]["answers"] == answers
        assert result["data"]["status"] == "submitted"
    
    def test_create_quiz_not_found(self):
        """Test creation fails when quiz doesn't exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Mock quiz not found
        mock_quiz_result = Mock()
        mock_quiz_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_quiz_result
        
        answers = {'q1': 'A'}
        result = self.submission.create('nonexistent-quiz', 'user-789', answers)
        
        assert result["success"] is False
        assert result["errors"] == "Quiz not found"

    def test_create_no_questions(self):
        """Test creation fails when quiz has no questions."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Mock quiz exists but no questions
        mock_quiz_result = Mock()
        mock_quiz_result.data = [{'time_limit_minutes': 30}]
        mock_questions_result = Mock()
        mock_questions_result.data = []
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            mock_quiz_result,
            mock_questions_result
        ]
        
        answers = {'q1': 'A'}
        result = self.submission.create('quiz-456', 'user-789', answers)
        
        assert result["success"] is False
        assert result["errors"] == "No questions found for this quiz"
    
    def test_create_invalid_question_id(self):
        """Test creation fails with invalid question ID."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Mock quiz and questions exist
        mock_quiz_result = Mock()
        mock_quiz_result.data = [{'time_limit_minutes': 30}]
        mock_questions_result = Mock()
        mock_questions_result.data = [{'id': 'q1'}, {'id': 'q2'}]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            mock_quiz_result,
            mock_questions_result
        ]
        
        # Include invalid question ID
        answers = {'q1': 'A', 'invalid-question': 'B'}
        result = self.submission.create('quiz-456', 'user-789', answers)
        
        assert result["success"] is False
        assert "Invalid question ID" in result["errors"]

    def test_create_invalid_answer_choice(self):
        """Test creation fails with invalid answer choice."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Mock quiz and questions exist
        mock_quiz_result = Mock()
        mock_quiz_result.data = [{'time_limit_minutes': 30}]
        mock_questions_result = Mock()
        mock_questions_result.data = [{'id': 'q1'}, {'id': 'q2'}]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            mock_quiz_result,
            mock_questions_result
        ]
        
        # Include invalid question ID
        answers = {'q1': 'A', 'q2': 'E'}
        result = self.submission.create('quiz-456', 'user-789', answers)
        
        assert result["success"] is False
        assert "Invalid answer choice" in result["errors"]
    
    def test_create_database_error(self):
        """Test creation handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database error")
        
        answers = {'q1': 'A'}
        result = self.submission.create('quiz-456', 'user-789', answers)
        
        assert result["success"] is False
        assert "Database error" in result["error"]

class TestQuizSubmissionUpdateResults:
    """Test updating submission results functionality."""
    def setup_method(self):
        """Set up test fixtures."""
        self.submission = QuizSubmission()
    
    @patch('app.models.quiz_submission.QuizSubmission.get_batch_quiz_statistics_rpc')
    @patch('app.models.quiz_submission.QuizSubmission.find_by_user')
    @patch('app.models.quiz_submission.QuizSubmission.find_by_user_and_quiz')
    @patch('app.models.quiz_submission.QuizSubmission.get_user_quiz_summary')
    def test_update_results_success(self,mock_user_quiz_summary, mock_find_by_user_quiz, mock_find_by_user, mock_batch_quiz_statistics_rpc):
        """Test successful results update."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        mock_find_by_user.cache_clear = Mock()
        mock_batch_quiz_statistics_rpc.cache_clear = Mock()
        mock_find_by_user_quiz.cache_clear = Mock()
        mock_user_quiz_summary.cache_clear = Mock()

        # Mock successful update
        scoring_result = {
            'score': 85,
            'percentage': 85.0,
            'correct_answers': 17,
            'total_questions': 20,
        }
        
        mock_result = Mock()
        mock_result.data = [{
            'id': 'submission-123',
            'score': 85,
            'percentage': 85.0,
            'questions_correct': 17,
            'questions_total': 20,
            'status': 'completed'
        }]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.submission.update_results('submission-123', scoring_result)
        
        assert result["success"] is True
        assert result["data"]["score"] == 85
        assert result["data"]["status"] == "completed"
        mock_batch_quiz_statistics_rpc.cache_clear.assert_called_once()
        mock_user_quiz_summary.cache_clear.assert_called_once()
        mock_find_by_user.cache_clear.assert_called_once()
        mock_find_by_user_quiz.cache_clear.assert_called_once()
    
    def test_update_results_not_found(self):
        """Test update when submission fails."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Mock no submission found
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result
        
        scoring_result = {'score': 85, 'percentage': 85.0}
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

class TestQuizSubmissionGetBestSubmission:
    """Test getting best submission functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.submission = QuizSubmission()

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
            'percentage': 95.0,
            'status': 'completed',
            'submitted_at': '2024-01-15T10:30:00Z'
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
        
        result = self.submission.get_best_submission('user-789', 'quiz-456')
        
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
        
        result = self.submission.get_best_submission('user-789', 'quiz-456')
        
        assert result["success"] is False
        assert result["error"] == "No submissions found"
    
    def test_get_best_submission_database_error(self):
        """Test get_best_submission handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database error")
        
        result = self.submission.get_best_submission('user-789', 'quiz-456')
        
        assert result["success"] is False
        assert "Database error" in result["error"]

class TestQuizSubmissionFindByUser:
    """Test finding submissions by user."""

    def setup_method(self):
        """Set up test fixtures."""
        self.submission = QuizSubmission()

    def test_find_by_user_success(self):
        """Test successful retrieval of user submissions."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_result = Mock()
        mock_result.data = [
                {
                    'id': 'sub-1',
                    'quiz_id': 'quiz-1',
                    'score': 85,
                    'submitted_at': '2024-01-15T10:30:00Z'
                },
                {
                    'id': 'sub-2',
                    'quiz_id': 'quiz-2',
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

class TestQuizSubmissionFindByQuiz:
    """Test finding submissions by quiz."""

    def setup_method(self):
        """Set up test fixtures."""
        self.submission = QuizSubmission()

    def test_find_by_quiz_success(self):
        """Test successful retrieval of user submissions."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_result = Mock()
        mock_result.data = [
                {
                    'id': 'sub-1',
                    'quiz_id': 'quiz-1',
                    'score': 85,
                    'submitted_at': '2024-01-15T10:30:00Z'
                },
                {
                    'id': 'sub-2',
                    'quiz_id': 'quiz-1',
                    'score': 92,
                    'submitted_at': '2024-01-16T14:20:00Z'
                }
            ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
        result = self.submission.find_by_quiz('quiz-1')
        
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["quiz_id"] == "quiz-1"
    
    def test_find_by_quiz_empty(self):
        """Test find_by_quiz when quiz has no submissions."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
        result = self.submission.find_by_quiz('quiz-1')
        
        assert result["success"] is True
        assert result["data"] == []

class TestQuizSubmissionFindByUserQuiz:
    """Test finding submissions by user and quiz."""

    def setup_method(self):
        """Set up test fixtures."""
        self.submission = QuizSubmission()

    def test_find_by_user_and_quiz_success(self):
        """Test successful retrieval of submissions."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_result = Mock()
        mock_result.data = [
                {
                    'id': 'sub-1',
                    'user_id':'user-235',
                    'quiz_id': 'quiz-1',
                    'score': 85,
                    'submitted_at': '2024-01-15T10:30:00Z'
                },
                {
                    'id': 'sub-2',
                    'user_id':'user-235',
                    'quiz_id': 'quiz-1',
                    'score': 92,
                    'submitted_at': '2024-01-16T14:20:00Z'
                }
            ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
        result = self.submission.find_by_user_and_quiz('user-235','quiz-1')
        
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["user_id"] == "user-235"
        assert result["data"][0]["quiz_id"] == "quiz-1"
    
    def test_find_by_user_and_quiz_empty(self):
        """Test find_by_user_and_quiz when user has no submissions for quiz."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
        result = self.submission.find_by_user_and_quiz('user-235','quiz-1')
        
        assert result["success"] is True
        assert result["data"] == []

class TestQuizSubmissionFindById:
    """Test finding submission by ID."""

    def setup_method(self):
        """Set up test fixtures."""
        self.submission = QuizSubmission()

    def test_find_by_id_success_with_user_filter(self):
        """Test successful retrieval by ID with user filter."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Mock successful query
        mock_result = Mock()
        mock_result.data = [{
            'id': 'submission-123',
            'quiz_id': 'quiz-456',
            'user_id': 'user-789',
            'score': 85,
            'answers': {'q1': 'A', 'q2': 'B'}
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
            'quiz_id': 'quiz-456',
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

class TestQuizSubmissionGetUserQuizSummary:
    """Test getting user quiz summary functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.submission = QuizSubmission()

    def test_get_user_quiz_summary_with_submissions(self):
        """Test summary when user has submissions."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_quiz_result = Mock()
        mock_quiz_result.data = [{'id':'quiz-id','total_points':100}]

        mock_submission = Mock()
        mock_submission.data = [{
            'id': 'submission-123',
            'quiz_id': 'quiz-456',
            'score': 85
        },
        {
            'id': 'submission-124',
            'quiz_id': 'quiz-457',
            'score': 80
        }
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_quiz_result
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = mock_submission
        
        result = self.submission.get_user_quiz_summary('user-789', 'quiz-456')
        
        assert result["success"] is True
        assert result["data"]["total_attempts"] == 2
        assert result["data"]["best_score"] == 85
        assert result["data"]["has_passed"] is True
    
    def test_get_user_quiz_summary_with_no_submissions(self):
        """Test summary when user has no submissions."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_quiz_result = Mock()
        mock_quiz_result.data = [{'id':'quiz-id','total_points':100}]

        mock_submission = Mock()
        mock_submission.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_quiz_result
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = mock_submission
        
        result = self.submission.get_user_quiz_summary('user-789', 'quiz-456')
        
        assert result["success"] is True
        assert result["data"]["total_attempts"] == 0
        assert result["data"]["best_score"] == 0
        assert result["data"]["has_passed"] is False
    
    def test_get_user_quiz_summary_quiz_not_found(self):
        """Test summary when quiz is not found."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_quiz_result = Mock()
        mock_quiz_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_quiz_result
        
        result = self.submission.get_user_quiz_summary('user-789', 'quiz-456')
        
        assert result["success"] is False
        assert result["error"] == "Quiz not found"

class TestQuizSubmissionGetBatchStatistics:
    """Test batch statistics functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.submission = QuizSubmission()

    def test_get_batch_statistics_success(self):
        """Test successful batch statistics retrieval."""
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        
        # Mock the RPC response 
        mock_batch_stats = Mock()
        mock_batch_stats.data = [
            {   
                "quiz_id": "quiz-1",
                "users_attempted": 25,
                "users_passed": 20,
                "pass_rate": 80.0,
                "average_score": 74,
                "total_submissions":100
            },
            {
                "quiz_id": "quiz-2",  
                "users_attempted": 30,
                "users_passed": 18,
                "pass_rate": 60.0,
                "average_score": 67,
                "total_submissions":100
            }
        ]
                
        mock_supabase.rpc.return_value.execute.return_value = mock_batch_stats
        
        quiz_ids = ["quiz-1", "quiz-2"]
        quiz_ids_str = json.dumps(quiz_ids, sort_keys=True)
        result = self.submission.get_batch_quiz_statistics_rpc(quiz_ids_str)
        
        assert result["success"] is True
        assert "quiz-1" in result["data"]
        assert "quiz-2" in result["data"]
        assert result["data"]["quiz-1"]["users_attempted"] == 25
        assert result["data"]["quiz-1"]["pass_rate"] == 80.0
        assert result["data"]["quiz-2"]["users_attempted"] == 30
        assert result["data"]["quiz-2"]["pass_rate"] == 60.0
    
    def test_get_batch_statistics_empty_quizzes(self):
        """Test batch statistics with empty quiz list."""
        quiz_ids_str = json.dumps([], sort_keys=True)
        result = self.submission.get_batch_quiz_statistics_rpc(quiz_ids_str)
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
        
        quiz_ids = ["quiz-1", "quiz-2"]
        quiz_ids_str = json.dumps(quiz_ids, sort_keys=True)
        result = self.submission.get_batch_quiz_statistics_rpc(quiz_ids_str)
        
        assert result["success"] is True
        assert "quiz-1" in result["data"]
        assert "quiz-2" in result["data"]
        assert result["data"]["quiz-1"]["users_attempted"] == 0
        assert result["data"]["quiz-1"]["pass_rate"] == 0
        assert result["data"]["quiz-2"]["users_attempted"] == 0
        assert result["data"]["quiz-2"]["pass_rate"] == 0
    
    def test_get_batch_statistics_rpc_failure(self):
        """Test batch statistics RPC failure handling."""
        # Mock RPC failure
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
                
        mock_supabase.rpc.return_value.execute.side_effect = Exception("RPC function not found")
        
        quiz_ids_str = json.dumps(["quiz-1"], sort_keys=True)
        result = self.submission.get_batch_quiz_statistics_rpc(quiz_ids_str)
        
        assert result["success"] is False
        assert "RPC function not found" in result["error"]
    
    # def test_get_batch_statistics_rpc_failure_errno11(self):
    #     """Test batch statistics RPC failure handling."""
    #     # Mock RPC failure
    #     mock_supabase = Mock()
    #     self.submission.supabase = mock_supabase
                
    #     mock_supabase.rpc.return_value.execute.side_effect = Exception("resource temporarily unavailable")
        
    #     quiz_ids_str = json.dumps(["quiz-1"], sort_keys=True)
        
    #     with pytest.raises(Exception, match=f"resource temporarily unavailable"):
    #         self.submission.get_batch_quiz_statistics_rpc(quiz_ids_str)

class TestQuizSubmissionDelete:
    """Test submission deletion functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.submission = QuizSubmission()

    @patch('app.models.quiz_submission.QuizSubmission.get_batch_quiz_statistics_rpc')
    @patch('app.models.quiz_submission.QuizSubmission.find_by_user')
    @patch('app.models.quiz_submission.QuizSubmission.find_by_user_and_quiz')
    @patch('app.models.quiz_submission.QuizSubmission.get_user_quiz_summary')
    def test_delete_success(self,mock_user_quiz_summary, mock_find_by_user_quiz, mock_find_by_user, mock_batch_quiz_statistics_rpc):
        """Test successful deletion."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.submission.supabase = mock_supabase
        mock_find_by_user.cache_clear = Mock()
        mock_batch_quiz_statistics_rpc.cache_clear = Mock()
        mock_find_by_user_quiz.cache_clear = Mock()
        mock_user_quiz_summary.cache_clear = Mock()
        
        # Mock successful deletion
        mock_result = Mock()
        mock_result.data = [{'id': 'submission-123'}]
        mock_supabase.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result
        result = self.submission.delete('submission-123', 'user-789')
        
        assert result["success"] is True
        assert result["message"] == "Submission deleted successfully"
        mock_batch_quiz_statistics_rpc.cache_clear.assert_called_once()
        mock_user_quiz_summary.cache_clear.assert_called_once()
        mock_find_by_user.cache_clear.assert_called_once()
        mock_find_by_user_quiz.cache_clear.assert_called_once()
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

class TestQuizSubmissionSince:
    """Test published since functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.submission = QuizSubmission()

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
            'quiz_id': 'quiz-456',
            'user_id': 'user-789',
            'answers': {'q1': 'A', 'q2': 'B', 'q3': 'C'},
            },
            {'id': 'submission-124',
            'quiz_id': 'quiz-456',
            'user_id': 'user-790',
            'answers': {'q1': 'A', 'q2': 'B', 'q3': 'C'},
            }
        ]
        mock_supabase.table.return_value.select.return_value.gte.return_value.execute.return_value = mock_result
        
        result = self.submission.get_quiz_submissions_since(since_date)
        
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
        
        result = self.submission.get_quiz_submissions_since(since_date)
        
        assert result["success"] is True
        assert len(result["data"]) == 0

class TestQuizSubmissionCountSubmissions:
    """Test getting total submissions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.submission = QuizSubmission()

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
