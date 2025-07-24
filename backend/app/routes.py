from flask import Blueprint, request, jsonify
#from . import db
from app.services.transpiler import transpile_code
from app.services.executor import execute_python
from app.services.errors import translate_error,translate_timeout_error

main = Blueprint('main', __name__)

@main.route('/api/code', methods=['POST'])
def run_code():
    data = request.get_json()
    isixhosa_code = data.get('code')
    session_id = data.get('session_id')  # Optional
    user_input = data.get('input')       # Optional

    try:
        if session_id:
            result = execute_python("", session_id, user_input)
        else:
            python_code = transpile_code(isixhosa_code)
            result = execute_python(python_code, session_id, user_input)

        if result.get("error"):
            error_message = result['error']
            if error_message.startswith('[Timeout]'):
                # Use specialized timeout/loop analyzer
                result['error'] = translate_timeout_error(result['code'])
            else:
                # Use regular error translator
                result['error'] = translate_error(error_message)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"output": None, "error": str(e), "completed": True}), 500