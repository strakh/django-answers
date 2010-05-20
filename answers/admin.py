from answers.models import Question, Answer, Vote, Report, Tag
from django.contrib import admin

admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Vote)
admin.site.register(Report)
admin.site.register(Tag)
