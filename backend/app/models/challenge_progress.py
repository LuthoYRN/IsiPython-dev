from app import supabase
from typing import Optional, List, Dict, Any

class UserChallengeProgress:
    def __init__(self):
        self.supabase = supabase  # Use the shared instance

    def get_or_create_progress(self, user_id: str, challenge_id: str) -> Dict[str, Any]:
        """Get existing progress or create new record"""
        try:
            # Try to get existing progress
            result = self.supabase.table('user_challenge_progress')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('challenge_id', challenge_id)\
                .execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            
            # Create new progress record
            progress_data = {
                'user_id': user_id,
                'challenge_id': challenge_id,
                'status': 'not_started',
                'best_score': 0,
                'attempts_count': 0
            }
            
            create_result = self.supabase.table('user_challenge_progress')\
                .insert(progress_data)\
                .execute()
            
            if create_result.data:
                return {"success": True, "data": create_result.data[0]}
            else:
                return {"success": False, "error": "Failed to create progress record"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_progress(self, user_id: str, challenge_id: str, submission_result: Dict[str, Any]) -> Dict[str, Any]:
        """Update user progress based on submission result"""
        try:
            # Get current progress
            progress_result = self.get_or_create_progress(user_id, challenge_id)
            if not progress_result["success"]:
                return progress_result
            
            current_progress = progress_result["data"]
            
            # Prepare updates
            updates = {
                'attempts_count': current_progress['attempts_count'] + 1
            }
            
            # Update best score if this submission is better
            new_score = float(submission_result.get('score', 0))
            if new_score > current_progress['best_score']:
                updates['best_score'] = new_score
                updates['best_submission_id'] = submission_result.get('submission_id')
            
            # Update status based on submission result
            submission_status = submission_result.get('status')
            if submission_status == 'passed':
                updates['status'] = 'completed'
                if not current_progress.get('completed_at'):
                    updates['completed_at'] = 'now()'
            elif current_progress['status'] == 'not_started':
                updates['status'] = 'in_progress'
            
            # Update in database
            result = self.supabase.table('user_challenge_progress')\
                .update(updates)\
                .eq('user_id', user_id)\
                .eq('challenge_id', challenge_id)\
                .execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to update progress"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_progress(self, user_id: str, challenge_id: str) -> Dict[str, Any]:
        """Get user's progress on a specific challenge"""
        try:
            result = self.supabase.table('user_challenge_progress')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('challenge_id', challenge_id)\
                .execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                # Return default progress if none exists
                return {
                    "success": True, 
                    "data": {
                        "status": "not_started",
                        "best_score": 0,
                        "attempts_count": 0,
                        "completed_at": None
                    }
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_all_progress(self, user_id: str) -> Dict[str, Any]:
        """Get user's progress on all challenges"""
        try:
            result = self.supabase.table('user_challenge_progress')\
                .select('*, challenges(title, difficulty_level, reward_points, tags)')\
                .eq('user_id', user_id)\
                .execute()
            
            return {"success": True, "data": result.data}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_challenges_with_progress(self, user_id: str = None, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get all challenges with user progress if user_id provided"""
        try:
            # Base query for challenges
            query = self.supabase.table('challenges').select('*')
            
            # Apply filters
            if filters:
                if filters.get('status'):
                    query = query.eq('status', filters['status'])
                else:
                    # Default to published challenges for students
                    query = query.eq('status', 'published')
                
                if filters.get('difficulty_level'):
                    query = query.eq('difficulty_level', filters['difficulty_level'])
                
                if filters.get('search'):
                    search_term = filters['search']
                    query = query.or_(f'title.ilike.%{search_term}%,short_description.ilike.%{search_term}%')
            else:
                # Default to published challenges
                query = query.eq('status', 'published')
            
            # Apply ordering
            order_by = filters.get('order_by', 'created_at') if filters else 'created_at'
            query = query.order(order_by)
            
            challenges_result = query.execute()
            
            if not challenges_result.data:
                return {"success": True, "data": []}
            
            challenges = challenges_result.data
            
            # If user_id provided, get their progress on each challenge
            if user_id:
                # Get user's progress on all challenges
                progress_result = self.supabase.table('user_challenge_progress')\
                    .select('challenge_id, status, best_score, attempts_count, completed_at')\
                    .eq('user_id', user_id)\
                    .execute()
                
                # Create progress lookup
                progress_lookup = {}
                if progress_result.data:
                    for progress in progress_result.data:
                        progress_lookup[progress['challenge_id']] = progress
                
                # Add progress to each challenge
                for challenge in challenges:
                    challenge_id = challenge['id']
                    user_progress = progress_lookup.get(challenge_id, {
                        'status': 'not_started',
                        'best_score': 0,
                        'attempts_count': 0,
                        'completed_at': None
                    })
                    challenge['user_progress'] = user_progress
            
            return {"success": True, "data": challenges}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_dashboard_stats(self, user_id: str) -> Dict[str, Any]:
        """Get dashboard statistics for a user"""
        try:
            # Get user's progress
            progress_result = self.get_user_all_progress(user_id)
            if not progress_result["success"]:
                return progress_result
            
            progress_data = progress_result["data"]
            
            # Calculate statistics
            total_challenges = len(progress_data)
            completed_challenges = len([p for p in progress_data if p['status'] == 'completed'])
            in_progress_challenges = len([p for p in progress_data if p['status'] == 'in_progress'])
            
            # Calculate total points earned
            total_points = sum(p['best_score'] for p in progress_data if p['best_score'] > 0)
            
            return {
                "success": True,
                "data": {
                    "total_challenges": total_challenges,
                    "completed_challenges": completed_challenges,
                    "in_progress_challenges": in_progress_challenges,
                    "completion_rate": round(completed_challenges / total_challenges * 100, 1) if total_challenges > 0 else 0,
                    "total_points_earned": round(total_points, 1)
                }
            }
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reset_progress(self, user_id: str, challenge_id: str) -> Dict[str, Any]:
        """Reset user's progress on a challenge (admin function)"""
        try:
            result = self.supabase.table('user_challenge_progress')\
                .delete()\
                .eq('user_id', user_id)\
                .eq('challenge_id', challenge_id)\
                .execute()
            
            return {"success": True, "message": "Progress reset successfully"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_leaderboard(self, challenge_id: str = None, limit: int = 50) -> Dict[str, Any]:
        """Get leaderboard for a specific challenge or overall"""
        try:
            if challenge_id:
                # Challenge-specific leaderboard
                result = self.supabase.table('user_challenge_progress')\
                    .select('user_id, best_score, completed_at, attempts_count')\
                    .eq('challenge_id', challenge_id)\
                    .neq('status', 'not_started')\
                    .order('best_score', desc=True)\
                    .order('completed_at')\
                    .limit(limit)\
                    .execute()
            
            return {"success": True, "data": result.data}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_global_leaderboard(self, limit: int = 50) -> Dict[str, Any]:
        """Get overall leaderboard aggregating all challenge points"""
        try:
            # Use PostgreSQL aggregation to sum points per user
            result = self.supabase.rpc('get_global_leaderboard', {
                'limit_count': limit
            }).execute()
            
            return {"success": True, "data": result.data}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_global_rank(self, user_id: str) -> Dict[str, Any]:
        """Get user's rank in global leaderboard"""
        try:
            # Get global leaderboard
            leaderboard_result = self.get_global_leaderboard(limit=1000)  # Get more users
            if not leaderboard_result["success"]:
                return leaderboard_result
            
            leaderboard = leaderboard_result["data"]
            
            # Find user's position
            for rank, user_data in enumerate(leaderboard, 1):
                if user_data['user_id'] == user_id:
                    return {
                        "success": True, 
                        "data": {
                            "rank": rank,
                            "total_users": len(leaderboard),
                            "user_stats": user_data
                        }
                    }
            
            return {"success": True, "data": {"rank": None, "total_users": len(leaderboard)}}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
# Create instance for use in routes
user_challenge_progress_model = UserChallengeProgress()