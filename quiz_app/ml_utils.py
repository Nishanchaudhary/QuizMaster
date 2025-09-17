import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from django.db.models import Count, Q
from .models import UserProgress


def calculate_effort_recommendation(user_progress):
    """
    Simple ML-based function to recommend effort needed to achieve 100%
    """
    if user_progress.questions_answered == 0:
        return "You need to start practicing! Answer at least 100 questions to get personalized recommendations."
    
    accuracy = user_progress.correct_answers / user_progress.questions_answered
    questions_needed = 0
    
    if accuracy < 0.5:
        questions_needed = 500
        return f"Your accuracy is low ({accuracy*100:.1f}%). You need to practice about {questions_needed} more questions to reach 100% mastery."
    elif accuracy < 0.7:
        questions_needed = 300
        return f"Your accuracy is moderate ({accuracy*100:.1f}%). You need to practice about {questions_needed} more questions to reach 100% mastery."
    elif accuracy < 0.9:
        questions_needed = 150
        return f"Your accuracy is good ({accuracy*100:.1f}%). You need to practice about {questions_needed} more questions to reach 100% mastery."
    else:
        questions_needed = 50
        return f"Your accuracy is excellent ({accuracy*100:.1f}%). You're almost there! Practice about {questions_needed} more questions to reach 100% mastery."





# quiz_app/ml_utils.py
def enhanced_effort_recommendation(user):
    from .models import QuizResult, UserProgress
    
    # Get user progress
    try:
        user_progress = UserProgress.objects.get(user=user)
    except UserProgress.DoesNotExist:
        return "Complete a few quizzes to get personalized recommendations."
    
    # Get user's performance data
    user_results = QuizResult.objects.filter(user=user)
    
    if user_results.count() < 2:
        return "Complete a few more quizzes to get personalized recommendations."
    
    # Calculate average accuracy
    if user_progress.questions_answered > 0:
        accuracy = (user_progress.correct_answers / user_progress.questions_answered) * 100
    else:
        accuracy = 0
    
    # Simple recommendation based on accuracy
    if accuracy < 50:
        return "Your accuracy is low. Focus on understanding the basics and review incorrect answers. You need to practice more questions to improve."
    elif accuracy < 70:
        return "Your accuracy is moderate. Keep practicing and focus on your weak areas. Review explanations for questions you get wrong."
    elif accuracy < 85:
        return "Your accuracy is good. You're making progress! Focus on consistent practice and timing."
    else:
        return "Your accuracy is excellent! You're close to mastery. Keep up the good work and focus on maintaining consistency."


def get_weak_categories(user):
    from .models import UserAnswer, Category
    
    # Get categories where user performance is below average
    user_answers = UserAnswer.objects.filter(user=user)
    
    if not user_answers.exists():
        return []
        
    category_stats = user_answers.values('question__category__name', 'question__category__id').annotate(
        total=Count('id'),
        correct=Count('id', filter=Q(is_correct=True))
    ).annotate(accuracy=100.0 * Count('id', filter=Q(is_correct=True)) / Count('id'))
    
    weak_categories = []
    for stat in category_stats:
        if stat['accuracy'] < 70:
            try:
                category = Category.objects.get(id=stat['question__category__id'])
                weak_categories.append({
                    'category': category,  # This should be the Category object, not a dict
                    'accuracy': stat['accuracy'],
                    'total': stat['total']
                })
            except Category.DoesNotExist:
                continue  # Skip if category doesn't exist
    
    return sorted(weak_categories, key=lambda x: x['accuracy'])[:5]


def check_achievements(user):
    from .models import Achievement, UserAchievement, QuizResult, UserAnswer
    
    achievements = Achievement.objects.all()
    user_achievements = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
    user_progress = UserProgress.objects.get(user=user)
    
    new_achievements = []
    
    for achievement in achievements:
        if achievement.id not in user_achievements:
            condition_met = False
            
            # Evaluate conditions
            if achievement.condition == 'first_quiz':
                condition_met = QuizResult.objects.filter(user=user).count() >= 1
            elif achievement.condition == 'perfect_score':
                condition_met = QuizResult.objects.filter(user=user, score=models.F('total_questions')).exists()
            elif achievement.condition == '100_questions':
                condition_met = user_progress.questions_answered >= 100
            elif achievement.condition == '500_questions':
                condition_met = user_progress.questions_answered >= 500
            elif achievement.condition == '5_quizzes':
                condition_met = user_progress.total_attempts >= 5
            elif achievement.condition == '20_quizzes':
                condition_met = user_progress.total_attempts >= 20
            elif achievement.condition == '90_percent_accuracy':
                condition_met = (user_progress.correct_answers / user_progress.questions_answered) >= 0.9 if user_progress.questions_answered > 0 else False
            
            if condition_met:
                UserAchievement.objects.create(user=user, achievement=achievement)
                new_achievements.append(achievement)
    
    return new_achievements