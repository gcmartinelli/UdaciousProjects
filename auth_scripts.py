import hashlib
import re
import random
import string
import hmac
from secrets import *
import models

def make_secure_val(val):
	return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
	val = secure_val.split('|')[0]
	if secure_val == make_secure_val(val):
		return val

def make_pw_hash(username, pw, salt=None):
	if not salt:
		salt = make_salt()
	return "%s|%s" % (salt, hashlib.sha256(username+pw+salt).hexdigest())

def make_salt():
	return ''.join(random.choice(string.letters) for x in range(5))

def valid_pw(username, pw, pw_hash):
	salt = pw_hash.split('|')[0]
	return pw_hash == make_pw_hash(username, pw, salt)


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
restricted_usrlist = {'login',
							'logout',
							'new',
							'edit',
							'circle',
							'dot',
							'sphere',
							'rss',
							'api',
							'debug',
							'admin',
							}

def valid_username(username):
	if username.lower() not in restricted_usrlist:
		return USER_RE.match(username)
	else:
		return None

def valid_password(password):
	return PASS_RE.match(password)

def valid_email(username, email):
	u = models.User.by_email(email)
	if u and u.username != username:
		error = "Looks like this e-mail is already registered..."
		return None, error
	test = EMAIL_RE.match(email)
	if not test:
		error = "Looks like this is not a valid e-mail"
		return None, error
	else:
		return email, None

def valid_verify(verify, password):
	if verify == password:
		return PASS_RE.match(verify)
	return None



