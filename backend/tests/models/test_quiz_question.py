import pytest
import sys
from pathlib import Path
from unittest.mock import patch, Mock

sys.path.append(str(Path(__file__).parent.parent.parent))
from app.models.quiz_question import QuizQuestion

class TestQuizQuestionValidation:
    """Test quiz question data validation."""
    
    def test_validate_data_valid_question(self):
        """Test validation with valid question data."""
        valid_data = {
            'question_text': 'What is the capital of France?',
            'option_a': 'Paris',
            'option_b': 'London',
            'option_c': 'Berlin',
            'option_d': 'Madrid',
            'correct_answer': 'A',
            'points_weight': 10,
            'question_order_idx': '1',
            'explanation': 'Paris is the capital of France'
        }
        
        errors = QuizQuestion.validate_data(valid_data)
        assert errors == {}

    def test_validate_data_missing_question_text(self):
        """Test validation fails when question text is missing."""
        invalid_data = {
            'option_a': 'Paris',
            'option_b': 'London',
            'option_c': 'Berlin',
            'option_d': 'Madrid',
            'correct_answer': 'A'
        }
        
        errors = QuizQuestion.validate_data(invalid_data)
        assert 'question_text' in errors
        assert errors['question_text'] == "Question text is required"
    
    def test_validate_data_empty_question_text(self):
        """Test validation fails when question text is empty."""
        invalid_data = {
            'question_text': '   ',
            'option_a': 'Paris',
            'option_b': 'London',
            'option_c': 'Berlin',
            'option_d': 'Madrid',
            'correct_answer': 'A'
        }
        
        errors = QuizQuestion.validate_data(invalid_data)
        assert 'question_text' in errors
        assert errors['question_text'] == "Question text is required"
    
    def test_validate_data_missing_options(self):
        """Test validation fails when options are missing."""
        invalid_data = {
            'question_text': 'What is the capital of France?',
            'option_a': 'Paris',
            'option_b': 'London',
            # Missing option_c and option_d
            'correct_answer': 'A'
        }
        
        errors = QuizQuestion.validate_data(invalid_data)
        assert 'option_c' in errors
        assert 'option_d' in errors
        assert errors['option_c'] == "Option C is required"
        assert errors['option_d'] == "Option D is required"
    
    def test_validate_data_empty_options(self):
        """Test validation fails when options are empty."""
        invalid_data = {
            'question_text': 'What is the capital of France?',
            'option_a': '   ',
            'option_b': '',
            'option_c': 'Berlin',
            'option_d': 'Madrid',
            'correct_answer': 'A'
        }
        
        errors = QuizQuestion.validate_data(invalid_data)
        assert 'option_a' in errors
        assert 'option_b' in errors
        assert errors['option_a'] == "Option A is required"
        assert errors['option_b'] == "Option B is required"
    
    def test_validate_data_invalid_correct_answer(self):
        """Test validation fails with invalid correct answer."""
        invalid_data = {
            'question_text': 'What is the capital of France?',
            'option_a': 'Paris',
            'option_b': 'London',
            'option_c': 'Berlin',
            'option_d': 'Madrid',
            'correct_answer': 'E'  # Invalid
        }
        
        errors = QuizQuestion.validate_data(invalid_data)
        assert 'correct_answer' in errors
        assert errors['correct_answer'] == "Correct answer must be A, B, C, or D"
    
    def test_validate_data_missing_correct_answer(self):
        """Test validation fails when correct answer is missing."""
        invalid_data = {
            'question_text': 'What is the capital of France?',
            'option_a': 'Paris',
            'option_b': 'London',
            'option_c': 'Berlin',
            'option_d': 'Madrid'
            # Missing correct_answer
        }
        
        errors = QuizQuestion.validate_data(invalid_data)
        assert 'correct_answer' in errors
        assert errors['correct_answer'] == "Correct answer must be A, B, C, or D"

    def test_validate_data_invalid_points_weight_zero(self):
        """Test validation fails with zero points weight."""
        invalid_data = {
            'question_text': 'What is the capital of France?',
            'option_a': 'Paris',
            'option_b': 'London',
            'option_c': 'Berlin',
            'option_d': 'Madrid',
            'correct_answer': 'A',
            'points_weight': 0
        }
        
        errors = QuizQuestion.validate_data(invalid_data)
        assert 'points_weight' in errors
        assert errors['points_weight'] == "Points weight must be greater than 0"

    def test_validate_data_invalid_points_weight_type(self):
        """Test validation fails with non-numeric points weight."""
        invalid_data = {
            'question_text': 'What is the capital of France?',
            'option_a': 'Paris',
            'option_b': 'London',
            'option_c': 'Berlin',
            'option_d': 'Madrid',
            'correct_answer': 'A',
            'points_weight': 'invalid'
        }
        
        errors = QuizQuestion.validate_data(invalid_data)
        assert 'points_weight' in errors
        assert errors['points_weight'] == "Points weight must be a valid number"
    
    def test_validate_data_missing_question_order_idx(self):
        """Test validation fails when question order index is missing."""
        invalid_data = {
            'question_text': 'What is the capital of France?',
            'option_a': 'Paris',
            'option_b': 'London',
            'option_c': 'Berlin',
            'option_d': 'Madrid',
            'correct_answer': 'A'
            # Missing question_order_idx
        }
        
        errors = QuizQuestion.validate_data(invalid_data)
        assert 'question_order_idx' in errors
        assert errors['question_order_idx'] == "Question order index is required"

    def test_validate_data_empty_question_order_idx(self):
        """Test validation fails when question order index is empty."""
        invalid_data = {
            'question_text': 'What is the capital of France?',
            'option_a': 'Paris',
            'option_b': 'London',
            'option_c': 'Berlin',
            'option_d': 'Madrid',
            'correct_answer': 'A',
            'question_order_idx': '   '
        }
        
        errors = QuizQuestion.validate_data(invalid_data)
        assert 'question_order_idx' in errors
        assert errors['question_order_idx'] == "Question order index cannot be empty if provided"

    def test_validate_data_boundary_values(self):
        """Test validation with boundary values."""
        boundary_data = {
            'question_text': 'Q',  # Minimum length
            'option_a': 'A',
            'option_b': 'B',
            'option_c': 'C',
            'option_d': 'D',
            'correct_answer': 'A',
            'points_weight': 0.1,  # Minimum allowed value > 0
            'question_order_idx': '1'
        }
        
        errors = QuizQuestion.validate_data(boundary_data)
        assert errors == {}

