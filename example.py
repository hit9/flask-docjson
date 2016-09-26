# -*- coding: utf-8 -*-

from flask import Flask, jsonify
import flask_docjson

app = Flask(__name__)


@app.errorhandler(flask_docjson.RequestValidationError)
def on_request_validation_error(err):
    """Returns bad request on request validation errors.
    """
    print(err)
    return jsonify(message='Bad request'), 400


@app.errorhandler(flask_docjson.ResponseValidationError)
def on_response_validation_error(err):
    """Returns bad response on response validation errors.
    """
    return jsonify(message='Bad response'), 500


@app.route('/item', methods=['POST', 'PUT'])
def create_item():
    """Create an item.

    Schema::

        POST/PUT /item
        {
            "name": string(10),
            "number": i8
        }

        200
        {
            "id": i32,
            "name": string(10),
            "number": i8
        }
        4XX/5XX
        {"message": string}
    """
    return jsonify(id=1, name='name', number=123)


@app.route('/item/<int:id>', methods=['GET'])
def get_item(id):
    """Get an item by id.

    Schema::

        GET /item/<i32:id>

        200
        {
            "id": i32,
            "name": string(10),
            "number": i8
        }
        4XX/5XX
        {"message": string}
    """
    return jsonify(id=id, name='name', number=123)


@app.route('/item/<int:id>', methods=['DELETE'])
def delete_item(id):
    """Delete an item by id.

    Schema::

        DELETE /item/<i32:id>

        201
        4XX/5XX
        {"message": string}
    """
    return '', 201


@app.route('/items', methods=['GET'])
def get_items():
    """Get all items.

    Schema::

        GET /items

        200
        [
            {
                "id": i32,
                "name": string(10),
                "number": i8
            },
            ...
        ]
        4XX/5XX
        {"message": string}
    """
    items = [dict(id=1, name='name', number=123)]
    return jsonify(items)


# Must be called after all route definitions
flask_docjson.register_all(app)

if __name__ == '__main__':
    app.run()
