import new
from urlparse import urlparse, urlunparse
from woozp_utils.json import json_encode
from django.utils.datastructures import MultiValueDict
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.template import RequestContext
from django.conf import settings
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django import forms

def json_to_response(vars, content_type=None):
    return HttpResponse(json_encode(vars), content_type=content_type)

class AjaxView(object):
    '''
    A view dispatching to different methods depending on the request type.
    A PreRun can be defined inheriting from PreRunForm to perform prerequisites validation.
    '''
    PreRun = None
    
    def __init__(self):
        self.__name__ = self.__class__.__name__
    
    def on_get_call(self, request, *args, **kargs):
        raise NotImplementedError()

    def on_post_call(self, request, *args, **kargs):
        raise NotImplementedError()
    
    def on_ajax_get_call(self, request, *args, **kargs):
        raise NotImplementedError()
    
    def on_ajax_post_call(self, request, *args, **kargs):
        raise NotImplementedError()
                
    def __call__(self, request, *args, **kargs):
        if self.PreRun:
            pre_run_form = self.PreRun(request, kargs, self)
            if not pre_run_form.is_valid():
                if settings.DEBUG:
                    return HttpResponse(pre_run_form.errors.as_text())
                else:
                    if request.is_ajax():
                        return pre_run_form.JSON_ERROR
                    else:
                        return pre_run_form.HTML_ERROR
                    
            
            request.pre_run_data = pre_run_form.cleaned_data
        
        if request.is_ajax():
            if request.method == "POST":
                method = self.on_ajax_post_call
            else:
                method = self.on_ajax_get_call
        elif request.method == "POST" or getattr(request,'is_fake_post',None):
            method = self.on_post_call
        else:
            method = self.on_get_call
            
        return method(request, *args, **kargs)
    
class PreRunForm(forms.Form):
    JSON_ERROR = json_to_response({'status':500, 'error':'Page was invalid',})
    HTML_ERROR = HttpResponseServerError('Page was invalid')
    
    def __init__(self, request, kargs, view):
        self.request = request
        self.view = view
        self.view_kargs = kargs
        data = MultiValueDict()
        for x in request.GET.copy(), request.POST.copy(), kargs:
            data.update(x)
        super(PreRunForm, self).__init__(data=data)
        
class InQuerysetPreRun(PreRunForm):
    '''A PreRun that validates certain parameters to be keys in corresponding querysets'''
    
    def __init__(self, request, kargs, view):
        super(InQuerysetPreRun, self).__init__(request, kargs, view)
        for field_desc in self.get_querysets(request, kargs, view):
            try:
                param_name, queryset = field_desc
                field_kargs = {}
            except ValueError:
                param_name, queryset, field_kargs = field_desc
            
            self.fields[param_name] = forms.ModelChoiceField(queryset, **field_kargs)
        
    def get_querysets(self, request, kargs, view):
        '''returns a list of tuples (param_name, queryset)
           therefore validating param_name is the id of one of the objects in queryset'''
        raise NotImplementedError('must redefine get_queryset')

class SmartPageView(AjaxView):
    '''
    A page that can be loaded as ajah content or as a stand alone page inside a skeleton
    Skeleton template receives 'inner_content_tpl_name' which is the template name (self.TEMPLATE)
    '''
    TEMPLATE = '' #Template containing the inner content html
    SKELETON = '' #Skeleton for stand alone page
    
    def skeleton_params(self, request, *args, **kargs):
        '''Return params to be passed to SKELETON
            This way we can serve just the inner content or the skeleton depending on the request type
        '''
        return {}
    
    def template_params(self, request, *args, **kargs):
        '''Return params to be passed to TEMPLATE,
            This way we can serve just the inner content or the skeleton depending on the request type
        '''
        return {}
    
    def in_skeleton(self, request, params, *args, **kargs):
        ''' return self.TEMPLATE inside skeleton, passing params '''
        params['inner_content_tpl_name'] = self.TEMPLATE
        skeleton_params = self.skeleton_params(request, *args, **kargs)
        skeleton_params.update(params)
        return request_response(request, self.SKELETON, skeleton_params)
    
    def on_get_call(self, request, *args, **kargs):
        params = self.template_params(request, *args, **kargs)
        return self.in_skeleton(request, params, *args, **kargs)
    
    on_post_call = on_get_call
    
    def on_ajax_get_call(self, request, *args, **kargs):
        defaults = self.template_params(request, *args, **kargs)
        html = render_to_string(self.TEMPLATE, defaults, context_instance=RequestContext(request))
        return json_to_response({'status': 200, 'html': html})
    
    on_ajax_post_call = on_ajax_get_call

