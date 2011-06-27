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
    version='0.1',
    url='https://github.com/wilsaj/',
    license='BSD',
    author='Andy Wilson',
    author_email='wilson.andrew.j@gmail.com',
    description='Flask extenstion module that provides an admin interface',
    long_description=__doc__,
    packages=['flaskext'],
    namespace_packages=['flaskext'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask>=0.7dev',
        'Flask-SQLAlchemy>=0.12dev',
        'Flask-WTF',
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
