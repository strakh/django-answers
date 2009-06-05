from django.conf import settings
from re import sub, compile

def trimText(text, maxlen = settings.DEFAULT_MAX_CHARS):
    if len(text) <= maxlen:
        return text
    else:
        return text[0:maxlen-3] + '...'

def mixedCaseId(text):
    """
    Returns a mixedCase string,suitable to be used as id.
    e.g.:
    
    >>> mixedCaseId("123 initial number")
    '_123InitialNumber'
    >>> mixedCaseId(" a __very__ invalid-id!!!!")
    'a__very__InvalidId'
    
    """
    words = sub(r'\W+', ' ', text).strip().split()
    return sub(r'^(\d)', r'_\1', words[0]) + ''.join(w.capitalize() for w in words[1:])

CAMEL_CASE_REGEX = compile("(_[a-z 0-9]){1}")
def underscore_to_camelcase(txt):
    '''converts an underscore_separated_string to a camelCasedString'''
    return CAMEL_CASE_REGEX.sub(lambda x: x.group()[1].upper(), txt)