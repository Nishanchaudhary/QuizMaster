from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import random


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#3B82F6")

    def __str__(self):
        return self.name

class Question(models.Model):
    question_text = models.TextField()
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)
    correct_option = models.IntegerField(choices=[(1, 'Option 1'), (2, 'Option 2'), (3, 'Option 3'), (4, 'Option 4')])
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    difficulty = models.CharField(max_length=10, choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ], default='medium')
    explanation = models.TextField(blank=True, help_text="Explanation of the correct answer")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.question_text[:50] + "..."

class QuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)
    time_taken = models.IntegerField(help_text="Time taken in seconds")
    quiz_type = models.CharField(max_length=20, default='standard', choices=[
        ('standard', 'Standard'),
        ('custom', 'Custom'),
        ('daily', 'Daily')
    ])
    
    def percentage(self):
        return round((self.score / self.total_questions) * 100, 2)
    
    def __str__(self):
        return f"{self.user.username} - {self.score}/{self.total_questions}"

class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='userprogress')
    total_attempts = models.IntegerField(default=0)
    average_score = models.FloatField(default=0)
    questions_answered = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    
    def update_stats(self, score, total_questions):
        self.total_attempts += 1
        self.questions_answered += total_questions
        self.correct_answers += score
        self.average_score = (self.average_score * (self.total_attempts - 1) + (score/total_questions)) / self.total_attempts
        self.save()
    
    def __str__(self):
        return f"{self.user.username} Progress"

class UserAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.IntegerField()
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)

class Leaderboard(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='leaderboard')
    score = models.IntegerField(default=0)
    rank = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-score', 'updated_at']

class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='trophy')
    condition = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'achievement']

class DailyQuestion(models.Model):
    date = models.DateField(unique=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    def __str__(self):
        return f"Daily Question for {self.date}"
    
@receiver(post_save, sender=User)
def create_user_progress(sender, instance, created, **kwargs):
    """Create UserProgress when a new User is created"""
    if created:
        UserProgress.objects.create(user=instance)

@receiver(post_save, sender=User)
def create_leaderboard_entry(sender, instance, created, **kwargs):
    """Create Leaderboard entry when a new User is created"""
    if created:
        Leaderboard.objects.create(user=instance)

# quiz_app/models.py
@receiver(post_save, sender=User)
def save_user_progress(sender, instance, **kwargs):
    """Save UserProgress when User is saved"""
    try:
        # Use the default reverse relation for ForeignKey
        user_progress = instance.userprogress_set.first()
        if user_progress:
            user_progress.save()
        else:
            UserProgress.objects.create(user=instance)
    except Exception:
        # Fallback if anything goes wrong
        UserProgress.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_leaderboard_entry(sender, instance, **kwargs):
    """Save Leaderboard when User is saved"""
    try:
        # For OneToOneField, we can use hasattr to check
        if hasattr(instance, 'leaderboard'):
            instance.leaderboard.save()
        else:
            Leaderboard.objects.create(user=instance)
    except Exception:
        # Fallback if anything goes wrong
        Leaderboard.objects.get_or_create(user=instance)