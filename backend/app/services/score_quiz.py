def _score_quiz_submission(questions, user_answers, total_points):
    """Score a quiz submission and return results"""
    questions_correct = 0
    questions_total = len(questions)
    detailed_results = []
    total_score = 0
    
    for question in questions:
        question_id = question["id"]
        correct_answer = question["correct_answer"]
        points_weight = question["points_weight"]
        user_answer = user_answers.get(question_id)
        
        is_correct = user_answer == correct_answer if user_answer is not None else False
        points_earned = points_weight if is_correct else 0
        
        if is_correct:
            questions_correct += 1
            total_score += points_earned
        
        detailed_results.append({
            "question_id": question_id,
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "points_weight":points_weight
        })
    
    # Calculate percentage
    percentage = (total_score / total_points * 100) if total_points > 0 else 0
    
    return {
        "score": total_score,
        "percentage": round(percentage, 2),
        "questions_correct": questions_correct,
        "questions_total": questions_total,
        "detailed_results": detailed_results,
        "status": "completed"
    }