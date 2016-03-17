# -*- coding: utf-8 -*-
# Developer: Andres Anies <andres_anies@hotmail.com>

from item_catalog import db
from datetime import datetime


class Category(db.Model):
    """
    Categories in which each item will be classified.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)

    def __init__(self, name):
        """
        Simple initializer for a category given its name.
        :param name: The name for the category.
        """
        self.name = name


class User(db.Model):
    """
    Users that login in the app for adding,
    editing and deleting items for a given category.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    email = db.Column(db.String(256), unique=True)

    def __init__(self, name, email):
        """
        Create a database instance of user given its name and email.
        :param name: First name and last name or a nickname.
        :param email: primary email user address.
        """
        self.name = name
        self.email = email


class Item(db.Model):
    """
    Items classified in categories which people can browse in the site
    and logged user can add, edit or delete their own items.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True)
    description = db.Column(db.String)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship(
        'Category', backref=db.backref('items', lazy='dynamic'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(
        'User', backref=db.backref('items', lazy='dynamic'))
    createdDateTime = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, title, description, category_id, user):
        """
        Create an item instance for saving into the database.
        :param title: String that represents in a unique way the item.
        :param description: Long text description used for describing the item.
        :param category_id: Category identifier used for associate.
          the item with a category.
        :param user: The user that is creating the item which is
          used for determine permissions on items.
        """
        self.title = title
        self.description = description
        self.category_id = category_id
        self.user = user

    @property
    def category_name(self):
        """
        Search for the name of the related category
        :return: Name of the related category to the item.
        """
        return self.category.name
