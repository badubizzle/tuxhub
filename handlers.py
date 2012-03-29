#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.web
import tornado.escape
import tornado.auth
import tornado.websocket
import pymongo,gridfs

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        #user = self.get_secure_cookie("current_user")
        #user = '{"username":"doganaydin"}'
        user = None # UNUTMA BURAYI
        if not user: return None
        return tornado.escape.json_decode(user)

    @property 
    def db(self):
        if not hasattr(BaseHandler,"_db"):
            _db = pymongo.Connection().tuxhub
        return _db

    @property
    def fs(self):
        if not hasattr(BaseHandler,"_fs"):
            _fs = gridfs.GridFS(self.db)
        return _fs

class SocketBaseHandler(tornado.websocket.WebSocketHandler):
    @property 
    def db(self):
        if not hasattr(SocketBaseHandler,"_db"):
            _db = pymongo.Connection().tuxhub
        return _db  

# Sadece sayfa yüklenmelerinde ve post işlemlerinde.
# Feed girmek için /update
class MainHandler(BaseHandler):
    def get(self):
        if self.current_user:
            feeds = self.db.feeds.find({})
            f = []
            for i in feeds:
                f.append(i)
            self.render("index_loggedin.html",feeds=f)
        else:
            self.render("index.html")

    def post(self):
        # Burada kontrol lazım.
        # feed json gelmeli {"user":"xx","message":"xyz","twitter":"true"}
        feed = self.get_argument("feed")
        self.db.feeds.save(tornado.escape.json_decode(feed))
        self.write(feed)

class UpdateHandler(SocketBaseHandler):
    LISTENERS = []
    def open(self):
        UpdateHandler.LISTENERS.append(self)
        self.write_message("Bağlandı %s" % str(self))

    def on_message(self,message):
        self.write_message("Dedi %s" % message)

    def on_close(self):
        print "kapandı"


class RegisterHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.render("register.html")
        else:
            self.redirect("/")

    def post(self):
        if self.get_argument("user_name",False): user_name = self.get_argument("user_name")
        else:
            self.write("Username required")
            return

        if self.get_argument("password",False): password = self.get_argument("password")
        else:
            self.write("Password required")
            return

        if self.get_argument("day",False): day = self.get_argument("day")
        else:
            self.write("Birth day required")
            return

        if self.get_argument("month",False): month = self.get_argument("month")
        else:
            self.write("Birth month required")
            return

        if self.get_argument("year",False): year = self.get_argument("year")
        else:
            self.write("Birth year required")
            return

        if not self.request.files["profile"][0]["filename"]:
            self.write("Profile picture required")
            return
        else:
            file_name = self.request.files["profile"][0]["filename"]
            file_body = self.request.files["profile"][0]["body"]

        profile_image = "profile_images/{0}/{1}".format(user_name,file_name)
        user = dict(
            user_name = user_name,
            password = password,
            birth_day = day +"/"+ month +"/"+ year,
            profile = profile_image
        )

        self.fs.put(file_body, filename=profile_image)
        self.db.users.save(user)
        self.redirect("/auth/login")


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