# forms.py

from django.contrib.auth.forms import AuthenticationForm
from django import forms


class CustomAuthForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'autofocus': True}))
