from flask import Blueprint, request, jsonify
from datetime import datetime
from app.models.quiz import quiz_model
from app.models.quiz_question import quiz_question_model
from app.models.quiz_submission import quiz_submission_model
from app.models.quiz_progress import user_quiz_progress_model
from app.routes.utility import get_current_sa_time,to_sa_time

student_quizzes = Blueprint('student_quizzes', __name__)

@student_quizzes.route('/api/quizzes/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics for the quizzes page"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        #Get total quizzes
        quizzes = quiz_model.find_all({"status":"published"})
        # Get user's dashboard statistics
        stats_result = user_quiz_progress_model.get_user_dashboard_stats(user_id)
        if not stats_result["success"]:
            return jsonify({"error": stats_result["error"]}), 500
        
        stats = stats_result["data"]
        
        # Get user's global rank
        rank_result = user_quiz_progress_model.get_user_global_rank(user_id)
        user_rank = None
        if rank_result["success"] and rank_result["data"]["rank"]:
            user_rank = rank_result["data"]["rank"]
        
        return jsonify({
            "message": "Dashboard stats retrieved successfully",
            "data": {
                "total_quizzes": len(quizzes["data"]),
                "completed_quizzes": stats["completed_quizzes"],
                "average_score": stats["average_score"],
                "user_global_rank": user_rank,
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@student_quizzes.route('/api/quizzes', methods=['GET'])
def list_quizzes():
    """Get all available quizzes with user progress and class statistics"""
    try:
        # Get query parameters
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        # Get quizzes with user progress
        result = user_quiz_progress_model.get_quizzes_with_progress(user_id)
        
        if not result["success"]:
            return jsonify({"error": result["error"]}), 500
        
        quizzes = result["data"]
        
        # For each quiz, get class statistics
        enhanced_quizzes = []
        for quiz in quizzes:
            if quiz['due_date']:
                due_date_str = to_sa_time(quiz['due_date'])
                due_date = datetime.fromisoformat(due_date_str.replace('Z', ''))
                if get_current_sa_time() > due_date:
                    continue
            total_points = quiz.get('total_points', 0)
            quiz_stats = quiz_submission_model.get_quiz_statistics(quiz['id'],total_points)
            
            # Determine status based on user progress
            user_progress = quiz.get('user_progress', {})
            if user_progress.get('status') == 'completed':
                status = 'completed'
            else:
                status = 'available'
            
            quiz_data = {
                # Quiz info
                "id": quiz['id'],
                "title": quiz['title'],
                "description": quiz.get('description'),
                "total_points": quiz['total_points'],
                "total_questions":quiz['total_questions'],
                "published_at": quiz['published_at'],
                "due_date": quiz['due_date'],
                "time_limit_minutes": quiz['time_limit_minutes'],
                "allow_multiple_attempts":quiz['allow_multiple_attempts'],
                "status": status,
                
                # Class statistics
                "class_statistics": quiz_stats["data"] if quiz_stats["success"] else {
                    "users_attempted": 0,
                    "users_passed": 0,
                    "pass_rate": 0,
                    "average_score": 0
                },
                
                # User performance
                "user_performance": {
                    "best_score": user_progress.get('best_score', 0),
                    "best_percentage": user_progress.get('best_percentage', 0),
                    "attempts_count": user_progress.get('attempts_count', 0)
                }
            }
            enhanced_quizzes.append(quiz_data)
        
        return jsonify({
            "message": "Quizzes retrieved successfully",
            "data": {
                "quizzes": enhanced_quizzes,
                "total_count": len(enhanced_quizzes)
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@student_quizzes.route('/api/quizzes/<quiz_id>', methods=['GET'])
def get_quiz_details(quiz_id):
    """Get detailed quiz information for taking the quiz"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        # Get quiz details
        quiz_result = quiz_model.find_by_id(quiz_id)
        if not quiz_result["success"]:
            return jsonify({"error": "Quiz not found"}), 404
        
        quiz = quiz_result["data"]
        
        # Only show published quizzes to students
        if quiz["status"] != "published":
            return jsonify({"error": "Quiz not available"}), 403
        
        # Get questions (without correct answers for students)
        questions_result = quiz_question_model.find_by_quiz(quiz_id, include_answers=False)
        questions = questions_result["data"] if questions_result["success"] else []
        
        return jsonify({
            "message": "Quiz details retrieved successfully",
            "data": {
                **quiz,
                "questions": questions
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@student_quizzes.route('/api/quizzes/<quiz_id>/submit', methods=['POST'])
def submit_quiz(quiz_id):
    """Submit quiz answers and get results"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        user_id = data.get('user_id')
        answers = data.get('answers', {})  # {"question_id": "A", ...}
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        # Verify quiz exists and is published
        quiz_result = quiz_model.find_by_id(quiz_id)
        if not quiz_result["success"] or quiz_result["data"]["status"] != "published":
            return jsonify({"error": "Quiz not found or not available"}), 404
        
        quiz = quiz_result["data"]
        # Create submission
        submission_result = quiz_submission_model.create(quiz_id, user_id, answers)
        if not submission_result["success"]:
            if submission_result.get("errors"):
                return jsonify({"error": submission_result["errors"]}), 400
            return jsonify({"error": submission_result["error"]}), 500
        
        submission = submission_result["data"]
        submission_id = submission["id"]
        
        # Get questions with correct answers for scoring
        questions_result = quiz_question_model.find_by_quiz(quiz_id, include_answers=True)
        if not questions_result["success"]:
            return jsonify({"error": "Failed to get quiz questions"}), 500
        
        questions = questions_result["data"]
        
        # Score the submission
        scoring_result = _score_quiz_submission(questions, answers, quiz["total_points"])
        
        # Update submission with results
        update_result = quiz_submission_model.update_results(submission_id, scoring_result)
        if not update_result["success"]:
            return jsonify({"error": "Failed to update submission results"}), 500
        
        final_submission = update_result["data"]
        
        # Update user progress
        progress_update = {
            "submission_id": submission_id,
            "score": final_submission["score"],
            "percentage": final_submission["percentage"],
            "status": final_submission["status"]
        }
        
        user_quiz_progress_model.update_progress(user_id, quiz_id, progress_update)
        
        return jsonify({
            "message": "Quiz submitted successfully",
            "data": {
                "submission": final_submission,
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@student_quizzes.route('/api/quizzes/<quiz_id>/results', methods=['GET'])
def get_quiz_results(quiz_id):
    """Get detailed results for user's best submission"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        # Get user's best submission for this quiz
        best_submission_result = quiz_submission_model.get_best_submission(user_id, quiz_id)
        if not best_submission_result["success"]:
            return jsonify({"error": "No submissions found for this quiz"}), 404
        
        submission = best_submission_result["data"]
        
        # Get quiz details
        quiz_result = quiz_model.find_by_id(quiz_id)
        if not quiz_result["success"]:
            return jsonify({"error": "Quiz not found"}), 404
        
        quiz = quiz_result["data"]
        
        # Get questions with correct answers
        questions_result = quiz_question_model.find_by_quiz(quiz_id, include_answers=True)
        questions = questions_result["data"] if questions_result["success"] else []
        
        return jsonify({
            "message": "Quiz results retrieved successfully",
            "data": {
                "quiz": quiz,
                "submission": submission,
                "questions": questions
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@student_quizzes.route('/api/quizzes/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get leaderboard for quizzes"""
    try:
        quiz_id = request.args.get('quiz_id')
        limit = request.args.get('limit', 500)
        
        if quiz_id:
            # Quiz-specific leaderboard
            leaderboard_result = user_quiz_progress_model.get_leaderboard(quiz_id, int(limit))
        else:
            # Global leaderboard
            leaderboard_result = user_quiz_progress_model.get_global_leaderboard(int(limit))
        
        if not leaderboard_result["success"]:
            return jsonify({"error": leaderboard_result["error"]}), 500
        
        return jsonify({
            "message": "Leaderboard retrieved successfully",
            "data": {
                "leaderboard": leaderboard_result["data"],
                "quiz_id": quiz_id,
                "limit": int(limit)
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _score_quiz_submission(questions, user_answers, total_points):
    """Score a quiz submission and return results"""
    questions_correct = 0
    questions_total = len(questions)
    detailed_results = []
    total_score = 0
    
    for question in questions:
        question_id = question["id"]
        correct_answer = question["correct_answer"]
        points_weight = question["points_weight"]
        user_answer = user_answers.get(question_id)
        
        is_correct = user_answer == correct_answer if user_answer is not None else False
        points_earned = points_weight if is_correct else 0
        
        if is_correct:
            questions_correct += 1
            total_score += points_earned
        
        detailed_results.append({
            "question_id": question_id,
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "points_weight":points_weight
        })
    
    # Calculate percentage
    percentage = (total_score / total_points * 100) if total_points > 0 else 0
    
    return {
        "score": total_score,
        "percentage": round(percentage, 2),
        "questions_correct": questions_correct,
        "questions_total": questions_total,
        "detailed_results": detailed_results,
        "status": "completed"
    }