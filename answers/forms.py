from django import forms
from django.utils.translation import ugettext as _
from models import Question, Profile, Answer, Vote

class QuestionForm(forms.ModelForm):
    tags = forms.CharField(required=False)
    class Meta:
        model = Question
        exclude = ('created', 'user')
        
class TextWithLength(forms.CharField):
    def __init__(self, *args, **kargs):
        kargs['widget'] = forms.Textarea(attrs={'class':'max-length-%s' % kargs['max_length']})
        super(self.__class__, self).__init__(*args, **kargs)
            
class AnswerForm(forms.ModelForm):
    body = TextWithLength(max_length=250)
    class Meta:
        model = Answer
        fields = ('body',)
        
class VoteForm(forms.ModelForm):
    value = forms.ChoiceField(Vote.VALUES, label=_("Puntaje"))
    class Meta:
        model = Vote
        fields = ('value',)
        
class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    password_confirm = forms.CharField(widget=forms.PasswordInput())
    
    def clean_password_confirm(self):
        if self.cleaned_data['password'] != self.cleaned_data['password_confirm']:
            raise forms.ValidationError(_("El password y la confirmacion son distintos."))
        return self.cleaned_data['password_confirm']
    
    class Meta:
        model = Profile
        fields = ('username', 'email', 'about')


