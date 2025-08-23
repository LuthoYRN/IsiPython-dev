from datetime import datetime, timedelta
import pytz

SOUTH_AFRICA_TZ = pytz.timezone('Africa/Johannesburg')

def get_week_start():
    """Get Monday 00:00:00 of current week"""
    today = get_current_sa_time()
    days_since_monday = today.weekday()  # 0=Monday, 6=Sunday
    monday = today - timedelta(days=days_since_monday)
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)

def to_sa_time(dt_str: str):
    # Parse the timestamp string from DB 
    dt = datetime.fromisoformat(dt_str)

    # If it has no timezone info, assume it was UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)

    # Convert to South African time
    return dt.astimezone(SOUTH_AFRICA_TZ).isoformat()

def get_current_sa_time() -> datetime:
    """Get current time in SA timezone"""
    return datetime.now(SOUTH_AFRICA_TZ)

def clear_challenge_dependent_caches():
    """
    Clear all caches that depend on challenge data.
    """
    try:
        # Import the model instances
        from app.models.challenge_progress import user_challenge_progress_model
        from app.models.challenge_submission import challenge_submission_model
        
        # Clear challenge progress caches
        if hasattr(user_challenge_progress_model, 'get_challenges_with_progress'):
            user_challenge_progress_model.get_challenges_with_progress.cache_clear()
        
        if hasattr(user_challenge_progress_model, 'get_user_all_progress'):
            user_challenge_progress_model.get_user_all_progress.cache_clear()
        
        # Clear challenge submission caches
        if hasattr(challenge_submission_model, 'find_by_user'):
            challenge_submission_model.find_by_user.cache_clear()

        if hasattr(challenge_submission_model,'get_batch_challenge_statistics_rpc'):
            challenge_submission_model.get_batch_challenge_statistics_rpc.cache_clear()    
        return {"success": True, "message": "Challenge dependent caches cleared"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def clear_quiz_dependent_caches():
    """
    Clear all caches that depend on quiz data.
    """
    try:
        # Import the model instances
        from app.models.quiz_progress import user_quiz_progress_model
        from app.models.quiz_submission import quiz_submission_model
        
        # Clear quiz progress caches
        if hasattr(user_quiz_progress_model, 'get_quizzes_with_progress'):
            user_quiz_progress_model.get_quizzes_with_progress.cache_clear()
        
        if hasattr(user_quiz_progress_model, 'get_user_all_progress'):
            user_quiz_progress_model.get_user_all_progress.cache_clear()
        
        if hasattr(quiz_submission_model, 'get_batch_quiz_statistics_rpc'):
            quiz_submission_model.get_batch_quiz_statistics_rpc.cache_clear()
            
        # Clear quiz submission caches
        if hasattr(quiz_submission_model, 'get_user_quiz_summary'):
            quiz_submission_model.get_user_quiz_summary.cache_clear()
            
        if hasattr(quiz_submission_model, 'find_by_user'):
            quiz_submission_model.find_by_user.cache_clear()
            
        return {"success": True, "message": "Quiz dependent caches cleared"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}