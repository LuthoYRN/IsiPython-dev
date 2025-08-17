from app import supabase
from typing import Optional, List, Dict, Any
from datetime import datetime

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
            
            if 'error' in results:
                update_data['error'] = results['error']
            
            if 'english_error' in results:
                update_data['english_error'] = results['english_error']
            
            # Update in database
            result = self.supabase.table('challenge_submissions')\
                .update(update_data)\
                .eq('id', submission_id)\
                .execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to update submission results"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

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

    def get_challenge_statistics(self, challenge_id: str) -> Dict[str, Any]:
        """Get statistics for a challenge"""
        try:
            # Get all submissions for this challenge
            all_submissions = self.supabase.table('challenge_submissions')\
                .select('user_id, status, score')\
                .eq('challenge_id', challenge_id)\
                .execute()
            
            if not all_submissions.data:
                return {
                    "success": True,
                    "data": {
                        "users_attempted": 0,
                        "users_completed": 0,
                        "pass_rate": 0
                    }
                }
            
            submissions = all_submissions.data
            
            # Get unique users who attempted this challenge
            total_submissions = len(submissions)
            unique_users = set(sub['user_id'] for sub in submissions)
            users_attempted = len(unique_users)
            
            # Get users who passed (have at least one passing submission)
            users_with_passing_submissions = set(
                sub['user_id'] for sub in submissions if sub['status'] == 'passed'
            )
            users_completed = len(users_with_passing_submissions)
            
            # Calculate pass rate based on users
            pass_rate = (users_completed / users_attempted * 100) if users_attempted > 0 else 0
            
            return {
                "success": True,
                "data": {
                    "total_submissions":total_submissions,
                    "users_attempted": users_attempted,      # Total unique users who tried
                    "users_completed": users_completed,      # Users who successfully passed
                    "pass_rate": round(pass_rate, 1),        # % of users who passed
                }
            }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    def delete(self, submission_id: str, user_id: str = None) -> Dict[str, Any]:
        """Delete a submission (with optional user check for security)"""
        try:
            query = self.supabase.table('challenge_submissions').delete().eq('id', submission_id)
            
            # Add user filter for security
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.execute()
            
            return {"success": True, "message": "Submission deleted successfully"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

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
            return {"success": False, "error": str(e)}

# Create instance for use in routes
challenge_submission_model = ChallengeSubmission()