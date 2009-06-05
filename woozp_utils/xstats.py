"""add x-django-xxx stats headers to the response.

based on https://pycon.coderanger.net/browser/django/trunk/pycon/middleware/xstats.py
alecu Removed some pycon-tech dependencies

original docs:
---
My take on the PageStatsMiddleware described here:
http://code.djangoproject.com/wiki/PageStatsMiddleware

If you have firefox and the web developer extension, go to:
    Information->View Response Headers (last item)

This feature is controled via the XStatsMiddleware feature
"""
from time import time
from itertools import islice
import thread

class XStatsMiddleware(object):
    def __init__(self):
        self.lock = thread.allocate()
#         from pycon.features import decorators
#         process_feat = decorators.feature('XStatsMiddleware',
#                                           disabled_func=self.process_passthrough,
#                                           auto_create_feat=True)
#         self.process_view = process_feat(self.process_xstats)
        
    def process_passthrough(self, request, view_func, view_args, view_kwargs):
        start = time()
        response = view_func(request, *view_args, **view_kwargs)
        response['x-django-total-time'] = "%.3fs" % (time() - start)
        return response
    
    def process_xstats(self, request, view_func, view_args, view_kwargs):
        # turn on debugging in db backend to capture time
        from django.db import connection
        from django.conf import settings
        debug = None
        self.lock.acquire()
        if settings.DEBUG is not True:
            debug = settings.DEBUG
            settings.DEBUG = True
        self.lock.release()
        # get number of db queries before we do anything
        n = len(connection.queries)

        # time the view
        start = time()
        response = view_func(request, *view_args, **view_kwargs)
        totTime = time() - start

        # compute the db time for the queries just run
        queries = len(connection.queries) - n
        if queries:
            dbTime = sum(float(q['time']) for q in islice(connection.queries, n, None))
            #for q in islice(connection.queries, n, None): print q['sql']
        else:
            dbTime = 0.0

        # and backout python time
        pyTime = totTime - dbTime

        self.lock.acquire()
        if debug is not None:
            # restore debugging setting
            settings.DEBUG = debug
        self.lock.release()
        
        response['x-django-total-time'] = "%.3fs" % totTime
        response['x-django-num-queries'] = repr(queries)
        response['x-django-query-time'] = "%.3fs" % dbTime
        response['x-django-python-time'] = "%.3fs" % pyTime
        return response
    
class XStatsMiddlewareFull(XStatsMiddleware):
    process_view = XStatsMiddleware.process_xstats

class XStatsMiddlewareFaster(XStatsMiddleware):
    process_view = XStatsMiddleware.process_passthrough
