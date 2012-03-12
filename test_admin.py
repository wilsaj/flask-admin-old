from __future__ import with_statement

from datetime import datetime
import sys
import unittest

from flask import Flask
import sqlalchemy as sa

from flask.ext import admin
from flask.ext.testing import TestCase

sys.path.append('./example/')

from example.declarative import simple
from example.declarative import multiple
from example.authentication import view_decorator
from example.flask_sqlalchemy import flaskext_sa_simple
from example.flask_sqlalchemy import flaskext_sa_example
from example.flask_sqlalchemy import flaskext_sa_multi_pk
from example.mongoalchemy import simple as ma_simple
import test.custom_form
import test.deprecation
import test.filefield
import test.sqlalchemy_with_defaults
from test.mongoalchemy_datastore import ConversionTest


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
        app = test.custom_form.create_app('sqlite://')
        return app

    def test_custom_form(self):
        rv = self.client.get('/admin/add/User/')
        assert "User name" in rv.data
        assert "Change Password"  in rv.data
        assert "Confirm Password"  in rv.data
        assert "Is Active"  in rv.data
        assert "_password_hash" not in rv.data


class SQLAlchemyWithDefaultsTest(TestCase):
    TESTING = True

    def create_app(self):
        app = test.sqlalchemy_with_defaults.create_app('sqlite://')
        return app

    def test_defaults_work(self):
        rv = self.client.get('/admin/add/TestModel/')
        assert "2194112" in rv.data
        assert "128uasdn1uinvuio12ioj!!@Rfja" in rv.data
        assert "22341.29"  in rv.data


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


class FlaskSQLAlchemyMultiPKsTest(TestCase):
    TESTING = True

    def create_app(self):
        app = flaskext_sa_multi_pk.create_app('sqlite://')

        # set app.db_session to the db.session so the SimpleTest tests
        # will work
        app.db_session = flaskext_sa_multi_pk.db.session

        # need to grab a request context since we use db.init_app() in
        # our application
        with app.test_request_context():
            address = flaskext_sa_multi_pk.Address(
                shortname=u'K2',
                name=u'K-II',
                street=u'Hauptstrasse 1',
                zipcode='10000',
                city=u'Berlin',
                country=u'Germany')
            flaskext_sa_multi_pk.db.session.add(address)
            flaskext_sa_multi_pk.db.session.flush()
            location = flaskext_sa_multi_pk.Location(
                address_shortname=address.shortname,
                room=u'2.01',
                position=u'left side')
            flaskext_sa_multi_pk.db.session.add(location)
            flaskext_sa_multi_pk.db.session.flush()
            flaskext_sa_multi_pk.db.session.add(
                flaskext_sa_multi_pk.Asset(name=u'asset1',
                                           address_shortname=address.shortname,
                                           location_room=location.room,
                                           location_position=location.position))
            flaskext_sa_multi_pk.db.session.commit()
        return app

    def test_index(self):
        # just make sure the app is initialized and works
        rv = self.client.get('/admin/')
        self.assert_200(rv)

    def test_list_asset(self):
        rv = self.client.get('/admin/list/Asset/?page=1')
        self.assert_200(rv)

    def test_list_location(self):
        rv = self.client.get('/admin/list/Location/')
        self.assert_200(rv)

    def test_view_location(self):
        rv = self.client.get('/admin/edit/Location/K2/2.01/left%20side/')
        self.assert_200(rv)

    def test_add_location(self):
        self.assertEqual(self.app.db_session.query(
                flaskext_sa_multi_pk.Location).count(), 1)
        rv = self.client.post('/admin/add/Location/',
                              data=dict(address=u'K2',
                                        address_shortname=u'K2',
                                        room=u'2.03',
                                        position=u''))
        self.assertEqual(self.app.db_session.query(
                flaskext_sa_multi_pk.Location).count(), 2)
        rv = self.client.get('/admin/edit/Location/K2/2.03/%1A/')
        assert 'edit-form' in rv.data

    def test_edit_location(self):
        rv = self.client.post('/admin/edit/Location/K2/2.01/left%20side/',
                              data=dict(address=u'K2',
                                        address_shortname=u'K2',
                                        room=u'2.01',
                                        position='right side'))
        rv = self.client.get('/admin/edit/Location/K2/2.01/right%20side/')
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


