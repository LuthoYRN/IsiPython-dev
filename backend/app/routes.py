from flask import Blueprint, request, jsonify
#from . import db
from app.services.transpiler import transpile_code
from app.services.executor import execute_python
from app.services.errors import translate_error

main = Blueprint('main', __name__)

@main.route('/api/code', methods=['POST'])
def run_code():
    data = request.get_json()
    isixhosa_code = data.get('code')

    try:
        python_code = transpile_code(isixhosa_code)
        output, error = execute_python(python_code)

        if error:
            translated = translate_error(error)
            return jsonify({"output": None, "error": translated}), 400

        return jsonify({"output": output, "error": None}), 200

    except Exception as e:
        return jsonify({"output": None, "error": str(e)}), 500