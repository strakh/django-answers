import sys
sys.path.append("../..")

import cookielib, urllib2
from django.utils import simplejson as json
from django.utils.http import urlencode
from django.conf import settings
from django.core.mail import send_mail

class InviterException(Exception):
    def __init__(self, errors):
        self.errors = [ v for k, v in errors.items() ]
        super(InviterException, self).__init__()
    def __str__(self):
        return str(self.errors)

def check_json_errors(data):
    if len(data["errors"]) > 0:
        raise InviterException(data["errors"])

class _Session:
    def __init__(self, user, passwd, service):
        self.user = user
        self.passwd = passwd
        self.service = service
        self.login()

    def login(self):
        self.cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        urlparams = {
            "provider_box":self.service.key,
            "email_box":self.user,
            "password_box":self.passwd,
            "json":"",
            "import":"Import Contacts",
        }
        ret = self._get_json(urlparams)
        self.contacts = ret["contacts"]
        self.session_id = ret["oi_session_id"]

    def _get_json(self, urlparams):
        encoded_params = urlencode(urlparams)
        socket = self.opener.open(settings.OPENINVITER_BASE_URL, encoded_params)
        data = json.loads(socket.read())
        check_json_errors(data)
        return data

    def invite(self, contact_ids, subject, message):
        return self.service.invite(self, contact_ids, subject, message)
    
    def invite_by_mail(self, contact_ids, subject, message):
        send_invite_mail(contact_ids, subject, message)

    def invite_by_social(self, contact_ids, subject, message):
        urlparams = {
            "subject_box":subject,
            "message_box":message,
            "provider_box":self.service.key,

            "email_box":self.user,
            "oi_session_id":self.session_id,

            "send":"Send Invites",
            "step":"send_invites",
            "json":"",
        }
        for n, userid in enumerate(contact_ids):
            urlparams["check_%d"%n] = str(n)
            urlparams["email_%d"%n] = userid
            urlparams["name_%d"%n] = self.contacts[userid]

        return self._get_json(urlparams)

class BaseService:
    def __init__(self, key, name):
        self.key = key
        self.name = name
        
    def login(self, user, passwd):
        return _Session(user, passwd, self)

class ServiceMail(BaseService):
    type = "email"
    section = "email"
    section_name = "Email Adresses"
    def invite(self, session, contact_ids, subject, message):
        return session.invite_by_mail(contact_ids, subject, message)

def send_invite_mail(contact_ids, subject, message):
    send_mail(subject, message, "invitations@tribester.com", contact_ids, fail_silently=False)

class ServiceSocial(BaseService):
    type = "social"
    @property
    def section(self):
        return self.key

    @property
    def section_name(self):
        return "Contacts in " + self.name

    def invite(self, session, contact_ids, subject, message):
        return session.invite_by_social(contact_ids, subject, message)

def _find_services():
    socket = urllib2.urlopen(settings.OPENINVITER_BASE_URL+"?json")
    data = json.loads(socket.read())
    check_json_errors(data)
    services = data["services"]
    allservices = {}
    allservices.update(services["email"])
    allservices.update(services["social"])
    service_classes = {
        "email": ServiceMail,
        "social": ServiceSocial,
    }

    ret = {}
    for key, value in allservices.iteritems():
        ret[key] = service_classes[value["type"]](key, value["name"])
    return ret

_services = None
def get_services():
    global _services
    if _services is None:
        _services = _find_services()
    return _services

if __name__ == "__main__":
    from pprint import pprint
    accounts = {
        "gmail": ("woobiztest@gmail.com", "jojojolalala"),
        "yahoo": ("woobiztest@yahoo.com", "jojojolalala"),
        "hotmail": ("woobiztest@hotmail.com", "jojojolalala"),
        "facebook": ("facebu@vortech.com.ar", "joe9090"),
    }
    for s,(u,pw) in accounts.items():
        print "logging into", s, "...",
        session = get_services()[s].login(u, pw)
        print "done!"
        print "finding contacts...",
        contacts = session.contacts
        print "done!"
        pprint(contacts)

    session = get_services()["gmail"].login("woobiztest@gmail.com", "jojojolalala")
    invitees = [
        "alecura@gmail.com", #:"Alejandro J. Cura",
        #"eromirou@gmail.com", #:"Cocho eRomirou",
        #"gnubis@gmail.com", #:"Futuro padre de Batman",
    ]

    """
    session = get_services()["facebook"].login("facebu@vortech.com.ar", "joe9090")
    invitees = [
        "611107328", #:"Tom\\\\u00e1s Rojas",
        "701591775", #:"Cristian Gabriel Bruno",
        "1068548412", #:"Ziliani Pablo",
    ]
    """

    pprint(session.contacts)
    subject = "los invito a mi fiestita!"
    message = "los invito a mi fiestita... (usando openinviter 1.6.5 y woozp_utils/inviter.py)"
    ret = session.invite( invitees, subject, message )
    print ret

    session = get_services()["gmail"].login("dame un error", "por favor")