class TabPageView(SmartPageView):
    '''
    A page that can be loaded as an ajah tab or as a stand alone page inside a skeleton
    Skeleton template receives 'starting_tab_id' with the current classname
    and starting_tab_content which is the template name (self.TEMPLATE)
    '''
    
    def in_skeleton(self, request, params, *args, **kargs):
        ''' return self.TEMPLATE inside skeleton, passing params '''
        params['starting_tab_id'] = getattr(self, 'CLASS_FOR_TAB', self.__class__).__name__
        params['starting_tab_content'] = request_to_string(request, self.TEMPLATE, self.template_params(request))
        skeleton_params = self.skeleton_params(request, *args, **kargs)
        skeleton_params.update(params)
        return request_response(request, self.SKELETON, skeleton_params)

def request_response(request, template, params=None):
    params = params or {}
    return render_to_response(template, params, context_instance=RequestContext(request))

def request_to_string(request, template, params=None):
    params = params or {}
    return render_to_string(template, params, context_instance=RequestContext(request))

def force_relative_url(url):
    ''' Make sure url is relative '''
    return urlunparse( ('','') + urlparse(url)[2:])

class RelativeHttpResponseRedirect(HttpResponseRedirect):
    '''a redirect always pointing to an url within the site'''
    def __init__(self, url):
        super(RelativeHttpResponseRedirect, self).__init__(force_relative_url(url))

def get_own_or_error(cls, id, profile):
    # Gets an existing model instance checking for ownership
    # Returns a tuple (instance, response_object) with the instance and the error response (on failure)
    if isinstance(id, int):
        try:
            instance = cls.objects.get(id=id)
        except cls.DoesNotExist:
            return None, HttpResponseNotFound("The required resource does not exist")
        if instance.owner != profile:
            return None, HttpResponseForbidden("You are triying to edit an image you don't own")
    else:
        instance = None
    return instance, None

from django.template import Variable
def get_fields(obj, *attribute_names, **renamed_names):
    """
    Returns a dictionary with the given attributes of a certain object.
    Attributes can be written in django Template notation (e.g. "attr.attr2")
    to allow nested lookups.
    Pass keyword arguments to change the name of the field in the result
    e.g. get_fields(obj, get_some_field="some_field")
    _keep_struct=False: Translates dots to subdictionaries. For example:
               'user.profile.name' -> result['user']['profile']['name']
    
    """
    def make_var(dict, namelist, value):
        name = namelist.pop(0)
        dict[name] = namelist and make_var({}, namelist, value) \
                              or value
        return dict

    result = {}
    _keep_struct = False
    if renamed_names.has_key('_keep_struct'):
        del renamed_names['_keep_struct']
        _keep_struct = True

    for attr_name in attribute_names:
        value = Variable(attr_name).resolve(obj)
        if _keep_struct:
            make_var(result, attr_name.split('.'), value)
        else:
            result[attr_name] = value

    for (attr_name, attr_new_name) in renamed_names.items():
        value = Variable(attr_name).resolve(obj)
        if _keep_struct:
            make_var(result, attr_new_name.split('.'), value)
        else:
            result[attr_new_name] = value

    return result

def context_processor_settings(request):
    return {'settings':settings, #deprecated
            'SETTINGS': settings,
            'REQUEST': request,}
