.. Flask-Admin documentation master file, created by
   sphinx-quickstart on Sat Feb 12 13:20:00 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


Flask-Admin
===========
.. module:: flaskext.admin

Flask-Admin is a `Flask`_ extension that aims to be a flexible,
customizable web-based interface to your datastore. Currently,
Flask-Admin only works with SQLAlchemy declarative models but support
for additional datastores will be added in future versions.

.. note::
   Flask-Admin will only work with versions of Flask 0.7 or above.

How it works
------------

First, create some SQLAlchemy declarative models using `SQLAlchemy`_
or `Flask-SQLAlchemy`_. For example::

    from sqlalchemy import create_engine, Column, Integer, String
    from sqlalchemy.ext.declarative import declarative_base

    engine = create_engine('sqlite://', convert_unicode=True)
    Base = declarative_base(bind=engine)

    class Student(Base):
        __tablename__ = 'student'

        id = Column(Integer, primary_key=True)
        name = Column(String(120), unique=True)

        def __repr__(self):
            return self.name

   class Teacher(Base):
        __tablename__ = 'teacher'

        id = Column(Integer, primary_key=True)
        name = Column(String(120), unique=True)

        def __repr__(self):
            return self.name


.. note::
   The __repr__ method of your model class will be used to describe
   specific instances of your models models in things like the list
   view. If you don't set it, the default __repr__ method will look
   something like `<__main__.Student object at 0x1bb1490>`, which
   won't be very useful for distinguishing model instances.


Then create a blueprint using those models and your sqlalchemy
session::

    from sqlalchemy.orm import scoped_session, sessionmaker

    db_session = scoped_session(sessionmaker(
        autocommit=False, autoflush=False,
        bind=engine))

    admin_blueprint = admin.create_admin_blueprint(
         (Student, Teacher), db_session)

The first argument to :func:`create_admin_blueprint()` can have two forms:
it can either be some python iterable like a list or tuple, or it can
be a python module that contains your models. The second argument is
the sqlalchemy session that will be used to access the database. By
default, Flask-Admin will not expose the primary keys of your
models. This is usually a good idea if you are using a primary key
that doesn't have any meaning outside of the database, like an
auto-incrementing integer, because changing a primary key changes the
nature of foreign key relationships. If you want to expose the primary
key, set ``exclude_pks=False`` in the :func:`create_admin_blueprint()` call.

Next, register this blueprint on your Flask app::

    app = Flask(__name__)
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

Now the admin interface is set up. If you are running the app with the
built-in development server via :meth:`app.run()`, then it should be
available at http://localhost:5000/admin .


A note on __init__
------------------

Your model classes must be able to be initialized without any
arguments. For example, the following works because in
:meth:`__init__`, name is a keyword argument and is therefore
optional::

    class Person(Base):
        id = Column(Integer, primary_key=True)
        name = Column(String(120), unique=True)

        def __init__(self, name=None):
            self.name = name

        def __repr__(self):
            return self.name


But the following will not work because in this case, the __init__
method of :class:`User` `requires` a name::

    class Person(Base):
        id = Column(Integer, primary_key=True)
        name = Column(String(120), unique=True)

        def __init__(self, name):
            self.name = name

        def __repr__(self):
            return self.name


Flask-Admin Endpoints
---------------------
If you want to refer to views in Flask-Admin, the following endpoints
are available:

:meth:`url_for('admin.index')`
    returns the url for the index view

:meth:`url_for('admin.list_view', model_name='some_model')`
    returns the list view for a given model

:meth:`url_for('admin.edit', model_name='some_model', model_key=primary_key)`
    returns the url for the page used for editing a specific model
    instance

:meth:`url_for('admin.add', model_name='some_model')`
    returns the url for the adding a new model instance

:meth:`url_for('admin.delete', model_name='some_model', model_key=primary_key)`
    returns the url for the page used for deleting a specific model
    instance


.. note::

  You can use the ``name`` argument in
  :func:`create_admin_blueprint()` to set the name of the
  blueprint. For example if ``name="my_named_admin"``, then the
  endpoint for the index becomes ``'my_named_admin.index'``. This is
  necessary if you are going to use more than one admin blueprint
  within the same app.


Custom Templates and Static Files
---------------------------------

Using Flask blueprints makes customizing the admin interface really
easy. Flask-Admin comes with a default set of templates and static
files. You can customize as much of the interface as you'd like by
just overriding any files you'd like to change. Just create your own
version of the files in the templates and/or static directories of
your app. Refer to the documentation on Flask blueprints for
more. There is also an example of this in the `view decorator
example`_.


Custom Forms
------------

Flask-Admin uses the WTForms library to automatically generate the
form that will be used to add a new instance of a model or edit an
existing model instance. There may be cases where the automatically
generated form isn't what you want, so you can also create a custom
form for Flask-Admin to use for a given model.

For example, consider the following model of a User that stores hashed
passwords::

    from sqlalchemy import Boolean, Column, Integer, String
    from sqlalchemy.ext.declarative import declarative_base

    Base = declarative_base()

    class User(Base):
        __tablename__ = 'user'

        id = Column(Integer, primary_key=True)
        username = Column(String(80), unique=True)
        _password_hash = Column('password', String(80), nullable=False)
        is_active = Column(Boolean, default=True)

        def __init__(self, username="", password="", is_active=True):
            self.username = username
            self.password = password
            self.is_active = is_active

        def check_password(self, password):
            return check_password_hash(self.pw_hash, password)

        @property
        def password(self):
            return self._password_hash

        @password.setter
        def password(self, password):
            self._password_hash = generate_password_hash(password)

        password = synonym('_password_hash', descriptor=password)

        def __repr__(self):
            return self.username


To allow this model to be used with a typical password and
confirmation field form, you could create the following form::

    from wtforms import Form, validators
    from wtforms.fields import BooleanField, TextField, PasswordField

    class UserForm(Form):
        """
        Form for creating or editting User object (via the admin). Define
        any handling of fields here. This form class also has precedence
        when rendering forms to a webpage, so the model-generated fields
        will come after it.
        """
        username = TextField(u'User name',
                             [validators.required(),
                              validators.length(max=80)])
        password = PasswordField('Change Password',
                                 [validators.optional(),
                                  validators.equal_to('confirm_password')])
        confirm_password = PasswordField()
        is_active = BooleanField(default=True)


And just use the model_forms argument when calling
:func:`create_admin_blueprint` to associate this form with the User
model::

    admin_blueprint = admin.create_admin_blueprint(
        (User,), db_session, model_forms={'User': UserForm})

Now the :class:`UserForm` will be used for editing and adding a new
user. If the form passes the validation checks, then password will
propagate to the User model and will be hashed and stored the password
in the database.

.. note::
   Due to the way that forms are generated, the order of input fields
   is difficult to control. This is something that is expected to
   improve in future versions, but for now a custom form is also the
   only way to specify the order of form fields.


More examples
-------------

The Flask-Admin `example directory`_ contains some sample applications
that demonstrate all of the patterns above, plus some additional ideas
on how you can configure the admin.


Current Limitations
-------------------

Flask-Admin does not support multiple-column primary keys.


API
---

.. autofunction:: create_admin_blueprint


.. define hyperlink targets used in these docs
.. _Flask: http://flask.pocoo.org/
.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Flask-SQLAlchemy: http://packages.python.org/Flask-SQLAlchemy/
.. _example directory: https://github.com/wilsaj/flask-admin/tree/master/example
.. _view decorator example: https://github.com/wilsaj/flask-admin/tree/master/example/authentication/view_decorator.py
