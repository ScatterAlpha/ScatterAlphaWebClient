import sys
import re
import logging
import json
from ModelDB.ModelDao import *
from Handler.EventHandler import *
from Handler.EventTypeListHandler import *
from Handler.RsvpHandler import *

import webapp2
import jinja2
import os
import hmac
from google.appengine.ext import db


secret = 'fart'

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
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
            community_id = int(self.request.get('community_id'))
            community_name = Community.search_by_ID(community_id)
            logging.info(community_name.community_name)
            self.render("updateCommunity.html", community_name = community_name.community_name, description = community_name.content)
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/login')
        else:
            community_name = self.request.get("community_name")
            content = self.request.get("description")
            c = Community.updateDescription(community_name, content)
            self.redirect("/community")

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
        self.render("signupform.html")

    def post(self):
        try:
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
                self.render('signupform.html', **params)
            else:
                u = User.register(self.username, self.password, self.name, self.permission)
                u.put()
                self.redirect('/listEvent');
        except:
            e = sys.exc_info()[0]
            self.redirect("/signup", error = e)
            
class UserSignup(BlogHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
              'Result': "False",
              'Error':"Invalid Request"
        } 
        self.response.out.write(json.dumps(obj))

    def post(self):
        try:
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
        except:
            e = sys.exc_info()[0]
            self.redirect("/userSignup", error = e)
            
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
        self.render('loginform.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/listEvent')
        else:
            msg = 'Invalid login'
            self.render('loginform.html', error = msg)
            
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
                    

                        
class About(BlogHandler):
    def get(self):
        if self.user:
            self.render("about.html")
        else:
            self.redirect('/login')
            
    def post(self):
        if not self.user:
            self.redirect('/login')
            
# class ListOfEvents(BlogHandler):
#     def get(self):
#         comm = ""
#         self.response.headers['Content-Type'] = 'application/json'
#         obj = ""
#         for c in comm:
#             com = Event.by_Community(int(c))
#             obj += {
#                     'id':com.key().id(),
#                     'event_message': com.event_message,
#                     'message_type': com.message_type,
#                     'venue': com.venue,
#                     'room': com.room,
#                     'date': com.date,
#                     'category': com.category,
#                     'admin_id': com.admin_id
#                 }
#         self.response.out.write(json.dumps(obj))          
#                         
#     def post(self):
#         self.response.headers['Content-Type'] = 'application/json'   
#         obj = {}
#         self.response.out.write(json.dumps(obj))
            


class CreateFollow(BlogHandler):
    def get(self):
        self.render("listcommunity.html")
        self.response.headers['Content-Type'] = 'application/json'
        cid = int(self.request.get('community_id'))
        logging.info(cid)
        uid = int(self.request.get('user_id'))
        logging.info(uid)
        if not Follow.by_User_Community(uid, cid):
            r = Follow.follow_entry(uid, cid)
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

class DeleteFollow(BlogHandler):
    def get(self):
        if self.user:
            cid = int(self.request.get('community_id'))
            logging.info(cid)
            uid = int(self.request.get('user_id'))
            logging.info(uid)
            r = Follow.search_by_userId_communityId(uid, cid)
            logging.info(r)
            if not r:
                db.delete(r)
                self.redirect("/community")
        else:   
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/login')

class NumberOfAttendees(BlogHandler):
   def get(self):
       eid = int(self.request.get('event_id'))
       res = Rsvp.count_by_event(eid)
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
       res = Rsvp.list_by_event(eid)
       lst = []
       for r in res:
           lst.append(User.by_id(r.user_id).name)
       self.response.headers['Content-Type'] = 'application/json'   
       obj = {
           'UserHandlers': lst
         } 
       self.response.out.write(json.dumps(obj))
                   
   def post(self):
       self.response.headers['Content-Type'] = 'application/json'   
       obj = {
           'UserHandlers': ""
       }
       self.response.out.write(json.dumps(obj))

class NumberOfFollowers(BlogHandler):
    def get(self):
        cid = int(self.request.get('community_id'))
        res = Follow.count_by_Community(cid)
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

class ListOfFollowers(BlogHandler):
    def get(self):
        cid = int(self.request.get('community_id'))
        res = Follow.list_by_Community(cid)
        lst = []
        for r in res:
            lst.append(User.by_id(r.user_id).name)
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
            'UserHandlers': lst
          } 
        self.response.out.write(json.dumps(obj))
                    
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
            'UserHandlers': ""
        }
        self.response.out.write(json.dumps(obj))
        

            
app = webapp2.WSGIApplication([('/', Login),
                               ('/signup', Signup),
                               ('/userSignup', UserSignup),
                               ('/login', Login),
                               ('/userLogin', UserLogin),
                               ('/userLogout', UserLogout),
                               ('/Logout', Logout),
                               ('/addEvent', AddEvent),
                               ('/listEvent', ListEvents),
                               ('/userListEvent', UserListEvents),
                               ('/deleteEvent', DeleteEvent),
                               ('/updateEvent', UpdateEvent),
                               ('/createCommunity', CreateCommunity),
                               ('/community', ListCommunity),
                               ('/userListCommunity', UserListCommunity),
                               ('/updatePwd', UpdatePassword),
                               ('/updateCommunity', UpdateCommunity),
                               ('/addRsvp', AddRsvp),
                               ('/deleteRsvp', DeleteRsvp),
                               ('/createFollow',CreateFollow),
                               ('/deleteFollow',DeleteFollow), 
                               ('/getNumberOfAttendees', NumberOfAttendees),
                               ('/getListOfAttendees', ListOfAttendees),
                               ('/getNumberOfFollowers', NumberOfFollowers),
                               ('/getListOfFollowers', ListOfFollowers),
                               ('/about', About),
                               ('/addEventType', AddEventType),
                               ('/listEventType', ListEventType),
                               ('/deleteEventType', DeleteEventType)
                               ],
                              debug=True)