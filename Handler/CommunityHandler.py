import logging
import json
import hmac
import webapp2
import os
import jinja2
from ModelDB.ModelDao import Community
from ModelDB.ModelDao import User


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



class AddCommunity(BlogHandler):
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
                    self.redirect('/listCommunity')
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
                self.redirect('/listCommunity')
            else:
                error = "Community Name and Description, please!"
                self.render("community.html",  community_name=community_name, content=content, error=error)

class DeleteCommunity(BlogHandler):
    def get(self):
        if self.user:
            self.render("community.html")
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/login')
            
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
                    

