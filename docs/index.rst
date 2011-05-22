.. Flask-Admin documentation master file, created by
   sphinx-quickstart on Sat Feb 12 13:20:00 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


Flask-Admin
===========

.. module:: flaskext.admin

Flask-Admin aims to be a flexible, customizable web-based interface to
your datastore. It isn't there yet.

Right now, Flask-Admin only works with SQLAlchemy.


How's it work?
--------------

A typical use looks something like this::

    from flask import Flask
    app = Flask(__name__)

    from my_app import my_models
    from my_app.database import db_session

    admin_mod = Admin(app, my_models, admin_db_session=db_session,
                      exclude_pks=True)
    app.register_module(admin_mod, url_prefix='/admin')


See the examples for more.

-------------

.. autofunction:: Admin

