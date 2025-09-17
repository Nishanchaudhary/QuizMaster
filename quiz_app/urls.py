from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # General URLs
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('terms-and-conditions/', views.Terms_and_Conditions, name='terms_and_conditions'),
    path('privacy-policy/', views.Privacy_policy, name='privacy_policy'),
    path('terms_of_service/', views.Terms_of_service, name='terms_of_service'),

    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    # Quiz URLs
    path('quiz/', views.quiz, name='quiz'),
    path('result/<int:result_id>/', views.result, name='result'),
    path('review/<int:result_id>/', views.review_quiz, name='review_quiz'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('add-question/', views.add_question, name='add_question'),
    path('progress/', views.progress_dashboard, name='progress'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('custom-quiz/', views.create_custom_quiz, name='custom_quiz'),
    path('daily-question/', views.question_of_the_day, name='daily_question'),
    path('export-results/', views.export_results, name='export_results'),
]