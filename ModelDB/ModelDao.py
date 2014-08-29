import random
import hashlib

from string import letters
from google.appengine.ext import db

def users_key(group = 'default'):
    return db.Key.from_path('users', group)

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)

def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)

def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))


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
    def by_id(cls, uid):
        return Rsvp.get_by_id(uid, parent = rsvp_key())
        
    @classmethod
    def by_user(cls, user_id):
        c = Rsvp.all().filter("user_id = ", user_id).get()
        return c
    
    @classmethod
    def by_user_event(cls, user_id, event_id):
        c = Rsvp.all().filter("user_id = ", user_id).filter("event_id = ", event_id).get()
        return c
    
    @classmethod
    def count_by_event(cls, event_id):
        c = Rsvp.all().filter("event_id = ", event_id).count(10000)
        return c

    @classmethod
    def list_by_event(cls, event_id):
        c = Rsvp.all().filter("event_id = ", event_id).fetch(10000)
        return c
        
    
    @classmethod
    def rsvp_entry(cls, user_id, event_id):
        return Rsvp(parent = rsvp_key(),
                    user_id = user_id,
                    event_id = event_id)
        
def follow_key(group = 'default'):
    return db.Key.from_path('follow', group)

class Follow(db.Model):
    user_id = db.IntegerProperty(required = True)
    community_id = db.IntegerProperty(required = True)
    
    @classmethod
    def follow_entry(cls, user_id, community_id):
        return Follow(parent = follow_key(),
                    user_id = user_id,
                    community_id = community_id)    
    
    @classmethod
    def by_User_Community(cls, user_id, community_id):
        c = Follow.all().filter("user_id = ", user_id).filter("community_id = ", community_id).get()
        if c:
            return True
        else:
            return False                
                
    @classmethod
    def search_by_userId_communityId(cls,user_id,community_id):            
        return  Follow.all().filter("user_id = ", user_id).filter("community_id = ", community_id).get()
    
    @classmethod
    def count_by_Community(cls, community_id):
        c = Follow.all().filter("community_id = ", community_id).count(10000)
        return c
    
    @classmethod
    def list_by_Community(cls, community_id):
        c = Follow.all().filter("community_id = ", community_id).fetch(10000)
        return c
                
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
    def by_id(cls, uid):
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
        
        
class EventTypeList(db.Model):
    EventTypeName = db.StringProperty(required = True)
    
    @classmethod
    def by_id(cls, uid):
        return EventTypeList.get_by_id(uid, parent = events_key())
    
    @classmethod
    def all_data(cls):
        return EventTypeList.all()
    
    @classmethod
    def by_event_type_name(cls, event_type_name):
        u = EventTypeList.all().filter('EventTypeName =', event_type_name).get()
        return u
    
    @classmethod
    def event_type_list_entry(cls, eventType):
        return EventTypeList(parent = events_key(),
                        EventTypeName = eventType)

        
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
    def by_venue_type(cls, room, venue, message_type):
        u = Event.all().filter('message_type =', message_type).filter('room =', room).filter('venue =', venue).get()
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

