from app import supabase
from typing import Dict, Any
from datetime import datetime
from functools import lru_cache
from app.utils.retry import retry_with_backoff  

class ChallengeSubmission:
    def __init__(self):
        self.supabase = supabase  # Use the shared instance

    def create(self, challenge_id: str, user_id: str, code: str) -> Dict[str, Any]:
        """Create a new challenge submission"""
        try:
            # Prepare submission data
            submission_data = {
                'challenge_id': challenge_id,
                'user_id': user_id,
                'code': code,
                'status': 'pending',
                'score': 0,
                'tests_passed': 0,
                'tests_total': 0
            }
            
            # Insert into database
            result = self.supabase.table('challenge_submissions').insert(submission_data).execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to create submission"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_results(self, submission_id: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Update submission with execution results"""
        try:
            # Prepare update data
            update_data = {}
            
            # Map execution results to database fields
            if 'status' in results:
                update_data['status'] = results['status']
            
            if 'score' in results:
                update_data['score'] = float(results['score'])
            
            if 'tests_passed' in results:
                update_data['tests_passed'] = int(results['tests_passed'])
            
            if 'tests_total' in results:
                update_data['tests_total'] = int(results['tests_total'])
            
            # Update in database
            result = self.supabase.table('challenge_submissions')\
                .update(update_data)\
                .eq('id', submission_id)\
                .execute()
            
            if result.data:
                self.get_batch_challenge_statistics_rpc.cache_clear()
                self.find_by_user_and_challenge.cache_clear()
                self.find_by_user.cache_clear()
                self.get_user_challenge_summary.cache_clear()
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to update submission results"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @lru_cache(maxsize=10)
    def find_by_user_and_challenge(self, user_id: str, challenge_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get user's submissions for a specific challenge"""
        try:
            result = self.supabase.table('challenge_submissions')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('challenge_id', challenge_id)\
                .order('submitted_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return {"success": True, "data": result.data}
                
        except Exception as e:
            self.find_by_user_and_challenge.cache_clear()
            return {"success": False, "error": str(e)}

    def find_by_id(self, submission_id: str, user_id: str = None) -> Dict[str, Any]:
        """Get submission by ID, optionally filtered by user for security"""
        try:
            query = self.supabase.table('challenge_submissions').select('*').eq('id', submission_id)
            
            # Add user filter for security
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Submission not found or access denied"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def count_submissions(self):
        """Get total challenge submissions in the platform"""
        try:
            result = supabase.table('challenge_submissions').select('id', count='exact').execute()
            count = result.count if result.count else 0
            return {"success": True, "count": count}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @lru_cache(maxsize=10)
    def find_by_user(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get all submissions by a user across all challenges"""
        try:
            result = self.supabase.table('challenge_submissions')\
                .select('*, challenges(title, difficulty_level, reward_points)')\
                .eq('user_id', user_id)\
                .order('submitted_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return {"success": True, "data": result.data}
                
        except Exception as e:
            self.find_by_user.cache_clear()
            return {"success": False, "error": str(e)}

    def find_by_challenge(self, challenge_id: str, limit: int = 100) -> Dict[str, Any]:
        """Get all submissions for a challenge (admin use)"""
        try:
            result = self.supabase.table('challenge_submissions')\
                .select('*')\
                .eq('challenge_id', challenge_id)\
                .order('submitted_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return {"success": True, "data": result.data}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_best_submission(self, user_id: str, challenge_id: str) -> Dict[str, Any]:
        """Get user's best submission for a challenge"""
        try:
            result = self.supabase.table('challenge_submissions')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('challenge_id', challenge_id)\
                .order('score', desc=True)\
                .order('submitted_at', desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "No submissions found"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @retry_with_backoff(max_retries=5, base_delay=0.3)
    @lru_cache(maxsize=50)
    def get_batch_challenge_statistics_rpc(self, challenge_ids_str: str) -> Dict[str, Any]:
        """Get challenge statistics using Supabase RPC function"""
        try:
            import json
            challenge_ids = json.loads(challenge_ids_str)
            
            if not challenge_ids:
                return {"success": True, "data": {}}
            
            result = self.supabase.rpc('get_challenge_batch_statistics', {
                'challenge_ids': challenge_ids
            }).execute()
            
            if not result.data:
                # Return empty stats for all challenges
                empty_stats = {
                    challenge_id: {
                        "users_attempted": 0,
                        "users_completed": 0,
                        "pass_rate": 0,
                    } for challenge_id in challenge_ids
                }
                return {"success": True, "data": empty_stats}
            
            # Convert to expected format
            stats_dict = {}
            for row in result.data:
                stats_dict[row['challenge_id']] = {
                    "users_attempted": int(row['users_attempted']),
                    "users_completed": int(row['users_completed']),
                    "pass_rate": float(row['pass_rate']),
                }
            
            return {"success": True, "data": stats_dict}
            
        except Exception as e:
            self.get_batch_challenge_statistics_rpc.cache_clear()
            error_str = str(e).lower()
            if ("resource temporarily unavailable" in error_str or 
                "connection" in error_str or
                "temporarily unavailable" in error_str):
                raise  
            else:
                return {"success": False, "error": str(e)}
                
    def delete(self, submission_id: str, user_id: str = None) -> Dict[str, Any]:
        """Delete a submission (with optional user check for security)"""
        try:
            query = self.supabase.table('challenge_submissions').delete().eq('id', submission_id)
            
            # Add user filter for security
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.execute()
            self.get_batch_challenge_statistics_rpc.cache_clear()
            self.find_by_user_and_challenge.cache_clear()
            self.find_by_user.cache_clear()
            self.get_user_challenge_summary.cache_clear()
            
            return {"success": True, "message": "Submission deleted successfully"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    def get_challenge_submissions_since(self, since_date: datetime) -> Dict[str, Any]:
        """Get challenge submissions since a specific date"""
        try:
            result = supabase.table('challenge_submissions')\
            .select('id', count='exact')\
            .gte('submitted_at', since_date.isoformat())\
            .execute()
            
            if result.data:
                return {"success": True, "data": result.data}
            else:
                return {"success": True, "data": []}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @lru_cache(maxsize=10)
    def get_user_challenge_summary(self, user_id: str, challenge_id: str) -> Dict[str, Any]:
        """Get summary of user's attempts on a challenge"""
        try:
            result = self.supabase.table('challenge_submissions')\
                .select('status, score, submitted_at')\
                .eq('user_id', user_id)\
                .eq('challenge_id', challenge_id)\
                .order('submitted_at', desc=True)\
                .execute()
            
            if not result.data:
                return {
                    "success": True,
                    "data": {
                        "total_attempts": 0,
                        "best_score": 0,
                        "status": "not_started",
                        "latest_attempt": None
                    }
                }
            
            submissions = result.data
            
            # Calculate summary
            total_attempts = len(submissions)
            best_score = max(float(sub['score']) for sub in submissions)
            has_passed = any(sub['status'] == 'passed' for sub in submissions)
            latest_attempt = submissions[0] if submissions else None
            
            # Determine overall status
            if has_passed:
                status = "completed"
            elif total_attempts > 0:
                status = "in_progress"
            else:
                status = "not_started"
            
            return {
                "success": True,
                "data": {
                    "total_attempts": total_attempts,
                    "best_score": best_score,
                    "status": status,
                    "latest_attempt": latest_attempt,
                    "has_passed": has_passed
                }
            }
                
        except Exception as e:
            self.get_user_challenge_summary.cache_clear()
            return {"success": False, "error": str(e)}

# Create instance for use in routes
challenge_submission_model = ChallengeSubmission()