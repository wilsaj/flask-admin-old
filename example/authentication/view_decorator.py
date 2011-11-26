from functools import wraps
import sys

from flask import Flask, g, redirect, render_template, request, session, url_for
from flask.ext import admin
from flask.ext.admin.datastore.sqlalchemy import SQLAlchemyDatastore
from sqlalchemy import create_engine, Table
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Text, String, Float, Time, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey

Base = declarative_base()

# ----------------------------------------------------------------------
# Association tables
# ----------------------------------------------------------------------
course_student_association_table = Table(
    'course_student_association',
    Base.metadata,
    Column('student_id', Integer, ForeignKey('student.id')),
    Column('course_id', Integer, ForeignKey('course.id')))


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------
class Course(Base):
    __tablename__ = 'course'

    id = Column(Integer, primary_key=True)
    subject = Column(String)
    teacher_id = Column(Integer, ForeignKey('teacher.id'), nullable=False)
    start_time = Column(Time)
    end_time = Column(Time)

    teacher = relationship('Teacher', backref='courses')
    students = relationship('Student',
                            secondary=course_student_association_table,
                            backref='courses')

    def __repr__(self):
        return self.subject


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


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def create_app(database_uri='sqlite://'):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'not secure'

    app.engine = create_engine(database_uri, convert_unicode=True)
    db_session = scoped_session(sessionmaker(
        autocommit=False, autoflush=False, bind=app.engine))
    datastore = SQLAlchemyDatastore(
        (Course, Student, Teacher), db_session)
    admin_blueprint = admin.create_admin_blueprint(
        datastore, view_decorator=login_required)

    @admin_blueprint.route('/login/', methods=('GET', 'POST'))
    def login():
        if request.form.get('username', None):
            session['user'] = request.form['username']
            return redirect(request.args.get('next', url_for('admin.index')))
        else:
            if request.method == 'POST':
                return render_template("login.html",
                                       bad_login=True)
            else:
                return render_template("login.html")

    @admin_blueprint.route('/logout/')
    def logout():
        del session['user']
        return redirect('/')

    @app.route('/')
    def go_to_admin():
        return redirect('/admin/')

    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    return app


if __name__ == '__main__':
    app = create_app('sqlite:///simple.db')
    Base.metadata.create_all(bind=app.engine)
    app.run(debug=True)
