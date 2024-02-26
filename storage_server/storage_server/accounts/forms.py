from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", max_length=50)
    password = forms.CharField(
        label="Password", strip=False, widget=forms.PasswordInput
    )

class RegistrationForm(UserCreationForm):
    username = forms.CharField(label="Username", max_length=50)
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'full_name', 'email']