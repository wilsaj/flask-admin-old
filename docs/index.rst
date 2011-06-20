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
  Flask-Admin is still under heavy development. Until the initial
  release, everything is subject to change. Feedback is appreciated!

.. note::
  Flask-Admin uses of blueprints, which are an upcoming Flask feature
  that allow a greater degree of flexibility and customization. This
  means Flask-Admin will not work with any version below Flask 0.7,
  which is soon to be released. The initial Flask-Admin 0.1 release
  will probably follow shortly after the Flask 0.7 release. If you
  want to try out Flask-Admin early, make sure you are running the
  `blueprints branch`_ of the Flask development version.

  .. _blueprints branch: https://github.com/mitsuhiko/flask/tree/blueprints


How to use it
-------------
Typical usage looks something like this::

    from flask import Flask
    from flaskext import admin
    from my_app import my_models

    app = Flask(__name__)

    from my_app.database import db_session

    admin_blueprint = admin.create_admin_blueprint(
         app, (Course, Student, Teacher), db_session, exclude_pks=True)
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

Where my_models is a module containing SQLAlchemy declarative models
which have been created either using Flask-SQLAlchemy extension or
with SQLAlchemy's declarative pattern.


Some Important Notes
--------------------

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

Because Flask-Admin needs to be able to instantiate a new ``User()``
without any arguments passed to it.



Customizing your Admin
----------------------

Using the Flask blueprints makes customizing the admin interface
really easy. For the file(s) you want to change, just override them by
creating them the themes and static directories of your app. Refer to
the Flask blueprint documentation for more and see the example in
`examples/authentication/view_decorator.py` for an example of how that
might work.


Endpoints for Flask-Admin views
-------------------------------
If you want to refer to views in Flask-Admin, the following endpoints
are available:

`url_for('admin.index')`
    returns the url for the index view

`url_for('admin.list_view', model_name='some_model')`
    returns the list view for a given model

`url_for('admin.edit', model_name='some_model', model_key=primary_key)`
    returns the url for the page used for editing a specific model
    instance

`url_for('admin.add', model_name='some_model')`
    returns the url for the adding a new model instance

`url_for('admin.delete', model_name='some_model', model_key=primary_key)`
    returns the url for the page used for deleting a specific model
    instance


.. note::

  You can use the ``name`` argument in the create_admin_blueprint()
  call to change the name of the blueprint. For example if
  ``name="my_named_admin"``, then the endpoint for the index becomes
  ``'my_named_admin.index'``. This is absolutely necessary if you are
  going to use multiple distinct admin blueprints within the same app.


API
---

.. autofunction:: create_admin_blueprint