class FileFieldTest(TestCase):
    TESTING = True

    def create_app(self):
        app = test.filefield.create_app('sqlite://')
        test_model = test.filefield.TestModel()
        app.db_session.add(test_model)
        app.db_session.commit()
        return app

    def test_file_field_enctype_rendered_on_add(self):
        rv = self.client.get('/admin/add/TestModel/')
        assert 'enctype="multipart/form-data"' in rv.data

    def test_file_field_enctype_rendered_on_edit(self):
        rv = self.client.get('/admin/edit/TestModel/1/')
        assert 'enctype="multipart/form-data"' in rv.data


class DeprecationTest(TestCase):
    """test that the old deprecated method of calling
    create_admin_blueprint still works
    """
    TESTING = True

    def create_app(self):
        app = test.deprecation.create_app('sqlite://')
        return app

    def test_index(self):
        rv = self.client.get('/admin/')
        self.assert_200(rv)


class MASimpleTest(TestCase):
    TESTING = True

    def create_app(self):
        app = ma_simple.create_app('masimple-test')
        # clear db of test objects first
        app.db_session.remove_query(ma_simple.Course).execute()
        app.db_session.remove_query(ma_simple.Teacher).execute()
        app.db_session.remove_query(ma_simple.Student).execute()
        app.db_session.insert(ma_simple.Course(
                subject="Maths",
                start_date=datetime(2011, 8, 12),
                end_date=datetime(2011,12,16)))
        app.db_session.insert(ma_simple.Student(name="Stewart"))
        app.db_session.insert(ma_simple.Student(name="Mike"))
        app.db_session.insert(ma_simple.Student(name="Jason"))
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
        course = self.app.db_session.query(ma_simple.Course).\
            filter(ma_simple.Course.subject == 'Maths').one()
        course_dict = dict([(key, str(getattr(course, key)))
                             for key in course.get_fields()])
        course_dict['end_date'] = "2012-05-31 00:00:00"
        rv = self.client.post('/admin/edit/Course/%s/' % course.mongo_id,
                              data=course_dict)
        new_course = self.app.db_session.query(ma_simple.Course).\
            filter(ma_simple.Course.subject == 'Maths').one()

        self.assertEqual(new_course.end_date, datetime(2012, 5, 31))
        self.assert_redirects(rv, '/admin/list/Course/')

    def test_add(self):
        self.assertEqual(self.app.db_session.query(ma_simple.Teacher).count(), 0)
        rv = self.client.post('/admin/add/Teacher/',
                              data=dict(name='Mr. Kohleffel'))
        self.assertEqual(self.app.db_session.query(ma_simple.Teacher).count(), 1)
        self.assert_redirects(rv, '/admin/list/Teacher/')

    def test_delete(self):
        student_query = self.app.db_session.query(ma_simple.Student)
        self.assertEqual(student_query.count(), 3)
        student = student_query.first()
        rv = self.client.get('/admin/delete/Student/%s/' % student.mongo_id)
        self.assertEqual(student_query.count(), 2)
        self.assert_redirects(rv, '/admin/list/Student/')

        rv = self.client.get('/admin/delete/Student/%s/' % student.mongo_id)
        self.assert_200(rv)
        assert "Student not found" in rv.data


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SimpleTest))
    suite.addTest(unittest.makeSuite(MultipleTest))
    suite.addTest(unittest.makeSuite(ViewDecoratorTest))
    suite.addTest(unittest.makeSuite(CustomFormTest))
    suite.addTest(unittest.makeSuite(FlaskSQLAlchemySimpleTest))
    suite.addTest(unittest.makeSuite(FlaskSQLAlchemyExampleTest))
    suite.addTest(unittest.makeSuite(FlaskSQLAlchemyMultiPKsTest))
    suite.addTest(unittest.makeSuite(SQLAlchemyWithDefaultsTest))
    suite.addTest(unittest.makeSuite(ExcludePKsTrueTest))
    suite.addTest(unittest.makeSuite(ExcludePKsFalseTest))
    suite.addTest(unittest.makeSuite(SmallPaginationTest))
    suite.addTest(unittest.makeSuite(LargePaginationTest))
    suite.addTest(unittest.makeSuite(FileFieldTest))
    suite.addTest(unittest.makeSuite(DeprecationTest))
    suite.addTest(unittest.makeSuite(ConversionTest))
    suite.addTest(unittest.makeSuite(MASimpleTest))
    return suite

if __name__ == '__main__':
    test_suite = suite()
    unittest.TextTestRunner(verbosity=2).run(test_suite)
