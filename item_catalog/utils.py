# -*- coding: utf-8 -*-
"""
Mixins and Behaviors for parsing and rendering items as well as
authenticating users and authorizing write operations over the items.
"""
import requests
from flask import make_response
from flask import session
from flask_restful import Resource, fields
from flask_restful import reqparse
from requests.exceptions import HTTPError
from simplexml import dumps
from werkzeug.exceptions import HTTPException

from item_catalog import GOOGLE_PLUS_CLIENT_ID
from item_catalog import api, db, models

__author__ = 'Andres Anies'
__email__ = 'andres_anies@hotmail.com'

# Response format for errors in services
error_fields = {
    'error': fields.String
}


class ItemResourceParser(object):
    """
    Parser converts input items into python dictionary
    and a response formatter that converts it back
    in to given media type.
    """
    item_fields = {
        'id': fields.Integer,
        'title': fields.String,
        'description': fields.String,
        'category_id': fields.Integer,
    }

    def __init__(self):
        """
        Initialize the input item parser.
        """
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('title', type=str)
        self.parser.add_argument('description', type=str)
        self.parser.add_argument('category_id', type=int)


class ItemPermissionsMixin(object):
    """
    Permission mixin used for check authorization on a
    give item for logged in users.
    """

    def check_current_user_permissions_on_item(self, item):
        """
        Make an authorization test on a given item and
        user on the current session.
        If the test fails a HTTPException with 403 status code will be raised.
        :param item: Item to be tested for write permissions.
        """
        has_permissions = item.user == self.get_current_user_or_403()
        if not has_permissions:
            raise HTTPException(
                description='Not authorized to perform actions on this item',
                response=403)

    def get_current_user_or_403(self):
        """
        Returns the user of the current session or
        raise an HTTPException with 403 status code.
        :return: The user of the current session.
        """
        user = self.get_current_user()
        if user:
            return user
        else:
            raise HTTPException(
                description="Unauthenticated users can't "
                            "perform actions on this item",
                response=403)

    def get_current_user(self):
        """
        Search a logged in user in the session using his email
        as a unique identifier.
        :return: The user on the current session.
        """
        if 'email' in session:
            user = models.User.query.filter_by(
                email=session['email']).first()
            return user


class ItemsPermissionsMixin(ItemPermissionsMixin):
    """
    Permission mixin which extends ItemPermissionsMixin
    used for testing authorization against a list of items.
    """

    def get_items_permissions(self, items):
        """
        Check permissions for the current logged in user on a list of items.
        :param items: List of items that are going to be tested.
        :return: The tested list of items which has an additional
          read_only attribute that specifies if the user
          has write permissions over that specific item.
        """
        for item in items:
            current_user = self.get_current_user()
            item.read_only = item.user != current_user or current_user is None
        return items


class ItemResource(ItemResourceParser, ItemPermissionsMixin, Resource):
    pass


class GooglePlusAuthenticationMixin(Resource):
    """
    Google plus oauth server flow implementation.
    """

    # Response format for success case in login services.
    success = {
        'detail': fields.String
    }

    def user_has_google_login(self, user_id):
        """
        Verify if a given google user is already authenticated.
        :param user_id: User identification use for the test.
        :return: The user access token if the given user is authenticated
         or False also if there is no logged in user or their ids not match.
        """
        return session.get('access_token') and (
            user_id == session.get('google_plus_id'))

    def get_google_user_info(self, access_token):
        """
        Fetch the basic user information from a google REST API.
        :param access_token: The access token for the logged in user.
        :return: Database instance of the user.
        """
        user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': access_token, 'alt': 'json'}
        user_data = requests.get(user_info_url, params=params).json()
        return self.get_user(user_data)

    def get_user(self, user_data):
        """
        Query a user by the email field in the database and if not exists
        it will create a user with the given data.
        :param user_data: Dictionary containing username and email of the user.
        :return: The database user instance.
        """
        user = models.User.query.filter_by(
            email=user_data['email']).first()
        if not user:
            user = models.User(user_data['name'], user_data['email'])
            db.session.add(user)
            db.session.commit()
        return user

    def save_user_to_session(self, credentials, google_plus_id):
        """
        Save the user data and credentials into the current session.
        :param credentials: Credentials object with a valid access token.
        :param google_plus_id: Google Plus identification number.
        """
        session['access_token'] = credentials.access_token
        session['google_plus_id'] = google_plus_id
        user = self.get_google_user_info(credentials.access_token)
        session['username'] = user.name
        session['email'] = user.email

    def delete_user_from_session(self):
        """
        Erase all the data in the current session
        associated with the logged in user.
        """
        del session['google_plus_id']
        del session['username']
        del session['email']
        del session['access_token']

    def validate_token(self, credentials):
        """
        Validate the given credentials(access token and subject)
        against a Google oauth validation API or raise an HTTPError.
        :param credentials: Credentials object used for validation
        """
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


@api.representation('application/xml')
def output_xml(data, code, headers=None):
    """
    Makes a Flask response with a XML encoded body.
    :param data: Payload used for generating a xml formatted response.
    :param code: HTTP status code.
    :param headers: HTTP extra headers.
    :return: Properly xml encoded response.
    """
    resp = make_response(dumps({'response': data}), code)
    resp.headers.extend(headers or {})
    return resp
