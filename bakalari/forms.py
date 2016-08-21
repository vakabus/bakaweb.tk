from django import forms
from django.forms import URLInput, PasswordInput, TextInput


class LoginForm(forms.Form):
    url = forms.CharField(max_length=256, label='', widget=URLInput(attrs={'id': 'login_url', 'class': 'pure-u-1 pure-u-md-1-4', 'placeholder': 'URL Bakalářů'}))
    username = forms.CharField(max_length=32, label='', widget=TextInput(attrs={'class': 'pure-u-1 pure-u-md-1-4', 'placeholder': 'Jméno'}))
    password = forms.CharField(max_length=128, label='', widget=PasswordInput(attrs={'class': 'pure-u-1 pure-u-md-1-4', 'placeholder': 'Heslo'}))