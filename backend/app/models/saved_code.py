from app import supabase  
from typing import Dict, Any

class SavedCode:
    def __init__(self):
        self.supabase = supabase  # Use the shared instance

    @staticmethod
    def validate_data(title: str, code: str) -> Dict[str, str]:
        """Validate saved code data"""
        errors = {}
        
        if not title or not title.strip():
            errors['title'] = "Title is required"
        else:
            title_clean = title.strip()
            
            # Check if title ends with .isi
            if not title_clean.lower().endswith('.isi'):
                errors['title'] = "Title must end with .isi extension"
            elif len(title_clean) > 255:
                errors['title'] = "Title must be 255 characters or less"
            elif len(title_clean) <= 4:  # Just ".isi" or shorter
                errors['title'] = "Title must have a name before .isi extension"
            
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
        import re
        
        original_title = title
        base_name = original_title[:-4]  # Remove '.isi'
        
        # Remove existing number pattern
        number_pattern = r'^(.+?)\((\d+)\)$'
        match = re.match(number_pattern, base_name)
        
        if match:
            base_name = match.group(1) #remove (1) in filename(1)
        
        # Get all existing titles for this user
        result = self.supabase.table('saved_code')\
            .select('title')\
            .eq('user_id', user_id)\
            .execute()
        
        if not result.data:
            # No existing files, return clean title
            return f"{base_name}.isi"
        
        existing_titles = {row['title'] for row in result.data}
        
        # Check if clean base name is available
        clean_title = f"{base_name}.isi"
        if clean_title not in existing_titles:
            return clean_title
        
        # Find the highest existing number for this base name
        max_number = 0
        
        for existing_title in existing_titles:
                
            existing_base = existing_title[:-4]  # Remove .isi
            
            if existing_base == base_name:
                # Base name without number exists
                max_number = max(max_number, 1)
            else:
                # Check if it matches pattern: basename(number)
                pattern = re.escape(base_name) + r'\((\d+)\)$'
                match = re.match(pattern, existing_base)
                if match:
                    number = int(match.group(1))
                    max_number = max(max_number, number)
        
        # Return next available number
        return f"{base_name}({max_number + 1}).isi"

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

            current_file = self.supabase.table('saved_code')\
                .select('title')\
                .eq('id', code_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if not current_file.data:
                return {"success": False, "error": "File not found or access denied"}
            
            current_title = current_file.data[0]['title']            
            new_title = updates['title']
            if current_title != new_title:
                updates['title'] = self._get_unique_title(new_title, user_id)
                    
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