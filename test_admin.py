import sys
import unittest

from flask import Flask
import sqlalchemy as sa

from flaskext import admin
from flaskext.testing import TestCase

sys.path.append('./example/')

from example.declarative import simple
from example.declarative import multiple
from example.declarative import custom_form
from example.authentication import view_decorator
from example.flask_sqlalchemy import flaskext_sa_simple
from example.flask_sqlalchemy import flaskext_sa_example


class SimpleTest(TestCase):
    TESTING = True

    def create_app(self):
        app = simple.create_app('sqlite://')
        teacher = simple.Teacher(name="Mrs. Jones")
        app.db_session.add(teacher)
        app.db_session.add(simple.Student(name="Stewart"))
        app.db_session.add(simple.Student(name="Mike"))
        app.db_session.add(simple.Student(name="Jason"))
        app.db_session.add(simple.Course(subject="maths", teacher=teacher))
        app.db_session.commit()
        return app

    def test_basic(self):
        rv = self.client.get('/')
        self.assert_redirects(rv, '/admin')

    def test_index(self):
        rv = self.client.get('/admin/')
        self.assert_200(rv)

    def test_list(self):
        rv = self.client.get('/admin/list/Student/?page=1')
        self.assert_200(rv)

    def test_edit(self):
        rv = self.client.post('/admin/edit/Course/1/',
                              data=dict(students=[1]))
        course = self.app.db_session.query(simple.Course).filter_by(id=1).one()
        self.assertEqual(len(course.students), 1)
        student = self.app.db_session.\
                  query(simple.Student).filter_by(id=1).one()
        self.assertEqual(len(student.courses), 1)
        self.assert_redirects(rv, '/admin/list/Course/')

    def test_add(self):
        self.assertEqual(self.app.db_session.query(simple.Teacher).count(), 1)
        rv = self.client.post('/admin/add/Teacher/',
                              data=dict(name='Mr. Kohleffel'))
        self.assertEqual(self.app.db_session.query(simple.Teacher).count(), 2)
        self.assert_redirects(rv, '/admin/list/Teacher/')

    def test_delete(self):
        self.assertEqual(self.app.db_session.query(simple.Student).count(), 3)
        rv = self.client.get('/admin/delete/Student/2/')
        self.assertEqual(self.app.db_session.query(simple.Student).count(), 2)
        self.assert_redirects(rv, '/admin/list/Student/')

        rv = self.client.get('/admin/delete/Student/2/')
        self.assert_200(rv)
        assert "Student not found" in rv.data


class MultipleTest(TestCase):
    TESTING = True

    def create_app(self):
        app = multiple.create_app('sqlite://')
        return app

    def test_admin1(self):
        rv = self.client.get('/admin1/')
        assert "Student" in rv.data
        assert "Course" not in rv.data

    def test_admin2(self):
        rv = self.client.get('/admin2/')
        assert "Student" not in rv.data
        assert "Course" in rv.data


class ViewDecoratorTest(TestCase):
    TESTING = True

    def create_app(self):
        self.app = view_decorator.create_app('sqlite://')
        return self.app

    def test_add_redirect(self):
        rv = self.client.get('/admin/add/Student/')
        self.assert_redirects(rv, "/admin/login/?next=http%3A%2F%2Flocalhost%2Fadmin%2Fadd%2FStudent%2F")

    def test_delete_redirect(self):
        rv = self.client.get('/admin/delete/Student/1/')
        self.assert_redirects(rv, "/admin/login/?next=http%3A%2F%2Flocalhost%2Fadmin%2Fdelete%2FStudent%2F1%2F")

    def test_edit_redirect(self):
        rv = self.client.get('/admin/edit/Student/1/')
        self.assert_redirects(rv, "/admin/login/?next=http%3A%2F%2Flocalhost%2Fadmin%2Fedit%2FStudent%2F1%2F")

    def test_index_redirect(self):
        rv = self.client.get('/admin/')
        self.assert_redirects(rv, "/admin/login/?next=http%3A%2F%2Flocalhost%2Fadmin%2F")

    def test_list_redirect(self):
        rv = self.client.get('/admin/list/Student/')
        self.assert_redirects(rv, "/admin/login/?next=http%3A%2F%2Flocalhost%2Fadmin%2Flist%2FStudent%2F")

    def test_login_logout(self):
        rv = self.client.post('/admin/login/',
                             data=dict(username='test',
                                       password='test'))
        self.assert_redirects(rv, '/admin/')

        rv = self.client.get('/admin/')
        self.assert200(rv)

        rv = self.client.get('/admin/logout/')
        self.assert_redirects(rv, '/')

        rv = self.client.get('/admin/')
        self.assert_redirects(rv, "/admin/login/?next=http%3A%2F%2Flocalhost%2Fadmin%2F")


