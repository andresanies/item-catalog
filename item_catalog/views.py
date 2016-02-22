# -*- coding: utf-8 -*-
# Developer: Andres Anies <andres_anies@hotmail.com>

from item_catalog import app, db, TEMPLATES
from item_catalog import models
from flask import send_from_directory
from flask_restful import Resource, fields
from flask_restful import marshal_with, reqparse


@app.route('/')
def catalog_app():
    return send_from_directory(TEMPLATES, 'catalog.html')


class Categories(Resource):
    category_fields = {
        'id': fields.Integer,
        'name': fields.String,
    }

    @marshal_with(category_fields)
    def get(self):
        return models.Category.query.all()


class ItemResource(Resource):
    item_fields = {
        'id': fields.Integer,
        'title': fields.String,
        'description': fields.String,
        'category_id': fields.Integer,
    }

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('title', type=str)
        self.parser.add_argument('description', type=str)
        self.parser.add_argument('category_id', type=int)


class Item(ItemResource):
    @marshal_with(ItemResource.item_fields)
    def get(self, item_id):
        return models.Item.query.filter_by(id=item_id).first_or_404()

    @marshal_with(ItemResource.item_fields)
    def put(self, item_id):
        item_data = self.parser.parse_args()
        item = models.Item.query.filter_by(id=item_id).first_or_404()
        item.title = item_data['title']
        item.description = item_data['description']
        item.category_id = item_data['category_id']
        db.session.commit()
        return item, 200

    def delete(self, item_id):
        pass


class CategoryItemList(Resource):
    @marshal_with(ItemResource.item_fields)
    def get(self, category):
        return models.Category.query.filter_by(
            name=category).first_or_404().items.all()


class ItemList(ItemResource):
    @marshal_with(ItemResource.item_fields)
    def post(self):
        item_data = self.parser.parse_args()
        item = models.Item(**item_data)
        db.session.add(item)
        db.session.commit()
        return item, 201


class LatestItems(ItemResource):
    def get(self):
        pass
