# quiz_app/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProgress, Leaderboard

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

@receiver(post_save, sender=User)
def save_user_progress(sender, instance, **kwargs):
    """Save UserProgress when User is saved"""
    try:
        instance.userprogress.save()
    except UserProgress.DoesNotExist:
        UserProgress.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_leaderboard_entry(sender, instance, **kwargs):
    """Save Leaderboard when User is saved"""
    try:
        instance.leaderboard.save()
    except Leaderboard.DoesNotExist:
        Leaderboard.objects.create(user=instance)