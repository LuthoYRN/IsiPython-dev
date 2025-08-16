from app import supabase
from typing import Optional, List, Dict, Any
import re
from datetime import datetime

class Quiz:
    def __init__(self):
        self.supabase = supabase  # Use the shared instance

    @staticmethod
    def validate_data(data: Dict[str, Any], exclude_id: Optional[str] = None) -> Dict[str, str]:
        """Validate quiz data"""
        errors = {}
        
        # Title validation
        if not data.get('title') or not data['title'].strip():
            errors['title'] = "Title is required"
        elif len(data['title'].strip()) > 255:
            errors['title'] = "Title must be 255 characters or less"
        
        # Time limit validation (has a default value)
        time_limit = data.get('time_limit_minutes')
        if time_limit is not None:
            try:
                time_limit = int(time_limit)
                if time_limit <= 0:
                    errors['time_limit_minutes'] = "Time limit must be greater than 0"
                elif time_limit > 360:  # 6 hours max
                    errors['time_limit_minutes'] = "Time limit cannot exceed 6 hours (360 minutes)"
            except (ValueError, TypeError):
                errors['time_limit_minutes'] = "Time limit must be a valid number"
        
        # Due date validation 
        due_date = data.get('due_date')
        if due_date:
            try:
                # Check if it's a future date
                if isinstance(due_date, str):
                    due_date_obj = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    if due_date_obj <= datetime.now(due_date_obj.tzinfo):
                        errors['due_date'] = "Due date must be in the future"
            except (ValueError, TypeError):
                errors['due_date'] = "Due date must be a valid date"
        else:
            errors['due_date'] = "Due date is required"
        
        # Instructions validation (optional array)
        instructions = data.get('instructions', [])
        if instructions is not None and not isinstance(instructions, list):
            errors['instructions'] = "Instructions must be an array"
        
        # Status validation
        valid_statuses = ['draft', 'published']
        status = data.get('status', 'draft')
        if status not in valid_statuses:
            errors['status'] = f"Status must be one of: {', '.join(valid_statuses)}"
        
        return errors

    @staticmethod
    def generate_slug(title: str) -> str:
        """Generate URL-friendly slug from title"""
        if not title:
            return ""
        
        # Convert to lowercase and remove special characters
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)  # Keep only letters, numbers, spaces, hyphens
        slug = re.sub(r'\s+', '-', slug)          # Replace spaces with hyphens
        slug = re.sub(r'-+', '-', slug)           # Replace multiple hyphens with single
        slug = slug.strip('-')                    # Remove leading/trailing hyphens
        
        return slug

    def _get_unique_slug(self, title: str, exclude_id: Optional[str] = None) -> str:
        """Generate unique slug, handling duplicates"""
        base_slug = self.generate_slug(title)
        
        if not base_slug:
            base_slug = "quiz"
        
        # Check if base slug is available
        query = self.supabase.table('quizzes').select('id').eq('slug', base_slug)
        
        # Exclude current quiz when updating
        if exclude_id:
            query = query.neq('id', exclude_id)
        
        result = query.execute()
        
        # If no conflicts, use base slug
        if not result.data:
            return base_slug
        
        # Find next available numbered slug
        counter = 2
        while True:
            numbered_slug = f"{base_slug}-{counter}"
            
            query = self.supabase.table('quizzes').select('id').eq('slug', numbered_slug)
            if exclude_id:
                query = query.neq('id', exclude_id)
            
            result = query.execute()
            
            if not result.data:
                return numbered_slug
            
            counter += 1

    def _check_title_uniqueness(self, title: str, exclude_id: Optional[str] = None) -> bool:
        """Check if title already exists"""
        query = self.supabase.table('quizzes')\
            .select('id')\
            .eq('title', title.strip())
        
        # Exclude current quiz when updating
        if exclude_id:
            query = query.neq('id', exclude_id)
        
        result = query.execute()
        return len(result.data) == 0  # True if title is unique

    def create(self, quiz_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new quiz"""
        try:
            # Validate quiz data
            validation_errors = self.validate_data(quiz_data)
            if validation_errors:
                return {"success": False, "errors": validation_errors}
            
            # Check for duplicate title
            title = quiz_data['title'].strip()
            if not self._check_title_uniqueness(title):
                return {"success": False, "errors": {"title": "A quiz with this title already exists"}}
            
            # Generate unique slug
            slug = self._get_unique_slug(title)
            
            # Prepare data for insertion
            insert_data = {
                'title': title,
                'slug': slug,
                'description': quiz_data.get('description', '').strip() or None,
                'instructions': quiz_data.get('instructions', []),
                'due_date': quiz_data.get('due_date'),
                'time_limit_minutes': int(quiz_data.get('time_limit_minutes', 60)),
                'total_questions': 0,  # Will be updated when questions are added
                'total_points': 0,     # Will be updated when questions are added
                'status': quiz_data.get('status', 'draft'),
                'randomize_question_order': quiz_data.get('randomize_question_order', False),
                'allow_multiple_attempts': quiz_data.get('allow_multiple_attempts', False),
                'send_notifications': quiz_data.get('send_notifications', False),
                'show_results_immediately': quiz_data.get('show_results_immediately', True)
            }
            
            # Insert into database
            result = self.supabase.table('quizzes').insert(insert_data).execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to create quiz"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def find_all(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get all quizzes with optional filtering"""
        try:
            # Start with base query
            query = self.supabase.table('quizzes').select('*')
            
            # Apply filters
            if filters:
                if filters.get('status'):
                    query = query.eq('status', filters['status'])
                
                if filters.get('search'):
                    # Search in title and description
                    search_term = filters['search']
                    query = query.or_(f'title.ilike.%{search_term}%,description.ilike.%{search_term}%')
            
            # Apply ordering
            order_by = filters.get('order_by', 'created_at') if filters else 'created_at'
            order_direction = filters.get('order_direction', 'desc') if filters else 'desc'
            
            if order_direction.lower() == 'desc':
                query = query.order(order_by, desc=True)
            else:
                query = query.order(order_by)
            
            # Apply pagination
            if filters and filters.get('limit'):
                limit = int(filters['limit'])
                query = query.limit(limit)
                
                if filters.get('offset'):
                    offset = int(filters['offset'])
                    query = query.offset(offset)
            
            result = query.execute()
            return {"success": True, "data": result.data}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def find_by_id(self, quiz_id: str) -> Dict[str, Any]:
        """Get quiz by ID"""
        try:
            result = self.supabase.table('quizzes')\
                .select('*')\
                .eq('id', quiz_id)\
                .execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Quiz not found"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update(self, quiz_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update quiz"""
        try:
            # Validate update data
            validation_errors = self.validate_data(updates, exclude_id=quiz_id)
            if validation_errors:
                return {"success": False, "errors": validation_errors}
            
            # Check for duplicate title if title is being updated
            if 'title' in updates:
                title = updates['title'].strip()
                if not self._check_title_uniqueness(title, exclude_id=quiz_id):
                    return {"success": False, "errors": {"title": "A quiz with this title already exists"}}
            
            # Prepare update data
            update_data = {}
            
            # Handle fields that can be updated
            updatable_fields = [
                'title', 'description', 'instructions', 'due_date','published_at',
                'time_limit_minutes', 'status', 'randomize_question_order',
                'allow_multiple_attempts', 'send_notifications', 'show_results_immediately'
            ]
            
            for field in updatable_fields:
                if field in updates:
                    if field == 'title':
                        # Update title and regenerate slug
                        title = updates['title'].strip()
                        update_data['title'] = title
                        update_data['slug'] = self._get_unique_slug(title, exclude_id=quiz_id)
                    elif field == 'description':
                        # Handle text field
                        value = updates[field].strip() if updates[field] else None
                        update_data[field] = value
                    elif field == 'time_limit_minutes':
                        # Handle numeric field
                        if updates[field] is not None:
                            update_data[field] = int(updates[field])
                        else:
                            update_data[field] = 60  # Default
                    else:
                        # Handle other fields directly
                        update_data[field] = updates[field]
            
            # Always update the updated_at timestamp
            update_data['updated_at'] = 'now()'
            
            # Update in database
            result = self.supabase.table('quizzes')\
                .update(update_data)\
                .eq('id', quiz_id)\
                .execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to update quiz or quiz not found"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete(self, quiz_id: str) -> Dict[str, Any]:
        """Delete quiz"""
        try:
            result = self.supabase.table('quizzes')\
                .delete()\
                .eq('id', quiz_id)\
                .execute()
            
            return {"success": True, "message": "Quiz deleted successfully"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_totals(self, quiz_id: str) -> Dict[str, Any]:
        """Update total_questions and total_points based on current questions"""
        try:
            # Get all questions for this quiz
            questions_result = self.supabase.table('quiz_questions')\
                .select('points_weight')\
                .eq('quiz_id', quiz_id)\
                .execute()
            
            questions = questions_result.data
            total_questions = len(questions)
            total_points = sum(float(q.get('points_weight', 0)) for q in questions)
            
            # Update quiz totals
            result = self.supabase.table('quizzes')\
                .update({
                    'total_points': int(total_points),
                    'total_questions': int(total_questions),
                    'updated_at': 'now()'
                })\
                .eq('id', quiz_id)\
                .execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to update quiz totals"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

# Create instance for use in routes
quiz_model = Quiz()