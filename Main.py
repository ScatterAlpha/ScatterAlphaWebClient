import os
import re
import random
import hashlib
import hmac
import logging
import datetime
import json
from string import letters

import webapp2
import jinja2

from google.appengine.ext import db


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

secret = 'fart'

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

class MainPage(BlogHandler):
  def get(self):
      self.write('Hello, Udacity!')
      
##### user stuff
def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)

def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)

def users_key(group = 'default'):
    return db.Key.from_path('users', group)

class User(db.Model):
    global current_user
    username = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    name = db.StringProperty(required = True)
    permission = db.StringProperty(required = True)

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())

    @classmethod
    def by_username(cls, username):
        u = User.all().filter('username =', username).get()
        return u

    @classmethod
    def register(cls, username, pw, name, perm):
        pw_hash = make_pw_hash(username, pw)
        return User(parent = users_key(),
                    username = username,
                    password = pw_hash,
                    name = name,
                    permission = perm)

    @classmethod
    def login(cls, username, pw):
        u = cls.by_username(username)
        if u and valid_pw(username, pw, u.password):
            #current_user = str(u.key(cls).id())
            return u
    
    @classmethod
    def setPermission(cls, username, permission):
        u = User.all().filter('username =', username).get()
        u.permission = permission
        u.put()
        
    @classmethod
    def getPermission(cls, username):
        u = User.all().filter('username =', username).get()
        return u.permission
        
def rsvp_key(group = 'default'):
    return db.Key.from_path('rsvp', group)

class Rsvp(db.Model):
    user_id = db.IntegerProperty(required = True)
    event_id = db.IntegerProperty(required = True)
    
    @classmethod
    def search_by_ID(cls, uid):
        return Rsvp.get_by_id(uid, parent = community_key())
        
    @classmethod
    def by_User(cls, user_id):
        c = Rsvp.all().filter("user_id = ", user_id).get()
        return c
    
    @classmethod
    def count_by_Event(cls, event_id):
        c = Rsvp.all().filter("event_id = ", event_id).count(10000)
        return c

    @classmethod
    def list_by_Event(cls, event_id):
        c = Rsvp.all().filter("event_id = ", event_id).fetch(10000)
        return c
        
    @classmethod
    def by_User_Event(cls, user_id, event_id):
        c = Rsvp.all().filter("user_id = ", user_id).filter("event_id = ", event_id).get()
        if c:
            return True
        else:
            return False
    
    @classmethod
    def rsvp_entry(cls, user_id, event_id):
        return Rsvp(parent = rsvp_key(),
                    user_id = user_id,
                    event_id = event_id)
        
        
def community_key(group = 'default'):
    return db.Key.from_path('community', group)

class Community(db.Model):
    community_name = db.StringProperty(required = True)
    super_admin_id = db.IntegerProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    
    @classmethod
    def all_data(cls):
        return Community.all()
    
    @classmethod
    def search_by_ID(cls, uid):
        return Community.get_by_id(uid, parent = community_key())
        
    @classmethod
    def by_Name(cls, community_nm):
        c = Community.all().filter("community_name = ", community_nm).get()
        if c:
            return c.key().id()
        else:
            return 0
        
    @classmethod
    def updateDescription(cls, name, content):
        c = Community.all().filter("community_name = ", name).get()
        c.content = content
        c.put()
    
    @classmethod
    def comm_entry(cls, name, content, super_adm):
        return Community(parent = community_key(),
                         community_name = name,
                         content = content,
                         super_admin_id = super_adm)
        
def events_key(group = 'default'):
    return db.Key.from_path('events', group)
        
