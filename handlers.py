#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.web
import tornado.escape
import tornado.auth
import pymongo

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user = self.get_secure_cookie("current_user")
        if not user: return None
        return tornado.escape.json_decode(user)

    @property 
    def db(self):
        if not _db:
            _db = pymongo.Connection().tuxhub
        return _db


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

class TwitterHandler(BaseHandler,tornado.auth.TwitterMixin):
    @tornado.web.asynchronous
    @tornado.web.addslash
    def get(self):
        if self.get_argument("oauth_token", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authorize_redirect(self.settings["site_url"]+"/auth/twitter")

    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Twitter auth failed")
        self.render("twitter_auth.html",user=user)
        #username = user["username"]
        #profile_image_url = user["profile_image_url_https"]
        #description = user["description"]
        #location = user["location"]
        #name = user["name"]
        #url = user["url"]
        #access_token = user["access_token"]
        #oauth_token = self.get_argument("oauth_token",None)