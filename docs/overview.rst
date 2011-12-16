Quick start
-----------

Start off by creating some data models. In this example we'll use
`SQLAlchemy`_ declarative models.  `Flask-SQLAlchemy`_ and
`MongoAlchemy`_ models are also supported. So here are our models::

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


Then create a datastore object using those models and your sqlalchemy
session::

    from flask.ext.admin.datastore.sqlalchemy import SQLAlchemyDatastore
    from sqlalchemy.orm import scoped_session, sessionmaker

    db_session = scoped_session(sessionmaker(bind=engine))

    admin_datastore = SQLAlchemyDatastore((Student, Teacher), db_session)


And create a blueprint using this datastore object::

    admin_blueprint = admin.create_admin_blueprint(admin_datastore)
    app = Flask(__name__)
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

Now the admin interface is set up. If you are running the app with the
built-in development server via :meth:`app.run()`, then it should be
available at http://localhost:5000/admin .



Some notes on model classes
---------------------------

The __repr__ method of your model class will be used to describe
specific instances of your models models in things like the list
view. If you don't set it, the default __repr__ method will look
something like `<__main__.Student object at 0x1bb1490>`, which won't
be very useful for distinguishing model instances.


Also, your model classes must be able to be initialized without any
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

:meth:`url_for('admin.list', model_name='some_model')`
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

Using Flask blueprints makes customizing the admin interface
easy. Flask-Admin comes with a default set of templates and static
files. It's possible to customize as much of the interface as you'd
like by overriding the files you'd like to change. To do this, just
create your own version of the files in the templates and/or static
directories used by your Flask application.

The following templates are defined in Flask-Admin:

`admin/base.html` - This is the primary base template that defines the
bulk of the look and feel of the Admin. If you are using any of the
default admin view templates, the base templates should provide the
following blocks::

    ``title`` - The title of the page (in the html title element)
    ``main`` - This is where the main content of each of the admin
    views is placed (like editing forms)

`admin/extra_base.html` - This is the template that is actually
inheritted by the default admin view templates. By extending
base.html, this template allows you to override some of behaviors
provided in the `base.html` template (e.g. navigation) while
maintaining the most of base template behavior (like setting up
Javascript-enhanced UI elements).

`admin/index.html` - The template used by the ``admin.index`` view

`admin/list.html` - The template used by the ``admin.list`` view

`admin/add.html` - The template used by the ``admin.add`` view

`admin/edit.html` - The template used by the ``admin.edit`` view


In addition, the following "helper" templates are defined. These
define Jinja macros that are used for rendering things like the
pagination and forms:

`admin/_formhelpers.html`

`admin/_paginationhelpers.html`

`admin/_statichelpers.html`



Refer to the `Flask documentation on blueprints`_ for specifics on how
blueprints effect the template search path. There is also an example
of extending the default admin templates in the `view decorator
example`_.


Custom Forms
------------

Flask-Admin uses the WTForms library to automatically generate the
form that will be used to add a new instance of a model or edit an
existing model instance. There may be cases where the automatically
generated form isn't what you want, so you can also create a custom
form for Flask-Admin to use for a given model.

For example, consider the following model of a User that stores hashed
passwords (originally from http://flask.pocoo.org/snippets/54/)::

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
:func:`SQLAlchemyDatastore` to associate this form with the User
model::

    admin_blueprint = admin.datastore.SQLAlchemyDatastore(
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


Changelog
---------

0.3.0
  - added datastore API to support additional datastores more easily
  - added MongoAlchemy support
  - added composite primary key support
  - changed `admin.list_view` endpoint to `admin.list` for consistency

0.2.0
  - 

0.1.0
  - initial release


.. _example directory: https://github.com/wilsaj/flask-admin/tree/master/example
.. _Flask-SQLAlchemy: http://packages.python.org/Flask-SQLAlchemy/
.. _Flask documentation on blueprints: http://flask.pocoo.org/docs/blueprints/
.. _MongoAlchemy: http://www.mongoalchemy.org/
.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _view decorator example: https://github.com/wilsaj/flask-admin/tree/master/example/authentication/view_decorator.py
