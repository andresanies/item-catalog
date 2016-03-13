# -*- coding: utf-8 -*-
# Developer: Andres Anies <andres_anies@hotmail.com>
from simplexml import dumps
from flask import make_response
from flask import session
from flask_restful import Resource, fields
from flask_restful import reqparse
from item_catalog import api, db, models
from item_catalog import GOOGLE_PLUS_CLIENT_ID
from werkzeug.exceptions import HTTPException
from requests.exceptions import HTTPError
import requests

error_fields = {
    'error': fields.String
}


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


@api.representation('application/xml')
def output_xml(data, code, headers=None):
    """Makes a Flask response with a XML encoded body"""
    resp = make_response(dumps({'response': data}), code)
    resp.headers.extend(headers or {})
    return resp
