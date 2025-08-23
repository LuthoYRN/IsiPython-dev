from flask import Blueprint, request, jsonify
from app.models.challenge import challenge_model
from app.models.quiz import quiz_model
from app.models.challenge_progress import user_challenge_progress_model
from app.models.quiz_progress import user_quiz_progress_model
from app.utils.utility import get_week_start

student_dashboard = Blueprint('student_dashboard', __name__)

@student_dashboard.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        # Get week start for "this week" calculations
        week_start = get_week_start()
        
        # === CHALLENGES STATS ===
        # Get all challenges in system
        all_challenges = challenge_model.find_all({"status": "published"})
        total_challenges = len(all_challenges["data"]) if all_challenges["success"] else 0
        
        # Get user's challenge progress
        user_challenge_stats = user_challenge_progress_model.get_user_dashboard_stats(user_id)
        completed_challenges = 0
        challenges_this_week = 0
        
        if user_challenge_stats["success"]:
            completed_challenges = user_challenge_stats["data"].get("completed_challenges", 0)
            
            # Get challenges completed this week
            week_progress = user_challenge_progress_model.get_user_progress_since(user_id, week_start)
            if week_progress["success"]:
                challenges_this_week = len([p for p in week_progress["data"] if p.get("status") == "completed"])
        
        challenges_progress = (completed_challenges / total_challenges * 100) if total_challenges > 0 else 0
        
        # === QUIZZES STATS ===
        # Get all quizzes in system
        all_quizzes = quiz_model.find_all({"status": "published"})
        total_quizzes = len(all_quizzes["data"]) if all_quizzes["success"] else 0
        
        # Get user's quiz progress
        user_quiz_stats = user_quiz_progress_model.get_user_dashboard_stats(user_id)
        attempted_quizzes = 0
        quizzes_this_week = 0
        
        if user_quiz_stats["success"]:
            user_all_progress = user_quiz_progress_model.get_user_all_progress(user_id)
            if user_all_progress["success"]:
                attempted_quizzes = len([p for p in user_all_progress["data"] if p.get("attempts_count", 0) > 0])
            
            quiz_week_progress = user_quiz_progress_model.get_user_progress_since(user_id, week_start)
            if quiz_week_progress["success"]:
                quizzes_this_week = len([p for p in quiz_week_progress["data"] if p.get("status") == "completed"])
                  
        quizzes_progress = (attempted_quizzes / total_quizzes * 100) if total_quizzes > 0 else 0
        
        # === OVERALL PROGRESS ===
        total_items = total_challenges + total_quizzes
        completed_items = completed_challenges + attempted_quizzes
        overall_progress = (completed_items / total_items * 100) if total_items > 0 else 0
        
        # Determine progress message
        if overall_progress >= 90:
            progress_message = "Excellent progress!"
        elif overall_progress >= 70:
            progress_message = "Great work!"
        elif overall_progress >= 50:
            progress_message = "Good progress!"
        elif overall_progress >= 25:
            progress_message = "Keep going!"
        else:
            progress_message = "Just getting started!"
        
        return jsonify({
            "message": "Dashboard stats retrieved successfully",
            "data": {
                "challenges": {
                    "completed": completed_challenges,
                    "total": total_challenges,
                    "progress": round(challenges_progress, 1),
                    "this_week": challenges_this_week
                },
                "quizzes": {
                    "attempted": attempted_quizzes,
                    "total": total_quizzes,
                    "progress": round(quizzes_progress, 1),
                    "this_week": quizzes_this_week
                },
                "overall": {
                    "progress": round(overall_progress, 1),
                    "message": progress_message,
                    "completed_items": completed_items,
                    "total_items": total_items
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@student_dashboard.route('/api/dashboard/learning-path', methods=['GET'])
def get_learning_path():
    """Get learning path with priority-based filling"""
    try:
        user_id = request.args.get('user_id')
        limit = int(request.args.get('limit', 3))
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        learning_path = []
        
        # === PRIORITY 1: IN-PROGRESS ITEMS ===
        in_progress_items = []
        
        # Get in-progress challenges
        challenges_result = user_challenge_progress_model.get_challenges_with_progress(user_id)
        if challenges_result["success"]:
            for challenge in challenges_result["data"]:
                if challenge.get("user_progress", {}).get("status") == "in_progress":
                    in_progress_items.append({
                        "id": challenge["id"],
                        "title": challenge["title"],
                        "type": "challenge",
                        "status": "in_progress",
                    })
        
        # If we have enough in-progress items, return them
        if len(in_progress_items) >= limit:
            learning_path = in_progress_items[:limit]
        else:
            # Add all in-progress items
            learning_path.extend(in_progress_items)
            remaining_slots = limit - len(in_progress_items)
            
            # === PRIORITY 2: BALANCED MIX ===
            if remaining_slots > 0:
                # Get 1 completed item for confidence
                completed_quizzes = []
                completed_challenges = []
                                
                # Get recent completed quizzes
                quizzes_result = user_quiz_progress_model.get_quizzes_with_progress(user_id)
                if quizzes_result["success"]:
                    for quiz in quizzes_result["data"]:
                        if quiz.get("user_progress", {}).get("status") == "completed":
                            completed_quizzes.append({
                                "id": quiz["id"],
                                "title": quiz["title"],
                                "type": "quiz",
                                "status": "completed",
                            })
                
                # Get recent completed challenges
                if challenges_result["success"]:
                    for challenge in challenges_result["data"]:
                        if challenge.get("user_progress", {}).get("status") == "completed":
                            completed_challenges.append({
                                "id": challenge["id"],
                                "title": challenge["title"],
                                "type": "challenge",
                                "status": "completed",
                            })

                balanced_completed = balance_items(completed_challenges, completed_quizzes, remaining_slots)
                # Add 1 completed item if available and we have space
                if balanced_completed and remaining_slots > 1:
                    learning_path.append(balanced_completed[0])
                    remaining_slots -= 1
                
                # === PRIORITY 3: NOT STARTED ITEMS ===
                if remaining_slots > 0:
                    not_started_challenges = []
                    not_started_quizzes = []
                    
                    # Get not-started challenges
                    all_challenges = challenge_model.find_all({"status": "published"})
                    if all_challenges["success"]:
                        user_challenge_progress = user_challenge_progress_model.get_user_all_progress(user_id)
                        user_challenge_ids = []
                        if user_challenge_progress["success"]:
                            user_challenge_ids = [p["challenge_id"] for p in user_challenge_progress["data"]]
                        
                        for challenge in all_challenges["data"]:
                            if challenge["id"] not in user_challenge_ids:
                                not_started_challenges.append({
                                    "id": challenge["id"],
                                    "title": challenge["title"],
                                    "type": "challenge",
                                    "status": "not_started",
                                })
                    
                    # Get not-started quizzes
                    all_quizzes = quiz_model.find_all({"status": "published"})
                    if all_quizzes["success"]:
                        user_quiz_progress = user_quiz_progress_model.get_user_all_progress(user_id)
                        user_quiz_ids = []
                        if user_quiz_progress["success"]:
                            user_quiz_ids = [p["quiz_id"] for p in user_quiz_progress["data"]]
                        
                        for quiz in all_quizzes["data"]:
                            if quiz["id"] not in user_quiz_ids:
                                not_started_quizzes.append({
                                    "id": quiz["id"],
                                    "title": quiz["title"],
                                    "type": "quiz",
                                    "status": "not_started",
                                })
                    
                    # Add not-started items to fill remaining slots
                    balanced_not_started = balance_items(not_started_challenges, not_started_quizzes, remaining_slots)
                    learning_path.extend(balanced_not_started[:remaining_slots])
                
                # === FALLBACK: FILL WITH COMPLETED IF NOTHING ELSE ===
                if len(learning_path) < limit and balanced_completed:
                    remaining_slots = limit - len(learning_path)
                    learning_path.extend(balanced_completed[1:remaining_slots+1])
        
        return jsonify({
            "message": "Learning path retrieved successfully",
            "data": learning_path[:limit]
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def balance_items(challenges, quizzes, limit):
    """Balance challenges and quizzes 50/50"""
    if not challenges and not quizzes:
        return []
    if not challenges:
        return quizzes[:limit]
    if not quizzes:
        return challenges[:limit]
    
    # Aim for 50/50 split
    half = limit // 2
    
    # Take equal amounts, or whatever's available
    challenge_count = min(half, len(challenges))
    quiz_count = min(half, len(quizzes))
    
    # If one type has fewer items, give remaining slots to the other
    remaining_slots = limit - challenge_count - quiz_count
    if remaining_slots > 0:
        if len(challenges) > challenge_count:
            challenge_count += min(remaining_slots, len(challenges) - challenge_count)
        elif len(quizzes) > quiz_count:
            quiz_count += min(remaining_slots, len(quizzes) - quiz_count)
    
    # Interleave for variety
    result = []
    for i in range(max(challenge_count, quiz_count)):
        if i < challenge_count:
            result.append(challenges[i])
        if i < quiz_count and len(result) < limit:
            result.append(quizzes[i])
    
    return result[:limit]
