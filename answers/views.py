from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseServerError
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login
from models import Question, Profile, Answer, Vote, Report
from forms import QuestionForm, AnswerForm, VoteForm, RegistrationForm
from django import forms
from django.utils.simplejson import dumps
from woozp_utils.view import request_response, AjaxView
from django.utils.translation import ugettext as _

def index(request):
    params = {'questions': Question.objects.all().order_by('-last_modified'),
              'form': QuestionForm(None),}
    return request_response(request, 'answers/list_questions.html', params)

class Register(AjaxView):
    def on_get_call(self, request):
        return request_response(request, 'answers/register.html',
                                {'form': RegistrationForm()})

    def on_post_call(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.instance.set_password(form.cleaned_data['password'])
            form.save()
            user = authenticate(username=form.instance.username, password=form.cleaned_data['password'])
            login(request, user)
            return HttpResponseRedirect(reverse('index'))
        return request_response(request, 'answers/register.html', {'form': form})

register = user_passes_test(lambda x: not x.is_authenticated(), login_url="/")(Register())

@login_required
def add_question(request):
    form = QuestionForm()
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            form.instance.user = request.user
            form.save()
            return HttpResponseRedirect(reverse('index'))
    
    return request_response(request, 'answers/add_question.html', {'form':form})
    
def view_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)

    params = {'question': question,
              'form': AnswerForm(),
              'vote_form': VoteForm(),
              'answers': question.public_answers,
              'voted': question.answers.filter(votes__user=request.user),
              'reported': question.answers.filter(reports__user=request.user),}
    return request_response(request, 'answers/view_question.html', params)

def answer_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    form = AnswerForm()
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            if request.user.is_authenticated():
                form.instance.user = request.user
            form.instance.question = question
            form.instance.ip = request.META['REMOTE_ADDR']
            form.save()
            return HttpResponseRedirect(reverse('view_question', args=[question_id]))

    return request_response(request, 'answers/answer_question.html',
                            {'form': form, 'question': question})
    
@login_required
def vote_answer(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id)
    form = VoteForm(request.POST)
    if not form.is_valid():
        return HttpResponseServerError(_("Were you playing with that form?"))
    
    Vote.objects.get_or_create(answer=answer, user=request.user,
                               defaults={'value':form.cleaned_data['value']})

    return HttpResponseRedirect(reverse('view_question', args=[answer.question.id]))

@login_required
def report_answer(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id)
    Report.objects.get_or_create(user=request.user, answer=answer)
    return HttpResponseRedirect(reverse('view_question', args=[answer.question.id]))
    