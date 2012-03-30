#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymongo,os

def mongodb_index():
    db = pymongo.Connection().tuxhub
    db.users.create_index("user_name",unique=True)

def js_minifier():
    os.system("java -jar compiler.jar --js=../static/bootstrap/js/jquery.min.js --js=../static/bootstrap/js/bootstrap.min.js --js=../static/js/jquery.validate.js --js=../static/js/main.js --js_output_file=../static/js/main.min.js")
    
mongodb_index()

js_minifier()