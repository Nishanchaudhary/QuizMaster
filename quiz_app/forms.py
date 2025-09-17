from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Question, Category

class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'option1', 'option2', 'option3', 'option4', 'correct_option', 'category', 'difficulty', 'explanation']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 3, 'class': 'w-full p-2 border rounded'}),
            'option1': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'option2': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'option3': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'option4': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'correct_option': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'category': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'difficulty': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'explanation': forms.Textarea(attrs={'rows': 2, 'class': 'w-full p-2 border rounded'}),
        }

class CustomQuizForm(forms.Form):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    difficulty = forms.ChoiceField(
        choices=[('all', 'All'), ('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')],
        widget=forms.RadioSelect,
        initial='all'
    )
    question_count = forms.IntegerField(
        min_value=5,
        max_value=100,
        initial=20,
        widget=forms.NumberInput(attrs={'class': 'w-full p-2 border rounded'})
    )

