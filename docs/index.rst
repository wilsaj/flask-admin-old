.. Flask-Admin documentation master file, created by
   sphinx-quickstart on Sat Feb 12 13:20:00 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


Flask-Admin
===========

.. module:: flaskext.admin

Flask-Admin aims to be a flexible, customizable web-based interface to
your datastore. It isn't there yet.

At the moment, Flask-Admin only works with SQLAlchemy.


How to use it
-------------

A typical usage looks something like this::

    from flask import Flask
    from flaskext.admin import Admin
    from flaskext impore themes
    from my_app import my_models

    app = Flask(__name__)

    from my_app.database import db_session

    themes.setup_themes(app)
    admin_mod = Admin(app, my_models, admin_db_session=db_session,
                      exclude_pks=True)
    app.register_module(admin_mod, url_prefix='/admin')


where my_models is a module containing SQLAlchemy declarative models
which have been created either using Flask-SQLAlchemy extension or
with SQLAlchemy's declarative pattern.


Customizing your interface
--------------------------

Flask-Admin makes use of Flask-Themes for rendering the admin
pages. This allows you to customize as much of the admin interface as
you want by changing individual static files or templates. You can
also completely replace the default theme with an altogether new one.

See the examples and the Flask-Themes documentation for more info on
that.


-------------

.. autofunction:: Admin

