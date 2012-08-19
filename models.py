from google.appengine.ext import db

from auth_scripts import *

class Project(db.Model):
	name = db.StringProperty(required=True)
	link = db.LinkProperty(required=True)
	description = db.TextProperty()
	creator = db.StringProperty()
	image = db.StringProperty()
	active = db.BooleanProperty(required=True)
	@classmethod
	def by_id(cls, projectid):
		p = cls.get_by_id(int(projectid))
		return p

class Comment(db.Model):
	projectid = db.StringProperty(required=True)
	username = db.StringProperty(required=True)
	useravatar = db.LinkProperty(required=False)
	text = db.TextProperty(required=True)
	date = db.DateTimeProperty(auto_now_add=True)
	@classmethod
	def register(cls, projectid, username, text, useravatar):
		return cls(projectid=projectid,
					username=username,
					useravatar=useravatar,
					text=text)
	@classmethod
	def by_id(cls, projectid):
		c = cls.all().filter('projectid =', projectid)
		return c

class User(db.Model):
	username = db.StringProperty(required=True)
	pw_hash = db.StringProperty(required=True)
	email = db.StringProperty()
	avatar = db.LinkProperty() 
	date = db.DateTimeProperty(auto_now_add=True)
	@classmethod
	def by_id(cls, uid):
		return cls.get_by_id(uid)
	@classmethod
	def by_username(cls, username):
		u = cls.all().filter('username =', username).get()
		return u
	@classmethod
	def by_email(cls, email):
		u = cls.all().filter('email =', email).get()
		return u
	@classmethod
	def register(cls, username, pw, email=None, avatar=None):
		pw_hash = make_pw_hash(username, pw)
		return cls(username=username,
					pw_hash=pw_hash,
					email=email,
					avatar=avatar)
	@classmethod
	def loginuser(cls, username, pw):
		u = cls.by_username(username)
		if u and valid_pw(username, pw, u.pw_hash):
			return u