from flask import Flask,  redirect
from flaskext import themes
from sqlalchemy import create_engine, Table

app = Flask(__name__)

SQLALCHEMY_DATABASE_URI = 'sqlite:///declarative_example.db'
SECRET_KEY = 'not secure'

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
    teacher_id = Column(Integer, ForeignKey('teacher.id'), nullable=False)

    # teacher = relation()
    # students = relation()

    def __repr__(self):
        return self.name


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
admin_mod = Admin(sys.modules[__name__], admin_db_session=db_session,
                  exclude_pks=True)
app.register_module(admin_mod, url_prefix='/admin')

@app.route('/')
def go_to_admin():
    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True)
