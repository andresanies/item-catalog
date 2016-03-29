# -*- coding: utf-8 -*-
"""
Database schema definitions using SqlAlchemy model declarative style.
"""

from datetime import datetime

from item_catalog import db

__author__ = 'Andres Anies'
__email__ = 'andres_anies@hotmail.com'


class Category(db.Model):
    """
    Categories in which each items will be classified.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)

    def __init__(self, name):
        """
        Simple initializer for a category when you give a name.
        :param name: The name for the category.
        """
        self.name = name


class User(db.Model):
    """
    Users who login to the app for adding,
    editing and deleting items.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    email = db.Column(db.String(256), unique=True)

    def __init__(self, name, email):
        """
        Create a database instance when the user gives his name and email.
        :param name: First name and last name or a nickname.
        :param email: primary email of the user .
        """
        self.name = name
        self.email = email


class Item(db.Model):
    """
    Items classified in categories where people can browse
    and logged in users can add, edit or delete their own items.
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
        Create a database instance when the user gives an
        item title description, and a related category.
        :param title: String that represents the item in a unique way.
        :param description: Long text description used for describing the item.
        :param category_id: Identifier used for associate
          the item with a category.
        :param user: The user who is creating an item who can have
          write permissions on that item.
        """
        self.title = title
        self.description = description
        self.category_id = category_id
        self.user = user

    @property
    def category_name(self):
        """
        Name of the related category of the item.
        :return: Name of the related category of the item.
        """
        return self.category.name
