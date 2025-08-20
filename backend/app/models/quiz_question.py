from app import supabase
from typing import List, Dict, Any

class QuizQuestion:
    def __init__(self):
        self.supabase = supabase  # Use the shared instance

    @staticmethod
    def validate_data(data: Dict[str, Any]) -> Dict[str, str]:
        """Validate question data"""
        errors = {}
        
        # Question text validation
        if not data.get('question_text') or not data['question_text'].strip():
            errors['question_text'] = "Question text is required"
        
        # Options validation
        required_options = ['option_a', 'option_b', 'option_c', 'option_d']
        for option in required_options:
            if not data.get(option) or not data[option].strip():
                errors[option] = f"{option.replace('_', ' ').title()} is required"
        
        # Correct answer validation
        correct_answer = data.get('correct_answer')
        if not correct_answer or correct_answer not in ['A', 'B', 'C', 'D']:
            errors['correct_answer'] = "Correct answer must be A, B, C, or D"
        
        # Points weight validation
        try:
            weight = float(data.get('points_weight', 1))
            if weight <= 0:
                errors['points_weight'] = "Points weight must be greater than 0"
        except (ValueError, TypeError):
            errors['points_weight'] = "Points weight must be a valid number"
        
        # Question order validation
        question_order_idx = data.get('question_order_idx')
        if question_order_idx is not None and not str(question_order_idx).strip():
            errors['question_order_idx'] = "Question order index cannot be empty if provided"
        elif not question_order_idx:
            errors['question_order_idx'] = "Question order index is required"
        return errors

    def create(self, quiz_id: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single question for a quiz"""
        try:
            # Validate question data
            validation_errors = self.validate_data(question_data)
            if validation_errors:
                return {"success": False, "errors": validation_errors}
            
            # Check if quiz exists
            quiz_check = self.supabase.table('quizzes')\
                .select('id')\
                .eq('id', quiz_id)\
                .execute()
            
            if not quiz_check.data:
                return {"success": False, "error": "Quiz not found"}
            
            # Prepare data for insertion
            insert_data = {
                'quiz_id': quiz_id,
                'question_text': question_data['question_text'].strip(),
                'option_a': question_data['option_a'].strip(),
                'option_b': question_data['option_b'].strip(),
                'option_c': question_data['option_c'].strip(),
                'option_d': question_data['option_d'].strip(),
                'correct_answer': question_data['correct_answer'].upper(),
                'explanation': question_data.get('explanation', '').strip() or None,
                'points_weight': float(question_data.get('points_weight', 1)),
                'question_order_idx': question_data.get('question_order_idx', str(len(self.find_by_quiz(quiz_id)["data"]) + 1))
            }
            
            # Insert into database
            result = self.supabase.table('quiz_questions').insert(insert_data).execute()
            
            if result.data:
                # Update quiz totals
                quiz = self._update_quiz_totals(quiz_id)
                return {"success": True,"updated_quiz":quiz, "data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to create question"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_bulk(self, quiz_id: str, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple questions for a quiz"""
        try:
            # Validate all questions first
            all_errors = {}
            for i, question in enumerate(questions):
                validation_errors = self.validate_data(question)
                if validation_errors:
                    for field, error in validation_errors.items():
                        all_errors[f'questions.{i}.{field}'] = error
            
            if all_errors:
                return {"success": False, "errors": all_errors}
            
            # Check if quiz exists
            quiz_check = self.supabase.table('quizzes')\
                .select('id')\
                .eq('id', quiz_id)\
                .execute()
            
            if not quiz_check.data:
                return {"success": False, "error": "Quiz not found"}
            
            # Get current question count for ordering
            current_questions = self.find_by_quiz(quiz_id)["data"]
            current_count = len(current_questions)
            
            # Prepare bulk insert data
            insert_data = []
            for i, question in enumerate(questions):
                insert_data.append({
                    'quiz_id': quiz_id,
                    'question_text': question['question_text'].strip(),
                    'option_a': question['option_a'].strip(),
                    'option_b': question['option_b'].strip(),
                    'option_c': question['option_c'].strip(),
                    'option_d': question['option_d'].strip(),
                    'correct_answer': question['correct_answer'].upper(),
                    'explanation': question.get('explanation', '').strip() or None,
                    'points_weight': float(question.get('points_weight', 1)),
                    'question_order_idx': question.get('question_order_idx', str(current_count + i + 1))
                })
            
            # Insert all questions
            result = self.supabase.table('quiz_questions').insert(insert_data).execute()
            
            if result.data:
                # Update quiz totals
                quiz = self._update_quiz_totals(quiz_id)
                return {"success": True,"updated_quiz":quiz, "data": result.data}
            else:
                return {"success": False, "error": "Failed to create questions"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def find_by_quiz(self, quiz_id: str, include_answers: bool = True) -> Dict[str, Any]:
        """Get all questions for a quiz"""
        try:
            # Select fields based on whether to include answers
            if include_answers:
                fields = '*'
            else:
                # Exclude correct_answer for student-facing queries
                fields = 'id, quiz_id, question_text, option_a, option_b, option_c, option_d, explanation, points_weight, question_order_idx, created_at'
            
            result = self.supabase.table('quiz_questions')\
                .select(fields)\
                .eq('quiz_id', quiz_id)\
                .order('question_order_idx')\
                .execute()
            
            return {"success": True, "data": result.data}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def find_by_id(self, question_id: str) -> Dict[str, Any]:
        """Get question by ID"""
        try:
            result = self.supabase.table('quiz_questions')\
                .select('*')\
                .eq('id', question_id)\
                .execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Question not found"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update(self, question_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a question"""
        try:
            # Validate update data
            validation_errors = self.validate_data(updates)
            if validation_errors:
                return {"success": False, "errors": validation_errors}
            
            # Get question to find quiz_id for total updates
            current_question = self.find_by_id(question_id)
            if not current_question["success"]:
                return current_question
            
            quiz_id = current_question["data"]["quiz_id"]
            
            # Prepare update data
            update_data = {}
            updatable_fields = [
                'question_text', 'option_a', 'option_b', 'option_c', 'option_d',
                'correct_answer', 'explanation', 'points_weight'
            ]
            
            for field in updatable_fields:
                if field in updates:
                    if field in ['question_text', 'option_a', 'option_b', 'option_c', 'option_d']:
                        update_data[field] = updates[field].strip()
                    elif field == 'correct_answer':
                        update_data[field] = updates[field].upper()
                    elif field == 'explanation':
                        update_data[field] = updates[field].strip() or None
                    elif field == 'points_weight':
                        update_data[field] = float(updates[field])
            
            # Update in database
            result = self.supabase.table('quiz_questions')\
                .update(update_data)\
                .eq('id',  question_id)\
                .execute()
            
            if result.data:
                # Update quiz totals if points changed
                if 'points_weight' in updates:
                    quiz = self._update_quiz_totals(quiz_id)
                return {"success": True, "updated_quiz":quiz,"data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to update question or question not found"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_by_quiz(self, quiz_id: str) -> Dict[str, Any]:
        """Delete all questions for a quiz"""
        try:
            result = self.supabase.table('quiz_questions')\
                .delete()\
                .eq('quiz_id', quiz_id)\
                .execute()
            
            # Update quiz totals (should be 0 after deleting all)
            self._update_quiz_totals(quiz_id)
            
            return {"success": True, "message": "All questions deleted successfully"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _update_quiz_totals(self, quiz_id: str):
        """Update quiz total_questions and total_points"""
        try:
            from app.models.quiz import quiz_model
            return quiz_model.update_totals(quiz_id)["data"]
        except Exception as e:
            print(f"Warning: Failed to update quiz totals: {e}")

# Create instance for use in routes
quiz_question_model = QuizQuestion()