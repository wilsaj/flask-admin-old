import sys

from flask import Flask,  redirect
from flask.ext import admin
from flask.ext.admin.datastore.sqlalchemy import SQLAlchemyDatastore
from sqlalchemy import create_engine, Table
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Time
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey


Base = declarative_base()


class Student(Base):
    __tablename__ = 'student'

    student_id = Column(Integer, primary_key=True)
    name = Column(String(120), primary_key=True)

    def __repr__(self):
        return self.name


class Teacher(Base):
    __tablename__ = 'teacher'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True)

    def __repr__(self):
        return self.name


def create_app(database_uri='sqlite://', pagination=25):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'not secure'
    engine = create_engine(database_uri, convert_unicode=True)
    app.db_session = scoped_session(sessionmaker(
        autocommit=False, autoflush=False,
        bind=engine))
    datastore = SQLAlchemyDatastore(
        (Student, Teacher), app.db_session, exclude_pks=False)
    admin_blueprint = admin.create_admin_blueprint(
        datastore, list_view_pagination=pagination)
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    Base.metadata.create_all(bind=engine)

    @app.route('/')
    def go_to_admin():
        return redirect('/admin')

    return app


if __name__ == '__main__':
    app = create_app('sqlite:///composite.db')
    app.run(debug=True)
