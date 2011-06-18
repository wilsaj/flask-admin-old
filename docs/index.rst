.. Flask-Admin documentation master file, created by
   sphinx-quickstart on Sat Feb 12 13:20:00 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


Flask-Admin
===========
.. module:: flaskext.admin

Flask-Admin aims to be a flexible, customizable web-based interface to
your datastore. It's not quite there yet. At the moment, Flask-Admin
only works with SQLAlchemy declarative models.

.. warning::
  The Flask-Admin extension is still under heavy development. Until an
  initial release, everything is subject to change. Feedback is very
  welcome!


How to use it
-------------
Typical usage looks something like this::

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


Some Important Notes
--------------------

You must run ``themes.setup_themes()`` on your app in order for the
admin views to have access to the templates and static files that ship
with Flask-Admin.

Also, your model classes must be able to be initialized without any
arguments. For example, this works::

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True)
        email = db.Column(db.String(120), unique=True)

        def __init__(self, username=None, email=None):
            self.username = username
            self.email = email


But this doesn't work::

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True)
        email = db.Column(db.String(120), unique=True)

        def __init__(self, username, email):
            self.username = username
            self.email = email

Because Flask-Admin needs to be able execute ``User()`` without any
arguments passed to it.



Customizing your Admin
----------------------
Currently, the best way to customize the admin interface is to copy
the 'admin_default' theme from flaskext/admin/themes/ and edit the
files accordingly. See the example in
`examples/authentication/view_decorator.py` for an example of how that
might work.


Endpoints for Flask-Admin views
-------------------------------
If you want to refer to views in Flask-Admin, the following endpoints
are available:

`url_for('flaskext.admin.index')`
    returns the url for the index view

`url_for('flaskext.admin.list_view', model_name='some_model')`
    returns the list view for a given model

`url_for('flaskext.admin.edit', model_name='some_model', model_key=primary_key)`
    returns the url for the page used for editing a specific model
    instance

`url_for('flaskext.admin.add', model_name='some_model')`
    returns the url for the adding a new model instance

`url_for('flaskext.admin.delete', model_name='some_model', model_key=primary_key)`
    returns the url for the page used for deleting a specific model
    instance


.. note::

  You can use the ``append_to_endpoints`` argument in the Admin
  constructor, in which case each of the view endpoints will have this
  value appended to the end of them. For example if
  ``append_to_endpoints="_my_admin"``, then the endpoint for the index
  becomes ``'flaskext.admin.index_my_admin'``. This is absolutely
  necessary if you are going to use multiple admin modules within the
  same app.


API
---

.. autoclass:: Admin

