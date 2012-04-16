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
