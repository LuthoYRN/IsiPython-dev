from flask import Blueprint, request, jsonify
from app.models.quiz import quiz_model
from app.models.quiz_question import quiz_question_model
from app.models.quiz_submission import quiz_submission_model

admin_quizzes = Blueprint('admin_quizzes', __name__)

@admin_quizzes.route('/api/admin/quizzes', methods=['POST'])
def create_or_update_quiz():
    """Create new quiz or update existing quiz"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract key fields
        quiz_id = data.get('id')  # If provided, we're updating
        questions = data.get('questions', [])
        action = data.get('action', 'save_draft')  # save_draft | publish
        valid_actions = ['save_draft', 'publish'] 
        if action not in valid_actions:
            return jsonify({
                "error": f"Invalid action. Must be one of: {', '.join(valid_actions)}"
            }), 400     
        # STEP 1: Check if we need to publish but don't have questions
        if action == 'publish' and not questions:
            return jsonify({"error": "Cannot publish quiz without questions"}), 400
        
        # STEP 2: Determine if we're creating or updating
        if quiz_id:
            # UPDATE EXISTING QUIZ
            result = _update_existing_quiz(quiz_id, data)
        else:
            # CREATE NEW QUIZ
            result = _create_new_quiz(data)
        
        if result["success"]:
            return jsonify({
                "message": "Quiz saved successfully" if action != 'publish' else "Quiz published successfully",
                "data": result["data"]
            }), 200 if quiz_id else 201
        else:
            # Handle validation errors vs other errors
            if "errors" in result:
                return jsonify({"errors": result["errors"]}), 400
            else:
                return jsonify({"error": result["error"]}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _create_new_quiz(data):
    """Create a new quiz with questions"""
    try:
        # STEP 1: Extract questions from data before creating quiz
        questions = data.get('questions', [])
        quiz_data = {k: v for k, v in data.items() if k not in ['questions', 'action']}
               
        # STEP 2: Create the quiz first (without questions)
        quiz_result = quiz_model.create(quiz_data)
        if not quiz_result["success"]:
            return quiz_result
        
        quiz = quiz_result["data"]
        quiz_id = quiz["id"]
        
        # STEP 3: Create questions if provided
        created_questions = []
        if questions:
            # Add question order indices if not provided
            for i, question in enumerate(questions):
                if not question.get('question_order_idx'):
                    question['question_order_idx'] = str(i + 1)
            
            question_result = quiz_question_model.create_bulk(quiz_id, questions)
            if question_result["success"]:
                created_questions = question_result["data"]
                quiz = question_result["updated_quiz"]
            else:
                # If questions fail, clean up by deleting the quiz
                quiz_model.delete(quiz_id)
                return {
                    "success": False,
                    "errors": f"Failed to create questions: {question_result.get('errors')}" if question_result.get('errors') else None,
                    "error": f"Failed to create questions: {question_result.get('error')}" if question_result.get('error') else "Unknown error"
                }
        
        # STEP 4: If action is publish and we have questions, update status to published
        action = data.get('action', 'save_draft')
        if action == 'publish' and created_questions:
            publish_result = quiz_model.update(quiz_id, {
                **quiz,
                'status':'published',
                'published_at':'now()'
            })
            if publish_result["success"]:
                quiz = publish_result["data"]  # Get updated quiz with published status
        
        # STEP 6: Return complete quiz with questions
        return {
            "success": True,
            "data": {
                **quiz,
                "questions": created_questions
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def _update_existing_quiz(quiz_id, data):
    """Update existing quiz and its questions"""
    try:
        # STEP 1: Check if quiz exists
        existing_quiz = quiz_model.find_by_id(quiz_id)
        quiz_data = existing_quiz["data"]
        if not existing_quiz["success"]:
            return {"success": False, "error": "Quiz not found"}
        
        quiz_updates = {k: v for k, v in data.items() 
                       if k not in ['id', 'questions', 'action']}
        questions = data.get('questions', [])
        updated_questions = []
        
        # STEP 2: Handle questions if provided
        if questions and not quiz_data['status'] == 'published':
            # Delete existing questions first
            quiz_question_model.delete_by_quiz(quiz_id)
            
            # Add question order indices if not provided
            for i, question in enumerate(questions):
                if not question.get('question_order_idx'):
                    question['question_order_idx'] = str(i + 1)
            
            # Create new questions
            question_result = quiz_question_model.create_bulk(quiz_id, questions)
            if question_result["success"]:
                updated_questions = question_result["data"]
            else:
                return {
                    "success": False,
                    "error": f"Failed to update questions: {question_result.get('error', question_result.get('errors', 'Unknown error'))}"
                }
        elif not questions and not quiz_data['status'] == 'published':
            quiz_question_model.delete_by_quiz(quiz_id) #empty question array and save as draft
        else:
            # Get existing questions - cannot edit questions if status is published
            existing_questions = quiz_question_model.find_by_quiz(quiz_id)
            if existing_questions["success"]:
                updated_questions = existing_questions["data"]
        
        # STEP 3: Update quiz info
        action = data.get('action', 'save_draft')
        if action == 'publish':
            quiz_updates['status'] = 'published'
            quiz_updates['published_at']='now()'
        elif action == 'save_draft':
            quiz_updates['status'] = 'draft'
            quiz_updates['published_at']=None
        
        quiz_result = quiz_model.update(quiz_id, quiz_updates)
        if not quiz_result["success"]:
            return quiz_result
        
        # STEP 4: Return complete quiz with questions
        return {
            "success": True,
            "data": {
                **quiz_result["data"],
                "questions": updated_questions
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@admin_quizzes.route('/api/admin/quizzes', methods=['GET'])
def list_quizzes():
    """List all quizzes with optional filtering and statistics"""
    try:
        # Get query parameters
        filters = {
            'status': request.args.get('status'),
            'search': request.args.get('search'),
            'order_by': request.args.get('order_by', 'created_at'),
            'order_direction': request.args.get('order_direction', 'desc')
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        result = quiz_model.find_all(filters)
        
        if not result["success"]:
            return jsonify({"error": result["error"]}), 500
        
        quizzes = result["data"]

        import json
        quiz_ids = [quiz['id'] for quiz in quizzes]
        batch_stats_result = quiz_submission_model.get_batch_quiz_statistics_rpc(
            json.dumps(quiz_ids, sort_keys=True)  # Sorted for consistent caching
        )
        
        batch_stats = batch_stats_result.get("data", {}) if batch_stats_result.get("success") else {}
        
        # Enhance each quiz with submission statistics 
        enhanced_quizzes = []
        for quiz in quizzes:
            quiz_data = {**quiz}
            if quiz.get('status') == 'published':
                # Get submission statistics for this quiz
                quiz_id = quiz['id']
                stats = batch_stats.get(quiz_id, {
                    "statistics":{
                        "attempts_count": 0,
                        "users_attempted": 0,
                        "users_passed": 0,
                        "average_score":0,
                        "pass_rate": 0,
                    }
                })
                
                quiz_data.update({
                    "statistics":{
                        "attempts_count": stats.get("total_submissions", 0),
                        "users_attempted": stats.get("users_attempted", 0),
                        "users_passed": stats.get("users_passed", 0),
                        "average_score": stats.get("average_score", 0),  
                        "pass_rate": stats.get("pass_rate", 0)
                    }
                })
            
            enhanced_quizzes.append(quiz_data)
        
        return jsonify({
            "message": "Quizzes retrieved successfully",
            "data": enhanced_quizzes,
            "filters_applied": filters,
            "total_count": len(enhanced_quizzes)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_quizzes.route('/api/admin/quizzes/<quiz_id>', methods=['GET'])
def get_quiz_details(quiz_id):
    """Get detailed quiz information including questions"""
    try:
        # Get quiz
        quiz_result = quiz_model.find_by_id(quiz_id)
        if not quiz_result["success"]:
            return jsonify({"error": quiz_result["error"]}), 404
        
        # Get questions
        questions_result = quiz_question_model.find_by_quiz(quiz_id, include_answers=True)
        questions = questions_result["data"] if questions_result["success"] else []
        
        return jsonify({
            "message": "Quiz details retrieved successfully",
            "data": {
                **quiz_result["data"],
                "questions": questions
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_quizzes.route('/api/admin/quizzes/<quiz_id>', methods=['DELETE'])
def delete_quiz(quiz_id):
    """Delete a quiz and all its questions"""
    try:
        # First delete all questions
        quiz_question_model.delete_by_quiz(quiz_id)
        
        # Then delete the quiz
        result = quiz_model.delete(quiz_id)
        
        if result["success"]:
            return jsonify({"message": result["message"]}), 200
        else:
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
          
    except Exception as e:
        return jsonify({"error": str(e)}), 500