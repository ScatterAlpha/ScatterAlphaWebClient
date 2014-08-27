import os
import hmac
import jinja2
import webapp2
from ModelDB.ModelDao import User
from ModelDB.ModelDao import EventTypeList
from google.appengine.ext import db

secret = 'fart'

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader('templates'),
                               autoescape = True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))
        
def render_post(response, post):
    response.out.write('<b>' + post.subject + '</b><br>')
    response.out.write(post.content)
    
class AddEventType(BlogHandler):
    def get(self):
        if self.user:
            self.render("addEventType.html")
        else:
            self.redirect("/login")
            
    def post(self):
        if self.user:
            eventTypeList = self.request.get("eventTypeList")
            event_type_entry = EventTypeList.event_type_list_entry(eventTypeList)
            event_type_entry.put()
            self.redirect("/listEventType")
        else:
            self.render("login")
class ListEventType(BlogHandler):
    def get(self):
        if self.user:
            event_type_list = EventTypeList.all_data()
            self.render("listEventType.html", list = event_type_list)
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/login')
            
class DeleteEventType(BlogHandler):
    def get(self):
        if self.user:
            event_type_id = int(self.request.get('event_type_id'))
            event_type_entry = EventTypeList.by_id(event_type_id)
            db.delete(event_type_entry)
            self.redirect("/listEventType")
        else:   
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/login')