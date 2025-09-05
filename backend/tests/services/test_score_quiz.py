import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from app.services.score_quiz import _score_quiz_submission

def test_score_quiz_all_correct():
    """Test scoring with all correct answers."""
    questions = [
        {"id": "1", "correct_answer": "A", "points_weight": 10},
        {"id": "2", "correct_answer": "B", "points_weight": 15}
    ]
    user_answers = {"1": "A", "2": "B"}
    total_points = 25
    
    result = _score_quiz_submission(questions, user_answers, total_points)
    
    assert result["score"] == 25
    assert result["percentage"] == 100.0
    assert result["questions_correct"] == 2
    assert result["questions_total"] == 2
    assert result["status"] == "completed"
    assert len(result["detailed_results"]) == 2

def test_score_quiz_all_wrong():
    """Test scoring with all wrong answers."""
    questions = [
        {"id": "1", "correct_answer": "A", "points_weight": 10},
        {"id": "2", "correct_answer": "B", "points_weight": 15}
    ]
    user_answers = {"1": "C", "2": "D"}
    total_points = 25
    
    result = _score_quiz_submission(questions, user_answers, total_points)
    
    assert result["score"] == 0
    assert result["percentage"] == 0.0
    assert result["questions_correct"] == 0
    assert result["questions_total"] == 2

def test_score_quiz_partial_correct():
    """Test scoring with some correct answers."""
    questions = [
        {"id": "1", "correct_answer": "A", "points_weight": 10},
        {"id": "2", "correct_answer": "B", "points_weight": 20}
    ]
    user_answers = {"1": "A", "2": "C"}  # First correct, second wrong
    total_points = 30
    
    result = _score_quiz_submission(questions, user_answers, total_points)
    
    assert result["score"] == 10
    assert result["percentage"] == 33.33
    assert result["questions_correct"] == 1
    assert result["questions_total"] == 2

def test_score_quiz_missing_answers():
    """Test scoring with some missing answers."""
    questions = [
        {"id": "1", "correct_answer": "A", "points_weight": 10},
        {"id": "2", "correct_answer": "B", "points_weight": 10}
    ]
    user_answers = {"1": "A"}  # Missing answer for question 2
    total_points = 20
    
    result = _score_quiz_submission(questions, user_answers, total_points)
    
    assert result["score"] == 10
    assert result["percentage"] == 50.0
    assert result["questions_correct"] == 1
    assert result["questions_total"] == 2

def test_score_quiz_empty_answers():
    """Test scoring with no answers provided."""
    questions = [
        {"id": "1", "correct_answer": "A", "points_weight": 10}
    ]
    user_answers = {}
    total_points = 10
    
    result = _score_quiz_submission(questions, user_answers, total_points)
    
    assert result["score"] == 0
    assert result["percentage"] == 0.0
    assert result["questions_correct"] == 0
    assert result["questions_total"] == 1

def test_score_quiz_zero_total_points():
    """Test scoring edge case with zero total points."""
    questions = [
        {"id": "1", "correct_answer": "A", "points_weight": 0}
    ]
    user_answers = {"1": "A"}
    total_points = 0
    
    result = _score_quiz_submission(questions, user_answers, total_points)
    
    assert result["score"] == 0
    assert result["percentage"] == 0  # Should handle division by zero
    assert result["questions_correct"] == 1  # Still counts as correct
    assert result["questions_total"] == 1

def test_score_quiz_detailed_results():
    """Test that detailed results are correctly formatted."""
    questions = [
        {"id": "q1", "correct_answer": "A", "points_weight": 5},
        {"id": "q2", "correct_answer": "B", "points_weight": 10}
    ]
    user_answers = {"q1": "A", "q2": "C"}
    total_points = 15
    
    result = _score_quiz_submission(questions, user_answers, total_points)
    
    detailed = result["detailed_results"]
    assert len(detailed) == 2
    
    # Check first question (correct)
    assert detailed[0]["question_id"] == "q1"
    assert detailed[0]["user_answer"] == "A"
    assert detailed[0]["correct_answer"] == "A"
    assert detailed[0]["is_correct"] == True
    assert detailed[0]["points_weight"] == 5
    
    # Check second question (wrong)
    assert detailed[1]["question_id"] == "q2"
    assert detailed[1]["user_answer"] == "C"
    assert detailed[1]["correct_answer"] == "B"
    assert detailed[1]["is_correct"] == False
    assert detailed[1]["points_weight"] == 10