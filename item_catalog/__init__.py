# -*- coding: utf-8 -*-
"""
Web app settings for Google Oauth API , Flask,
SqlAlchemy, SeaSurf CSRF security, REST configs and URLs mapping.
"""

import json
import os

from flask import Flask
from flask.ext.seasurf import SeaSurf
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy

__author__ = 'Andres Anies'
__email__ = 'andres_anies@hotmail.com'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URI = 'sqlite:///%s/catalog.sqlite3' % BASE_DIR
TEMPLATES = os.path.join(BASE_DIR, 'templates')

GOOGLE_PLUS_CLIENT_SECRETS = os.path.join(BASE_DIR, 'client_secrets.json')
GOOGLE_PLUS_CLIENT_ID = json.loads(
    open(GOOGLE_PLUS_CLIENT_SECRETS, 'r').read())['web']['client_id']

app = Flask(__name__)
api = Api(app)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
csrf = SeaSurf(app)

from . import views

api.add_resource(views.Categories, '/categories/')

api.add_resource(views.CategoryItemList, '/items/<category>')
api.add_resource(views.ItemList, '/items/')
api.add_resource(views.Item, '/items/<int:item_id>')

api.add_resource(views.LatestItems, '/latest_items/')

api.add_resource(views.Catalog, '/catalog/')

api.add_resource(views.GooglePlusAuth, '/google_login/')

app.secret_key = 'F13Zr47j\3yX R~X@H!jmM]Lwf/,?KT'
