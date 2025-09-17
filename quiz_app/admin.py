from django.contrib import admin
from .models import Question, QuizResult, UserProgress, UserAnswer, Category, Leaderboard, Achievement, UserAchievement, DailyQuestion

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'category', 'difficulty', 'correct_option', 'created_at')
    list_filter = ('category', 'difficulty', 'created_at')
    search_fields = ('question_text',)

@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'total_questions', 'percentage', 'quiz_type', 'completed_at')
    list_filter = ('quiz_type', 'completed_at')
    search_fields = ('user__username',)

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_attempts', 'average_score', 'accuracy')
    readonly_fields = ('total_attempts', 'average_score', 'questions_answered', 'correct_answers')
    
    def accuracy(self, obj):
        if obj.questions_answered > 0:
            return f"{(obj.correct_answers / obj.questions_answered) * 100:.2f}%"
        return "0%"

@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'selected_option', 'is_correct', 'answered_at')
    list_filter = ('is_correct', 'answered_at')
    search_fields = ('user__username', 'question__question_text')

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'rank', 'updated_at')
    readonly_fields = ('updated_at',)
    ordering = ('-score', 'updated_at')

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'icon')
    search_fields = ('name', 'description')

@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'unlocked_at')
    list_filter = ('achievement', 'unlocked_at')
    search_fields = ('user__username', 'achievement__name')

@admin.register(DailyQuestion)
class DailyQuestionAdmin(admin.ModelAdmin):
    list_display = ('date', 'question')
    list_filter = ('date',)