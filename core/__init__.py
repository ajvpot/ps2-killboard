from flask import Flask, g
from flask_admin import Admin
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import timedelta

import os

app = Flask("killboard")
app.config['APP_PATH'] = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
app.config['APP_PORT'] = 8080
# app.config['SERVER_NAME'] = ''

app.config['PS2_FILTER_ENABLE'] = False
app.config['PS2_INTERESTED_IDS'] = [5428392193625290673, 5428308138483718321, 5428308138483717921, 5428401268685703233, 5428297992006952913]

app.config['PS2_QUERY_INTERVAL'] = 2


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://killboard:killboard@127.0.0.1/killboard'

app.config['RECAPTCHA_PUBLIC_KEY'] = '6LeYiAkTAAAAAAzFMOG5kn4uVFu4fye2PA9S-1Zg'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LeYiAkTAAAAAIyXM6EsMBfQxo-25Wdlw4A0G397'

# 100 megabytes
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
app.secret_key = "replacethasdfasdis"
app.config['CSRF_SECRET'] = "replacethisdasdgfdgfdgs"

#from util.form.form import render_control
admin = Admin(app, name="PS2Thing")
import core.admin

# this is how you could make a function globally available in views
app.jinja_env.globals.update(app=app)

# this is how you could add a filter to be globally available in views
# app.jinja_env.filters['formatElapsedTime'] = formatElapsedTime
# login manager
import core.login

# to add new routes just import them here
import core.routes.main
import core.routes.users