class CustomFormTest(TestCase):
    TESTING = True

    def create_app(self):
        app = custom_form.create_app('sqlite://')
        return app

    def test_custom_form(self):
        rv = self.client.get('/admin/add/User/')
        assert "User name" in rv.data
        assert "Change Password"  in rv.data
        assert "Confirm Password"  in rv.data
        assert "Is Active"  in rv.data
        assert "_password_hash" not in rv.data


class FlaskSQLAlchemySimpleTest(SimpleTest):
    TESTING = True

    def create_app(self):
        app = flaskext_sa_simple.create_app('sqlite://')

        # set app.db_session to the db.session so the SimpleTest tests
        # will work
        app.db_session = flaskext_sa_simple.db.session

        # need to grab a request context since we use db.init_app() in
        # our application
        with app.test_request_context():
            teacher = flaskext_sa_simple.Teacher(name="Mrs. Jones")
            flaskext_sa_simple.db.session.add(teacher)
            flaskext_sa_simple.db.session.add(flaskext_sa_simple.Student(name="Stewart"))
            flaskext_sa_simple.db.session.add(flaskext_sa_simple.Student(name="Mike"))
            flaskext_sa_simple.db.session.add(flaskext_sa_simple.Student(name="Jason"))
            flaskext_sa_simple.db.session.add(flaskext_sa_simple.Course(subject="maths", teacher=teacher))
            flaskext_sa_simple.db.session.commit()
        return app


class FlaskSQLAlchemyExampleTest(TestCase):
    TESTING = True

    def create_app(self):
        app = flaskext_sa_example.create_app('sqlite://')
        return app

    def test_index(self):
        # just make sure the app is initialized and works
        rv = self.client.get('/admin/')
        self.assert_200(rv)


class ExcludePKsTrueTest(TestCase):
    TESTING = True

    def create_app(self):
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'not secure'
        engine = sa.create_engine('sqlite://', convert_unicode=True)
        app.db_session = sa.orm.scoped_session(sa.orm.sessionmaker(
            autocommit=False, autoflush=False,
            bind=engine))
        admin_blueprint = admin.create_admin_blueprint(
            (simple.Course, simple.Student, simple.Teacher),
            app.db_session, exclude_pks=True)
        app.register_blueprint(admin_blueprint, url_prefix='/admin')
        simple.Base.metadata.create_all(bind=engine)
        return app

    def test_exclude_pks(self):
        rv = self.client.get('/admin/add/Student/')
        assert "Id" not in rv.data


class ExcludePKsFalseTest(TestCase):
    TESTING = True

    def create_app(self):
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'not secure'
        engine = sa.create_engine('sqlite://', convert_unicode=True)
        app.db_session = sa.orm.scoped_session(sa.orm.sessionmaker(
            autocommit=False, autoflush=False,
            bind=engine))
        admin_blueprint = admin.create_admin_blueprint(
            (simple.Course, simple.Student, simple.Teacher),
            app.db_session, exclude_pks=False)
        app.register_blueprint(admin_blueprint, url_prefix='/admin')
        simple.Base.metadata.create_all(bind=engine)
        return app

    def test_exclude_pks(self):
        rv = self.client.get('/admin/add/Student/')
        assert "Id" in rv.data


class SmallPaginationTest(TestCase):
    TESTING = True

    def create_app(self):
        app = simple.create_app('sqlite://', pagination=25)
        for i in range(500):
            app.db_session.add(simple.Student(name="Student%s" % i))
        app.db_session.commit()
        return app

    def test_low_list_view_pagination(self):
        rv = self.client.get('/admin/list/Student/?page=1')
        assert '<a href="/admin/list/Student/?page=2">></a>' in rv.data


class LargePaginationTest(TestCase):
    TESTING = True

    def create_app(self):
        app = simple.create_app('sqlite://', pagination=1000)
        for i in range(50):
            app.db_session.add(simple.Student(name="Student%s" % i))
        app.db_session.commit()
        return app

    def test_high_list_view_pagination(self):
        rv = self.client.get('/admin/list/Student/')
        assert '<a href="/admin/list/Student/?page=2">></a>' not in rv.data


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SimpleTest))
    suite.addTest(unittest.makeSuite(MultipleTest))
    suite.addTest(unittest.makeSuite(ViewDecoratorTest))
    suite.addTest(unittest.makeSuite(CustomFormTest))
    suite.addTest(unittest.makeSuite(FlaskSQLAlchemySimpleTest))
    suite.addTest(unittest.makeSuite(FlaskSQLAlchemyExampleTest))
    suite.addTest(unittest.makeSuite(ExcludePKsTrueTest))
    suite.addTest(unittest.makeSuite(ExcludePKsFalseTest))
    suite.addTest(unittest.makeSuite(SmallPaginationTest))
    suite.addTest(unittest.makeSuite(LargePaginationTest))
    return suite


if __name__ == '__main__':
    unittest.main()
