import re
import sys
import json
import jinja2
import os
import hmac
import webapp2
import logging
from ModelDB.ModelDao import *

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
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))



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