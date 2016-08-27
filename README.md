flask-docjson
=============

A micro flask extension to validate json schemas via docstring.

Example
-------

```python
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
```

License
-------

BSD.
