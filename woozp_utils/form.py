import urllib
from itertools import chain
from django import forms
import django.forms.widgets as django_widgets
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.utils.translation import ugettext
from django.utils.safestring import mark_safe
from django.forms.util import ValidationError
from django.utils.encoding import force_unicode
from django.utils.html import escape, conditional_escape
from woozp_utils.text import mixedCaseId, underscore_to_camelcase
from woozp_utils.image import is_valid_image
from django.forms import MultiWidget
from django.forms.forms import pretty_name
from django.utils.dates import MONTHS_3
from datetime import datetime

class IntChoiceField(forms.ChoiceField):
    def clean(self, *args, **kargs):
        cleaned = super(IntChoiceField, self).clean(*args, **kargs)
        if cleaned:
            return int(cleaned)
        return None

class IntMultipleChoiceField(forms.MultipleChoiceField):
    def clean(self, *args, **kargs):
        cleaned = super(IntMultipleChoiceField, self).clean(*args, **kargs)
        if cleaned:
            cleaned = [int(c) for c in cleaned]
        return cleaned
        
class PaginationModelForm(forms.ModelForm):
    DEFAULT_PER_PAGE = 10
    per_page = IntChoiceField(choices=[(x,str(x)) for x in (10,20,30)], initial=DEFAULT_PER_PAGE, label="results per page", required=False)
    page_number = forms.IntegerField(initial=1, required=False)

    def clean_per_page(self):
        return self.cleaned_data['per_page'] or self.DEFAULT_PER_PAGE
    
    def clean_page_number(self):
        return self.cleaned_data['page_number'] or 1

class BaseCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    OPEN_TAG = u'<ul>'
    CLOSE_TAG = u'</ul>'
    
    def _render(self, cb, option_label, rendered_cb):
        return u'<li><label>%s %s</label></li>' % (rendered_cb, conditional_escape(force_unicode(option_label)))
        
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = [self.OPEN_TAG]
        # Normalize to strings.
        str_values = set([force_unicode(v) for v in value])
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
            cb = forms.CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)
            rendered_cb = cb.render(name, option_value)
            output.append(self._render(cb, option_label, rendered_cb))
        output.append(self.CLOSE_TAG)
        return mark_safe(u'\n'.join(output))

class CheckboxSelectMultiple(BaseCheckboxSelectMultiple):
    OPEN_TAG = u'<span class="form-control">'
    CLOSE_TAG = u'</span>'
    
    def _render(self, cb, option_label, rendered_cb):
        return u'<span class="form-control-item"><label for="%s">%s</label>%s</span>' % \
                (cb.attrs['id'], conditional_escape(force_unicode(option_label)), rendered_cb)
    
class DivCheckboxSelectMultiple(BaseCheckboxSelectMultiple):
    OPEN_TAG = u''
    CLOSE_TAG = u''
    
    def _render(self, cb, option_label, rendered_cb):
        return u'<div class="form-item"><label for="%s">%s</label>%s</div>' % \
                (cb.attrs['id'], conditional_escape(force_unicode(option_label)), rendered_cb)

class TemplatedCheckboxes(forms.SelectMultiple):
    has_structure = True
    choice_template = u"""\
<div class="form-item checkboxes" id="%(id)sFormItem">
    <label for="%(id)s" class="main-label">%(label)s</label>
    %(control)s
</div>"""
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = []
        str_values = set([force_unicode(v) for v in value]) # Normalize to strings.
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id=mixedCaseId('%s%s' % (attrs['id'], i)))
            cb = forms.CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)
            rendered_cb = cb.render(name, option_value)
            output.append(
                self.choice_template % {
                         'id': cb.attrs['id'],
                      'label': escape(force_unicode(option_label)),
                      'value': option_value,
                    'control': rendered_cb
                }
            )
        return mark_safe(u'\n'.join(output))

    def id_for_label(self, id_):
        if id_:
            id_ += '_0'
        return id_
    id_for_label = classmethod(id_for_label)
    
class TemplatedRadioFieldRenderer(django_widgets.RadioFieldRenderer):
    """
    An object used by RadioSelect to enable customization of radio widgets.
    """
    field_wrapper = u"""\
    <div class="form-item radios" id="%(id)sFormItem">
        <span class="main-label">%(label)s</span>
        <div class="form-control">
            %(choices)s
        </div>
    </div>"""
    
    choice_template = u"""\
    <div class="form-control-item radios" id="%(id)s">
        <label for="id_%(id)s" class="main-label">%(label)s</label>
        %(control)s
    </div>"""
    
    def render(self):
        """Outputs some structure for this set of radio fields."""
        id = mixedCaseId(self.name)
        label = self.attrs.get('label', self.name)
        choices = u'\n'.join([self.choice_template % {
            'id': '%s_%s' % (id, w.index),
            'label': conditional_escape(force_unicode(w.choice_label)),
            'control': w.tag()
        } for w in self])
        
        return mark_safe(self.field_wrapper % {'id': id, 'label': label, 'choices': choices})

class RelaxedEmailField(forms.EmailField):
    '''Like an emailfield but cleans data to "" if there is no email instead of raising ValidationError '''
    def clean(self, value):
        """
        Validates that the input matches the regular expression. Returns a
        Unicode object.
        """
        value = super(forms.RegexField, self).clean(value)
        if value == u'':
            return value
        if not self.regex.search(value):
            return ''
        return value
    
class ModelChoiceFieldDigitID(forms.models.ModelChoiceField):
    ''' To solve a bug where value of '1004.' or '444e'
        is considered valid, but causes the string to number conversion to fail 
        when the query executes, we check here that value is all digits'''
    def clean(self, value):
        if value and not value.isdigit():
            raise ValidationError(ugettext(u'Select a valid choice. That choice is not one of the available choices.'))
        return super(ModelChoiceFieldDigitID, self).clean(value)

