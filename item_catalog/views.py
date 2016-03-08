# -*- coding: utf-8 -*-
# Developer: Andres Anies <andres_anies@hotmail.com>

from item_catalog import app, db, csrf, TEMPLATES
from item_catalog import GOOGLE_PLUS_CLIENT_ID
from item_catalog import GOOGLE_PLUS_CLIENT_SECRETS
from item_catalog import models
from sqlalchemy import desc
from flask import send_from_directory
from flask import session
from flask_restful import Resource, fields
from flask_restful import marshal_with, reqparse
from flask_restful import marshal

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import requests
from requests.exceptions import HTTPError
from werkzeug.exceptions import HTTPException
from collections import namedtuple


@app.route('/')
def catalog_web_app():
    response = send_from_directory(TEMPLATES, 'catalog.html')
    return response


error_fields = {
    'error': fields.String
}


class Categories(Resource):
    category_fields = {
        'id': fields.Integer,
        'name': fields.String,
    }

    @marshal_with(category_fields)
    def get(self):
        return models.Category.query.all()


class ItemResourceParser(object):
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


class ItemPermissionsMixin(object):
    def check_current_user_permissions_on_item(self, item):
        has_permissions = item.user == self.get_current_user_or_403()
        if not has_permissions:
            raise HTTPException(
                description='Not authorized to perform actions on this item',
                response=403)

    def get_current_user_or_403(self):
        user = self.get_current_user()
        if user:
            return user
        else:
            raise HTTPException(
                description="Unauthenticated users can't perform actions on this item",
                response=403)

    def get_current_user(self):
        if 'email' in session:
            user = models.User.query.filter_by(
                email=session['email']).first()
            return user


class ItemsPermissionsMixin(ItemPermissionsMixin):
    def get_items_permissions(self, items):
        for item in items:
            current_user = self.get_current_user()
            item.read_only = item.user != current_user or current_user is None
        return items


class ItemResource(ItemResourceParser, ItemPermissionsMixin, Resource):
    pass


class Item(ItemResource):
    @marshal_with(ItemResource.item_fields)
    def get(self, item_id):
        return models.Item.query.filter_by(id=item_id).first_or_404()

    @csrf.include
    def put(self, item_id):
        item_data = self.parser.parse_args()
        item = models.Item.query.filter_by(id=item_id).first_or_404()
        try:
            self.check_current_user_permissions_on_item(item)
            item.title = item_data['title']
            item.description = item_data['description']
            item.category_id = item_data['category_id']
            db.session.commit()
            return marshal(item, self.item_fields), 200
        except HTTPException as e:
            return marshal({'error': e.description}, error_fields), e.response

    @csrf.include
    def delete(self, item_id):
        item = models.Item.query.filter_by(id=item_id).first_or_404()
        try:
            self.check_current_user_permissions_on_item(item)
            db.session.delete(item)
            db.session.commit()
            return '', 204
        except HTTPException as e:
            return marshal({'error': e.description}, error_fields), e.response


class CategoryItemList(ItemsPermissionsMixin, ItemResource):
    item_fields = ItemResource.item_fields
    item_fields['read_only'] = fields.Boolean

    @marshal_with(item_fields)
    def get(self, category):
        items = models.Category.query.filter_by(
            name=category).first_or_404().items.all()
        return self.get_items_permissions(items)


class ItemList(ItemResource):
    @csrf.include
    @marshal_with(ItemResource.item_fields)
    def post(self):
        item_data = self.parser.parse_args()
        item = models.Item(user=self.get_current_user_or_403(), **item_data)
        db.session.add(item)
        db.session.commit()
        return item, 201


class LatestItems(ItemsPermissionsMixin, ItemResource):
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


class GooglePlusAuthenticationMixin(Resource):
    success = {
        'detail': fields.String
    }

    def user_has_google_login(self, user_id):
        return session.get('access_token') and (
            user_id == session.get('google_plus_id'))

    def get_google_user_info(self, access_token):
        user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': access_token, 'alt': 'json'}
        user_data = requests.get(user_info_url, params=params).json()
        return self.get_user(user_data)

    def get_user(self, user_data):
        user = models.User.query.filter_by(
            email=user_data['email']).first()
        if not user:
            user = models.User(user_data['name'], user_data['email'])
            db.session.add(user)
            db.session.commit()
        return user

    def save_user_to_session(self, credentials, google_plus_id):
        session['access_token'] = credentials.access_token
        session['google_plus_id'] = google_plus_id
        user = self.get_google_user_info(credentials.access_token)
        session['username'] = user.name
        # session['picture'] = user['picture']
        session['email'] = user.email

    def delete_user_from_session(self):
        del session['google_plus_id']
        del session['username']
        del session['email']
        del session['access_token']

    def validate_token(self, credentials):
        # Check that the access token is valid.
        result = requests.get(
            'https://www.googleapis.com/oauth2/v1/tokeninfo'
            '?access_token=%s' % credentials.access_token)

        # If there was an error in the access token info, abort.
        if result.status_code != requests.codes.ok:
            result.raise_for_status()

        # Verify that the access token is used for the intended user.
        if result.json()['user_id'] != credentials.id_token['sub']:
            raise HTTPError("Token's user ID doesn't match given user ID.")

        # Verify that the access token is valid for this app.
        if result.json()['issued_to'] != GOOGLE_PLUS_CLIENT_ID:
            raise HTTPError("Token's client ID does not match app's.")


class GooglePlusAuth(GooglePlusAuthenticationMixin, Resource):
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
            return marshal({'error': message}, error_fields), 500

    def get_credentials(self):
        credentials_dict = self.parser.parse_args()
        return self.Credentials(**credentials_dict.credentials)

    def delete(self):
        access_token = session['access_token']
        if not access_token:
            return marshal({'error': 'Current user is not logged.'}, error_fields), 401
        self.delete_user_from_session()
        return marshal({'detail': 'Successfully logout.'},
                       self.success), 200
