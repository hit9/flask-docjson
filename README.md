flask-docjson
=============

A micro module to validate flask request and response json schemas via
view function docstrings.

```python
@app.route('/item/<id>', methods=['GET'])
@flask_docjson.validate
def get(id):
    """Get an item by id.

    Schema::

        GET /item/<i32:id>

        200
        {
            "id": i32,
            "name": string(32),
            "tags": [string, ...]
        }
    """
    pass
```

It's **strongly recommended** that you checkout [example](example.py) at first.

Installation
------------

```
pip install flask-docjson
```

Usage
-----

* Validate routes selectively via decorator:

   ```python
   @app.route('/user/<int:id>', methods=['GET'])
   @flask_docjson.validate
   def get_user(id):
       """Schema::
           ...
       """
   ```

* Validate all routes, no need to decorate view functions one by one:

   ```python
   # Must be called after all route definitions
   flask_docjson.register_all(app)
   ```

Schema
------

The validator only works when:

1. Given docstring contains a marker `Schema::` or `Schema:`.
2. The marker is followed by a code block.

Here is an example schema:

```
Schema::

    POST/PUT /user
    {
        "name": string,
        "email": string,
        "class_no": i8
    }

    200
    {
        "id": i32,
        ...
    }
    4XX/5XX
    {"error": string}
```

A flask-docjson schema should contain one `request` and multiple `responses`
descriptions, its structure:

```
Schema::

    <Methods> <Route>
    <Request-JSON-Schema>

    <StatusCode>
    <Response-JSON-Schema>
    ...
```

The first json schema is for request, and the following json schemas are for
responses.

`Methods` contains a single or multiple http methods, e.g. `DELETE`, `POST/PUT`
, all method names should in upper case. Supported method names are:

   * `POST`
   * `GET`
   * `PUT`
   * `DELETE`
   * `PATCH`
   * `HEAD`
   * `OPTIONS`

`Route` is a flask url rule, but supports stricter variable types. e.g.
`/user/<i32:id>`, `/name/<string(32):name>`. Note that these types are
validators but not converters. We still need to use flask built-in converters:

```python
@app.route("/<int:id>", methods=['GET'])  # OK
# @app.route("/<id>", methods=['GET'])  # BAD
def get(id):
    """Schema::

        GET /<i32:id>
        200
     """
```
 
`JSON-Schema` has json like structure, it may be an array of type definitions,
or an object of key-type pairs. And both `array` and `object` are also types.
Some examples:

   * `[u8, u16, u32]` (array of base types)
   * `{"text": string(255), "id": i32}` (object of base types)
   * `[{"key": i16}, ...]` (array of objects)
   * `{"key": [u32, ...]}` (object with array values)
   * `[u32, ...]` (also called [ellipsis array](#ellipsis-array))
   * `{"id": i32, ...}` (also called [ellipsis object](#ellipsis-object))

`StatusCode` contains a single or multiple status codes, e.g. `204/200`.
What's more, status code matcher like `4XX`, `5XX` are also supported.

In standard JSON, schema with a trailing comma (e.g. `{"key": "value",}`) is 
illegal, but our JSON schema allows this. Because that makes modifications by 
line convenient.

Base Types
----------

* Boolean: `bool`
* Number: `u8`, `u16`, `u32`, `u64`, `i8`, `i16`, `i32`, `i64`, `float`
* String: `string`, `string(maxlength)` (e.g. `string(32)`)

Container Types
---------------

* Array: e.g. `[u8, i32, string]`, `[u8, ...]`. 
* Object: e.g. `{"name": string(32)}`, `{"id": i32, ...}`.

Ellipsis Array
--------------

An array definition with ellipsis is called "ellipsis array", for an example:

```
{
    "item": [u8, ...]
}
```

1. Empty list (aka `[]`) is able to pass ellipsis array validation.
2. For this example, all elements in given `items` should be an `u8`.

Ellipsis Object
---------------

An object definition with ellipsis is called "ellipsis object", for an example:

```
{
    "id": i32,
    ...
}
```

1. An ellipsis object indicates given object value may contain more fields,
   but docjson won't (also can't) validate them.
2. For a non-ellipsis object definition, given object value shouldn't contain
   any keys that dosen't exist in the type definition.

Nullable Value
--------------

By default, values shouldn't be nullable and `None` value causes validation
error. An example to change this behavior is:

```
{
    "optional-string": string(32)*,
    "optional-integer": i32*
}
```

And, nullable values are optional in objects, `key not exists` error won't throw.

But note that `*` can't be used with the whole request/response json schema, that
is to say schemas like the following definition are illegal:

```
GET /

200
{
    "name": string
}*
```

No Content
----------

Some requests or responses have no content, we just leave the json schema blank:

* Request schema without content example:

   ```
   GET /data
   200
   {"key": float}
   ```

* Response schema without content example:

   ```
   DELETE /data/<i32:id>
   204
   ```

Comments
--------

We may want to comment on some json fields:

```
PUT /order
{
    "price": float, // precision:10, scale:2
}

200
{
    "id": i32,
     ...
}
```

Exceptions
----------

* `flask_docjson.Error`: Raised when a flask-docjson error occurred.
* `flask_docjson.ParserError`: Raised when a parser error occurred.
* `flask_docjson.LexerError`: Raised when a lexer error (e.g. bad token) occurred.
* `flask_docjson.GrammarError`: Raised when a grammar error occurred.
* `flask_docjson.ValidationError`: Raised when some request or response data is invalid.
* `flask_docjson.RequestValidationError`: Raised some when request data is invalid.
* `flask_docjson.ResponseValidationError`: Raised some when response data is invalid.

`Error` is the base exception. `ParserError` only occurrs on flask app bootstrap, it
won't be raised during processing requests.

`ValidationError` should be catched manually, we recommend to use the
flask built-in decorator `app.errorhandler`. And we can also get `code`,
`reason` and related `value` from a `ValidationError` instance:

```python
@app.errorhandler(flask_docjson.ValidationError)
def on_validatino_error(err):
    return jsonify(message='Validation error:{0} {1} on {2}'.format(err.code, err.reason, err.value)), 400
```

Language Description
--------------------

* Document: `Schema ::= Request Response*`.
* Request: `Request ::= Method* Route JsonSchema`
* Response: `Response ::= StatusCode* JsonSchema`
* Method: `Method ::= POST|PUT|GET|DELETE|PATCH|HEAD|OPTIONS`. Method separator is `/`.
* Route: `Route ::= StaticRoute* RouteVar* StaticRoute*`. e.g. `/user/<i32:id>`
* StatusCode: `StatusCode ::= Integer|Matcher`. e.g. `200`, `4XX`
* JsonSchema: `JsonSchema ::= Array | Object`.
* Array: `Array ::= '[' Value* | Value* '...' ']'`
* Object: `Object ::= '{' KeyValue* '}'`
* KeyValue: `KeyValue ::= Key ':' Value`
* Value: `Array ::= BaseType | Array | Object`

License
-------
BSD.
