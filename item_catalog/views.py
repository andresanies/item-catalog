# -*- coding: utf-8 -*-
# Developer: Andres Anies <andres_anies@hotmail.com>

from item_catalog import app, db, csrf, TEMPLATES
from item_catalog import models
from item_catalog import utils
from sqlalchemy import desc
from flask import send_from_directory
from flask import session
from flask_restful import Resource, fields
from flask_restful import marshal_with, reqparse
from flask_restful import marshal

from requests.exceptions import HTTPError
from werkzeug.exceptions import HTTPException
from collections import namedtuple


@app.route('/')
def catalog_web_app():
    response = send_from_directory(TEMPLATES, 'catalog.html')
    return response


class Categories(Resource):
    category_fields = {
        'id': fields.Integer,
        'name': fields.String,
    }

    @marshal_with(category_fields)
    def get(self):
        return models.Category.query.all()


class Item(utils.ItemResource):
    @marshal_with(utils.ItemResource.item_fields)
    def get(self, item_id):
        return models.Item.query.filter_by(id=item_id).first_or_404()

    @csrf.include
    def put(self, item_id):
        item_data = self.parser.parse_args()
        item = models.Item.query.filter_by(id=item_id).first_or_404()

        if models.Item.query.filter(
                        models.Item.title == item_data['title'],
                        models.Item.id != item_id).first():
            return {'title': 'There is already an item with that title'}, 400

        try:
            self.check_current_user_permissions_on_item(item)
            item.title = item_data['title']
            item.description = item_data['description']
            item.category_id = item_data['category_id']
            db.session.commit()
            return marshal(item, self.item_fields), 200
        except HTTPException as e:
            return marshal({'error': e.description}, utils.error_fields), e.response

    @csrf.include
    def delete(self, item_id):
        item = models.Item.query.filter_by(id=item_id).first_or_404()
        try:
            self.check_current_user_permissions_on_item(item)
            db.session.delete(item)
            db.session.commit()
            return '', 204
        except HTTPException as e:
            return marshal({'error': e.description}, utils.error_fields), e.response


class CategoryItemList(utils.ItemsPermissionsMixin, utils.ItemResource):
    item_fields = utils.ItemResource.item_fields
    item_fields['read_only'] = fields.Boolean

    @marshal_with(item_fields)
    def get(self, category):
        items = models.Category.query.filter_by(
            name=category).first_or_404().items.all()
        return self.get_items_permissions(items)


class ItemList(utils.ItemResource):
    @csrf.include
    def post(self):
        item_data = self.parser.parse_args()

        if models.Item.query.filter(
                        models.Item.title == item_data['title']).first():
            return {'title': 'There is already an item with that title'}, 400

        item = models.Item(user=self.get_current_user_or_403(), **item_data)
        db.session.add(item)
        db.session.commit()
        return marshal(item, self.item_fields), 201


class LatestItems(utils.ItemsPermissionsMixin, utils.ItemResource):
    item_fields = {
        'id': fields.Integer,
        'title': fields.String,
        'description': fields.String,
        'category_id': fields.Integer,
        'category_name': fields.String,
        'read_only': fields.Boolean
    }

    @marshal_with(item_fields)
    def get(self):
        items = models.Item.query.order_by(
            desc(models.Item.createdDateTime)).limit(10).all()
        return self.get_items_permissions(items)


class Catalog(Resource):
    item_fields = {
        'id': fields.Integer,
        'title': fields.String,
        'description': fields.String,
        'category_id': fields.Integer,
        'category_name': fields.String,
    }
    catalog_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'items': fields.List(fields.Nested(item_fields))
    }

    @marshal_with(catalog_fields, envelope='categories')
    def get(self):
        return models.Category.query.all()


class GooglePlusAuth(utils.GooglePlusAuthenticationMixin, Resource):
    Credentials = namedtuple('Credentials', 'access_token id_token')

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('credentials', type=dict)

    @csrf.include
    def post(self):
        credentials = self.get_credentials()
        try:
            self.validate_token(credentials)
            google_plus_id = credentials.id_token['sub']
            if not self.user_has_google_login(google_plus_id):
                self.save_user_to_session(credentials, google_plus_id)
            return marshal({'detail': 'User logged in successfully'},
                           self.success), 200
        except HTTPError as error:
            message = error.response.reason if error.response else error.message
            return marshal({'error': message}, utils.error_fields), 500

    def get_credentials(self):
        credentials_dict = self.parser.parse_args()
        return self.Credentials(**credentials_dict.credentials)

    def delete(self):
        access_token = session['access_token']
        if not access_token:
            return marshal({'error': 'Current user is not logged.'}, utils.error_fields), 401
        self.delete_user_from_session()
        return marshal({'detail': 'Successfully logout.'},
                       self.success), 200
