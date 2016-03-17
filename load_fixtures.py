# -*- coding: utf-8 -*-
# Developer: Andres Anies <andres_anies@hotmail.com>

from item_catalog import db
from item_catalog.models import Category

# Create all database tables.
db.create_all()

# List of categories that will be
# associated with each item.
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

# Populate the database with the categories in the list.
for category_name in categories:
    category = Category(category_name)
    db.session.add(category)

db.session.commit()
