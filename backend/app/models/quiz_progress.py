from app import supabase
from typing import Dict, Any
from datetime import datetime

class UserQuizProgress:
    def __init__(self):
        self.supabase = supabase  # Use the shared instance

    def get_or_create_progress(self, user_id: str, quiz_id: str) -> Dict[str, Any]:
        """Get existing progress or create new record"""
        try:
            # Try to get existing progress
            result = self.supabase.table('user_quiz_progress')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('quiz_id', quiz_id)\
                .execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            
            # Create new progress record
            progress_data = {
                'user_id': user_id,
                'quiz_id': quiz_id,
                'status': 'not_started',
                'best_score': 0,
                'best_percentage':0,
                'attempts_count': 0,
            }
            
            create_result = self.supabase.table('user_quiz_progress')\
                .insert(progress_data)\
                .execute()
            
            if create_result.data:
                return {"success": True, "data": create_result.data[0]}
            else:
                return {"success": False, "error": "Failed to create progress record"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_progress(self, user_id: str, quiz_id: str, submission_result: Dict[str, Any]) -> Dict[str, Any]:
        """Update user progress based on quiz submission result"""
        try:
            # Get current progress
            progress_result = self.get_or_create_progress(user_id, quiz_id)
            if not progress_result["success"]:
                return progress_result
            
            current_progress = progress_result["data"]
            
            # Prepare updates
            updates = {
                'attempts_count': current_progress['attempts_count'] + 1
            }
            
            # Update best score if this submission is better
            new_score = float(submission_result.get('score', 0))
            new_percentage = float(submission_result.get('percentage', 0))
            new_completion = False
            if new_score > current_progress['best_score']:
                new_completion = True
                updates['best_score'] = new_score
                updates['best_percentage']=new_percentage
                updates['best_submission_id'] = submission_result.get('submission_id')
            
            # Update status based on submission result
            submission_status = submission_result.get('status')
            if submission_status == 'completed':
                updates['status'] = 'completed'
                if not current_progress.get('completed_at') or new_completion:
                    updates['completed_at'] = 'now()'
            
            # Update last attempt time
            updates['last_attempt_at'] = 'now()'
            
            # Update in database
            result = self.supabase.table('user_quiz_progress')\
                .update(updates)\
                .eq('user_id', user_id)\
                .eq('quiz_id', quiz_id)\
                .execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to update progress"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_progress(self, user_id: str, quiz_id: str) -> Dict[str, Any]:
        """Get user's progress on a specific quiz"""
        try:
            result = self.supabase.table('user_quiz_progress')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('quiz_id', quiz_id)\
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
                        "best_percentage":0,
                        "attempts_count": 0,
                        "completed_at": None,
                        "last_attempt_at": None
                    }
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_all_progress(self, user_id: str) -> Dict[str, Any]:
        """Get user's progress on all quizzes"""
        try:
            result = self.supabase.table('user_quiz_progress')\
                .select('*, quizzes(title, total_questions, total_points, time_limit_minutes)')\
                .eq('user_id', user_id)\
                .execute()
            
            return {"success": True, "data": result.data}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_progress_since(self, user_id: str, since_date: datetime) -> Dict[str, Any]:
        """Get user's quiz progress since a specific date"""
        try:
            result = self.supabase.table('user_quiz_progress')\
                .select('*')\
                .eq('user_id', user_id)\
                .gte('completed_at', since_date.isoformat())\
                .execute()
            
            if result.data:
                return {"success": True, "data": result.data}
            else:
                return {"success": True, "data": []}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_quizzes_with_progress(self, user_id: str = None, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get all quizzes with user progress if user_id provided"""
        try:
            # Base query for quizzes
            query = self.supabase.table('quizzes').select('*')
            
            # Apply filters
            if filters:
                if filters.get('status'):
                    query = query.eq('status', filters['status'])
                else:
                    # Default to published quizzes for students
                    query = query.eq('status', 'published')
                
                if filters.get('search'):
                    search_term = filters['search']
                    query = query.or_(f'title.ilike.%{search_term}%,description.ilike.%{search_term}%')
            else:
                # Default to published quizzes
                query = query.eq('status', 'published')
            
            # Apply ordering
            order_by = filters.get('order_by', 'created_at') if filters else 'created_at'
            query = query.order(order_by)
            
            quizzes_result = query.execute()
            
            if not quizzes_result.data:
                return {"success": True, "data": []}
            
            quizzes = quizzes_result.data
            
            # If user_id provided, get their progress on each quiz
            if user_id:
                # Get user's progress on all quizzes
                progress_result = self.supabase.table('user_quiz_progress')\
                    .select('quiz_id, status, best_score,best_percentage, attempts_count, completed_at')\
                    .eq('user_id', user_id)\
                    .execute()
                
                # Create progress lookup
                progress_lookup = {}
                if progress_result.data:
                    for progress in progress_result.data:
                        progress_lookup[progress['quiz_id']] = progress
                
                # Add progress to each quiz
                for quiz in quizzes:
                    quiz_id = quiz['id']
                    user_progress = progress_lookup.get(quiz_id, {
                        'status': 'not_started',
                        'best_score': 0,
                        'best_percentage':0,
                        'attempts_count': 0,
                        'completed_at': None
                    })
                    quiz['user_progress'] = user_progress
            
            return {"success": True, "data": quizzes}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_dashboard_stats(self, user_id: str) -> Dict[str, Any]:
        """Get dashboard statistics for a user's quiz performance"""
        try:
            # Get user's progress
            progress_result = self.get_user_all_progress(user_id)
            if not progress_result["success"]:
                return progress_result
            
            progress_data = progress_result["data"]
            
            # Calculate statistics
            completed_quizzes = len([p for p in progress_data if p['status'] == 'completed'])
            
            # Calculate average score for completed quizzes
            completed_scores = [p['best_percentage'] for p in progress_data if p['status'] == 'completed']
            average_score = sum(completed_scores) / len(completed_scores) if completed_scores else 0
            
            return {
                "success": True,
                "data": {
                    "completed_quizzes": completed_quizzes,
                    "average_score": round(average_score, 1),
                }
            }
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_leaderboard(self, quiz_id: str = None, limit: int = 50) -> Dict[str, Any]:
        """Get leaderboard for a specific quiz or overall"""
        try:
            if quiz_id:
                # Quiz-specific leaderboard
                result = self.supabase.table('user_quiz_progress')\
                    .select('user_id, best_score, best_percentage, completed_at, attempts_count')\
                    .eq('quiz_id', quiz_id)\
                    .eq('status', 'completed')\
                    .order('best_percentage', desc=True)\
                    .order('completed_at')\
                    .limit(limit)\
                    .execute()
                
                return {"success": True, "data": result.data}
            else:
                # Global leaderboard
                return self.get_global_leaderboard(limit)
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    def get_global_leaderboard(self, limit: int = 50) -> Dict[str, Any]:
        """Get overall leaderboard aggregating all quiz performance"""
        try:
            # Use PostgreSQL aggregation to calculate average score and quiz count per user
            result = self.supabase.rpc('get_quiz_global_leaderboard', {
                'limit_count': limit
            }).execute()
            
            return {"success": True, "data": result.data}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    def get_user_global_rank(self, user_id: str) -> Dict[str, Any]:
        """Get user's rank in global quiz leaderboard"""
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
user_quiz_progress_model = UserQuizProgress()