class Event(db.Model):
    event_message = db.StringProperty(required = True)
    message_type = db.StringProperty(required = True)
    venue = db.StringProperty(required = True)
    room = db.StringProperty(required = True)
    date = db.DateTimeProperty(required = True)
    community_id = db.IntegerProperty(required = True)
    category = db.StringProperty(required = True)
    admin_id = db.IntegerProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    
    @classmethod
    def by_id(cls, uid):
        return Event.get_by_id(uid, parent = events_key())

    @classmethod
    def by_event_message(cls, event_message):
        u = Event.all().filter('event_message =', event_message).get()
        return u
    
    @classmethod
    def by_venue(cls, venue):
        u = Event.all().filter('venue =', venue).get()
        return u
    
    @classmethod
    def by_Community(cls, community_id):
        u = Event.all().filter('community_id =', community_id).fetch(1000)
        return u
    
    @classmethod
    def convertToDate(cls, dateInput):
        dtarr = dateInput.split("T")
        dt = dtarr[0]
        tm = dtarr[1]
    
    @classmethod
    def event_entry(cls, evnt_msg, msg_type, venue, room, date, comm_id, category, admin_id):
        return Event(parent = events_key(),
                         event_message = evnt_msg,
                         message_type = msg_type,
                         venue = venue,
                         room = room,
                         date = date,
                         community_id = comm_id,
                         category = category,
                         admin_id = admin_id)



USER_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

NAME_RE  = re.compile(r"^[ a-zA-Z]{3,20}$")
def valid_name(name):
    return not name or NAME_RE.match(name)

class CreateCommunity(BlogHandler):
    def get(self):
        if self.user:
            self.render("community.html")
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/login')
        community_name = self.request.get('community_name')
        super_admin_id = self.user.key().id()
        content = self.request.get('content')
        
        if(Community.all_data().count(100) != 0):
            if not (Community.by_Name(community_name) != 0):
                if community_name and content:
                    p = Community.comm_entry(community_name, content, super_admin_id)
                    p.put()
                    self.redirect('/community')
                else:
                    error = "Community Name and Description, please!"
                    self.render("community.html",  community_name=community_name, content=content, error=error)
            else:
                error = "Community already exists!!"
                self.render("community.html",  community_name=community_name, content=content, error=error)
        else:
            if community_name and content:
                p = Community.comm_entry(community_name, content, super_admin_id)
                p.put()
                self.redirect('/community')
            else:
                error = "Community Name and Description, please!"
                self.render("community.html",  community_name=community_name, content=content, error=error)
            
class UpdateCommunity(BlogHandler):
    def get(self):
        if self.user:
            cid = int(self.request.get('q'))
            comm_name = Community.search_by_ID(cid)
            logging.info(comm_name.community_name)
            self.render("updateCommunity.html", community_name = comm_name.community_name, description = comm_name.content)
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/login')
        else:
            name = self.request.get("community_name")
            content = self.request.get("description")
            c = Community.updateDescription(name, content)
            self.redirect("/listCommunity")

class ListCommunity(BlogHandler):
    def get(self):
        if self.user:
            communities = Community.all_data()
            self.render("listCommunity.html", communities = communities)
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/login')
            
class UserListCommunity(BlogHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
            'Result': "Invalid Request",
            'Error':""
        } 
        self.response.out.write(json.dumps(obj))

    def post(self):
        communities = Community.all_data()
        logging.info("communities")
        self.response.headers['Content-Type'] = 'application/json'   
        obj = []
        for c in communities:
            logging.info("content "+c.content)
            obj.append({
                    'id':str(c.key().id()),
                    'community_name': str(c.community_name),
                    'admin_id': str(c.super_admin_id),
                    'content': str(c.content)
                })
        self.response.out.write(json.dumps(obj))
#     else:
#             self.response.headers['Content-Type'] = 'application/json'   
#             obj = {'Error':'Invalid user'} 
#             self.response.out.write(json.dumps(obj))
                    

