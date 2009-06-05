from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class Profile(User):
    about = models.TextField()

class Question(models.Model):
    user = models.ForeignKey(User)
    title = models.CharField("La pregunta en si", max_length=250)
    body = models.TextField("Elabora un poco mas")
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now_add=True)
    tags = models.TextField()
    
    @property
    def public_answers(self):
        '''
        Si una respuesta tiene mas de 5 reportes necesita un ratio puntos/reportes mayor a 2
        para seguir apareciendo.
        '''
        reports_count_sql = 'SELECT COUNT(*) FROM answers_report WHERE answers_report.answer_id = answers_answer.id'
        points_count_sql = 'SELECT SUM(value) FROM answers_vote WHERE answers_vote.answer_id = answers_answer.id'
        votes_count_sql = 'SELECT COUNT(*) FROM answers_vote WHERE answers_vote.answer_id = answers_answer.id'
        return self.answer_set.all().order_by('-points')\
                    .extra(select = {'reports': reports_count_sql,
                                     'points': points_count_sql,
                                     'votes': votes_count_sql,},
                           where = ['((reports >= 5 AND (points/reports) > 2) OR reports < 5 )'])
                    
                    
    def save(self):
        for t in self.tags.split(','):
            if len(t) < 50:
                Tag.objects.get_or_create(text=t)
        self.last_modified = datetime.now()
        return super(Question, self).save()

class Answer(models.Model):
    question = models.ForeignKey(Question)
    user = models.ForeignKey(User, null=True)
    ip = models.IPAddressField()
    body = models.TextField("Tu respuesta")
    created = models.DateTimeField(auto_now_add=True)
    
    def save(self):
        q = self.question
        q.last_modified = datetime.now()
        q.save()
        return super(Answer, self).save()

class Vote(models.Model):
    VALUES = [(str(x),x) for x in range(1,6)]
    user = models.ForeignKey(User)
    answer = models.ForeignKey(Answer)
    value = models.SmallIntegerField(choices=VALUES)
    created = models.DateTimeField(auto_now_add=True)
    
class Report(models.Model):
    user = models.ForeignKey(User)
    answer = models.ForeignKey(Answer)
    created = models.DateTimeField(auto_now_add=True)

class Tag(models.Model):
    text = models.CharField(max_length=50)
    
    def __unicode__(self):
        return unicode(self.text)