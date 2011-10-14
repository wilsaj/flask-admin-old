"""
Flask-Admin
-----------

Flask-Admin is a Flask extension module that aims to be a flexible,
customizable web-based interface to your datastore.

Links
`````

* `documentation <http://packages.python.org/Flask-Admin>`_
* `development version
  <http://github.com/wilsaj/flask-admin/zipball/master#egg=Flask-Admin-dev>`_

"""
from setuptools import setup


setup(
    name='Flask-Admin',
    version='0.2.0',
    url='https://github.com/wilsaj/flask-admin/',
    license='BSD',
    author='Andy Wilson',
    author_email='wilson.andrew.j@gmail.com',
    description='Flask extenstion module that provides an admin interface',
    long_description=__doc__,
    packages=['flask_admin'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask>=0.7',
        'Flask-WTF',
        'Flask-SQLAlchemy',
    ],
    test_suite='test_admin.suite',
    tests_require=[
        'Flask-SQLAlchemy>=0.12',
        'Flask-Testing',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
