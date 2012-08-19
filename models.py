from google.appengine.ext import db

class Project(db.Model):
	name = db.StringProperty(required=True)
	link = db.LinkProperty(required=True)
	description = db.TextProperty()
	creator = db.StringProperty()
	image = db.StringProperty()
	active = db.BooleanProperty(required=True)

class Comment(db.Model):
	projectid = db.StringProperty(required=True)
	username = db.StringProperty(required=True)
	text = db.TextProperty(required=True)
	date = db.DateTimeProperty(auto_now_add=True)