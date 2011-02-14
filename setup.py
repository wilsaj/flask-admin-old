"""
Flask-Admin
-----------

Description goes here...

Links
`````

* `documentation <http://packages.python.org/Flask-Admin>`_
* `development version
  <http://github.com/wilsaj/flask-admin/zipball/master#egg=Flask-Admin-dev>`_

"""
from setuptools import setup


setup(
    name='Flask-Admin',
    version='0.1',
    url='<enter URL here>',
    license='BSD',
    author='wilsaj',
    author_email='wilson.andrew.j+flaskadmin@gmail.com',
    description='Flask admin!',
    long_description=__doc__,
    packages=['flaskext'],
    namespace_packages=['flaskext'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask',
        'Flask-SQLAlchemy',
        'Flask-WTF',
        'webhelpers', # note: this should be replaced w/Flask-SQLAlchemy pagination
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
