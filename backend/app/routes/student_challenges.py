from flask import Blueprint, request, jsonify
from app.models.challenge import challenge_model
from app.services.challenge_executor import execute_challenge_submission
from app.models.challenge_testcase import challenge_test_case_model
from app.models.challenge_submission import challenge_submission_model
from app.models.challenge_progress import user_challenge_progress_model

student_challenges = Blueprint('student_challenges', __name__)

@student_challenges.route('/api/challenges/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics for the challenges page"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        # Get user's dashboard statistics
        stats_result = user_challenge_progress_model.get_user_dashboard_stats(user_id)
        if not stats_result["success"]:
            return jsonify({"error": stats_result["error"]}), 500
        
        stats = stats_result["data"]
        
        # Get user's global rank
        rank_result = user_challenge_progress_model.get_user_global_rank(user_id)
        user_rank = None
        if rank_result["success"] and rank_result["data"]["rank"]:
            user_rank = rank_result["data"]["rank"]
        
        return jsonify({
            "message": "Dashboard stats retrieved successfully",
            "data": {
                "completed_challenges": stats["completed_challenges"],
                "total_points_earned": stats["total_points_earned"],
                "success_rate": stats["completion_rate"],
                "user_global_rank": user_rank,
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@student_challenges.route('/api/challenges', methods=['GET'])
def list_challenges():
    """Get all available challenges with user progress"""
    try:
        # Get query parameters
        user_id = request.args.get('user_id')
        difficulty = request.args.get('difficulty')
        search = request.args.get('search')
        limit = request.args.get('limit', 20)
        order_by = request.args.get('order_by', 'created_at')
        order_direction = request.args.get('order_direction', 'asc')
        
        # Build filters
        filters = {
            'limit': int(limit),
            'order_by': order_by,
            'order_direction': order_direction
        }
        
        if difficulty:
            filters['difficulty_level'] = difficulty
        if search:
            filters['search'] = search
        
        # Get challenges with user progress
        if user_id:
            result = user_challenge_progress_model.get_challenges_with_progress(user_id, filters)
        else:  
            return jsonify({"error": "user_id is required"}), 400
        
        if not result["success"]:
            return jsonify({"error": result["error"]}), 500
        
        challenges = result["data"]
        
        # For each challenge, get additional statistics (pass rate, users completed)
        enhanced_challenges = []
        for challenge in challenges:
            challenge_stats = challenge_submission_model.get_challenge_statistics(challenge['id'])
            
            challenge_data = {
                **challenge,
                "statistics": challenge_stats["data"] if challenge_stats["success"] else {
                    "users_attempted": 0,
                    "users_completed": 0, 
                    "pass_rate": 0
                }
            }
            enhanced_challenges.append(challenge_data)
        
        return jsonify({
            "message": "Challenges retrieved successfully",
            "data": {
                "challenges": enhanced_challenges,
                "total_count": len(enhanced_challenges),
                "filters_applied": filters
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@student_challenges.route('/api/challenges/<challenge_id>', methods=['GET'])
def get_challenge_details(challenge_id):
    """Get detailed challenge information for the challenge page"""
    try:
        user_id = request.args.get('user_id')
        
        # Get challenge details
        challenge_result = challenge_model.find_by_id(challenge_id)
        if not challenge_result["success"]:
            return jsonify({"error": "Challenge not found"}), 404
        
        challenge = challenge_result["data"]
        
        # Only show published challenges to students 
        if challenge["status"] != "published":
            return jsonify({"error": "Challenge not available"}), 403
        
        # Get test cases 
        test_cases_result = challenge_test_case_model.find_by_challenge(challenge_id)
        test_cases = []
        
        if test_cases_result["success"]:
            for test_case in test_cases_result["data"]:
                # Only include non-hidden example test cases and input data
                if not test_case.get('is_hidden', False) and test_case.get('is_example'):
                    student_test_case = {
                        "input_data": test_case["input_data"],
                        "explanation": test_case.get("explanation"),
                        "expected_output":test_case.get("expected_output")
                    }          
                    test_cases.append(student_test_case)

        # Get user's submissions for this challenge
        submissions_result = challenge_submission_model.find_by_user_and_challenge(
            user_id, challenge_id
        )
        
        submissions = submissions_result["data"]
        
        # Get user's progress summary
        summary_result = challenge_submission_model.get_user_challenge_summary(user_id, challenge_id)
        summary = summary_result["data"] if summary_result["success"] else {}
        
        
        return jsonify({
            "message": "Challenge details retrieved successfully",
            "data": {
                **challenge,
                "test_cases": test_cases,
                "submissions": submissions,
                "summary": summary,
                "total_submissions": len(submissions)
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@student_challenges.route('/api/challenges/<challenge_id>/progress', methods=['GET'])
def get_user_progress(challenge_id):
    """Get user's progress on a specific challenge"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        # Verify challenge exists
        challenge_result = challenge_model.find_by_id(challenge_id)
        if not challenge_result["success"]:
            return jsonify({"error": "Challenge not found"}), 404
        
        # Get user's progress
        progress_result = user_challenge_progress_model.get_user_progress(user_id, challenge_id)
        if not progress_result["success"]:
            return jsonify({"error": progress_result["error"]}), 500
        
        progress = progress_result["data"]
        
        # Get user's best submission details
        best_submission = None
        if progress.get("best_submission_id"):
            best_result = challenge_submission_model.find_by_id(
                progress["best_submission_id"], user_id
            )
            if best_result["success"]:
                best_submission = best_result["data"]
        
        return jsonify({
            "message": "User progress retrieved successfully",
            "data": {
                "progress": progress,
                "best_submission": best_submission
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@student_challenges.route('/api/challenges/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get leaderboard for challenges"""
    try:
        challenge_id = request.args.get('challenge_id')  
        limit = request.args.get('limit', 50)
        
        if challenge_id:
            # Challenge-specific leaderboard
            leaderboard_result = user_challenge_progress_model.get_leaderboard(
                challenge_id, int(limit)
            )
        else:
            # Global leaderboard
            leaderboard_result = user_challenge_progress_model.get_global_leaderboard(int(limit))
        
        if not leaderboard_result["success"]:
            return jsonify({"error": leaderboard_result["error"]}), 500
        
        return jsonify({
            "message": "Leaderboard retrieved successfully",
            "data": {
                "leaderboard": leaderboard_result["data"],
                "challenge_id": challenge_id,
                "limit": int(limit)
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@student_challenges.route('/api/challenges/<challenge_id>/submit', methods=['POST'])
def submit_challenge_solution(challenge_id):
    """Submit code solution for a challenge"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        user_id = data.get('user_id')
        code = data.get('code')
        
        # Validate required fields
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        if not code or not code.strip():
            return jsonify({"error": "Code is required"}), 400
        
        # Verify challenge exists and is published
        challenge_result = challenge_model.find_by_id(challenge_id)
        if not challenge_result["success"]:
            return jsonify({"error": "Challenge not found"}), 404
        
        challenge = challenge_result["data"]
        
        # Only allow submissions to published challenges
        if challenge["status"] != "published":
            return jsonify({"error": "Challenge is not available for submission"}), 403
        
        # Execute the submission
        execution_result = execute_challenge_submission(
            challenge_id, user_id, code
        )
        
        if not execution_result["success"]:
            return jsonify({"error": execution_result["error"]}), 500
        
        # Return detailed results
        response_data = {
            "message": "Code submitted and executed successfully",
            "submission_id": execution_result["submission_id"],
            "status": execution_result["status"],
            "score": execution_result["score"],
            "tests_passed": execution_result["tests_passed"],
            "tests_total": execution_result["tests_total"]
        }
        if execution_result.get("test_results"):
            response_data["test_results"] = execution_result["test_results"]
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@student_challenges.route('/api/challenges/<challenge_id>/submissions/<user_id>', methods=['GET'])
def get_user_challenge_submissions(challenge_id, user_id):
    """Get user's submission history for a challenge"""
    try: 
        limit = request.args.get('limit', 10)
        
        submissions_result = challenge_submission_model.find_by_user_and_challenge(
            user_id, challenge_id, int(limit)
        )
        
        if not submissions_result["success"]:
            return jsonify({"error": submissions_result["error"]}), 500
        
        return jsonify({
            "message": "Submissions retrieved successfully",
            "data": submissions_result["data"]
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500