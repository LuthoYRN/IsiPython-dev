from flask import Blueprint, jsonify
from app.models.challenge import challenge_model
from app.models.quiz import quiz_model
from app.models.challenge_submission import challenge_submission_model
from app.models.student import student_model
from app.models.quiz_submission import quiz_submission_model
from app.utils.utility import get_week_start

admin_dashboard = Blueprint('admin_dashboard', __name__)

@admin_dashboard.route('/api/admin/dashboard/stats', methods=['GET'])
def get_admin_dashboard_stats():
    """Get admin dashboard overview statistics"""
    try:
        week_start = get_week_start()
        
        # === TOTAL STUDENTS ===
        students_result = student_model.get_student_count()
        total_students = students_result.get("count", 0) if students_result.get("success") else 0
        
        # Calculate growth - students added this week
        new_students_result = student_model.get_students_added_since(week_start)
        new_students_this_week = new_students_result.get("count", 0) if new_students_result.get("success") else 0
        
        # Calculate percentage growth
        students_growth = 0
        if total_students > 0:
            students_growth = (new_students_this_week / total_students) * 100
        
        # === ACTIVE CHALLENGES ===
        active_challenges_result = challenge_model.find_all({"status": "published"})
        total_active_challenges = len(active_challenges_result["data"]) if active_challenges_result["success"] else 0
        
        # Challenges published this week
        challenges_week_result = challenge_model.get_challenges_published_since(week_start)
        new_challenges_this_week = len(challenges_week_result["data"]) if challenges_week_result["success"] and challenges_week_result["data"] else 0
        
        # Calculate percentage growth
        challenges_growth = 0
        if total_active_challenges > 0:
            challenges_growth = (new_challenges_this_week / total_active_challenges) * 100
        
        # === ACTIVE QUIZZES ===
        active_quizzes_result = quiz_model.find_all({"status": "published"})
        total_active_quizzes = len(active_quizzes_result["data"]) if active_quizzes_result["success"] else 0
        
        # Quizzes published this week
        quizzes_week_result = quiz_model.get_quizzes_published_since(week_start)
        new_quizzes_this_week = len(quizzes_week_result["data"]) if quizzes_week_result["success"] and quizzes_week_result["data"] else 0
        
        # Calculate percentage growth
        quizzes_growth = 0
        if total_active_quizzes > 0:
            quizzes_growth = (new_quizzes_this_week / total_active_quizzes) * 100
        
        # === TOTAL SUBMISSIONS ===
        # Count challenge submissions
        challenge_count_result = challenge_submission_model.count_submissions()
        total_challenge_submissions = challenge_count_result.get("count", 0) if challenge_count_result.get("success") else 0
        
        # Count quiz submissions
        quiz_count_result = quiz_submission_model.count_submissions()
        total_quiz_submissions = quiz_count_result.get("count", 0) if quiz_count_result.get("success") else 0
        
        total_submissions = total_challenge_submissions + total_quiz_submissions
        
        # Submissions this week
        challenge_subs_week_result = challenge_submission_model.get_challenge_submissions_since(week_start)
        quiz_subs_week_result = quiz_submission_model.get_quiz_submissions_since(week_start)
        
        challenge_subs_count = len(challenge_subs_week_result["data"]) if challenge_subs_week_result.get("success") and challenge_subs_week_result["data"] else 0
        quiz_subs_count = len(quiz_subs_week_result["data"]) if quiz_subs_week_result.get("success") and quiz_subs_week_result["data"] else 0
        
        new_submissions_this_week = challenge_subs_count + quiz_subs_count
        
        # Calculate percentage growth
        submissions_growth = 0
        if total_submissions > 0:
            submissions_growth = (new_submissions_this_week / total_submissions) * 100
        
        # === RECENT CHALLENGES (all statuses, based on updated_at) ===
        recent_challenges = []
        all_challenges_result = challenge_model.find_all({})  # Get all challenges (drafts + published)
        if all_challenges_result["success"]:
            # Get recent challenges sorted by updated_at
            recent_challenges_data = sorted(
                all_challenges_result["data"], 
                key=lambda x: x.get('updated_at', x.get('created_at', '')), 
                reverse=True
            )[:3]
            
            for challenge in recent_challenges_data:
                recent_challenges.append({
                    "id": challenge["id"],
                    "title": challenge["title"],
                    "difficulty": challenge.get("difficulty", "medium"),
                    "status": challenge["status"]
                })
        
        # === RECENT QUIZZES (all statuses, based on updated_at) ===
        recent_quizzes = []
        all_quizzes_result = quiz_model.find_all({})  # Get all quizzes (drafts + published)
        if all_quizzes_result["success"]:
            # Get recent quizzes sorted by updated_at
            recent_quizzes_data = sorted(
                all_quizzes_result["data"], 
                key=lambda x: x.get('updated_at', x.get('created_at', '')), 
                reverse=True
            )[:3]
            
            for quiz in recent_quizzes_data:
                recent_quizzes.append({
                    "id": quiz["id"],
                    "title": quiz["title"],
                    "total_questions": quiz.get("total_questions", 0),
                    "status": quiz["status"]
                })
        
        return jsonify({
            "message": "Admin dashboard stats retrieved successfully",
            "data": {
                "overview": {
                    "total_students": {
                        "count": total_students,
                        "growth_percentage": round(students_growth, 1),
                        "new_this_week": new_students_this_week
                    },
                    "active_challenges": {
                        "count": total_active_challenges,
                        "growth_percentage": round(challenges_growth, 1),
                        "new_this_week": new_challenges_this_week
                    },
                    "active_quizzes": {
                        "count": total_active_quizzes,
                        "growth_percentage": round(quizzes_growth, 1),
                        "new_this_week": new_quizzes_this_week
                    },
                    "total_submissions": {
                        "count": total_submissions,
                        "growth_percentage": round(submissions_growth, 1),
                        "new_this_week": new_submissions_this_week
                    }
                },
                "recent_challenges": recent_challenges,
                "recent_quizzes": recent_quizzes
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500