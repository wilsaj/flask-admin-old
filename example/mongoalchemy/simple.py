import sys

from flask import Flask,  redirect
from flask.ext import admin
from mongoalchemy.document import Document
from mongoalchemy import fields, session
from wtforms import fields as wtfields
from wtforms import Form


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------
class Course(Document):
    subject = fields.StringField()

    def __repr__(self):
        return self.subject


# class Student(Base):
#     name = fields.StringField()

#     def __repr__(self):
#         return self.name


# class Teacher(Base):
#     name = fields.StringField()

#     def __repr__(self):
#         return self.name


# ----------------------------------------------------------------------
# Forms
# ----------------------------------------------------------------------
class CourseForm(Form):
    subject = wtfields.TextField(u'Subject')


def create_app(database_uri='sqlite://', pagination=25):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'not secure'
    app.db_session = session.Session.connect('simple-example')
    datastore = admin.datastore.MongoAlchemyDatastore(
        (Course,), app.db_session, model_forms={'Course': CourseForm})
    admin_blueprint = admin.create_admin_blueprint(
        datastore, list_view_pagination=pagination)
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    @app.route('/')
    def go_to_admin():
        return redirect('/admin')

    return app


if __name__ == '__main__':
    app = create_app('sqlite:///simple.db')
    app.run(debug=True)
