# -*- coding: utf-8 -*-

'''
Flask-DocJSON
-------------

Validate flask request and response json schemas via docstring.


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
    description='Validate flask request and response json schemas via '
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
