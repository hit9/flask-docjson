# -*- coding: utf-8 -*-

from flask import Flask, jsonify
import flask_docjson

app = Flask(__name__)


@app.errorhandler(flask_docjson.RequestValidationError)
def on_request_validation_error(err):
    return jsonify(message='Bad request'), 400

@app.errorhandler(flask_docjson.ResponseValidationError)
def on_response_validation_error(err):
    return jsonify(message='Bad response'), 500


@app.route('/item', methods=['POST', 'PUT'])
def create_item():
    """Schema::

        POST/PUT /item
        {
            "name": string(10),
            "number": i8
        }

        200
        {
            "id": i32,
            "name": string(10),
            "number": i8,
            "tags": [string, ...]
        }
        4XX/5XX
        {"message": string}
    """
    return jsonify(**{
        'id': 1,
        'name': 'example',
        'number': 9500,
        'tags': ['example-tag']
    })

flask_docjson.register_all(app)

if __name__ == '__main__':
    app.run()
