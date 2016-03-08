# -*- coding: utf-8 -*-
# Developer: Andres Anies <andres_anies@hotmail.com>

from flask import Flask
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask.ext.seasurf import SeaSurf
import os
import json

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

app.secret_key = 'r\x80\xd4\xc7_\x99%\x81W\xbf\xefK\xcc\xcc\xb4\xebG\x16\xa8\xe2\xd0\xb3s\x1a'
