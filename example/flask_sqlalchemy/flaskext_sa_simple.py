from flask import Flask,  redirect
from flask.ext import admin
from flask.ext.admin.datastore.sqlalchemy import SQLAlchemyDatastore
from flaskext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ----------------------------------------------------------------------
# Association tables
# ----------------------------------------------------------------------
course_student_association_table = db.Table(
    'course_student_association',
    db.Column('student_id', db.Integer, db.ForeignKey('student.id')),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id')))


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------
class Course(db.Model):
    __tablename__ = 'course'

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String)
    teacher_id = db.Column(db.Integer,
                           db.ForeignKey('teacher.id'), nullable=False)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)

    teacher = db.relationship('Teacher', backref='courses')
    students = db.relationship('Student',
                               secondary=course_student_association_table,
                               backref='courses')

    def __repr__(self):
        return self.subject


class Student(db.Model):
    __tablename__ = 'student'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)

    def __repr__(self):
        return self.name


class Teacher(db.Model):
    __tablename__ = 'teacher'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)

    def __repr__(self):
        return self.name


def create_app(database_uri='sqlite://'):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SECRET_KEY'] = 'not secure'
    db.init_app(app)
    datastore = SQLAlchemyDatastore(
        (Course, Student, Teacher), db.session)
    admin_blueprint = admin.create_admin_blueprint(datastore)
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    db.create_all(app=app)

    @app.route('/')
    def go_to_admin():
        return redirect('/admin')
    return app


if __name__ == '__main__':
    app = create_app('sqlite:///simple.db')
    app.run(debug=True)
