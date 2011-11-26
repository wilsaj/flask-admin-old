import sys

from flask import Flask,  redirect
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


def create_app(database_uri='sqlite://'):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'not secure'

    app.engine = create_engine(database_uri, convert_unicode=True)
    app.db_session = scoped_session(sessionmaker(
        autocommit=False, autoflush=False, bind=app.engine))
    datastore1 = SQLAlchemyDatastore(
        (Student, Teacher), app.db_session)
    admin_blueprint1 = admin.create_admin_blueprint(
        datastore1, name='admin1')
    datastore2 = SQLAlchemyDatastore(
        (Course,), app.db_session)
    admin_blueprint2 = admin.create_admin_blueprint(
        datastore2, name='admin2')
    app.register_blueprint(admin_blueprint1, url_prefix='/admin1')
    app.register_blueprint(admin_blueprint2, url_prefix='/admin2')
    Base.metadata.create_all(bind=app.engine)
    return app


if __name__ == '__main__':
    app = create_app('sqlite:///simple.db')
    app.run(debug=True)
