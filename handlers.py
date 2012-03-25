#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.web

class BaseHandler(tornado.web.RequestHandler):
	pass

class MainHandler(BaseHandler):
	def get(self):
		pass


class RegisterHandler(BaseHandler):
	def get(self):
		pass


class LoginHandler(BaseHandler):
	def get(self):
		pass

class LogoutHandler(BaseHandler):
	def get(self):
	    pass

class ApiHandler(BaseHandler):
	def get(self):
		pass

class UserHandler(BaseHandler):
	def get(self,username):
		self.write(username)

class PictureHandler(BaseHandler):
	def get(self,picture):
		pass