class OptgroupModelChoiceField(forms.ChoiceField):
    """Uses an optgroup for choices and a queryset for cleaning to a model instance"""
    
    def __init__(self, choices, queryset, **kargs):
        self.qs = queryset
        super(OptgroupModelChoiceField, self).__init__(choices, **kargs)  
      
    def clean(self, value):
        """ cleans the selected id to a model in model_list"""
        try:
            return self.qs.filter(pk=int(value))[0]
        except IndexError:
            raise ValidationError(ugettext(u'Select a valid choice. That choice is not one of the available choices.'))

class ModelListMultipleChoiceField(forms.MultipleChoiceField):
    """A MultipleChoiceField whose choices are a list
        of models of the same class instead of a queryset,
        useful with list of models queried directly to the db"""
    
    def __init__(self, choices, label_func=unicode, **kargs):
        self.model_list = choices
        ch = [(m.id, label_func(m)) for m in choices]
        super(ModelListMultipleChoiceField, self).__init__(ch, **kargs)  
      
    def clean(self, value):
        """
        Validates that the input is a list or tuple.
        """
        ret = []
        for v in value:
            for m in self.model_list:
                if m.id == int(v):
                    ret.append(m)
                    break
            
        return ret
    
def flatten_errors(form):
    '''Flatten form errors to a dict of (field-name: text )'''
    non_field_errors = form.errors.pop('__all__', None)
    errors = dict((form[name].auto_id, form[name].errors.as_text()) for name in form.errors)
    errors['non_field_errors'] = non_field_errors
    return errors

def flatten_formset_errors(*args):
    errors = {}
    for formset in args:
        for form in formset.forms:
            if not form.is_valid():
                errors.update(flatten_errors(form))
    return errors

class AllSplittedDateTimeWidget(forms.widgets.MultiWidget):
    """
    A Widget that splits datetime input into two <input type="text"> boxes.
    """
    curr_year = datetime.today().year
    date_choices = [MONTHS_3.items(), #months
               [(v,v) for v in range(1,32)], #days
               [(curr_year+x, curr_year+x) for x in range(2)], #years, this and the next one
               [(x, '%02i' % x) for x in [12] + range(1,12)], #hours
               [(x, '%02i' % x) for x in range(60)],
               [('AM','AM'),('PM','PM')],] #cardinality
    
    def __init__(self, attrs=None):
        widgets = tuple( forms.widgets.Select(attrs=attrs, choices=c) for c in self.date_choices )
        super(AllSplittedDateTimeWidget, self).__init__(widgets, attrs)

    def render(self, *args, **kargs):
        return super(AllSplittedDateTimeWidget, self).render(*args, **kargs)
        
    def format_output(self, widgets):
        return '%s %s %s <label class="inline">At</label> %s %s %s' % tuple(widgets)
    
    def decompress(self, value):
        if not value:
            value = datetime.today() #When no value, show today instead of all '1'.
        mer, hour = divmod(value.hour, 12) 
        return [value.month, value.day, value.year, hour, value.minute, ['AM','PM'][mer] ]
    
class AllSplittedDateTimeField(forms.MultiValueField):
    widget = AllSplittedDateTimeWidget
    default_error_messages = {'invalid_date': "Please enter a valid date",}

    def __init__(self, *args, **kwargs):
        errors = self.default_error_messages.copy()
        if 'error_messages' in kwargs:
            errors.update(kwargs['error_messages'])
        fields = tuple(forms.IntegerField() for i in range(5)) +\
                 (forms.ChoiceField(choices=AllSplittedDateTimeWidget.date_choices[-1]) ,)
        super(AllSplittedDateTimeField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if not data_list and self.required:
            raise ValidationError(self.error_messages['invalid_date'])

        if data_list:
            month, day, year, hour, minute, card = data_list
            if hour == 12: hour = 0
            if card == 'PM': hour += 12
            
            try:
                return datetime(year, month, day, hour, minute)
            except:
                raise ValidationError(self.error_messages['invalid_date'])
        return mark_safe(self.structure % params)
    
class ImageFromURLField(forms.URLField):
    def __init__(self, *a, **kw):
        kw['verify_exists'] = True
        super(ImageFromURLField, self).__init__(*a, **kw)

    def clean(self, value):
        url = super(ImageFromURLField, self).clean(value)
        if url:
            wf = urllib.urlopen(url)
            if wf.headers.getmaintype() != 'image':
                raise forms.ValidationError(u'Enter a URL for a valid image.')
            
            importedFile = TemporaryUploadedFile(url.split('/')[-1], wf.headers.gettype(), int(wf.headers.get('Content-Length')), None)
            importedFile.write(wf.read())
            wf.close()
            importedFile.seek(0)
            if not is_valid_image(importedFile):
                raise forms.ValidationError(u'Enter a URL for a valid image.')
            return importedFile
        return url

import re
class CurrencyInput(forms.TextInput):
    def render(self, name, value, attrs=None):
        if value != '':
            try:
                value = u"%.2f" % value
            except TypeError:
                pass
        return super(CurrencyInput, self).render(name, value, attrs)
    
class CurrencyField(forms.RegexField):
    widget = CurrencyInput
    currencyRe = re.compile(r'^[0-9]{1,5}([,\.][0-9][0-9])?$')
    def __init__(self, *args, **kwargs):
        super(CurrencyField, self).__init__(
            self.currencyRe, None, None, *args, **kwargs)

    def clean(self, value):
        value = super(CurrencyField, self).clean(value)
        if value == u'':
            return None
        return float(value)

