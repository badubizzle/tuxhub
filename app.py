#!/usr/bin/env python
#-*- coding:utf-8 -*-

import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.escape
import tornado.options
from tornado.options import define, options
import handlers, os

define("port",default=18888,type=int)

urls = [
	(r"/", handlers.MainHandler),
	(r"/register", handlers.RegisterHandler),
	(r"/login", handlers.LoginHandler),
	(r"/logout", handlers.LogoutHandler),
	(r"/api", handlers.ApiHandler),
	(r"/p/(?P<picture>.*)", handlers.PictureHandler),
	(r"/(?P<username>.*)", handlers.UserHandler),
]

settings = dict({
	"template_path": os.path.join(os.path.dirname(__file__),"templates"),
	"static_path": os.path.join(os.path.dirname(__file__),"static"),
	"cookie_secret": "ösaOPU)=()(/=+TY=0m552â§ªâªâª»“€0H/()/^)(=h0JKjô←←jhAHODF8*))"
})

application = tornado.web.Application(urls,**settings)

def main():
	tornado.options.parse_command_line()
	server = tornado.httpserver.HTTPServer(application)
	server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	main()