Quick start
-----------

First create some SQLAlchemy declarative models using `SQLAlchemy`_ or
`Flask-SQLAlchemy`_. For example::

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


Then create a datastore object using those models and your sqlalchemy
session::

    from flask.ext import admin
    from sqlalchemy.orm import scoped_session, sessionmaker

    db_session = scoped_session(sessionmaker(
        autocommit=False, autoflush=False,
        bind=engine))

    admin_datastore = admin.datastore.SQLAlchemyDatastore(
        (Student, Teacher), db_session)


The first argument to :func:`SQLAlchemyDatastore()` can have two
forms: it can either be some python iterable like a list or tuple, or
it can be a python module that contains your models. The second
argument is the SQLAlchemy session that will be used to access the
database. By default, Flask-Admin will not expose the primary keys of
your models. This is usually a good idea if you are using a primary
key that doesn't have any meaning outside of the database, like an
auto-incrementing integer, because changing a primary key changes the
nature of foreign key relationships. If you want to expose the primary
key, set ``exclude_pks=False`` when instantiating your
:func:`SQLAlchemyDatastore()`.


Then create a blueprint using this datastore object and register this
blueprint on your Flask app::

    admin_blueprint = admin.create_admin_blueprint(admin_datastore)
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




.. _Flask-SQLAlchemy: http://packages.python.org/Flask-SQLAlchemy/
.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _example directory: https://github.com/wilsaj/flask-admin/tree/master/example

