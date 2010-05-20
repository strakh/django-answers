import os.path
from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login',
        {'template_name': 'answers/login.html'}, name='login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout',
        {'next_page': '/'}, name='logout'),
    (r'^answers/', include('answers.urls')),
    (r'^$', 'django.views.generic.simple.redirect_to', { 'url': '/answers/'}),
    (r'static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)