# -*- coding: utf-8 -*-
# Developer: Andres Anies <andres_anies@hotmail.com>

from item_catalog import db
from datetime import datetime


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)

    def __init__(self, name):
        self.name = name


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True)
    description = db.Column(db.String)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship(
        'Category', backref=db.backref('items', lazy='dynamic'))
    createdDateTime = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, title, description, category_id):
        self.title = title
        self.description = description
        self.category_id = category_id

    @property
    def category_name(self):
        return self.category.name
