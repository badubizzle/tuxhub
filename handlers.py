#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.web
import tornado.escape
import tornado.auth
import tornado.websocket
import pymongo,gridfs
from helpers import *

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user = self.get_secure_cookie("current_user") or False
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

class Utility(object):
    def get_followed_users(self,username):
        #    {"following": ["x_user", "y_user"], "count": 2}
        #    {"count": 0}
        f = self.db.follow.find_one({"follower":username},{"_id":0,"follower":0}) or {}
        f["count"] = len(f.get("following",""))
        return f

    def get_followers(self,username):
        #    {"count": 2, "followers": ["x_user", "y_user"]}
        #    {"count": 0, "followers": []}

        _f = self.db.follow.find({"following":username},{"_id":0,"following":0})
        f = {"followers":[],"count":0}
        for i in _f:
            f["followers"].append(i["follower"])
        f["count"] = len(f["followers"])
        if f["count"] <= 0:
            f.pop("followers")
        return f

class SocketBaseHandler(tornado.websocket.WebSocketHandler):
    def get_current_user(self):
        user = self.get_secure_cookie("current_user") or False
        if not user: return None
        return tornado.escape.json_decode(user)
    @property 
    def db(self):
        if not hasattr(SocketBaseHandler,"_db"):
            _db = pymongo.Connection().tuxhub
        return _db  

# Sadece sayfa yüklenmelerinde ve post işlemlerinde.
# Feed girmek için /update
class MainHandler(BaseHandler,Utility):
    def get(self):
        if self.current_user:
            # bu listeyi cachele. Her mesajda sorgu yaparsa iki güne alırız makineyi elimize
            following = self.get_followed_users(self.current_user["user_name"]).get("following",[])
            following.append(self.current_user["user_name"]) # add myself to list because i must see my feeds
            start = int(self.get_argument("start",0))
            if start > 0:
            	feeds = self.db.feeds.find({"user":{"$in":following}}).sort("_id",-1).skip(int(start)).limit(20)
            else:
            	feeds = self.db.feeds.find({"user":{"$in":following}}).sort("_id",-1).limit(20)
            f = []
            for i in feeds:
                u = self.db.users.find_one({"user_name":i["user"]})
                i["profile"] = u["profile"]
                f.append(i)
            self.render("index_loggedin.html",feeds=f)
        else:
            self.render("index.html")

    def post(self):
        # Burada kontrol lazım.
        # feed json gelmeli {"user":"xx","message":"xyz","twitter":"true"}
        feed = {
            "user":self.current_user["user_name"],
            "text":self.get_argument("feed"),
            "time":self.get_argument("time")
        }
        self.write(str(self.db.feeds.save(feed)))

class UpdateHandler(SocketBaseHandler,Utility):
    LISTENERS = []
    TEMPLATE = """
    <div id="%s" class="well">
        <div class="user"><img width="50" height="50" src="/p/%s"><b>%s: </b> (<span class="timeago">%s</span>)</div>
        <div class="feed_content">&nbsp;&nbsp;%s</div>
    </div>
    """
    def open(self):
        UpdateHandler.LISTENERS.append(self)
        print "Bağlandı %s" % str(self)

    @tornado.web.authenticated
    def on_message(self,message):
        # bu listeyi cachele. Her mesajda sorgu yaparsa iki güne alırız makineyi elimize
        following = self.get_followed_users(self.current_user["user_name"]).get("following",[])
        following.append(self.current_user["user_name"])

        for i in UpdateHandler.LISTENERS:
            m = tornado.escape.json_decode(message)
            if m["user_name"] in following:
                u = self.db.users.find_one({"user_name":m["user_name"]})
                t = UpdateHandler.TEMPLATE % (m["id"],u["profile"], m["user_name"], m["time"], tornado.escape.xhtml_escape(m["feed"]))
                i.write_message("%s" % t)
            else:
                print "err"

    def on_close(self):
        UpdateHandler.LISTENERS.remove(self)
        print "kapandı"


class RegisterHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.render("register.html")
        else:
            self.redirect("/")

    def post(self):
        if self.get_argument("name",False): name = self.get_argument("name")
        else:
            self.write("Name required")
            return

        if self.get_argument("user_name",False): user_name = self.get_argument("user_name")
        else:
            self.write("Username required")
            return

        if self.get_argument("password",False): password = self.get_argument("password")
        else:
            self.write("Password required")
            return

        if self.get_argument("confirm_password",False):
            confirm_password = self.get_argument("confirm_password")
            if confirm_password != password:
                self.write("Passwords not match")
                return 
        else:
            self.write("Confirm Password required")
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

        try:
        	file_name = self.request.files["profile"][0]["filename"]
        	file_body = self.request.files["profile"][0]["body"]
        except KeyError:
            self.write("Profile picture required")
            return

        file_type = type_of(file_body)
        if not file_type or type_of(file_body) not in ["png","jpeg"]:
            self.write("Profile image must be png or jpeg")
            return

        profile_image = "profile_images/{0}/{1}".format(user_name,file_name)
        user = dict(
            name= name,
            user_name = user_name,
            password = password,
            birth_day = day +"/"+ month +"/"+ year,
            profile = profile_image
        )

        self.fs.put(file_body, filename=profile_image,content_type=file_type)
        self.db.users.save(user)
        self.redirect("/auth/login")


class LoginHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.render("login.html")
        else:
            self.redirect("/")

    def post(self):
        user_name = self.get_argument("user_name",False)
        password = self.get_argument("password",False)
        if user_name and password:
            user = self.db.users.find_one({"user_name": user_name, "password": password},{"_id":0})
            if user:
                self.set_secure_cookie("current_user",tornado.escape.json_encode(user))
                self.redirect("/")
            else:
                self.write("User is not exist. <a href='/auth/register'>Register?</a>")
        else:
            self.write("You must fill both username and password")


class LogoutHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie("current_user")
        self.redirect("/")


class UserHandler(BaseHandler):
    def get(self,username):
        pass

class PictureHandler(BaseHandler):
    def get(self,picture):
        profile = self.fs.get_last_version(picture)
        if profile:
            header = "image/%s" % profile.content_type
            print profile.content_type
            self.set_header("Content-Type",header)
            self.write(profile.read())


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
        self.db.save(user)
        self.render("twitter_auth.html",user=user)
        #username = user["username"]
        #profile_image_url = user["profile_image_url_https"]
        #description = user["description"]
        #location = user["location"]
        #name = user["name"]
        #url = user["url"]
        #access_token = user["access_token"]
        #oauth_token = self.get_argument("oauth_token",None)


class ProfileHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        user = dict(
            info = self.db.users.find({"user_name":self.current_user["user_name"]},{"_id":0}),
            feeds = self.db.feeds.find({"user_name":self.current_user["user_name"]})
        )
        self.render("profile.html", user = user)

class FollowHandler(BaseHandler,Utility):
    def get(self):
        username = self.get_argument("username",False)
        _type = self.get_argument("type",False)
        if username and _type:
            if _type == "followers":
                f = self.get_followers(username)

            if _type == "following":
                f = self.get_followed_users(username)
               
            self.write(tornado.escape.json_encode(f))
        else:
            self.write("ERROR")

    @tornado.web.authenticated
    def post(self):
        username = self.get_argument("username",False)
        action = self.get_argument("action",False)
        if username and action:
            if action == "follow":
                self.db.follow.update({"follower":self.current_user["user_name"]},{"$push":{"following":username}},True)
                self.write("OK")
            elif action == "unfollow":
                self.db.follow.update({"follower":self.current_user["user_name"]},{"$pull":{"following":username}},True)
                self.write("OK")
        else:
            self.write("ERROR")
        # CONTROL

class BlockHandler(BaseHandler):
    def get(self):
    	username = self.get_argument("username",False)
    	if username:
    		blocked_users = self.db.block.find_one({"username":username},{"_id":0})
    		self.write(tornado.escape.json_encode(blocked_users))

    @tornado.web.authenticated
    def post(self):
    	username = self.get_argument("username",False)
        action = self.get_argument("action",False)
        if username and action:
            if action == "block":
                self.db.block.update({"username":self.current_user["user_name"]},{"$push":{"blocked":username}},True)
                self.write("OK")
            elif action == "unblock":
                self.db.block.update({"username":self.current_user["user_name"]},{"$pull":{"blocked":username}},True)
                self.write("OK")
        else:
            self.write("ERROR")
        # CONTROL 

class LikeHandler(BaseHandler):
    def get(self):
        feed_id = self.get_argument("feed_id",False)
        if feed_id:
            likers = self.db.likes.find_one({"feed_id":feed_id},{"_id":0})
            self.write(tornado.escape.json_encode(likers))
        else:
            self.write("ERROR")

    @tornado.web.authenticated
    def post(self):
        feed_id = self.get_argument("feed_id",False)
        action = self.get_argument("action",False)

        if feed_id and action:
            if action == "like":
                self.db.likes.update({"feed_id":feed_id},{"$push":{"username":self.current_user["user_name"]}},True)
                self.write("OK")
            elif action == "unlike":
                self.db.likes.update({"feed_id":feed_id},{"$pull":{"username":self.current_user["user_name"]}},True)
                self.write("OK")
        else:
            self.write("ERROR")
        # CONTROL

