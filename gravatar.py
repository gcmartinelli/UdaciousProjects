import urllib, hashlib

def make_gravatar(email=''):
  default = "http://lorempixel.com/50/50/abstract"
  gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + "?"
  gravatar_url += urllib.urlencode({"d":default})
  return gravatar_url
