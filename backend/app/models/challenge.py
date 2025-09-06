from app import supabase
from typing import Optional, Dict, Any
from datetime import datetime
from app.utils.utility import clear_challenge_dependent_caches
import re
from functools import lru_cache

class Challenge:
    def __init__(self):
        self.supabase = supabase  # Use the shared instance

    @staticmethod
    def validate_data(data: Dict[str, Any]) -> Dict[str, str]:
        """Validate challenge data"""
        errors = {}
        
        # Title validation
        title = data.get('title', '').strip()
        
        if not title:
            errors['title'] = "Title is required"
        elif len(title) > 255:
            errors['title'] = "Title must be 255 characters or less"
            
        # Problem statement validation
        if not data.get('problem_statement') or not data['problem_statement'].strip():
            errors['problem_statement'] = "Problem statement is required"
        
        # Difficulty level validation
        valid_difficulties = ['Easy', 'Medium', 'Hard']
        if not data.get('difficulty_level') or data['difficulty_level'] not in valid_difficulties:
            errors['difficulty_level'] = f"Difficulty must be one of: {', '.join(valid_difficulties)}"
        
        # Reward points validation
        reward_points = data.get('reward_points', 0)
        try:
            reward_points = int(reward_points)
            if reward_points < 0:
                errors['reward_points'] = "Reward points must be 0 or greater"
        except (ValueError, TypeError):
            errors['reward_points'] = "Reward points must be a valid number"
        
        # Estimated time validation
        estimated_time = data.get('estimated_time')
        if estimated_time is not None:
            try:
                estimated_time = int(estimated_time)
                if estimated_time <= 0:
                    errors['estimated_time'] = "Estimated time must be greater than 0"
            except (ValueError, TypeError):
                errors['estimated_time'] = "Estimated time must be a valid number"
        
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
            base_slug = "challenge"
        
        # Check if base slug is available
        query = self.supabase.table('challenges').select('id').eq('slug', base_slug)
        
        # Exclude current challenge when updating
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
            
            query = self.supabase.table('challenges').select('id').eq('slug', numbered_slug)
            if exclude_id:
                query = query.neq('id', exclude_id)
            
            result = query.execute()
            
            if not result.data:
                return numbered_slug
            
            counter += 1

    def _check_title_uniqueness(self, title: str, exclude_id: Optional[str] = None) -> bool:
        """Check if title already exists"""
        query = self.supabase.table('challenges')\
            .select('id')\
            .eq('title', title.strip())
        
        # Exclude current challenge when updating
        if exclude_id:
            query = query.neq('id', exclude_id)
        
        result = query.execute()
        return len(result.data) == 0  # True if title is unique

    def create(self, challenge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new challenge"""
        try:
            # Validate input data
            validation_errors = self.validate_data(challenge_data)
            if validation_errors:
                return {"success": False, "errors": validation_errors}
            
            title = challenge_data['title'].strip()
            if not self._check_title_uniqueness(title):
                return {"success": False, "errors": {"title": "A challenge with this title already exists"}}
           
            # Generate unique slug
            title = challenge_data['title'].strip()
            slug = self._get_unique_slug(title)
            
            # Prepare data for insertion
            insert_data = {
                'title': title,
                'slug': slug,
                'short_description': challenge_data.get('short_description', '').strip() or None,
                'problem_statement': challenge_data['problem_statement'].strip(),
                'difficulty_level': challenge_data['difficulty_level'],
                'tags': challenge_data.get('tags', []),
                'reward_points': int(challenge_data.get('reward_points', 0)),
                'estimated_time': int(challenge_data['estimated_time']) if challenge_data.get('estimated_time') else None,
                'status': challenge_data.get('status', 'draft'),
                'send_notifications': challenge_data.get('send_notifications', False),
            }
            
            # Insert into database
            result = self.supabase.table('challenges').insert(insert_data).execute()
            
            if result.data:
                self.find_by_id.cache_clear()
                clear_challenge_dependent_caches()
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to create challenge"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def find_all(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get all challenges with optional filtering"""
        try:
            # Start with base query
            query = self.supabase.table('challenges').select('*')
            
            # Apply filters
            if filters:
                if filters.get('status'):
                    query = query.eq('status', filters['status'])
                
                if filters.get('difficulty_level'):
                    query = query.eq('difficulty_level', filters['difficulty_level'])
                
                if filters.get('search'):
                    # Search in title and short_description
                    search_term = filters['search']
                    query = query.or_(f'title.ilike.%{search_term}%,short_description.ilike.%{search_term}%')
            
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
    
    @lru_cache(maxsize=500)
    def find_by_id(self, challenge_id: str) -> Dict[str, Any]:
        """Get challenge by ID"""
        try:
            result = self.supabase.table('challenges')\
                .select('*')\
                .eq('id', challenge_id)\
                .execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Challenge not found"}
                
        except Exception as e:
            self.find_by_id.cache_clear()
            clear_challenge_dependent_caches()
            return {"success": False, "error": str(e)}

    def update(self, challenge_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update challenge"""
        try:
            # Validate update data
            validation_errors = self.validate_data(updates)
            if validation_errors:
                return {"success": False, "errors": validation_errors}
            
            if 'title' in updates:
                title = updates['title'].strip()
                if not self._check_title_uniqueness(title, exclude_id=challenge_id):
                    return {"success": False, "errors": {"title": "A challenge with this title already exists"}}
           
            # Prepare update data
            update_data = {}
            
            # Handle fields that can be updated
            updatable_fields = [
                'title', 'short_description', 'problem_statement', 
                'difficulty_level', 'tags', 'reward_points', 'published_at',
                'estimated_time', 'status', 'send_notifications'
            ]
            
            for field in updatable_fields:
                if field in updates:
                    if field == 'title':
                        # Update title and regenerate slug
                        title = updates['title'].strip()
                        update_data['title'] = title
                        update_data['slug'] = self._get_unique_slug(title, exclude_id=challenge_id)
                    elif field in ['short_description', 'problem_statement']:
                        # Handle text fields
                        value = updates[field].strip() if updates[field] else None
                        update_data[field] = value
                    elif field in ['reward_points', 'estimated_time']:
                        # Handle numeric fields
                        if updates[field] is not None:
                            update_data[field] = int(updates[field])
                        else:
                            update_data[field] = None
                    else:
                        # Handle other fields directly
                        update_data[field] = updates[field]
            
            # Always update the updated_at timestamp
            update_data['updated_at'] = 'now()'
            
            # Update in database
            result = self.supabase.table('challenges')\
                .update(update_data)\
                .eq('id', challenge_id)\
                .execute()
            
            if result.data:
                self.find_by_id.cache_clear()
                clear_challenge_dependent_caches()
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to update challenge or challenge not found"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_challenges_published_since(self, since_date: datetime) -> Dict[str, Any]:
        """Get published challenges since a specific date"""
        try:
            result = self.supabase.table('challenges')\
            .select('*')\
            .eq('status', 'published')\
            .gte('published_at', since_date.isoformat())\
            .execute()
            
            if result.data:
                return {"success": True, "data": result.data}
            else:
                return {"success": True, "data": []}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete(self, challenge_id: str) -> Dict[str, Any]:
        """Delete challenge"""
        try:
            result = self.supabase.table('challenges')\
                .delete()\
                .eq('id', challenge_id)\
                .execute()
            if result.data:
                self.find_by_id.cache_clear()
                clear_challenge_dependent_caches()
                return {"success": True, "message": "Challenge deleted successfully"}
            else:
                return {"success": False, "error": "Failed to delete or challenge not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        
# Create instance for use in routes
challenge_model = Challenge()