# -*- coding: utf-8 -*-
"""
Service a single one page UI and multiple web services for CRUD operations
on items and get a list of previously saved categories.
"""

from collections import namedtuple

from flask import send_from_directory
from flask import session
from flask_restful import Resource, fields
from flask_restful import marshal
from flask_restful import marshal_with, reqparse
from requests.exceptions import HTTPError
from sqlalchemy import desc
from werkzeug.exceptions import HTTPException

from item_catalog import app, db, csrf, TEMPLATES
from item_catalog import models
from item_catalog import utils

__author__ = 'Andres Anies'
__email__ = 'andres_anies@hotmail.com'


@app.route('/')
def catalog_web_app():
    """
    Single page app template with all elements
    compressed in the file catalog.html.
    :return: Single page web app with out any server side rendering.
    """
    response = send_from_directory(TEMPLATES, 'catalog.html')
    return response


class Categories(Resource):
    """
    List of registered categories.
    """
    category_fields = {
        'id': fields.Integer,
        'name': fields.String,
    }

    @marshal_with(category_fields)
    def get(self):
        """
        Query and return all the categories from the database.
        :return: List of categories.
        """
        return models.Category.query.all()


class Item(utils.ItemResource):
    """
    REST like resource for retrieve, update and delete operations
    on a single item given the items id.
    """

    @marshal_with(utils.ItemResource.item_fields)
    def get(self, item_id):
        """
        Search for a specific item by its id.
        :param item_id: An identifier of the item.
        :return: The hole item info.
        """
        return models.Item.query.filter_by(id=item_id).first_or_404()

    @csrf.include
    def put(self, item_id):
        """
        Fully update the item if the current user has write permissions
        and validate unique fields.
        :param item_id: An identifier of the item.
        :return: The updated item.
        """
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
            return marshal(
                {'error': e.description}, utils.error_fields), e.response

    @csrf.include
    def delete(self, item_id):
        """
        Erase the item if the user has the permissions.
        :param item_id: An identifier of the item.
        :return: HTTP 204 if the item was successfully deleted or
          it will raise an HTTPException with 403 status code.
        """
        item = models.Item.query.filter_by(id=item_id).first_or_404()
        try:
            self.check_current_user_permissions_on_item(item)
            db.session.delete(item)
            db.session.commit()
            return '', 204
        except HTTPException as e:
            return marshal(
                {'error': e.description}, utils.error_fields), e.response


class CategoryItemList(utils.ItemsPermissionsMixin, utils.ItemResource):
    """
    Shows a list of items filtered by a specific category.
    """
    item_fields = utils.ItemResource.item_fields
    item_fields['read_only'] = fields.Boolean

    @marshal_with(item_fields)
    def get(self, category):
        """
        Search for a complete list of items related to a given category.
        :param category: The category title used for the items search.
        :return: A category related list of items with an addition
          field 'read_only' that indicates whether the current user
          has no write permission over each item.
        """
        items = models.Category.query.filter_by(
            name=category).first_or_404().items.all()
        return self.get_items_permissions(items)


class ItemList(utils.ItemResource):
    """
    Write only list for creating an item.
    """

    @csrf.include
    def post(self):
        """
        Create an item from its title, description, category id
        and the current logged in user.
        :return: The created item with its associated id.
        """
        item_data = self.parser.parse_args()

        if models.Item.query.filter(
                        models.Item.title == item_data['title']).first():
            return {'title': 'There is already an item with that title'}, 400

        item = models.Item(user=self.get_current_user_or_403(), **item_data)
        db.session.add(item)
        db.session.commit()
        return marshal(item, self.item_fields), 201


class LatestItems(utils.ItemsPermissionsMixin, utils.ItemResource):
    """
    List the last 10 recently created items
    sorted from the most recent to oldest.
    """
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
        """
        List the latest 10 items.
        :return: A list of the latest items.
        """
        items = models.Item.query.order_by(
            desc(models.Item.createdDateTime)).limit(10).all()
        return self.get_items_permissions(items)


class Catalog(Resource):
    """
    API endpoint that list all the categories and items
    available in the web app formatted as JSON or XML.
    """
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
        """
        List all the categories and items.
        :return: A complete list of all the categories and its related items.
        """
        return models.Category.query.all()


class GooglePlusAuth(utils.GooglePlusAuthenticationMixin, Resource):
    """
    Google Plus login implementation.
    """
    Credentials = namedtuple('Credentials', 'access_token id_token')

    def __init__(self):
        """
        Initialize the credentials parser.
        """
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('credentials', type=dict)

    @csrf.include
    def post(self):
        """
        Triggers the google plus login flow which validates the access token
        and confirm that the user identity match the one who generated
        the token, then if the user is not already logged in it will try to
        log in the user into the session.
        :return: Successful response if the user logs in without any error or
          a formatted error message with the related status code.
        """
        credentials = self.get_credentials()
        try:
            self.validate_token(credentials)
            google_plus_id = credentials.id_token['sub']
            if not self.user_has_google_login(google_plus_id):
                self.save_user_to_session(credentials, google_plus_id)
            return marshal({'detail': 'User logged in successfully'},
                           self.success), 200
        except HTTPError as error:
            message = error.response.reason \
                if error.response else error.message
            return marshal({'error': message}, utils.error_fields), 500

    def get_credentials(self):
        """
        Converts the credentials dictionary to a namedtuple so
        its attributes can be accessed in the same way as a
        google flow credentials object.
        :return: Credentials named tuple used as credentials object.
        """
        credentials_dict = self.parser.parse_args()
        return self.Credentials(**credentials_dict.credentials)

    @csrf.include
    def delete(self):
        """
        Logs out a user by deleting its info from the current session.
        :return: Successful response if the user logs out without any error or
          a formatted error message with the related status code.
        """
        if 'access_token' not in session:
            return marshal(
                {'error': 'Current user is not logged in.'},
                utils.error_fields), 401
        self.delete_user_from_session()
        return marshal({'detail': 'Successfully logout.'},
                       self.success), 200
