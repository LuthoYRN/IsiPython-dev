from flask import Blueprint, request, jsonify
#from . import db
from app.services.transpiler import transpile_code
from app.services.executor import execute_python,kill_session
from app.services.errors import translate_error,translate_timeout_error
from app.models.saved_code import saved_code_model

main = Blueprint('main', __name__)

@main.route('/api/save', methods=['POST'])
def save_code():
    """Save new code snippet"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        title = data.get('title')
        code = data.get('code')
        user_id = data.get('user_id')
        
        # Basic validation
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        result = saved_code_model.create(title, code, user_id)
        
        if result["success"]:
            return jsonify({
                "message": "Code saved successfully",
                "data": result["data"]
            }), 201
        elif "errors" in result:
            return jsonify({"error": result["errors"]}), 400
        else:
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main.route('/api/saved/<user_id>', methods=['GET'])
def get_user_saved_code(user_id):
    """Get all saved code for a specific user"""
    try:
        result = saved_code_model.find_by_user(user_id)
        
        if result["success"]:
            return jsonify({
                "message": "Saved code retrieved successfully",
                "data": result["data"]
            }), 200
        else:
            return jsonify({"error": result["error"]}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/api/saved/update/<code_id>', methods=['PUT'])
def update_saved_code(code_id):
    """Update an existing saved code snippet"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        # Remove user_id from data before passing to update
        update_data = {k: v for k, v in data.items() if k != 'user_id'}
        
        result = saved_code_model.update(code_id, user_id, **update_data)
        
        if result["success"]:
            return jsonify({
                "message": "Code updated successfully",
                "data": result["data"]
            }), 200
        elif "errors" in result:
            return jsonify({"errors": result["errors"]}), 400
        else:
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main.route('/api/saved/delete/<code_id>', methods=['DELETE'])
def delete_saved_code(code_id):
    """Delete a saved code snippet"""
    try:
        data = request.get_json()
        user_id = data.get('user_id') if data else None
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        result = saved_code_model.delete(code_id, user_id)
        
        if result["success"]:
            return jsonify({
                "message": result["message"]
            }), 200
        else:
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/api/code', methods=['POST'])
def run_code():
    data = request.get_json()
    isixhosa_code = data.get('code')
    session_id = data.get('session_id')  # Optional
    user_input = data.get('input')       # Optional

    try:
        if session_id:
            result = execute_python("", "", {}, session_id, user_input)
        else:
            python_code, line_mapping = transpile_code(isixhosa_code)
            result = execute_python(isixhosa_code, python_code, line_mapping, session_id, user_input)

        if result.get("error"):
            error_message = result['error']
            line_mapping = result.get('line_mapping', {})
            
            if error_message.startswith('[Timeout]'):
                # Use specialized timeout/loop analyzer
                result['error'] = translate_timeout_error(result.get('code', ''))
            else:
                # Use regular error translator with line mapping
                result['error'] = translate_error(error_message, line_mapping)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"output": None, "error": str(e), "completed": True}), 500
    
@main.route('/api/debug/start', methods=['POST'])
def start_debug():
    """Start a debugging session"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        isixhosa_code = data.get('code')
        
        if not isixhosa_code:
            return jsonify({"error": "Code is required"}), 400
        
        # Transpile with debug mode enabled
        python_code, line_mapping = transpile_code(isixhosa_code, debug_mode=True)
        
        result = execute_python(isixhosa_code, python_code, line_mapping, session_id=None, user_input=None)

        if result.get("error"):
            error_message = result['error']
            result_line_mapping = result.get('line_mapping', line_mapping)
            
            if error_message.startswith('[Timeout]'):
                result['error'] = translate_timeout_error(result.get('code', ''))
            else:
                result['error'] = translate_error(error_message, result_line_mapping)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"output": None, "error": str(e), "completed": True}), 500

@main.route('/api/session/kill/<session_id>', methods=['DELETE'])
def terminate_session(session_id):
    """Kill a running execution session"""
    try:
        result = kill_session(session_id)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/api/debug/step', methods=['POST'])
def debug_step():
    """Send step command to continue debugging"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        session_id = data.get('session_id')
        user_input = data.get('input', "")  # Default to empty string for debug steps
        
        if not session_id:
            return jsonify({"error": "Session ID is required"}), 400
        
        result = execute_python("", "", {}, session_id, user_input=user_input)
        
        if result.get("error"):
            error_message = result['error']
            line_mapping = result.get('line_mapping', {})
            
            if error_message.startswith('[Timeout]'):
                result['error'] = translate_timeout_error(result.get('code', ''))
            else:
                result['error'] = translate_error(error_message, line_mapping)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"output": None, "error": str(e), "completed": True}), 500