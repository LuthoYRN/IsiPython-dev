from flask import Blueprint, request, jsonify
from app.utils.utility import clear_challenge_dependent_caches,clear_quiz_dependent_caches

cache_maintenance = Blueprint('cache_maintenance', __name__)

@cache_maintenance.route('/api/cache', methods=['DELETE'])
def clear_cache():
    try:
        quiz_clear_result = clear_quiz_dependent_caches()
        challenge_clear_result = clear_challenge_dependent_caches()
        
        if quiz_clear_result["success"] and challenge_clear_result["success"]:
            return jsonify({
                "message": "Caches cleared successfully",
            }), 200        
    except Exception as e:
        return jsonify({"error": str(e)}), 500