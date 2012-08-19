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
from google.appengine.ext import db
from google.appengine.api.datastore_errors import BadValueError

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
								autoescape=True)

class Project(db.Model):
	name = db.StringProperty(required=True)
	link = db.LinkProperty(required=True)
	description = db.TextProperty()
	creator = db.StringProperty()
	image = db.StringProperty()
	active = db.BooleanProperty(required=True)

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

class MainHandler(Handler):
    def get(self):
    	projects = db.GqlQuery("SELECT * from Project WHERE active = True")
        self.render("home.html", projects=projects)

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
			project = Project(name=name, link=link, description=description, 
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
								('/about', About)],
                              debug=False)
