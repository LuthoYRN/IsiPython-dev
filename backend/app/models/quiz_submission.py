from app import supabase
from typing import Dict, Any
from datetime import datetime
from functools import lru_cache

class QuizSubmission:
    def __init__(self):
        self.supabase = supabase  # Use the shared instance

    def create(self, quiz_id: str, user_id: str, answers: Dict[str, Any], time_taken: int = 0) -> Dict[str, Any]:
        """Create a new quiz submission"""
        try:
            quiz_result = self.supabase.table('quizzes')\
                .select('time_limit_minutes')\
                .eq('id', quiz_id)\
                .execute()
            
            if not quiz_result.data:
                return {"success": False, "errors": "Quiz not found"}
            
            quiz = quiz_result.data[0]
            
            # Validate time taken
            if time_taken > quiz["time_limit_minutes"]:
                return {"success": False, "errors": "Time taken cannot exceed time limit"}
            
            questions_result = self.supabase.table('quiz_questions')\
                .select('id')\
                .eq('quiz_id', quiz_id)\
                .execute()
            
            if not questions_result.data:
                return {"success": False, "errors": "No questions found for this quiz"}
            
            valid_question_ids = {q['id'] for q in questions_result.data}
            valid_choices = {'A', 'B', 'C', 'D'}
            
            # Validate answers
            for question_id, answer in answers.items():
                # Check if question ID exists
                if question_id not in valid_question_ids:
                    return {"success": False, "errors": f"Invalid question ID: {question_id}"}
                
                # Check if answer choice is valid (skip empty answers)
                if answer and answer not in valid_choices:
                    return {"success": False, "errors": f"Invalid answer choice '{answer}'. Must be A, B, C, or D"}
                
            # Prepare submission data
            submission_data = {
                'quiz_id': quiz_id,
                'user_id': user_id,
                'answers': answers,  # JSON object with question_id: answer mappings
                'score': 0,  # Will be calculated
                'questions_correct': 0,
                'questions_total': 0,
                'time_taken': time_taken,  # in minutes
                'status': 'submitted'
            }
            
            # Insert into database
            result = self.supabase.table('quiz_submissions').insert(submission_data).execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to create submission"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_results(self, submission_id: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Update submission with scoring results"""
        try:
            # Prepare update data
            update_data = {}
            
            # Map scoring results to database fields
            if 'score' in results:
                update_data['score'] = float(results['score'])
            
            if 'questions_correct' in results:
                update_data['questions_correct'] = int(results['questions_correct'])
            
            if 'questions_total' in results:
                update_data['questions_total'] = int(results['questions_total'])
            
            if 'detailed_results' in results:
                update_data['detailed_results'] = results['detailed_results']
            
            if 'percentage' in results:
                update_data['percentage'] = float(results['percentage'])
            
            # Update status to completed
            update_data['status'] = 'completed'
            
            # Update in database
            result = self.supabase.table('quiz_submissions')\
                .update(update_data)\
                .eq('id', submission_id)\
                .execute()
            
            if result.data:
                self.get_quiz_statistics.cache_clear()
                self.get_user_quiz_summary.cache_clear()
                self.find_by_user.cache_clear()
                self.find_by_user_and_quiz.cache_clear()
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to update submission results"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    @lru_cache(maxsize=10)
    def find_by_user_and_quiz(self, user_id: str, quiz_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get user's submissions for a specific quiz"""
        try:
            result = self.supabase.table('quiz_submissions')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('quiz_id', quiz_id)\
                .order('submitted_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return {"success": True, "data": result.data}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def find_by_id(self, submission_id: str, user_id: str = None) -> Dict[str, Any]:
        """Get submission by ID, optionally filtered by user for security"""
        try:
            query = self.supabase.table('quiz_submissions').select('*').eq('id', submission_id)
            
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
    
    def count_submissions(self) -> Dict[str, Any]:
        """Get number of quiz submissions in the platform"""
        try:
            result = supabase.table('quiz_submissions').select('id', count='exact').execute()
            count = result.count if result.count else 0
            return {"success": True, "count": count}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @lru_cache(maxsize=10)
    def find_by_user(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get all submissions by a user across all quizzes"""
        try:
            result = self.supabase.table('quiz_submissions')\
                .select('*, quizzes(title, total_questions, total_points)')\
                .eq('user_id', user_id)\
                .order('submitted_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return {"success": True, "data": result.data}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def find_by_quiz(self, quiz_id: str, limit: int = 100) -> Dict[str, Any]:
        """Get all submissions for a quiz (admin use)"""
        try:
            result = self.supabase.table('quiz_submissions')\
                .select('*')\
                .eq('quiz_id', quiz_id)\
                .order('submitted_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return {"success": True, "data": result.data}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_best_submission(self, user_id: str, quiz_id: str) -> Dict[str, Any]:
        """Get user's best submission for a quiz"""
        try:
            result = self.supabase.table('quiz_submissions')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('quiz_id', quiz_id)\
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
        
    @lru_cache(maxsize=200)  # Cache up to 200 quiz statistics 
    def get_quiz_statistics(self, quiz_id: str) -> Dict[str, Any]:
        """Get statistics for a quiz"""
        try:
            quiz_result = self.supabase.table('quizzes')\
                .select('total_points')\
                .eq('id', quiz_id)\
                .execute()
            
            if not quiz_result.data:
                return {"success": False, "error": "Quiz not found"}
            
            total_points = quiz_result.data[0]['total_points']
            # Get all submissions for this quiz
            all_submissions = self.supabase.table('quiz_submissions')\
                .select('user_id, score, questions_correct, questions_total')\
                .eq('quiz_id', quiz_id)\
                .execute()
            
            if not all_submissions.data:
                return {
                    "success": True,
                    "data": {
                        "total_submissions": 0,
                        "users_attempted": 0,
                        "users_passed": 0,
                        "pass_rate": 0,
                        "average_score": 0
                    }
                }
            
            submissions = all_submissions.data
            
            # Get unique users who attempted this quiz
            total_submissions = len(submissions)
            unique_users = set(sub['user_id'] for sub in submissions)
            users_attempted = len(unique_users)
            
            # Calculate best submission per user for pass rate
            user_best_submissions = {}
            for sub in submissions:
                user_id = sub['user_id']
                if user_id not in user_best_submissions:
                    user_best_submissions[user_id] = sub
                else:
                    # Keep the best score submission for each user
                    if sub.get('score', 0) > user_best_submissions[user_id].get('score', 0):
                        user_best_submissions[user_id] = sub
            
            # Count users who passed (>=50% on their best attempt) 
            users_passed = 0
            
            for user_id, best_sub in user_best_submissions.items():
                score = best_sub.get('score', 0)
                
                # Calculate percentage for this user's best attempt
                percentage = (score / total_points) * 100 if total_points > 0 and score > 0 else 0
                
                if percentage >= 50:
                    users_passed += 1
            
            # Calculate pass rate
            pass_rate = (users_passed / users_attempted * 100) if users_attempted > 0 else 0
            
            # Calculate average scores based on best attempts 
            scores = [sub.get('score', 0) for sub in user_best_submissions.values()]
            average_score = sum(scores) / len(scores) if scores else 0
            average_score = (average_score / total_points) * 100 if total_points > 0 and average_score > 0 else 0
            
            return {
                "success": True,
                "data": {
                    "total_submissions": total_submissions,
                    "users_attempted": users_attempted,
                    "users_passed": users_passed,
                    "pass_rate": round(pass_rate, 1),
                    "average_score": round(average_score, 1)
                }
            }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    def delete(self, submission_id: str, user_id: str = None) -> Dict[str, Any]:
        """Delete a submission (with optional user check for security)"""
        try:
            query = self.supabase.table('quiz_submissions').delete().eq('id', submission_id)
            
            # Add user filter for security
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.execute()
            
            return {"success": True, "message": "Submission deleted successfully"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_quiz_submissions_since(self, since_date: datetime) -> Dict[str, Any]:
        """Get quiz submissions since a specific date"""
        try:
            result = supabase.table('quiz_submissions')\
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
    def get_user_quiz_summary(self, user_id: str, quiz_id: str) -> Dict[str, Any]:
        """Get summary of user's attempts on a quiz"""
        try:
            # Get quiz total points
            quiz_result = self.supabase.table('quizzes')\
                .select('total_points')\
                .eq('id', quiz_id)\
                .execute()
            
            if not quiz_result.data:
                return {"success": False, "error": "Quiz not found"}
            
            total_points = quiz_result.data[0]['total_points']

            # Get user's submissions
            result = self.supabase.table('quiz_submissions')\
                .select('score, questions_correct, questions_total, submitted_at, time_taken, status')\
                .eq('user_id', user_id)\
                .eq('quiz_id', quiz_id)\
                .order('submitted_at', desc=True)\
                .execute()
            
            if not result.data:
                return {
                    "success": True,
                    "data": {
                        "total_attempts": 0,
                        "best_score": 0,
                        "best_percentage": 0,
                        "status": "not_started",
                        "latest_attempt": None,
                        "has_passed": False
                    }
                }
            
            submissions = result.data
            
            # Calculate summary
            total_attempts = len(submissions)
            best_score = max(float(sub.get('score', 0)) for sub in submissions)
            
            # Calculate best percentage with safety check
            best_percentage = 0
            if total_points > 0:
                for sub in submissions:
                    score = sub.get('score', 0)
                    if score > 0:
                        percentage = (score / total_points) * 100
                        best_percentage = max(best_percentage, percentage)
            
            latest_attempt = submissions[0] if submissions else None
            
            has_passed = best_percentage >= 50     
            
            return {
                "success": True,
                "data": {
                    "total_attempts": total_attempts,
                    "best_score": best_score,
                    "best_percentage": round(best_percentage, 1),
                    "status": "completed",
                    "latest_attempt": latest_attempt,
                    "has_passed": has_passed
                }
            }
                
        except Exception as e:
            return {"success": False, "error": str(e)}

# Create instance for use in routes
quiz_submission_model = QuizSubmission()