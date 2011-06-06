import sys

from flask import Flask,  redirect
from flaskext import themes
from flaskext import admin
from sqlalchemy import create_engine, Table
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Text, String, Float, Time, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey

app = Flask(__name__)

SQLALCHEMY_DATABASE_URI = 'sqlite:///simple.db'
app.config['SECRET_KEY'] = 'not secure'

engine = create_engine(SQLALCHEMY_DATABASE_URI, convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False,
                                         bind=engine))
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
    # teacher = relation()
    # students = relation()

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


themes.setup_themes(app)
admin1 = admin.Admin(app, [Student, Teacher], db_session,
                        exclude_pks=True)
admin2 = admin.Admin(app, [Course], db_session,
                        exclude_pks=True)
app.register_module(admin1, url_prefix='/admin1')
app.register_module(admin2, url_prefix='/admin2')

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
    app.run(debug=True)
