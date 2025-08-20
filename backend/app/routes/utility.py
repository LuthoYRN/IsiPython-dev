from datetime import datetime, timedelta

def get_week_start():
    """Get Monday 00:00:00 of current week"""
    today = datetime.now()
    days_since_monday = today.weekday()  # 0=Monday, 6=Sunday
    monday = today - timedelta(days=days_since_monday)
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)