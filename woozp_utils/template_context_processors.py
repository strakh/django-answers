from django.conf import settings

def common_template_variables(request):
    return {'SETTINGS': settings, 'REQUEST': request}

def message_from_session(request):
    s = request.session
    msg_kinds = ['message', 'ok_message', 'error_message']
    messages = {}
    for m_kind in msg_kinds:
        if m_kind in s:
            messages[m_kind] = s.pop(m_kind)
    return messages
