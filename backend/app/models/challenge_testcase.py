from app import supabase
from typing import Dict, Any
from functools import lru_cache

class ChallengeTestCase:
    def __init__(self):
        self.supabase = supabase  # Use the shared instance

    @staticmethod
    def validate_data(data: Dict[str, Any]) -> Dict[str, str]:
        """Validate test case data"""
        errors = {}
        
        # Expected output validation
        if not data.get('expected_output') or not data['expected_output'].strip():
            errors['expected_output'] = "Expected output is required"
        
        # Input data validation (must be array)
        input_data = data.get('input_data', [])
        if not isinstance(input_data, list):
            errors['input_data'] = "Input data must be an array"
        
        # Points weight validation
        try:
            weight = float(data.get('points_weight', 0))
            if weight < 0:
                errors['points_weight'] = "Points weight must be 0 or greater"
        except (ValueError, TypeError):
            errors['points_weight'] = "Points weight must be a valid number"
            
        # Boolean field validation 
        required_boolean_fields = ['is_hidden', 'is_example']
        for field in required_boolean_fields:
            if field not in data:
                errors[field] = f"{field.replace('_', ' ').title()} is required"
            elif not isinstance(data[field], bool):
                errors[field] = f"{field.replace('_', ' ').title()} must be true or false"
        
        # Logical validation: hidden and example cannot both be true
        if data.get('is_hidden') and data.get('is_example'):
            errors['is_hidden'] = "Test case cannot be both hidden and an example"
            errors['is_example'] = "Test case cannot be both hidden and an example"
        
        return errors

    def create(self, challenge_id: str, test_case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single test case for a challenge"""
        try:
            # Validate test case data
            validation_errors = self.validate_data(test_case_data)
            if validation_errors:
                return {"success": False, "errors": validation_errors}
            
            # Check if challenge exists
            challenge_check = self.supabase.table('challenges')\
                .select('id, reward_points')\
                .eq('id', challenge_id)\
                .execute()
            
            if not challenge_check.data:
                return {"success": False, "error": "Challenge not found"}
            
            # Prepare data for insertion
            insert_data = {
                'challenge_id': challenge_id,
                'input_data': test_case_data.get('input_data', []),
                'expected_output': test_case_data['expected_output'].strip(),
                'explanation': test_case_data.get('explanation', '').strip() or None,
                'is_hidden': test_case_data.get('is_hidden', False),
                'is_example': test_case_data.get('is_example', False),
                'points_weight': float(test_case_data.get('points_weight', 0))
            }
            
            # Insert into database
            result = self.supabase.table('challenge_test_cases').insert(insert_data).execute()
            
            if result.data:
                self.find_by_challenge.cache_clear()
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to create test case"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    @lru_cache(maxsize=300)
    def find_by_challenge(self, challenge_id: str) -> Dict[str, Any]:
        """Get all test cases for a challenge"""
        try:
            result = self.supabase.table('challenge_test_cases')\
                .select('*')\
                .eq('challenge_id', challenge_id)\
                .order('created_at')\
                .execute()
            
            return {"success": True, "data": result.data}
                
        except Exception as e:
            self.find_by_challenge.cache_clear()
            return {"success": False, "error": str(e)}

    def find_by_id(self, test_case_id: str) -> Dict[str, Any]:
        """Get test case by ID"""
        try:
            result = self.supabase.table('challenge_test_cases')\
                .select('*')\
                .eq('id', test_case_id)\
                .execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Test case not found"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update(self, test_case_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a test case"""
        try:
            # Validate update data
            validation_errors = self.validate_data(updates)
            if validation_errors:
                return {"success": False, "errors": validation_errors}
            
            # Prepare update data
            update_data = {}
            updatable_fields = [
                'input_data', 'expected_output', 'explanation', 
                'is_hidden', 'is_example', 'points_weight'
            ]
            
            for field in updatable_fields:
                if field in updates:
                    if field == 'expected_output':
                        update_data[field] = updates[field].strip()
                    elif field == 'explanation':
                        update_data[field] = updates[field].strip() or None
                    elif field == 'points_weight':
                        update_data[field] = float(updates[field])
                    else:
                        update_data[field] = updates[field]
            
            # Update in database
            result = self.supabase.table('challenge_test_cases')\
                .update(update_data)\
                .eq('id', test_case_id)\
                .execute()
            
            if result.data:
                self.find_by_challenge.cache_clear()
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to update test case or test case not found"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}


    def delete_by_challenge(self, challenge_id: str) -> Dict[str, Any]:
        """Delete all test cases for a challenge"""
        try:
            result = self.supabase.table('challenge_test_cases')\
                .delete()\
                .eq('challenge_id', challenge_id)\
                .execute()
            
            self.find_by_challenge.cache_clear()
            return {"success": True, "message": "All test cases deleted successfully"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def validate_weights_sum(self, challenge_id: str) -> Dict[str, Any]:
        """Validate that test case weights sum to challenge reward points"""
        try:
            # Get challenge reward points
            challenge_result = self.supabase.table('challenges')\
                .select('reward_points')\
                .eq('id', challenge_id)\
                .execute()
            
            if not challenge_result.data:
                return {"success": False, "error": "Challenge not found"}
            
            reward_points = challenge_result.data[0]['reward_points']
            
            # Get test case weights
            test_cases_result = self.supabase.table('challenge_test_cases')\
                .select('points_weight')\
                .eq('challenge_id', challenge_id)\
                .execute()
            
            total_weight = sum(float(tc.get('points_weight', 0)) for tc in test_cases_result.data)
            
            is_valid = total_weight == reward_points
            
            return {
                "success": True,
                "data": {
                    "is_valid": is_valid,
                    "total_weight": total_weight,
                    "reward_points": reward_points,
                    "difference": total_weight - reward_points
                }
            }
                
        except Exception as e:
            return {"success": False, "error": str(e)}

challenge_test_case_model = ChallengeTestCase()