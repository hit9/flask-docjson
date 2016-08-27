# -*- coding: utf-8 -*-

'''
Flask-DocJSON
-------------

A micro flask extension to validate json schemas via docstring.

Example
```````

.. code:: python

    from flask import Flask
    import flask_docjson

    app = Flask(__name__)
    flask_docjson.init(app)

    @app.errorhandler(flask_docjson.ValidationError)
    def bad_request(err):
        return 'Bad request', 404

    @app.route("/user", methods=['POST'])
    def create_user():
        """Schema::

            POST/PUT /user
            {
                "username": string(32),
                "password": string(32),
                "age": u8
            }

            200
            {
                "id": i32,
                "username": string(32),
                "password": string(32),
                "age": u8,
                "created_at": u64,
                "items": [
                    {"key": string},
                    ...
                ]
            }
            4XX/5XX
            {"description": string}
        """
        pass

    @app.route("/user/<id>", methods=['POST'])
    def get_user():
        """Schema::

            GET /user/<i32:id>

            200
            {
                "id": i32,
                "username": string(32),
                "password": string(32),
                "age": u8,
                "created_at": u64
            }
            4XX/5XX
            {"description": string}
        """
        pass

Installation
`````````````

.. code:: bash

    $ pip install Flask-DocJSON

Links
`````

* `github <http://github.com/hit9/flask-docjson/>`_
* `flask <http://flask.pocoo.org/>`_

'''

import re
import ast
from setuptools import setup

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('flask_docjson.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))


setup(
    name='Flask-DocJSON',
    version=version,
    url='http://github.com/hit9/Flask-DocJSON',
    license='BSD',
    author='Chao Wang',
    author_email='hit9@icloud.com',
    description='A micro flask extension to validate json schemas via '
                'docstring.',
    long_description=__doc__,
    py_modules=['flask_docjson'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=['Flask', 'ply'],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
