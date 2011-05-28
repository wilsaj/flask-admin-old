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


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True)
    _password_hash = Column('password', String(80), nullable=False)
    is_active = Column(Boolean, default=True)

    #constructor
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


class UserFormBase(Form):
    """
    Form for creating or editting User object (via the admin). Define
    any handling of fields here. This form class also has precedence
    when rendering forms to a webpage, so the model-generated fields
    will come after it.
    """
    username = TextField(u'User name', [validators.required(),
                                        validators.length(max=80)])
    password = PasswordField('', [validators.optional(),
                                  validators.equal_to('confirm_password')])
    confirm_password = PasswordField()


class UserForm(UserFormBase, admin.model_form(User, exclude=['id'], converter=admin.AdminConverter())):
    """
    User form, as a mixin of UserFormBase and the form generated from
    the User SQLAlchemy model
    """
    pass


themes.setup_themes(app)
admin_mod = admin.Admin(sys.modules[__name__], admin_db_session=db_session,
                        model_forms={'User': UserForm}, exclude_pks=True)
app.register_module(admin_mod, url_prefix='/admin')


@app.route('/')
def go_to_admin():
    return redirect('/admin')

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
    app.run(debug=True)
