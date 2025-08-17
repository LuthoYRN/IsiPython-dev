from flask import Blueprint, request, jsonify
from app.models.challenge import challenge_model
from app.models.challenge_testcase import challenge_test_case_model

admin_challenges = Blueprint('admin_challenges', __name__)

@admin_challenges.route('/api/admin/challenges', methods=['POST'])
def create_or_update_challenge():
    """Create new challenge or update existing challenge"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract key fields
        challenge_id = data.get('id')  # If provided, we're updating
        test_cases = data.get('test_cases', [])
        reward_points = data.get('reward_points', 0)
        action = data.get('action', 'save_draft')  # save_draft | publish 
        valid_actions = ['save_draft', 'publish'] 
        if action not in valid_actions:
            return jsonify({
                "error": f"Invalid action. Must be one of: {', '.join(valid_actions)}"
            }), 400
        
        # STEP 1: Validate test case weights BEFORE any database operations
        if test_cases:
            validation_result = _validate_test_case_weights(test_cases, reward_points)
            if not validation_result["valid"]:
                return jsonify({"error": validation_result["error"]}), 400
        
        # STEP 2: Check if we need to publish but don't have test cases
        if action == 'publish' and not test_cases:
            return jsonify({"error": "Cannot publish challenge without test cases"}), 400
        
        # STEP 3: Check if we need to publish and have test cases
        if action == 'publish' and test_cases:
            publish_validation = _validate_challenge_for_publishing(test_cases)
            if not publish_validation["valid"]:
                return jsonify({"success": False, "error": publish_validation["error"]}),400
        
        # STEP 4: Determine if we're creating or updating
        if challenge_id:
            # UPDATE EXISTING CHALLENGE
            result = _update_existing_challenge(challenge_id, data)
        else:
            # CREATE NEW CHALLENGE
            result = _create_new_challenge(data)
        
        if result["success"]:
            return jsonify({
                "message": "Challenge saved successfully" if action != 'publish' else "Challenge published successfully",
                "data": result["data"]
            }), 200 if challenge_id else 201
        else:
            # Handle validation errors vs other errors
            if "errors" in result:
                return jsonify({"errors": result["errors"]}), 400
            else:
                return jsonify({"error": result["error"]}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _validate_test_case_weights(test_cases, reward_points):
    """Validate that test case weights sum to reward points"""
    try:
        reward_points = float(reward_points)
        total_weight = 0
        
        for i, test_case in enumerate(test_cases):
            try:
                weight = float(test_case.get('points_weight', 0))
                if weight < 0:
                    return {
                        "valid": False,
                        "error": f"Test case {i + 1}: Points weight cannot be negative"
                    }
                total_weight += weight
            except (ValueError, TypeError):
                return {
                    "valid": False,
                    "error": f"Test case {i + 1}: Points weight must be a valid number"
                }
        
        if total_weight != reward_points:
            return {
                "valid": False,
                "error": f"Test case weights ({total_weight}) must equal reward points ({reward_points})"
            }
        
        return {"valid": True}
        
    except (ValueError, TypeError):
        return {
            "valid": False,
            "error": "Reward points must be a valid number"
        }

def _create_new_challenge(data):
    """Create a new challenge with test cases"""
    try:
        # STEP 1: Extract test cases from data before creating challenge
        test_cases = data.get('test_cases', [])
        challenge_data = {k: v for k, v in data.items() if k != 'test_cases'}
        
        # STEP 2: Create the challenge first (without test cases)
        challenge_result = challenge_model.create(challenge_data)
        if not challenge_result["success"]:
            return challenge_result
        
        challenge = challenge_result["data"]
        challenge_id = challenge["id"]
        
        # STEP 3: Create test cases if provided
        created_test_cases = []
        if test_cases:
            for i, test_case in enumerate(test_cases):
                test_case_result = challenge_test_case_model.create(challenge_id, test_case)
                if test_case_result["success"]:
                    created_test_cases.append(test_case_result["data"])
                else:
                    # If any test case fails, clean up by deleting the challenge
                    challenge_model.delete(challenge_id)
                    return {
                        "success": False,
                        "errors":f"Failed to create test case {i + 1}: {test_case_result['errors']}" if test_case_result.get("errors") else None,
                        "error": f"Failed to create test case {i + 1}: {test_case_result['error']}" if test_case_result.get("error") else "Unknown error"
                    }
         # STEP 4: If action is publish and we have test cases, update status to published
        if challenge_data['action'] == 'publish' and created_test_cases:
            publish_result = challenge_model.update(challenge_id, {
                **challenge,
                'status': 'published',
                'published_at': 'now()'
            })
            if publish_result["success"]:
                challenge = publish_result["data"]  # Get updated challenge with published status
            else:
                # If publish fails, still return the draft challenge 
                pass
        
        # STEP 5: Return complete challenge with test cases
        return {
            "success": True,
            "data": {
                **challenge,
                "test_cases": created_test_cases
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
    
def _update_existing_challenge(challenge_id, data):
    """Update existing challenge and its test cases"""
    try:
        # STEP 1: Check if challenge exists
        existing_challenge = challenge_model.find_by_id(challenge_id)
        challenge_data = existing_challenge["data"]
        if not existing_challenge["success"]:
            return {"success": False, "error": "Challenge not found"}
        
        challenge_updates = {k: v for k, v in data.items() 
                           if k not in ['id', 'test_cases', 'action']}
        test_cases = data.get('test_cases', [])
        updated_test_cases = []
        
        # STEP 2: Handle test cases if provided
        if test_cases:
            # Delete existing test cases first
            challenge_test_case_model.delete_by_challenge(challenge_id)
            
            # Create new test cases
            for test_case in test_cases:
                test_case_result = challenge_test_case_model.create(challenge_id, test_case)
                if test_case_result["success"]:
                    updated_test_cases.append(test_case_result["data"])
                else:
                    # If any test case fails, return error
                    return {
                        "success": False,
                        "error": f"Failed to create test case: {test_case_result['error']}"
                    }
        elif not test_cases and not challenge_data['status'] == 'published':
            challenge_test_case_model.delete_by_challenge(challenge_id) #empty test case array and save as draft
        else:
            # Get existing test cases if none provided
            existing_test_cases = challenge_test_case_model.find_by_challenge(challenge_id)
            if existing_test_cases["success"]:
                updated_test_cases = existing_test_cases["data"]

        # STEP 3: Update challenge info (exclude test_cases)
        action = data.get('action', 'save_draft')
        if action == 'publish':
            challenge_updates['status'] = 'published'
            challenge_updates['published_at'] = 'now()'
        elif action == 'save_draft':
            challenge_updates['status'] = 'draft'
            challenge_updates['published_at'] = None
        # preview doesn't change status
        
        challenge_result = challenge_model.update(challenge_id, challenge_updates)
        if not challenge_result["success"]:
            return challenge_result

        # STEP 4: Return complete challenge with test cases
        return {
            "success": True,
            "data": {
                **challenge_result["data"],
                "test_cases": updated_test_cases
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def _validate_challenge_for_publishing(test_cases: list = None) -> dict:
    """Validate that challenge has required test cases for publishing"""  
    # Check for required test case types
    has_example = any(tc.get('is_example', False) for tc in test_cases)
    has_hidden = any(tc.get('is_hidden', False) for tc in test_cases)
    
    errors = []
    if not has_example:
        errors.append("At least 1 example test case is required")
    if not has_hidden:
        errors.append("At least 1 hidden test case is required")
    
    if errors:
        return {
            "valid": False,
            "error": ". ".join(errors) + "."
        }
    
    return {"valid": True}

@admin_challenges.route('/api/admin/challenges', methods=['GET'])
def list_challenges():
    """List all challenges with optional filtering"""
    try:
        # Get query parameters
        filters = {
            'status': request.args.get('status'),
            'difficulty_level': request.args.get('difficulty'),
            'search': request.args.get('search'),
            'limit': request.args.get('limit', 20),
            'offset': request.args.get('offset', 0),
            'order_by': request.args.get('order_by', 'created_at'),
            'order_direction': request.args.get('order_direction', 'desc')
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        result = challenge_model.find_all(filters)
        
        if result["success"]:
            return jsonify({
                "message": "Challenges retrieved successfully",
                "data": result["data"],
                "filters_applied": filters
            }), 200
        else:
            return jsonify({"error": result["error"]}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_challenges.route('/api/admin/challenges/<challenge_id>', methods=['GET'])
def get_challenge_details(challenge_id):
    """Get detailed challenge information including test cases"""
    try:
        # Get challenge
        challenge_result = challenge_model.find_by_id(challenge_id)
        if not challenge_result["success"]:
            return jsonify({"error": challenge_result["error"]}), 404
        
        # Get test cases
        test_cases_result = challenge_test_case_model.find_by_challenge(challenge_id)
        test_cases = test_cases_result["data"] if test_cases_result["success"] else []
        
        return jsonify({
            "message": "Challenge details retrieved successfully",
            "data": {
                **challenge_result["data"],
                "test_cases": test_cases
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_challenges.route('/api/admin/challenges/<challenge_id>', methods=['DELETE'])
def delete_challenge(challenge_id):
    """Delete a challenge"""
    try:
        result = challenge_model.delete(challenge_id)
        
        if result["success"]:
            return jsonify({"message": result["message"]}), 200
        else:
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500