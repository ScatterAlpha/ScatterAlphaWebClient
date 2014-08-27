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
        if self.user:
            self.render("success.html")
        else:
            self.redirect("/login")

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
                
        
                if event_msg and msg_type and venue and room and date and community_name and category and admin_id:
                    p = Event.event_entry(event_msg,msg_type,venue,room,date,community_id,category,admin_id)
                    p.put()
                    self.redirect('/listEvent')
                else:
                    error = "Please fill all the fields!!"
                    self.render("success.html",  event_message = event_msg, message_type = msg_type, venue = venue, room = room, date = date, community_id = community_id, category = category, admin_id = admin_id, error=error)
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
                self.redirect("/listEvent")
            else:   
                self.redirect("/login")
        except:
            e = sys.exc_info()[0]
            error = e
            self.redirect("/listEvent", error = error)

    def post(self):
        if not self.user:
            self.redirect('/login')


class ListEvents(BlogHandler):
    def get(self):
        if self.user:
            logging.info(self.user.username)
            events = Event.all()
            self.render("listevents.html", events = events, user_id=self.user.key().id())
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/login')
            
class UserListEvents(BlogHandler):
    def get(self):
        try:
            self.response.headers['Content-Type'] = 'application/json'   
            obj = {
                    'Result': "Invalid Request",
                    'Error':""
                  } 
            self.response.out.write(json.dumps(obj))
        except:
            e = sys.exc_info()[0]
            self.response.headers['Content-Type'] = 'application/json'   
            obj = {
                    'Result': "Exception",
                    'Error':e
                  } 
            self.response.out.write(json.dumps(obj))
            

    def post(self):
        try:
            events = Event.all()
            self.response.headers['Content-Type'] = 'application/json'   
            obj = []
            for e in events:
                obj.append({
                        'id':str(e.key().id()),
                        'admin_id': str(e.admin_id),
                        'category': str(e.category),
                        'date': str(e.date),
                        'event_message':str(e.event_message),
                        'venue':str(e.venue)+str(e.room)
                })        
            self.response.out.write(json.dumps(obj))
        except Exception:
            logging.info("There was an error")
        
class UpdateEvent(BlogHandler):
    def get(self):
        try:
            if self.user:
                event_id = int(self.request.get('event_id'))
                logging.info(event_id)
                event_name = Event.by_id(int(event_id))
                community = Community.search_by_ID(event_name.community_id)
                logging.info(event_name.date.strftime('%Y-%m-%dT%H:%M'))
                logging.info(event_name.community_id)
                comm_obj = Community.search_by_ID(event_name.community_id)
                logging.info(comm_obj)
                logging.info(comm_obj.community_name)
                self.render("updateevent.html", 
                            event_id = event_id,
                            event_msg = event_name.event_message,
                            msg_type = event_name.message_type, 
                            venue = event_name.venue,
                            date = event_name.date.strftime('%Y-%m-%dT%H:%M'),
                            room=event_name.room,
                            community_name = community.community_name,
                            cat=event_name.category)
            else:
                self.redirect("/login")
        except Exception:
            logging.info("There was an error")

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
                    self.redirect('/listEvent')
                else:
                    error = "Please fill all the fields!!"
                    self.render("success.html",  event_message = event_msg, message_type = msg_type, venue = venue, room = room, date = date, community_id = community_id, category = category, admin_id = admin_id, error=error)
        except Exception:
            logging.info("There was an error")