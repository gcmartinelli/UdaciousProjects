#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import jinja2
import os
from google.appengine.api.datastore_errors import BadValueError
import logging
from google.appengine.ext import db

from gravatar import make_gravatar
import models
from auth_scripts import *

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
								autoescape=True)

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		user = self.user
		path = self.path
		if not self.user:
			user = None
		self.write(self.render_str(template, user=user, path=path, **kw))

	####cookie stuff
	def set_secure_cookie(self, name, val):
		cookie_val = make_secure_val(val)
		self.response.headers.add_header('Set-Cookie',
			'%s=%s; Path=/' % (name, cookie_val))

	def read_secure_cookie(self, name):
		cookie_val = self.request.cookies.get(name)
		return cookie_val and check_secure_val(cookie_val)

	def logincookie(self, user):
		self.set_secure_cookie('user_id', str(user.key().id()))

	def logout(self):
		self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

	###set
	def initialize(self, *a, **kw):
		webapp2.RequestHandler.initialize(self, *a, **kw)
		uid = self.read_secure_cookie('user_id')
		self.path = self.request.path
		self.user = uid and models.User.by_id(int(uid))

	###Handler 404 error
	def error404(self):
		self.render('404.html')

class MainHandler(Handler):
    def get(self):
    	projects = models.Project.all().filter('active =', True)
        self.render("home.html", projects=projects)

class Signup(Handler):
	def write_form(self, username="", email="", user_error="",
					pass_error="", verify_error="", email_error=""):
		self.render('signup.html', username=username, email=email,
					user_error=user_error, pass_error=pass_error,
					verify_error=verify_error, email_error=email_error)

	def get(self):
		self.write_form()

	def post(self):
		have_error = False
		self.username = self.request.get('username')
		self.password = self.request.get('password')
		self.verify = self.request.get('verify')
		self.email = self.request.get('email')
		if self.email:
			self.avatar = make_gravatar(self.email)
		else:
			self.avatar = make_gravatar('')

		params = dict(username=self.username)

		if not valid_username(self.username):
			params['user_error'] = "That's not a valid username."
			have_error = True

		if not valid_password(self.password):
			params['pass_error'] = "That wasn't a valid password."
			have_error = True

		if not valid_verify(self.verify, self.password):
			params['verify_error'] = "Passwords didn't match."
			have_error = True

		if self.email != '' and not valid_email(self.username, self.email):
			params['email_error'] = "That's not a valid email."
			have_error = True

		if have_error:
			self.write_form(**params)
		else:
			self.done()

	def done(self, *a, **kw):
		raise NotImplementedError

class Register(Signup):
	def done(self):
		u = models.User.by_username(self.username)
		if u:
			msg = 'That username already exists.'
			self.write_form(user_error=msg)
		else:
			u = models.User.register(self.username, self.password, 
				self.email, self.avatar)
			u.put()
			self.logincookie(u)
			self.redirect('/')

class Login(Handler):
	def get(self):
		if self.user:
			self.redirect('/')
		else:
			message = ""
			self.render('login.html', message=message)

	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')

		u = models.User.loginuser(username, password)
		if u:
			self.logincookie(u)
			self.redirect('/')

		else: 
			error = "Ops... are you sure you got the username and password right?"
			self.render('login.html', error=error)

class Logout(Handler):
	def get(self):
		self.logout()
		self.redirect('/')

class CommentHandler(Handler):
	def get(self, projectid):
		project = models.Project.by_id(projectid)
		if not project:
			self.redirect('/')
		else:
			comments = models.Comment.by_id(projectid)
			self.render("comments.html", comments=comments)


	def post(self, projectid):
		text = self.request.get("text")
		username = self.user.username
		avatar = self.user.avatar
		projectid = projectid
		c = models.Comment.register(projectid, username, text, avatar)
		c.put()
		self.redirect('/comments/%s' % (projectid))

class Submit(Handler):
	def get(self, name="", link="", description="", creator=""):
		self.render("submit.html")
	
	def post(self):
		errors = {"name_error": "",
				"link_error": "",
				"description_error": ""}

		name = self.request.get("name")
		user_link = self.request.get("link")
		user_description = self.request.get("description")
		creator = self.request.get("creator")

		link = validateURL(user_link)
		description = validateDescription(user_description)

		if not name:
			errors["name_error"] = "Please submit a project name."
		if not link:
			errors["link_error"] = "This is not a valid URL (please include http://)."
		if not description:
			errors["description_error"] = "We also need a description with less than 100 characters."
		if any(errors.values()):
			self.render("submit.html", name=name, description=user_description, link=user_link,
						name_error=errors["name_error"], link_error=errors["link_error"],
						description_error=errors["description_error"], creator=creator)

		if name and link and description:
			project = models.Project(name=name, link=link, description=description, 
							creator=creator, active=False, image="")
			project.put()
			self.redirect("/thankyou")

class Thankyou(Handler):
	def get(self):
		self.render("thankyou.html")

class About(Handler):
	def get(self):
		self.render("about.html")

def validateURL(url):
	linkProperty = db.LinkProperty()
	try:
		linkProperty.validate(url)
	except BadValueError:
		return None
	return url 

def validateDescription(description):
	if len(description) < 100:
		return description

app = webapp2.WSGIApplication([('/', MainHandler),
								('/submit', Submit),
								('/thankyou', Thankyou),
								('/about', About),
								('/signup/?', Register),
								('/login/?', Login),
								('/logout/?', Logout),
								('/comments/([0-9])/?', CommentHandler),],
                              debug=False)
