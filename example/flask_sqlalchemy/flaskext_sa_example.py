from flask import Flask, redirect
from flask.ext import admin
from flask.ext.admin.datastore.sqlalchemy import SQLAlchemyDatastore
from flaskext.sqlalchemy import SQLAlchemy

from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

    def __init__(self, username=None, email=None):
        self.username = username
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.username


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    body = db.Column(db.Text)
    pub_date = db.Column(db.DateTime)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category',
        backref=db.backref('posts', lazy='dynamic'))

    def __init__(self, title=None, body=None, category=None, pub_date=None):
        self.title = title
        self.body = body
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date
        self.category = category

    def __repr__(self):
        return '<Post %r>' % self.title


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    def __init__(self, name=None):
        self.name = name

    def __repr__(self):
        return '<Category %r>' % self.name


def create_app(database_uri='sqlite://'):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SECRET_KEY'] = 'seeeeecret'

    db.init_app(app)
    datastore = SQLAlchemyDatastore(
        (User, Post, Category), db.session)
    admin_blueprint = admin.create_admin_blueprint(datastore)
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    db.create_all(app=app)

    @app.route('/')
    def go_to_admin():
        return redirect('/admin')
    return app

if __name__ == '__main__':
    app = create_app('sqlite:///flask_sqlalchemy_example.db')
    app.run(debug=True)
