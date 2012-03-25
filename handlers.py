#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.web
import tornado.escape

class BaseHandler(tornado.web.RequestHandler):
	def get_current_user(self):
		user = self.get_secure_cookie("current_user")
		if not user: return None
		return tornado.escape.json_decode(user)


class MainHandler(BaseHandler):
	def get(self):
		if self.current_user:
			self.render("index_loggedin.html")
		else:
			self.render("index.html")


class RegisterHandler(BaseHandler):
	def get(self):
		if not self.current_user:
			self.render("register.html")
		else:
			self.redirect("/")

	def post(self):
		# Save user
		pass


class LoginHandler(BaseHandler):
	def get(self):
		if not self.current_user:
			self.render("login.html")
		else:
			self.redirect("/")

	def post(self):
		# Create secure cookie
		pass

class LogoutHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self):
	    self.clear_cookie("current_user")

class ApiHandler(BaseHandler):
	def get(self):
		pass

class UserHandler(BaseHandler):
	def get(self,username):
		self.write(username)

class PictureHandler(BaseHandler):
	def get(self,picture):
		pass