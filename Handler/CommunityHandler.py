import logging
import json
import hmac
import webapp2
import os
import jinja2
from ModelDB.ModelDao import Community
from ModelDB.ModelDao import User
from google.appengine.ext import db

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
        logging.info("user id "+str(uid))
        self.user = uid and User.by_id(int(uid))



class AddCommunity(BlogHandler):
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
            community_name = self.request.get('community_name')
            super_admin_id = self.user.key().id()
            content = self.request.get('content')
            self.response.headers['Content-Type'] = 'application/json'
            if community_name and content:
                if not Community.by_Name(community_name):
                    p = Community.comm_entry(community_name, content, super_admin_id)
                    p.put()
                    self.response.headers['Content-Type'] = 'application/json'   
                    obj = {
                        'Result': "True",
                        'Error':""
                    } 
                    self.response.out.write(json.dumps(obj))
                else:
                    obj = {
                        'Result': "False",
                        'Error':"Already Exists"
                    }
                    self.response.out.write(json.dumps(obj))
            else:
                self.response.headers['Content-Type'] = 'application/json'   
                obj = {
                        'Result': "False",
                        'Error':"Community Name and Description, please!"       
                    }
                self.response.out.write(json.dumps(obj))

class DeleteCommunity(BlogHandler):
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
            community_id = int(self.request.get('community_id'))
            if Community.by_id(community_id):
                community = Community.by_id(community_id)
                db.delete(community)
                self.response.headers['Content-Type'] = 'application/json'   
                obj = {
                       'Result': "True",
                        'Error':""
                    } 
                self.response.out.write(json.dumps(obj))
            else:
                 self.response.headers['Content-Type'] = 'application/json'   
                 obj = {
                    'Result': "False",
                    'Error':"Does not Exists"
                 } 
                 self.response.out.write(json.dumps(obj))
       
class UpdateCommunity(BlogHandler):
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
            community_name = self.request.get("community_name")
            content = self.request.get("content")
            Community.updateDescription(community_name, content)
            obj = {
                    'Result': "True",
                    'Error':""
                  } 
            self.response.out.write(json.dumps(obj))
                                    
class ListCommunity(BlogHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
            'Result': "False",
            'Error':"Invalid Request"
        } 
        self.response.out.write(json.dumps(obj))

    def post(self):
        communities = Community.all_data()
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