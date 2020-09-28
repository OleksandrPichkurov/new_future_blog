from django import forms
from django.forms.widgets import Textarea
from .models import Comment

class EmailPostForm(forms.Form): #форма для отправки постов на емейл.
    name = forms.CharField(max_length=25)
    email = forms.EmailField()
    to = forms.EmailField()
    comments = forms.CharField(required=False,widget=forms.Textarea)

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('name', 'email', 'body')
