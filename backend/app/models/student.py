from app import supabase
from typing import Dict, Any
from datetime import datetime

class Student:
    def __init__(self):
        self.supabase = supabase  # Use the shared instance
        
    def get_student_count(self) -> Dict[str, Any]:
        """Get number of students in the platform"""
        try:
            result = self.supabase.table('profiles').select('id', count='exact').execute()
            count = result.count if result.count else 0
            return {"success": True, "count": count}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_students_added_since(self, since_date: datetime) -> Dict[str, Any]:
        """Get count of students created since a specific date"""
        try:
            result = self.supabase.table('profiles')\
                .select('id', count='exact')\
                .gte('created_at', since_date.isoformat())\
                .execute()
            
            count = result.count if result.count else 0
            return {"success": True, "count": count}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete(self, user_id: str) -> Dict[str, Any]:
        """Delete student"""
        try:
            result = self.supabase.table('profiles')\
                .delete()\
                .eq('id', user_id)\
                .execute()
            
            return {"success": True, "message": "Student deleted successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        
# Create instance for use in routes
student_model = Student()