class Signup(BlogHandler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.name = self.request.get('name')
        self.permission = self.request.get('permission')

        params = dict(username = self.username,
                      name = self.name)
        
        u = User.by_username(self.username)
        if u:
            params['error_username'] = 'That user already exists.';
            have_error = True;

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_name(self.name):
            params['error_name'] = "That's not a valid name."
            have_error = True
            
        if have_error:
            self.render('signup-form.html', **params)
        else:
            u = User.register(self.username, self.password, self.name, self.permission)
            u.put()
            self.redirect('/listevent');
            
class UserSignup(BlogHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
              'Result': "False",
              'Error':"Invalid Request"
        } 
        self.response.out.write(json.dumps(obj))

    def post(self):
        have_error = False
        dictlist = []
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.name = self.request.get('name')
        self.permission = self.request.get('permission')

        params = dict(username = self.username,
                      name = self.name)
        
        u = User.by_username(self.username)
        if u:
            params['error_username'] = 'That user already exists.';
            have_error = True;

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_name(self.name):
            params['error_name'] = "That's not a valid name."
            have_error = True
            
        if have_error:
            for key, value in params.iteritems():
                temp = value
                dictlist.append(temp)
            self.response.headers['Content-Type'] = 'application/json'   
            obj = {
                'Result': "False",
                'Error':dictlist
            } 
            self.response.out.write(json.dumps(obj))
        else:
            u = User.register(self.username, self.password, self.name, self.permission)
            u.put()
            self.response.headers['Content-Type'] = 'application/json'   
            obj = {
                'Result': "True",
                'Error':""
              } 
            self.response.out.write(json.dumps(obj))
            
            
class UpdatePassword(BlogHandler):
    def get(self):
        if self.user:
            self.render("updatePassword.html")
        else:
            self.redirect("/login")
            
    def post(self):
        params = dict(username = self.username,
                      name = self.name)
        if not self.user:
            self.redirect("/login")
        else:    
            old_password = self.request.get("old_password")
            new_password =self.request.get("new_password")
            cfm_password = self.request.get("cfm_password")
            
        
        if old_password != self.user.password:
            params['error_password'] = "That was not the old password"
            
        if not valid_password(self.new_password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif self.new_password != self.cfm_password:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True
        else:    
            u = User.register(self.username, new_password, self.name, self.permission)
            u.put()


class Login(BlogHandler):
    def get(self):
        self.render('login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/listevent')
        else:
            msg = 'Invalid login'
            self.render('login-form.html', error = msg)
            
class UserLogin(BlogHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
            'Result': "False",
            'Error':""
          } 
        self.response.out.write(json.dumps(obj))

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        u = User.login(username, password)
        if u:
            self.login(u)
            self.response.headers['Content-Type'] = 'application/json'   
            obj = {
                'Result': "True",
                'Error':""
              } 
            self.response.out.write(json.dumps(obj))
        else:
            msg = 'Invalid login'
            self.response.headers['Content-Type'] = 'application/json'   
            obj = {
                'Result': "False",
                'Error': msg
              } 
            self.response.out.write(json.dumps(obj))

class Logout(BlogHandler):
    def get(self):
        self.logout()
        self.redirect('/login')
        
class UserLogout(BlogHandler):
    def get(self):
        self.logout()

class Welcome(BlogHandler):
    def get(self):
        username = self.request.get('username')
        if valid_username(username):
            self.render('welcome.html', username = username)
        else:
            self.redirect('/unit2/signup')
                    
class AddEvent(BlogHandler):
    def get(self):
        if self.user:
            self.render("success.html")
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/login')
        
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
            p = Event.event_entry(event_msg,msg_type,venue,room,date,community_id,category,admin_id)
            p.put()
            self.redirect('/listevent')
        else:
            error = "Please fill all the fields!!"
            self.render("success.html",  event_message = event_msg, message_type = msg_type, venue = venue, room = room, date = date, community_id = community_id, category = category, admin_id = admin_id, error=error)

class DeleteEvent(BlogHandler):
    def get(self):
        if self.user:
            cid = int(self.request.get('q'))
            event = Event.by_id(cid)
            db.delete(event)
            self.redirect("/listevent")
        else:   
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/login')


class ListEvents(BlogHandler):
    def get(self):
        if self.user:
            logging.info(self.user.username)
            events = Event.all()
            self.render("listevents.html", events = events)
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/login')
            
class UserListEvents(BlogHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
                'Result': "Invalid Request",
                'Error':""
              } 
        self.response.out.write(json.dumps(obj))

    def post(self):
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
        
class updateEvent(BlogHandler):
    def get(self):
        if self.user:
            eid = int(self.request.get('q'))
            event_name = Event.by_id(eid)
            community = Community.search_by_ID(event_name.community_id)
            logging.info(event_name.date.strftime('%Y-%m-%dT%H:%M'))
            logging.info(event_name.community_id)
            comm_obj = Community.search_by_ID(event_name.community_id)
            logging.info(comm_obj)
            logging.info(comm_obj.community_name)
            self.render("updateevent.html", 
                        eid = eid,
                        event_msg = event_name.event_message,
                        msg_type = event_name.message_type, 
                        venue = event_name.venue,
                        date = event_name.date.strftime('%Y-%m-%dT%H:%M'),
                        room=event_name.room,
                        community_name = community.community_name,
                        cat=event_name.category)
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/login')
        else:
            event = Event.by_id(self.request.get('eid'))
            
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
        
            setattr(event, 'event_message', event_msg)
            setattr(event, 'message_type', msg_type)
            setattr(event, 'venue', venue)
            setattr(event, 'room', room)
            setattr(event, 'date', date)
            setattr(event, 'community_id', community_id)
            
            
            if event_msg and msg_type and venue and room and date and community_id and category and admin_id:
                event.put()
                self.redirect('/listevent')
            else:
                error = "Please fill all the fields!!"
                self.render("success.html",  event_message = event_msg, message_type = msg_type, venue = venue, room = room, date = date, community_id = community_id, category = category, admin_id = admin_id, error=error)
            
class ListSubAdmin(BlogHandler):
    def get(self):
        if self.user:
            sadmin = User.all().filter("permission = ", "subadmin")
            self.render("listsubadmin.html", sadmins = sadmin)
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/login')
            
class DeleteSubAdmin(BlogHandler):
    def get(self):
        if self.user:
            cid = int(self.request.get('q'))
            username = User.by_ID(cid)
            logging.info(username)
            db.delete(username)
            self.redirect("/listsubadmin")
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/login')

class About(BlogHandler):
    def get(self):
        if self.user:
            self.render("about.html")
        else:
            self.redirect('/login')
            
    def post(self):
        if not self.user:
            self.redirect('/login')
            
class ListOfEvents(BlogHandler):
    def get(self):
        uid = int(self.request.get('user_id'))
#         comm = Follow.by_User_Id(uid)
        comm = ""
        self.response.headers['Content-Type'] = 'application/json'
        obj = ""
        for c in comm:
            com = Event.by_Community(int(c))
            obj += {
                    'id':com.key().id(),
                    'event_message': com.event_message,
                    'message_type': com.message_type,
                    'venue': com.venue,
                    'room': com.room,
                    'date': com.date,
                    'category': com.category,
                    'admin_id': com.admin_id
                }
        self.response.out.write(json.dumps(obj))          
                        
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {}
        self.response.out.write(json.dumps(obj))
            
class CreateRsvp(BlogHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        uid = int(self.request.get('user_id'))
        eid = int(self.request.get('event_id'))
        if not Rsvp.by_User_Event(uid, eid):
            r = Rsvp.rsvp_entry(uid, eid)
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
                    
class NumberOfAttendees(BlogHandler):
    def get(self):
        eid = int(self.request.get('event_id'))
        res = Rsvp.count_by_Event(eid)
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
            'Number': res
          } 
        self.response.out.write(json.dumps(obj))
                    
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
            'Number': -1 
        }
        self.response.out.write(json.dumps(obj))
        
class ListOfAttendees(BlogHandler):
    def get(self):
        eid = int(self.request.get('event_id'))
        res = Rsvp.list_by_Event(eid)
        lst = []
        for r in res:
            lst.append(User.by_id(r.user_id).name)
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
            'User': lst
          } 
        self.response.out.write(json.dumps(obj))
                    
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
            'User': ""
        }
        self.response.out.write(json.dumps(obj))
            
app = webapp2.WSGIApplication([('/', Login),
                               ('/signup', Signup),
                               ('/usersignup', UserSignup),
                               ('/login', Login),
                               ('/userlogin', UserLogin),
                               ('/userlogout', UserLogout),
                               ('/logout', Logout),
                               ('/addevent', AddEvent),
                               ('/listevent', ListEvents),
                               ('/userlistevent', UserListEvents),
                               ('/deleteevent', DeleteEvent),
                               ('/updateevent', updateEvent),
                               ('/createcommunity', CreateCommunity),
                               ('/community', ListCommunity),
                               ('/userlistcommunity', UserListCommunity),
                               ('/updatePwd', UpdatePassword),
                               ('/updateCommunity', UpdateCommunity),
                               ('/listsubadmin', ListSubAdmin),
                               ('/createRsvp', CreateRsvp),
                               ('/getNumberOfAttendees', NumberOfAttendees),
                               ('/getListOfAttendees', ListOfAttendees),
                               ('/about', About),
                               ],
                              debug=True)
