from ModelDB.ModelDao import *
from Handler.EventHandler import *
from Handler.EventTypeListHandler import *
from Handler.RsvpHandler import *
from Handler.CommunityHandler import *
from Handler.UserHandler import *
from Handler.FollowHandler import *

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
        

USER_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

NAME_RE  = re.compile(r"^[ a-zA-Z]{3,20}$")
def valid_name(name):
    return not name or NAME_RE.match(name)
                        
app = webapp2.WSGIApplication([('/', Login),
                                 ('/signup', Signup),
                                 ('/login', Login),
                                 ('/logout', Logout),
                                 ('/updatePassword', UpdatePassword),
                                 ('/about', About),
                                 ('/addEvent', AddEvent),
                                 ('/getEvent', GetEventById),
                                 ('/listEvents', ListEvents),
                                 ('/deleteEvent', DeleteEvent),
                                 ('/updateEvent', UpdateEvent),                                                              
                                 ('/addCommunity', AddCommunity),
                                 ('/listCommunity', ListCommunity),
                                 ('/updateCommunity', UpdateCommunity),
                                 ('/deleteCommunity', DeleteCommunity),                               
                                 ('/addRsvp', AddRsvp),
                                 ('/deleteRsvp', DeleteRsvp),
                                 ('/getNumberOfAttendees', NumberOfAttendees),
                                 ('/getListOfAttendees', ListOfAttendees),                               
                                 ('/addFollow',AddFollow),
                                 ('/deleteFollow',DeleteFollow),                               
                                 ('/getNumberOfFollowers', NumberOfFollowers),
                                 ('/getListOfFollowers', ListOfFollowers),                               
                                 ('/addEventType', AddEventType),
                                 ('/listEventType', ListEventType),
                                 ('/deleteEventType', DeleteEventType)
                               ],
                              debug=True)