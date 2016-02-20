# -*- coding: utf-8 -*-
# Developer: Andres Anies <andres_anies@hotmail.com>

from item_catalog import db
from item_catalog.models import Category

db.create_all()

categories = [
    "Soccer",
    "Basketball",
    "Baseball",
    "Frisbee",
    "Snowboarding",
    "Rock Climbing",
    "Foosball",
    "Skating",
    "Hockey",
]

for category_name in categories:
    category = Category(category_name)
    db.session.add(category)

db.session.commit()
