import time
import random
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=0.5):
    """Decorator that retries failed operations with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except OSError as e:
                    # Handle errno 11 (Resource temporarily unavailable)
                    if e.errno == 11 and attempt < max_retries:
                        last_exception = e
                        
                        # Exponential backoff with jitter for OSError
                        delay = base_delay * (2 ** attempt)
                        jitter = random.uniform(0, 0.1)
                        total_delay = delay + jitter
                        
                        print(f"OSError errno 11 detected, retrying in {total_delay:.2f}s (attempt {attempt + 2}/{max_retries + 1})")
                        time.sleep(total_delay)
                        continue
                    raise  # Re-raise if not errno 11 or max retries reached
                    
                except Exception as e:
                    # Check if it's a Supabase/connection error by examining error message
                    error_str = str(e).lower()
                    
                    if (("resource temporarily unavailable" in error_str or 
                         "connection" in error_str or
                         "timeout" in error_str or
                         "temporarily unavailable" in error_str) and 
                        attempt < max_retries):
                        
                        last_exception = e
                        
                        # Exponential backoff with jitter for connection errors
                        delay = base_delay * (2 ** attempt)
                        jitter = random.uniform(0, 0.1)
                        total_delay = delay + jitter
                        
                        print(f"Connection error detected: '{str(e)[:50]}...', retrying in {total_delay:.2f}s (attempt {attempt + 2}/{max_retries + 1})")
                        time.sleep(total_delay)
                        continue
                    
                    raise  # Re-raise non-retryable exceptions immediately
            
            # All retries exhausted, raise the last exception
            raise last_exception
        
        for attr in ("cache_clear","cache_info","cache_parameters"):
            if hasattr(func, attr):
                setattr(wrapper, attr, getattr(func, attr))
    
        return wrapper
    return decorator