from app import supabase  
from typing import Optional, List, Dict, Any

class SavedCode:
    def __init__(self):
        self.supabase = supabase  # Use the shared instance

    @staticmethod
    def validate_data(title: str, code: str) -> Dict[str, str]:
        """Validate saved code data"""
        errors = {}
        
        if not title or not title.strip():
            errors['title'] = "Title is required"
        elif len(title.strip()) > 255:
            errors['title'] = "Title must be 255 characters or less"
        
        if not code or not code.strip():
            errors['code'] = "Code is required"
        
        return errors
    
    def create(self, title: str, code: str, user_id: str) -> Dict[str, Any]:
        """Create a new saved code entry"""
        try:
            # Validate input
            validation_errors = self.validate_data(title, code)
            if validation_errors:
                return {"success": False, "errors": validation_errors}
            
            #check if filename already exists
            unique_title = self._get_unique_title(title.strip(), user_id)
            # Insert into database
            result = self.supabase.table('saved_code').insert({
                'title': unique_title.strip(),
                'code': code,
                'user_id': user_id
            }).execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to save code"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_unique_title(self, title: str, user_id: str) -> str:
        """Generate a unique title by appending numbers if needed"""
        original_title = title
        counter = 1
        current_title = original_title
        
        while True:
            # Check if current title exists
            existing = self.supabase.table('saved_code')\
                .select('id')\
                .eq('user_id', user_id)\
                .eq('title', current_title)\
                .execute()
            
            if not existing.data:
                return current_title
            
            # Title exists, try with number
            current_title = f"{original_title}({counter})"
            counter += 1
            
            # Safety check 
            if counter > 100:
                # Fallback with timestamp
                import time
                timestamp = int(time.time())
                return f"{original_title}({timestamp})"
    
    def find_by_user(self, user_id: str) -> Dict[str, Any]:
        """Get all saved code for a specific user"""
        try:
            result = self.supabase.table('saved_code')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('updated_at',desc=True)\
                .execute()
            
            return {"success": True, "data": result.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def find_by_id(self, code_id: str, user_id: str = None) -> Dict[str, Any]:
        """Get saved code by ID, optionally filtered by user"""
        try:
            query = self.supabase.table('saved_code').select('*').eq('id', code_id)
            
            # Add user filter if provided (for security)
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Code not found or access denied"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update(self, code_id: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """Update saved code entry"""
        try:
            # Build update dictionary from valid fields
            valid_fields = ['title', 'code']
            updates = {k: v for k, v in kwargs.items() if k in valid_fields}
            
            if not updates:
                return {"success": False, "error": "No valid fields to update"}
            
            # Validate if title or code are being updated
            if 'title' in updates or 'code' in updates:
                validation_errors = self.validate_data(
                    updates.get('title', 'valid'),  # Use placeholder if not updating
                    updates.get('code', 'valid')
                )
                if validation_errors:
                    return {"success": False, "errors": validation_errors}
            
            # Clean title if provided
            if 'title' in updates:
                updates['title'] = updates['title'].strip()
            
            result = self.supabase.table('saved_code')\
                .update(updates)\
                .eq('id', code_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to update or access denied"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete(self, code_id: str, user_id: str) -> Dict[str, Any]:
        """Delete saved code entry"""
        try:
            result = self.supabase.table('saved_code')\
                .delete()\
                .eq('id', code_id)\
                .eq('user_id', user_id)\
                .execute()
            
            return {"success": True, "message": "Code deleted successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
saved_code_model = SavedCode()