class TestQuizQuestionCreate:
    """Test question creation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.question = QuizQuestion()

    @patch('app.models.quiz_question.QuizQuestion._update_quiz_totals')
    @patch('app.models.quiz_question.QuizQuestion.find_by_quiz')
    def test_create_question_success(self,mock_find_by_quiz, mock_update_quiz_totals):
        """Test successful question creation."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.question.supabase = mock_supabase
        mock_find_by_quiz.cache_clear = Mock()
        
        # Mock quiz exists check
        mock_quiz_result = Mock()
        mock_quiz_result.data = [{'id': 'quiz-id'}]
        
        # Mock successful insertion
        mock_question_data = {
            'id': 'question-id',
            'quiz_id': 'quiz-id',
            'question_text': 'What is Python?',
            'option_a': 'A snake',
            'option_b': 'A programming language',
            'option_c': 'A movie',
            'option_d': 'A car',
            'correct_answer': 'B',
            'points_weight': 10
        }
        
        mock_insert_result = Mock()
        mock_insert_result.data = [mock_question_data]
        
        # Mock _update_quiz_totals
        mock_update_quiz_totals.return_value = {
            'id': 'quiz-id',
            'total_questions': 3,
            'total_points': 30
        }
        
        # Setup mock chain
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_quiz_result
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_result
        
        question_data = {
            'question_text': 'What is Python?',
            'option_a': 'A snake',
            'option_b': 'A programming language',
            'option_c': 'A movie',
            'option_d': 'A car',
            'correct_answer': 'B',
            'points_weight': 10,
            'question_order_idx': '1'
        }
        
        result = self.question.create('quiz-id', question_data)
        
        assert result["success"] is True
        assert result["data"]["question_text"] == "What is Python?"
        assert result["data"]["quiz_id"] == "quiz-id"
        assert "updated_quiz" in result
        assert result["updated_quiz"]["total_questions"] == 3
        mock_find_by_quiz.cache_clear.assert_called_once()
    
    def test_create_question_validation_errors(self):
        """Test question creation fails with validation errors."""
        invalid_data = {
            'question_text': '',  # Invalid
            'option_a': 'A',
            'correct_answer': 'E'  # Invalid
        }
        
        result = self.question.create('quiz-id', invalid_data)
        
        assert result["success"] is False
        assert "errors" in result
        assert len(result["errors"]) > 0
    
    def test_create_question_quiz_not_found(self):
        """Test question creation fails when quiz doesn't exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.question.supabase = mock_supabase
        
        # Mock quiz not found
        mock_quiz_result = Mock()
        mock_quiz_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_quiz_result
        
        question_data = {
            'question_text': 'What is Python?',
            'option_a': 'A snake',
            'option_b': 'A programming language',
            'option_c': 'A movie',
            'option_d': 'A car',
            'correct_answer': 'B',
            'question_order_idx': '1'
        }
        
        result = self.question.create('nonexistent-quiz', question_data)
        
        assert result["success"] is False
        assert result["error"] == "Quiz not found"
    @patch('app.models.quiz_question.QuizQuestion.find_by_quiz')
    def test_create_question_database_failure(self,mock_find_by_quiz):
        """Test question creation handles database failures."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.question.supabase = mock_supabase
        mock_find_by_quiz = Mock()
        
        # Mock quiz exists
        mock_quiz_result = Mock()
        mock_quiz_result.data = [{'id': 'quiz-id'}]
        
        # Mock database failure on insert
        mock_insert_result = Mock()
        mock_insert_result.data = None
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_quiz_result
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_result
        
        question_data = {
            'question_order_idx': '1',
            'question_text': 'What is Python?',
            'option_a': 'A snake',
            'option_b': 'A programming language',
            'option_c': 'A movie',
            'option_d': 'A car',
            'correct_answer': 'B',
        }
        
        result = self.question.create('quiz-id', question_data)
        
        assert result["success"] is False
        assert "error" in result
        assert result['error'] == "Failed to create question"
        mock_find_by_quiz.assert_not_called()

