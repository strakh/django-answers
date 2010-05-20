from django.conf.urls.defaults import *

urlpatterns = patterns('answers.views',
    url(r'^register/$', 'register', name='register'),
    url(r'^add_question/$', 'add_question', name='add_question'),
    url(r'^view_question/(?P<question_id>.*)/$', 'view_question', name='view_question'),
    url(r'^answer_question/(?P<question_id>.*)/$', 'answer_question', name='answer_question'),
    url(r'^vote_answer/(?P<answer_id>.*)/$', 'vote_answer', name='vote_answer'),
    url(r'^report_answer/(?P<answer_id>.*)/$', 'report_answer', name='report_answer'),
    url(r'^$', 'index', name='index'),
)