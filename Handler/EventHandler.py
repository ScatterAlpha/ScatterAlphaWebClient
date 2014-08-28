import datetime
import sys
import logging
import os
import hmac
import jinja2
import webapp2
import json
from ModelDB.ModelDao import Community
from ModelDB.ModelDao import Event
from ModelDB.ModelDao import User
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

class AddEvent(BlogHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
              'Result': "False",
              'Error':"Invalid Request"
        } 
        self.response.out.write(json.dumps(obj))

    def post(self):
        if not self.user:
            self.redirect('/login')
        else:
            try:
                event_msg = self.request.get('event_message')
                msg_type = self.request.get('message_type')
                venue = self.request.get('venue')
                room = self.request.get('room')
                dt = self.request.get('date')
                community_name = self.request.get('community_name')
                category = self.request.get('category')
                admin_id = self.user.key().id()
                date = datetime.datetime.strptime(dt, '%Y-%m-%dT%H:%M')
                community_id = int(Community.by_Name(community_name))
                self.response.headers['Content-Type'] = 'application/json'   
               
                if event_msg and msg_type and venue and room and date and community_name and category and admin_id:
                    p = Event.event_entry(event_msg,msg_type,venue,room,date,community_id,category,admin_id)
                    p.put()
                    obj = {
                    'Result': "True",
                    'Error':""
                        } 
                    self.response.out.write(json.dumps(obj))
                    self.redirect('/listEvent')
                else:
                    
                    obj = {
                    'Result': "True",
                    'Error':"Please fill all the fields!!"
                        } 
                    self.response.out.write(json.dumps(obj))
                    
            except:
                e = sys.exc_info()[0]
                self.redirect("/listEvent", error = e)
                

class DeleteEvent(BlogHandler):
    def get(self):
        try:
            if self.user:
                event_id = int(self.request.get('event_id'))
                event = Event.by_id(event_id)
                db.delete(event)
                obj = {
                    'Result': "True",
                    'Error':""
                        } 
                self.response.out.write(json.dumps(obj))
                self.redirect("/listEvent")
            else:   
                obj = {
                    'Result': "True",
                    'Error':""
                        } 
                self.response.out.write(json.dumps(obj))
                self.redirect("/login")
        except:
            e = sys.exc_info()[0]
            error = e
            self.render("listevents.html", error = error)

    def post(self):
        if not self.user:
            self.redirect('/login')


class ListEvents(BlogHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
              'Result': "False",
              'Error':"Invalid Request"
        } 
        self.response.out.write(json.dumps(obj))

    def post(self):
        self.response.headers['Content-Type'] = 'application/json'   
        obj = []
        events = Event.all()
        for c in events:
            logging.info("content "+c.content)
            obj.append({
                    'id':str(c.key().id()),
                    'community_name': str(c.community_name),
                    'admin_id': str(c.super_admin_id),
                    'content': str(c.content)
                })
        self.response.out.write(json.dumps(obj))
            
        
class UpdateEvent(BlogHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
              'Result': "False",
              'Error':"Invalid Request"
        } 
        self.response.out.write(json.dumps(obj))

    def post(self):
        try:
            if not self.user:
                self.redirect('/login')
            else:
                event_id = self.request.get('event_id')
                logging.info(event_id)
                event =  Event.by_id(int(event_id))
                logging.info(event)
                event_msg = self.request.get('event_message')
                msg_type = self.request.get('message_type')
                venue = self.request.get('venue')
                room = self.request.get('room')
                dt = self.request.get('date')
                community_name = self.request.get('community_name')
                category = self.request.get('category')
                admin_id = self.user.key().id()
                date = datetime.datetime.strptime(dt, '%Y-%m-%dT%H:%M')
                community_id = int(Community.by_Name(community_name))            
                
                if event_msg and msg_type and venue and room and date and community_id and category and admin_id:
                    setattr(event, 'event_message', event_msg)
                    setattr(event, 'message_type', msg_type)
                    setattr(event, 'venue', venue)
                    setattr(event, 'room', room)
                    setattr(event, 'date', date)
                    setattr(event, 'community_id', community_id)
                    event.put()
                    obj = {
                    'Result': "True",
                    'Error':""
                    } 
                    self.response.out.write(json.dumps(obj))
                    self.redirect('/listEvent')
                else:
                    error = "Please fill all the fields!!"
                    
        except Exception:
            logging.info("There was an error")