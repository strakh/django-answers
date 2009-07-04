import os.path
from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from answers.views import *

admin.autodiscover()

urlpatterns = patterns('',
    (r'dialectica/static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    url(r'^dialectica/register/$', register, name='register'),
    (r'^dialectica/admin/(.*)', admin.site.root),
    url(r'^dialectica/accounts/login/$', 'django.contrib.auth.views.login',
        {'template_name': 'answers/login.html'}, name='login'),
    url(r'^dialectica/accounts/logout/$', 'django.contrib.auth.views.logout',
        {'next_page': '/'}, name='logout'),
    url(r'^dialectica/add_question/$', add_question, name="add_question"),
    url(r'^dialectica/view_question/(?P<question_id>.*)/$', view_question, name="view_question"),
    url(r'^dialectica/answer_question/(?P<question_id>.*)/$', answer_question, name="answer_question"),
    url(r'^dialectica/vote_answer/(?P<answer_id>.*)/$', vote_answer, name="vote_answer"),
    url(r'^dialectica/report_answer/(?P<answer_id>.*)/$', report_answer, name="report_answer"),
    url(r'^dialectica/$', index, name='index'),
)