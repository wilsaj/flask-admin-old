.. Flask-Admin documentation master file, created by
   sphinx-quickstart on Sat Feb 12 13:20:00 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


Flask-Admin
===========

.. module:: flaskext.admin

Flask-Admin aims to be a flexible, customizable web-based interface to
your datastore. It isn't there yet.

At the moment, Flask-Admin only works with SQLAlchemy declarative
models.


Usage
-----

A typical usage looks something like this::

    from flask import Flask
    from flaskext import themes
    from flaskext.admin import Admin
    from my_app import my_models

    app = Flask(__name__)

    from my_app.database import db_session

    themes.setup_themes(app)
    admin_mod = Admin(app, my_models, db_session,
                      exclude_pks=True)
    app.register_module(admin_mod, url_prefix='/admin')


Where my_models is a module containing SQLAlchemy declarative models
which have been created either using Flask-SQLAlchemy extension or
with SQLAlchemy's declarative pattern.


Customizing the Admin interface
-------------------------------

Currently, the best way to customize the admin interface is to copy
the 'admin_default' theme from flaskext/admin/themes/ and edit the
files accordingly.


-------------

.. autoclass:: Admin

