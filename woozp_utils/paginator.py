from django.core.paginator import Paginator, InvalidPage
from django import forms
from woozp_utils.form import IntChoiceField
from django.template.loader import render_to_string

class PaginationForm(forms.Form):
    DEFAULT_PER_PAGE = 10
    per_page = IntChoiceField(choices=[(x,str(x)) for x in (10,20,30)], initial=DEFAULT_PER_PAGE, label="results per page", required=False)
    page_number = forms.IntegerField(initial=1, required=False)
    
    def clean_per_page(self):
        return self.cleaned_data['per_page'] or self.DEFAULT_PER_PAGE
    
    def clean_page_number(self):
        return self.cleaned_data['page_number'] or 1
    
def make_paginator(objects, data=None, action=''):
    '''(optionally) Handles the data submitted by a pagination form,
       returns a rendered paginator and the current page '''
    form = PaginationForm(data=data or {})
    form.is_valid()
    paginator = Paginator(objects, form.cleaned_data['per_page'])
    
    try:
        page = paginator.page(form.cleaned_data['page_number'])
    except InvalidPage, e:
        page = paginator.page(paginator.num_pages)
    
    paginator_params = {
        'paginator': paginator,
        'page': page,
        'viewswitcher': False,
        'pagination_form': form,
        'action': action,
    }
    rendered_paginator = render_to_string('widgets/simple_paginator.tpl', paginator_params)

    return page, rendered_paginator
    