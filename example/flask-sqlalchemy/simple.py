import sys

from flask import Flask,  redirect
from flaskext.sqlalchemy import SQLAlchemy
from flaskext import themes
from flaskext import admin

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask_sqlalchemy_example2.db'
app.config['SECRET_KEY'] = 'not secure'
db = SQLAlchemy(app)

# ----------------------------------------------------------------------
# Association tables
# ----------------------------------------------------------------------
course_student_association_table = db.Table(
    'course_student_association_table',
    db.Column('student_id', db.Integer, db.ForeignKey('student.id')),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id')))


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------
class Course(db.Model):
    __tablename__ = 'course'

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)

    teacher = db.relationship('Teacher', backref='courses')
    students = db.relationship('Student',
                            secondary=course_student_association_table,
                            backref='courses')
    # teacher = relation()
    # students = relation()

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

db.create_all()

themes.setup_themes(app)
admin_mod = admin.Admin(app, (Course, Student, Teacher),
                        db_session=db.session,
                        exclude_pks=True)
app.register_module(admin_mod, url_prefix='/admin')


@app.route('/')
def go_to_admin():
    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True)
