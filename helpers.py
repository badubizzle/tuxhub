#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PIL import Image
import StringIO
import re
import tornado.escape

def type_of(content):
    try:
        i=Image.open(StringIO.StringIO(content))
        return i.format.lower()
    except IOError:
        return False

def linkify(feed):
    regex = re.compile("\@[a-zA-Z0-9_]+",re.IGNORECASE)
    mentions = regex.findall(feed)
    for i in mentions:
        feed = feed.replace(i,"<a href='/user/%s'>%s</a>" % (i.replace("@",""),i))
    return tornado.escape.xhtml_unescape(tornado.escape.linkify(feed))
