import sys
import unittest

from flaskext.testing import TestCase

class SimpleTest(TestCase):
    TESTING = True

    def create_app(self):
        sys.path.append('./example/declarative/')
        import simple
        app = simple.create_app('sqlite://')
        teacher = simple.Teacher(name="Mrs. Jones")
        student = simple.Student(name="Forbes Minor")
        app.db_session.add(teacher)
        app.db_session.add(student)
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
        rv = self.client.get('/admin/edit/Course/1/')
        self.assert_200(rv)

    def test_add(self):
        rv = self.client.get('/admin/add/Course/')
        self.assert_200(rv)

    def test_delete(self):
        rv = self.client.get('/admin/delete/Course/1/')
        self.assert_redirects(rv, '/admin/list/Course/')

        rv = self.client.get('/admin/delete/Course/1/')
        self.assert_200(rv)


if __name__ == '__main__':
    unittest.main()
