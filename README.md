flask-docjson
=============

Validate flask request and response json schemas via docstring.

```json
GET /user/<i32:id>
200
{"id": i32, "name": string(32)}
```

Example
-------

Please checkout [example.py](example.py).

Install
-------

```
pip install flask-docjson
```

License
-------
BSD.