class TestQuizQuestionCreateBulk:
    """Test bulk question creation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.question = QuizQuestion()
    @patch('app.models.quiz_question.QuizQuestion._update_quiz_totals')
    @patch('app.models.quiz_question.QuizQuestion.find_by_quiz')
    def test_create_bulk_success(self,mock_find_by_quiz, mock_update_totals):
        """Test successful bulk question creation."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.question.supabase = mock_supabase
        mock_find_by_quiz.cache_clear = Mock()

        mock_quiz_result = Mock()
        mock_quiz_result.data = [{'id': 'quiz-id'}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_quiz_result
        
        # Mock successful bulk insertion
        mock_questions_data = [
            {'id': 'q1', 'question_text': 'Question 1'},
            {'id': 'q2', 'question_text': 'Question 2'}
        ]
        
        mock_insert_result = Mock()
        mock_insert_result.data = mock_questions_data
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_result
        
        # Mock _update_quiz_totals
        mock_update_totals.return_value = {'updated': True}
        
        questions_data = [
            {
                'question_text': 'Question 1',
                'option_a': 'A1', 'option_b': 'B1', 'option_c': 'C1', 'option_d': 'D1',
                'correct_answer': 'A', 'question_order_idx': '1'
            },
            {
                'question_text': 'Question 2',
                'option_a': 'A2', 'option_b': 'B2', 'option_c': 'C2', 'option_d': 'D2',
                'correct_answer': 'B', 'question_order_idx': '2'
            }
        ]
        
        result = self.question.create_bulk('quiz-id', questions_data)
        
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert "updated_quiz" in result
        mock_find_by_quiz.cache_clear.assert_called_once()

    def test_create_bulk_validation_errors(self):
        """Test bulk creation fails with validation errors."""
        invalid_questions = [
            {
                'question_text': 'Valid Question',
                'option_a': 'A', 'option_b': 'B', 'option_c': 'C', 'option_d': 'D',
                'correct_answer': 'A', 'question_order_idx': '1'
            },
            {
                'question_text': '',  # Invalid
                'option_a': 'A', 'correct_answer': 'E'  # Invalid
            }
        ]
        
        result = self.question.create_bulk('quiz-id', invalid_questions)
        
        assert result["success"] is False
        assert "errors" in result
        assert "questions.1.question_text" in result["errors"]
    
    @patch('app.models.quiz_question.QuizQuestion.find_by_quiz')
    def test_create_bulk_quiz_not_found(self,mock_find_by_quiz):
        """Test bulk creation handles database failures."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.question.supabase = mock_supabase

        mock_quiz_result = Mock()
        mock_quiz_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_quiz_result
        
        # Mock database failure
        
        questions_data = [
            {
                'question_text': 'Question 1',
                'option_a': 'A', 'option_b': 'B', 'option_c': 'C', 'option_d': 'D',
                'correct_answer': 'A', 'question_order_idx': '1'
            },
            {
                'question_text': 'Question 2',
                'option_a': 'A2', 'option_b': 'B2', 'option_c': 'C2', 'option_d': 'D2',
                'correct_answer': 'B', 'question_order_idx': '2'
            }
        ]
        
        result = self.question.create_bulk('quiz-id', questions_data)
        
        assert result["success"] is False
        assert result["error"] == "Quiz not found"
    
    @patch('app.models.quiz_question.QuizQuestion.find_by_quiz')
    def test_create_bulk_database_failure(self,mock_find_by_quiz):
        """Test bulk creation handles database failures."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.question.supabase = mock_supabase

        mock_quiz_result = Mock()
        mock_quiz_result.data = [{'id': 'quiz-id'}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_quiz_result
        
        # Mock database failure
        mock_insert_result = Mock()
        mock_insert_result.data = None
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_result
        
        questions_data = [
            {
                'question_text': 'Question 1',
                'option_a': 'A', 'option_b': 'B', 'option_c': 'C', 'option_d': 'D',
                'correct_answer': 'A', 'question_order_idx': '1'
            },
            {
                'question_text': 'Question 2',
                'option_a': 'A2', 'option_b': 'B2', 'option_c': 'C2', 'option_d': 'D2',
                'correct_answer': 'B', 'question_order_idx': '2'
            }
        ]
        
        result = self.question.create_bulk('quiz-id', questions_data)
        
        assert result["success"] is False
        assert result["error"] == "Failed to create questions"

class TestQuizQuestionFindByQuiz:
    """Test finding questions by quiz."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.question = QuizQuestion()

    def test_find_by_quiz_success_with_answers(self):
        """Test successful retrieval with answers included."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.question.supabase = mock_supabase
        
        mock_questions = [
            {
                'id': 'q1',
                'quiz_id': 'quiz-id',
                'question_text': 'Question 1',
                'correct_answer': 'A'
            },
            {
                'id': 'q2',
                'quiz_id': 'quiz-id',
                'question_text': 'Question 2',
                'correct_answer': 'B'
            }
        ]
        
        mock_result = Mock()
        mock_result.data = mock_questions
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_result
        
        result = self.question.find_by_quiz('quiz-id', include_answers=True)
        
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["correct_answer"] == "A"
        assert result["data"][1]["correct_answer"] == "B"
        mock_supabase.table.return_value.select.assert_called_with('*')

    def test_find_by_quiz_success_without_answers(self):
            """Test successful retrieval without answers (student view)."""
            # Mock the supabase instance
            mock_supabase = Mock()
            self.question.supabase = mock_supabase
            
            mock_questions = [
                {
                    'id': 'q1',
                    'quiz_id': 'quiz-id',
                    'question_text': 'Question 1'
                }
            ]
            
            mock_result = Mock()
            mock_result.data = mock_questions
            mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_result
            
            result = self.question.find_by_quiz('quiz-id', include_answers=False)
            
            assert result["success"] is True
            assert len(result["data"]) == 1
            expected_fields = 'id, quiz_id, question_text, option_a, option_b, option_c, option_d, points_weight, question_order_idx, created_at'
            mock_supabase.table.return_value.select.assert_called_with(expected_fields)
    
    def test_find_by_quiz_empty_result(self):
        """Test find_by_quiz when no questions exist."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.question.supabase = mock_supabase
        
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_result
        
        result = self.question.find_by_quiz('quiz-id')
        
        assert result["success"] is True
        assert result["data"] == []
    
    def test_find_by_quiz_database_error(self):
        """Test find_by_quiz handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.question.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database error")
        
        result = self.question.find_by_quiz('quiz-id')
        
        assert result["success"] is False
        assert "Database error" in result["error"]

class TestQuizQuestionFindById:
    """Test finding question by ID."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.question = QuizQuestion()

    def test_find_by_id_success(self):
        """Test successful retrieval of question by ID."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.question.supabase = mock_supabase
        
        mock_question = [{
            'id': 'question-id',
            'quiz_id': 'quiz-id',
            'question_text': 'What is Python?',
            'correct_answer': 'B'
        }]
        
        mock_result = Mock()
        mock_result.data = mock_question
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.question.find_by_id('question-id')
        
        assert result["success"] is True
        assert result["data"]["id"] == "question-id"
        assert result["data"]["question_text"] == "What is Python?"

    def test_find_by_id_not_found(self):
            """Test find_by_id when question doesn't exist."""
            # Mock the supabase instance
            mock_supabase = Mock()
            self.question.supabase = mock_supabase
            
            mock_result = Mock()
            mock_result.data = []
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
            
            result = self.question.find_by_id('nonexistent-id')
            
            assert result["success"] is False
            assert result["error"] == "Question not found"
    
    def test_find_by_id_database_error(self):
        """Test find_by_id handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.question.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database error")
        
        result = self.question.find_by_id('question-id')
        
        assert result["success"] is False
        assert "Database error" in result["error"]

class TestQuizQuestionUpdate:
    """Test question update functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.question = QuizQuestion()

    @patch('app.models.quiz_question.QuizQuestion._update_quiz_totals')
    @patch('app.models.quiz_question.QuizQuestion.find_by_quiz')
    @patch('app.models.quiz_question.QuizQuestion.find_by_id')
    def test_update_question_success(self,mock_find_by_id,mock_find_by_quiz,mock_update_totals):
        """Test successful question update."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.question.supabase = mock_supabase
        mock_find_by_quiz.cache_clear = Mock()
        
        # Mock find_by_id to get current question
        mock_find_by_id.return_value = {
            "success": True,
            "data": {"quiz_id": "quiz-id"}
        }
        
        mock_find_by_quiz.cache_clear = Mock()
        # Mock _update_quiz_totals
        mock_update_totals.return_value =={'updated': True}
        
        mock_updated_question = {
            'id': 'question-id',
            'question_text': 'Updated Question',
            'points_weight': 15
        }
        
        mock_result = Mock()
        mock_result.data = [mock_updated_question]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result
        
        updates = {
            'question_order_idx':'1',
            'question_text': 'Updated Question',
            'points_weight': 15,
            'option_a': 'A', 'option_b': 'B', 'option_c': 'C', 'option_d': 'D',
            'correct_answer': 'C'
        }
        
        result = self.question.update('question-id', updates)
        print(result)
        assert result["success"] is True
        assert result["data"]["question_text"] == "Updated Question"
        assert "updated_quiz" in result
        mock_update_totals.assert_called_once()
        mock_find_by_quiz.cache_clear.assert_called_once()

    def test_update_question_validation_errors(self):
        """Test question update fails with validation errors."""
        invalid_updates = {
            'question_text': '',  # Invalid
            'correct_answer': 'E',  # Invalid
            'points_weight': 0  # Invalid
        }
        
        result = self.question.update('question-id', invalid_updates)
        
        assert result["success"] is False
        assert "errors" in result
        assert 'question_text' in result["errors"]
        assert 'correct_answer' in result["errors"]
        assert 'points_weight' in result["errors"]
        
    @patch('app.models.quiz_question.QuizQuestion.find_by_id')
    def test_update_question_not_found_current(self,mock_find_by_id):
        """Test question update when current question doesn't exist."""
        # Mock find_by_id to return not found
        mock_find_by_id.return_value= {
            "success": False,
            "error": "Question not found"
        }
        
        updates = {
            'question_order_idx':'1',
            'question_text': 'Updated Question',
            'points_weight': 15,
            'option_a': 'A', 'option_b': 'B', 'option_c': 'C', 'option_d': 'D',
            'correct_answer': 'C'
        }
        
        result = self.question.update('nonexistent-id', updates)
        
        assert result["success"] is False
        assert result["error"] == "Question not found"

    @patch('app.models.quiz_question.QuizQuestion.find_by_id')
    def test_update_question_database_failure(self,mock_find_by_id):
        """Test question update when update operation fails."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.question.supabase = mock_supabase
        
        # Mock find_by_id to succeed
        mock_find_by_id.return_value = {
            "success": True,
            "data": {"quiz_id": "quiz-id"}
        }
        
        # Mock update operation to find no records
        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result
        
        updates = {
            'question_order_idx':'1',
            'question_text': 'Updated Question',
            'points_weight': 15,
            'option_a': 'A', 'option_b': 'B', 'option_c': 'C', 'option_d': 'D',
            'correct_answer': 'C'
        }
        
        result = self.question.update('question-id', updates)
        
        assert result["success"] is False
        assert result["error"] == "Failed to update question"
    
class TestQuizQuestionDeleteByQuiz:
    """Test deleting questions by quiz."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.question = QuizQuestion()

    @patch('app.models.quiz_question.QuizQuestion._update_quiz_totals')
    @patch('app.models.quiz_question.QuizQuestion.find_by_quiz')
    def test_delete_by_quiz_success(self,mock_find_by_quiz,mock_update_quiz_totals):
        """Test successful deletion of questions by quiz."""
        # Mock the supabase instance
        mock_supabase = Mock()
        self.question.supabase = mock_supabase
        mock_find_by_quiz.cache_clear = Mock()
        
        # Mock _update_quiz_totals
        mock_update_quiz_totals.return_value = {"data": "quiz_data"}
        
        mock_result = Mock()
        mock_result.data = [{'id': 'q1'}, {'id': 'q2'}]
        mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_result
        
        result = self.question.delete_by_quiz('quiz-id')
        
        assert result["success"] is True
        assert result["message"] == "All questions deleted successfully"
        mock_find_by_quiz.cache_clear.assert_called_once()
        mock_update_quiz_totals.assert_called_once_with('quiz-id')
    
    @patch('app.models.quiz_question.QuizQuestion._update_quiz_totals')
    @patch('app.models.quiz_question.QuizQuestion.find_by_quiz')
    def test_delete_by_quiz_database_error(self,mock_find_by_quiz,mock_update_quiz_totals):
        """Test delete_by_quiz handles database errors."""
        # Mock the supabase instance to raise an exception
        mock_supabase = Mock()
        self.question.supabase = mock_supabase
        mock_supabase.table.side_effect = Exception("Database error")
        
        result = self.question.delete_by_quiz('quiz-id')
        
        assert result["success"] is False
        assert "Database error" in result["error"]
        mock_find_by_quiz.cache_clear.assert_not_called()
        mock_update_quiz_totals.assert_not_called()