import sys

from flask import Flask
from flaskext.sqlalchemy import SQLAlchemy
from flaskext import themes
from flaskext.admin import Admin

from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask_sqlalchemy_example.db'
app.config['SECRET_KEY'] = 'seeeeecret'
db = SQLAlchemy(app)


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

db.create_all()


themes.setup_themes(app)
admin_mod = Admin(app, (User, Post, Category),
                  db.session, exclude_pks=True)
app.register_module(admin_mod, url_prefix='/admin')

if __name__ == '__main__':
    app.run(debug=True)
