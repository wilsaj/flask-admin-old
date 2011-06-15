import sys
import unittest

from flaskext.testing import TestCase

sys.path.append('./example/declarative/')
import simple
import multiple


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
        student = self.app.db_session.query(simple.Student).filter_by(id=1).one()
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



if __name__ == '__main__':
    unittest.main()
