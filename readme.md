# Item Catalog Web App

This application provides a list of items within a variety of categories as well as provide 
a user registration and authentication through Google Plus OAuth API. Registered users will have the ability to post, 
edit and delete their own items, and the non authenticated users will just browse the items and categories
in read only mode.

## App Structure

- `item_catalog` Python package which contains a flask REST API using SqlAlchemy as a database ORM framework.
  - `__init__.py` Web app setting for Google Oauth API , Flask, SqlAlchemy, SeaSurf CSRF security, 
       REST configs and URLs mapping.
  - `models.py` Database schema definitions using SqlAlchemy model declarative style.
  - `views.py` Service a single one page UI and multiple web services for CRUD operations 
       on items and get a list of previously saved categories.
  - `utils.py` Mixins and Behaviors for parsing and rendering items as well as authenticating users and authorizing 
       write operations over the items.
       
- `static` HTML5 Single one page web app using web components and Polymer as web framework for building a modular 
     models based app.
     
- `templates` HTML5 templates for the flask app.
  - `catalog.html` Single one page app compressed as one file, served by a flask view 
       with no need of any server side rendering.  
       
- `load_fixtures.py` Setup the database schema and load a list of a defined categories.
- `runserver.py` Bootstrap the Flask web application.

## Setup

### Requirements

- `Python runtime 2.7.x`: Runtime environment for python scripts. 
- `SQLite`: Super light DBMS for storing users, items and categories.

### Installing python required libraries using pip
```
pip install -r requirements.txt
```

### Setting up database schema and loading fixtures
```
python load_fixtures.py
```

### Obtain OAuth credentials from Google 

1. Check the [OAuth 2.0 Google APIs documentation]
    (https://developers.google.com/identity/protocols/OAuth2) in order to create the 
    Client ID & Secret for the catalog app.
2. Save your google client secret keys in a file call `client_secrets.json` in the main directory.

## Start the web server
```
python runserver.py
```
