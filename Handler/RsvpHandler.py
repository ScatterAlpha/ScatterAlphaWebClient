import os
import hmac
import jinja2
import webapp2
import json
from ModelDB.ModelDao import User
from ModelDB.ModelDao import Rsvp
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

class AddRsvp(BlogHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        user_id = int(self.request.get('user_id'))
        event_id = int(self.request.get('event_id'))
        if not Rsvp.by_user_event(user_id, event_id):
            r = Rsvp.rsvp_entry(user_id, event_id)
            r.put()              
            obj = {
                'Result': "True"
              }
        else:
            obj = {
                'Result': "False"
              }             
        self.response.out.write(json.dumps(obj))
        
            
    def post(self):
        self.redirect('/login')

class DeleteRsvp(BlogHandler):
    def get(self):
        if self.user:
            user_id = int(self.request.get('user_id'))
            event_id = int(self.request.get('event_id'))
            rsvp_entry = Rsvp.by_user_event(user_id, event_id)
            db.delete(rsvp_entry)
            self.redirect("/listEvent")
        else:   
            self.redirect("/listEvent")

    def post(self):
        if not self.user:
            self.redirect('/login')