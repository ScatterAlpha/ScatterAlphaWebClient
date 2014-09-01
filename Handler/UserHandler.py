import logging
import re
import sys
import json
import jinja2
import os
import hmac
import webapp2
from ModelDB.ModelDao import User

USER_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

NAME_RE  = re.compile(r"^[ a-zA-Z]{3,20}$")
def valid_name(name):
    return not name or NAME_RE.match(name)


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader("templates"),
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
        logging.info("user_id login "+str(cookie_val))
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        logging.info("user id "+str(uid))
        self.user = uid and User.by_id(int(uid))

class Signup(BlogHandler):
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
        self.cfmpassword = self.request.get('cfmpassword')
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
        elif self.password != self.cfmpassword:
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
            self.old_password = self.request.get("old_password")
            self.new_password =self.request.get("new_password")
            self.cfm_password = self.request.get("cfm_password")
            self.username = self.request.get('username')
            
        params = dict()
        self.response.headers['Content-Type'] = 'application/json'
        if self.old_password != self.user.password:
            params['error_password'] = "That was not the old password"
            obj = {
                    'Result': "False",
                    'Error': params
            }
        if not valid_password(self.new_password):
            params['error_password'] = "That wasn't a valid password."
            obj = {
                    'Result': "False",
                    'Error': params
            }
        elif self.new_password != self.cfm_password:
            params['error_verify'] = "Your passwords didn't match."
            obj = {
                    'Result': "False",
                    'Error': params
            }
        else:    
            u = User.by_username(self.username)
            setattr(u, 'password', self.new_password)
            u.put()   
            obj = {
                'Result': "True",
            } 
        self.response.out.write(json.dumps(obj))

class Login(BlogHandler):
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
                'Id': str(u.key().id()),
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
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
            'Result': "False",
            'Error':"Invalid Request"
          } 
        self.response.out.write(json.dumps(obj))    
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
            'Result': "True",
            'Error':""
          }
        self.logout() 
        self.response.out.write(json.dumps(obj))
        


class About(BlogHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
            'Result': "False",
            'Error':""
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
            obj = {
                'Result': "True",
                'Message':"Lorem Ipsum"
            } 
            self.response.out.write(json.dumps(obj))