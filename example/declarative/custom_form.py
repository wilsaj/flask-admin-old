import sys

from flask import Flask,  redirect
from flask.ext import admin
from flask.ext.admin.datastore.sqlalchemy import SQLAlchemyDatastore
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, Integer, Text, String, Float, Time
from sqlalchemy.orm import synonym
from werkzeug import check_password_hash, generate_password_hash
from wtforms import Form, validators
from wtforms.fields import BooleanField, TextField, PasswordField


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

    __mapper_args__ = {
        'order_by': username
        }


class UserForm(Form):
    """
    Form for creating or editting User object (via the admin). Define
    any handling of fields here. This form class also has precedence
    when rendering forms to a webpage, so the model-generated fields
    will come after it.
    """
    username = TextField(u'User name',
                         [validators.required(), validators.length(max=80)])
    password = PasswordField('Change Password',
                             [validators.optional(),
                              validators.equal_to('confirm_password')])
    confirm_password = PasswordField()
    is_active = BooleanField(default=True)


def create_app(database_uri='sqlite://'):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'not secure'
    engine = create_engine(database_uri, convert_unicode=True)
    db_session = scoped_session(sessionmaker(
        autocommit=False, autoflush=False,
        bind=engine))
    datastore = SQLAlchemyDatastore(
        (User,), db_session, model_forms={'User': UserForm})
    admin_blueprint = admin.create_admin_blueprint(
        datastore)
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    Base.metadata.create_all(bind=engine)

    @app.route('/')
    def go_to_admin():
        return redirect('/admin')

    return app


if __name__ == '__main__':
    app = create_app('sqlite:///simple.db')
    app.run(debug=True)
