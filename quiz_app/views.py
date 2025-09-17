from .models import Question, UserProgress, UserAnswer, Category, Leaderboard, Achievement, UserAchievement, DailyQuestion,QuizResult
from .forms import NewUserForm, QuestionForm, CustomQuizForm
from .ml_utils import calculate_effort_recommendation, enhanced_effort_recommendation, check_achievements, get_weak_categories
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.db.models import Count, Q, F
from django.utils import timezone
from django.contrib.auth.models import User
from .models import UserProgress
from django.urls import reverse
from django.contrib import messages
import random
import time
import csv


def is_admin(user):
    return user.is_staff

def register(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Create user progress record (should be handled by signals, but just in case)
            UserProgress.objects.get_or_create(user=user)
            Leaderboard.objects.get_or_create(user=user)
            return redirect("index")
        else:
            return render(request, "registration/register.html", {"form": form})
    else:
        form = NewUserForm()
    return render(request, "registration/register.html", {"form": form})
def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return render(request, 'registration/login.html', {'error': 'Invalid credentials'})
    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    return redirect('index')

def index(request):
    # Get daily question
    today = timezone.now().date()
    daily_question = DailyQuestion.objects.filter(date=today).first()
    
    # Get leaderboard top 5
    leaders = Leaderboard.objects.all()[:5]
    
    # Get categories for filter
    categories = Category.objects.all()
    
    # Get statistics for the homepage
    total_questions = Question.objects.count()
    total_users = User.objects.count()
    total_quizzes = QuizResult.objects.count()
    
    return render(request, 'index.html', {
        'daily_question': daily_question,
        'leaders': leaders,
        'categories': categories,
        'total_questions': total_questions,
        'total_users': total_users,
        'total_quizzes': total_quizzes,
    })

@login_required
def quiz(request):
    if request.method == 'POST':
        # Process quiz results
        score = 0
        answers = request.POST
        start_time = float(request.POST.get('start_time', time.time()))
        time_taken = round(time.time() - start_time, 2)
        
        # Get quiz type
        quiz_type = request.session.get('quiz_type', 'standard')
        
        # Get all questions from session
        question_ids = request.session.get('quiz_questions', [])
        questions = Question.objects.filter(id__in=question_ids)
        
        user_answers = []
        for question in questions:
            user_answer = answers.get(f'question_{question.id}')
            if user_answer:
                is_correct = int(user_answer) == question.correct_option
                if is_correct:
                    score += 1
                
                # Save user answer
                user_answers.append(UserAnswer(
                    user=request.user,
                    question=question,
                    selected_option=int(user_answer),
                    is_correct=is_correct
                ))
        
        # Bulk create user answers
        UserAnswer.objects.bulk_create(user_answers)
        
        # Save result
        total_questions = len(questions)
        quiz_result = QuizResult.objects.create(
            user=request.user,
            score=score,
            total_questions=total_questions,
            time_taken=time_taken,
            quiz_type=quiz_type
        )
        
        # Update user progress
        user_progress, created = UserProgress.objects.get_or_create(user=request.user)
        user_progress.update_stats(score, total_questions)
        
        # Update leaderboard
        leaderboard, created = Leaderboard.objects.get_or_create(user=request.user)
        leaderboard.score = user_progress.correct_answers
        leaderboard.save()
        
        # Update ranks
        update_leaderboard_ranks()
        
        # Check for new achievements
        new_achievements = check_achievements(request.user)
        if new_achievements:
            request.session['new_achievements'] = [achievement.name for achievement in new_achievements]
        
        # Clear session data
        for key in ['quiz_questions', 'quiz_type', 'quiz_start_time']:
            if key in request.session:
                del request.session[key]
            
        return redirect('result', result_id=quiz_result.id)
    
    else:
        # Check if custom quiz
        quiz_type = request.GET.get('type', 'standard')
        request.session['quiz_type'] = quiz_type
        
        if quiz_type == 'custom':
            # Get custom quiz parameters from session
            custom_params = request.session.get('custom_quiz_params', {})
            categories = custom_params.get('categories', [])
            difficulty = custom_params.get('difficulty', 'all')
            question_count = custom_params.get('question_count', 20)
            
            # Build query
            questions = Question.objects.all()
            if categories:
                questions = questions.filter(category__id__in=categories)
            if difficulty != 'all':
                questions = questions.filter(difficulty=difficulty)
                
            questions = list(questions)
            if len(questions) > question_count:
                questions = random.sample(questions, question_count)
                
        elif quiz_type == 'daily':
            # Get today's daily question
            today = timezone.now().date()
            daily_question = DailyQuestion.objects.filter(date=today).first()
            questions = [daily_question.question] if daily_question else []
            
        else:  # Standard quiz
            # Get 100 random questions
            all_questions = list(Question.objects.all())
            if len(all_questions) > 100:
                questions = random.sample(all_questions, 100)
            else:
                questions = all_questions
                
        # Store question IDs in session
        request.session['quiz_questions'] = [q.id for q in questions]
        request.session['quiz_start_time'] = time.time()
        
        return render(request, 'quiz.html', {
            'questions': questions, 
            'start_time': time.time(),
            'quiz_type': quiz_type
        })


@login_required
def create_custom_quiz(request):
    categories = Category.objects.all()
    
    if request.method == 'POST':
        form = CustomQuizForm(request.POST)
        if form.is_valid():
            selected_categories = form.cleaned_data['categories']
            difficulty = form.cleaned_data['difficulty']
            question_count = form.cleaned_data['question_count']
            
            # Store parameters in session
            request.session['custom_quiz_params'] = {
                'categories': [cat.id for cat in selected_categories],
                'difficulty': difficulty,
                'question_count': question_count
            }
            
            # Redirect to quiz page with custom type parameter
            return redirect(f'{reverse("quiz")}?type=custom')
        else:
            # Form is invalid, show errors
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomQuizForm()
    
    return render(request, 'custom_quiz.html', {'form': form, 'categories': categories})




@login_required
def result(request, result_id):
    result = get_object_or_404(QuizResult, id=result_id, user=request.user)
    user_progress = UserProgress.objects.get(user=request.user)
    effort_recommendation = enhanced_effort_recommendation(request.user)
    
    # Get new achievements if any
    new_achievements = request.session.pop('new_achievements', [])
    
    return render(request, 'result.html', {
        'result': result,
        'effort_recommendation': effort_recommendation,
        'new_achievements': new_achievements
    })

@login_required
def review_quiz(request, result_id):
    result = get_object_or_404(QuizResult, id=result_id, user=request.user)
    
    # Get questions and user answers for this quiz
    questions = Question.objects.filter(id__in=request.session.get('review_questions', []))
    user_answers = {}
    
    for question in questions:
        user_answer = UserAnswer.objects.filter(
            user=request.user, 
            question=question,
            answered_at__date=result.completed_at.date()
        ).first()
        if user_answer:
            user_answers[question.id] = {
                'selected_option': user_answer.selected_option,
                'is_correct': user_answer.is_correct
            }
    
    return render(request, 'review.html', {
        'result': result,
        'questions': questions,
        'user_answers': user_answers
    })

@user_passes_test(is_admin)
def admin_dashboard(request):
    total_questions = Question.objects.count()
    total_users = User.objects.count()
    total_quizzes = QuizResult.objects.count()
    
    return render(request, 'admin_dashboard.html', {
        'total_questions': total_questions,
        'total_users': total_users,
        'total_quizzes': total_quizzes
    })

@user_passes_test(is_admin)
def add_question(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = QuestionForm()
    
    return render(request, 'add_question.html', {'form': form})

@login_required
def progress_dashboard(request):
    # Get or create user progress
    user_progress, created = UserProgress.objects.get_or_create(user=request.user)
    
    quiz_results = QuizResult.objects.filter(user=request.user).order_by('-completed_at')[:10]
    
    # Category performance
    categories = Category.objects.all()
    category_performance = []
    for category in categories:
        correct = UserAnswer.objects.filter(
            user=request.user, 
            question__category=category, 
            is_correct=True
        ).count()
        total = UserAnswer.objects.filter(
            user=request.user, 
            question__category=category
        ).count()
        accuracy = (correct / total * 100) if total > 0 else 0
        category_performance.append({
            'category': category,
            'accuracy': round(accuracy, 1),
            'total': total
        })
    
    # Get user achievements
    achievements = UserAchievement.objects.filter(user=request.user).select_related('achievement')
    
    return render(request, 'progress.html', {
        'user_progress': user_progress,
        'quiz_results': quiz_results,
        'category_performance': category_performance,
        'achievements': achievements
    })

def leaderboard(request):
    leaders = Leaderboard.objects.all()[:20]
    
    # Add rank numbers
    for i, leader in enumerate(leaders):
        leader.rank = i + 1
    
    return render(request, 'leaderboard.html', {'leaders': leaders})

@login_required
def question_of_the_day(request):
    today = timezone.now().date()
    
    # Get or create today's question
    daily_question, created = DailyQuestion.objects.get_or_create(
        date=today,
        defaults={'question': Question.objects.order_by('?').first()}
    )
    
    if request.method == 'POST':
        selected_option = int(request.POST.get('answer'))
        is_correct = (selected_option == daily_question.question.correct_option)
        
        # Record answer
        UserAnswer.objects.create(
            user=request.user,
            question=daily_question.question,
            selected_option=selected_option,
            is_correct=is_correct
        )
        
        # Update user progress
        user_progress, created = UserProgress.objects.get_or_create(user=request.user)
        user_progress.update_stats(1 if is_correct else 0, 1)
        
        return render(request, 'daily_question_result.html', {
            'is_correct': is_correct,
            'correct_option': daily_question.question.correct_option,
            'explanation': daily_question.question.explanation,
            'question': daily_question.question
        })
    
    # Check if user already answered today's question
    already_answered = UserAnswer.objects.filter(
        user=request.user,
        question=daily_question.question,
        answered_at__date=today
    ).exists()
    
    return render(request, 'daily_question.html', {
        'question': daily_question.question,
        'already_answered': already_answered
    })

@login_required
def export_results(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="quizmaster_results.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Score', 'Total Questions', 'Percentage', 'Time Taken', 'Quiz Type'])
    
    results = QuizResult.objects.filter(user=request.user).order_by('-completed_at')
    for result in results:
        writer.writerow([
            result.completed_at.strftime('%Y-%m-%d %H:%M'),
            result.score,
            result.total_questions,
            f"{result.percentage()}%",
            f"{result.time_taken}s",
            result.get_quiz_type_display()
        ])
    
    return response

def update_leaderboard_ranks():
    # Update all leaderboard ranks based on score and last updated time
    leaders = Leaderboard.objects.all().order_by('-score', 'updated_at')
    
    for rank, leader in enumerate(leaders, start=1):
        if leader.rank != rank:
            leader.rank = rank
            leader.save()

def about(request):
    return render(request, 'about.html')

def contact(request):
    if request.method == 'POST':
        # Handle contact form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you would typically send an email or save to database
        messages.success(request, 'Thank you for your message! We will get back to you soon.')
        return redirect('contact')
    return render(request, 'contact.html')

def Terms_and_Conditions(request):
    return render(request, 'terms_and_conditions.html')

def Privacy_policy(request):
    return render(request, 'privacy_policy.html')

def Terms_of_service(request):
    return render(request,'Terms_of_service.html')