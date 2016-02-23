# -*- coding: utf-8 -*-
# Developer: Andres Anies <andres_anies@hotmail.com>

from flask import Flask
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URI = 'sqlite:///%s/catalog.sqlite3' % BASE_DIR
TEMPLATES = os.path.join(BASE_DIR, 'templates')

app = Flask(__name__)
api = Api(app)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from . import views

api.add_resource(views.Categories, '/categories/')

api.add_resource(views.CategoryItemList, '/items/<category>')
api.add_resource(views.ItemList, '/items/')
api.add_resource(views.Item, '/items/<int:item_id>')

api.add_resource(views.LatestItems, '/latest_items/')

api.add_resource(views.Catalog, '/catalog/')
