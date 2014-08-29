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
            self.response.headers['Content-Type'] = 'application/json'   
            obj = {
                  'Result': "False",
                  'Error':"Invalid User"
            } 
            self.response.out.write(json.dumps(obj))
        else:
            self.response.headers['Content-Type'] = 'application/json'
            
            event_msg = self.request.get('event_message')
            msg_type = self.request.get('message_type')
            venue = self.request.get('venue')
            room = self.request.get('room')
            dt = self.request.get('date')
            community_name = self.request.get('community_name')
            category = self.request.get('category')
            admin_id = self.user.key().id()
            date = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
            community_id = int(Community.by_Name(community_name))   
               
            if event_msg and msg_type and venue and room and date and community_name and category and admin_id:
                if not Event.by_venue_type(room, venue, msg_type):
                    p = Event.event_entry(event_msg,msg_type,venue,room,date,community_id,category,admin_id)
                    p.put()
                    obj = {
                        'Result': "True",
                        'Error':""
                    }
                else:
                    obj = {
                        'Result': "False",
                        'Error':"Already Exists"
                    } 
            else:
                obj = {
                    'Result': "True",
                    'Error':"Please fill all the fields!!"
                } 
            self.response.out.write(json.dumps(obj))
                    
class DeleteEvent(BlogHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
              'Result': "False",
              'Error':"Invalid Request"
        } 
        self.response.out.write(json.dumps(obj))

    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        if self.user:
            event_id = int(self.request.get('event_id'))
            if Event.by_id(event_id):
                event = Event.by_id(event_id)
                db.delete(event)
                obj = {
                    'Result': "True",
                    'Error':""
                }
            else:
                 obj = {
                    'Result': "False",
                    'Error':"Does not Exists"
                }
        else:   
            obj = {
                'Result': "True",
                'Error':""
            } 
        self.response.out.write(json.dumps(obj))


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
            obj.append({
                    'id':str(c.key().id()),
                    'event_message': str(c.event_message),
                    'message_type': str(c.message_type),
                    'venue':str(c.venue),
                    'room':str(c.room),
                    'category': str(c.category),
                    'community_id':str(c.community_id),
                    'date':str(c.date)
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
        if not self.user:
            self.response.headers['Content-Type'] = 'application/json'   
            obj = {
                      'Result': "False",
                      'Error':"Invalid User"
            } 
            self.response.out.write(json.dumps(obj))
        else:
            self.response.headers['Content-Type'] = 'application/json'
            event_id = self.request.get('event_id')
            event =  Event.by_id(int(event_id))                
            event_msg = self.request.get('event_message')
            msg_type = self.request.get('message_type')
            venue = self.request.get('venue')
            room = self.request.get('room')
            dt = self.request.get('date')
            community_name = self.request.get('community_name')
            category = self.request.get('category')
            admin_id = self.user.key().id()
            date = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
            community_id = int(Community.by_Name(community_name))            
                
            if event and event_msg and msg_type and venue and room and date and community_id and category and admin_id:
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
            else:
                obj = {
                    'Result': "False",
                    'Error':"Please fill all the fields!!"
                }
            self.response.out.write(json.dumps(obj))
                