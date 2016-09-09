# -*- coding: utf-8 -*-

import unittest
import flask_docjson as m
from flask import Response


class TestParser(unittest.TestCase):

    def test_simple(self):
        """Schema::

            POST/PUT /item
            {
                "name": string,
                "number": i16,
                "children": [
                    {"id": i32},
                    ...
                ]
            }

            200
            {
                "id": i32,
                "name": string,
                "number": i16,
                "children": [
                    {"id": i32},
                    ...
                ]
            }
            4XX/5XX
            {"message": string}
        """
        schema = m.parse(self.test_simple.__doc__)
        assert schema == {
            'request': {
                'route': ['/item', {}],
                'methods': [m.M_POST, m.M_PUT],
                'schema': {
                    'name': ((m.T_STRING, None), False),
                    'number': (m.T_I16, False),
                    'children': ([({'id': (m.T_I32, False)}, False),
                                  m.S_ELLIPSIS], False)
                },
            },
            'responses': [
                {'status_code': [200],
                 'schema': {
                     'id': (m.T_I32, False),
                     'name': ((m.T_STRING, None), False),
                     'number': (m.T_I16, False),
                     'children': ([({'id': (m.T_I32, False)}, False),
                                   m.S_ELLIPSIS], False)
                 }},
                {'status_code': ['4XX', '5XX'],
                 'schema': {'message': ((m.T_STRING, None), False)}}
            ]
        }

    def test_empty(self):
        assert m.parse(None) is None
        assert m.parse('test') is None

    def test_string_escape(self):
        """Schema::

            POST /user
            {"specialkey\\"\\t\\r": i8}
            200/4XX/5XX
        """
        schema = m.parse(self.test_string_escape.__doc__)
        assert schema['request']['schema'] == {
            'specialkey"\t\r': (m.T_I8, False),
        }

    def test_no_content(self):
        """Schema::
            GET /user/<i32:id>
            201
        """
        schema = m.parse(self.test_no_content.__doc__)
        assert schema == {
            'request': {
                'route': ['/user/<id>', {'id': m.T_I32}],
                'methods': [m.M_GET],
                'schema': None,
            },
            'responses': [{'status_code': [201], 'schema': None}]
        }

    def test_alternative_schema_sign(self):
        """Schema:

            GET /user/<i32:id>

            200
            {
                "id": i32,
                "name": string(33)
            }
        """
        schema = m.parse(self.test_alternative_schema_sign.__doc__)
        assert schema == {
            'request': {
                'route': ['/user/<id>', {'id': m.T_I32}],
                'methods': [m.M_GET],
                'schema': None,
            },
            'responses': [
                {'status_code': [200],
                 'schema': {'id': (m.T_I32, False), 'name': ((m.T_STRING, 33),
                                                             False)}}
            ],
        }

    def test_schema_array(self):
        """Schema:
            GET /users
            200
            [
                {"id": i32, "name": string(32)},
                ...
            ]
        """
        schema = m.parse(self.test_schema_array.__doc__)
        assert schema == {
            'request': {
                'route': ['/users', {}],
                'methods': [m.M_GET],
                'schema': None,
            },
            'responses': [
                {'status_code': [200],
                 'schema': [({'id': (m.T_I32, False), 'name': (
                     (m.T_STRING, 32),
                     False)}, False), m.S_ELLIPSIS]}
            ]
        }

    def test_bad_status_code_matcher(self):
        """Schema::
            GET /users
            x00
            [
                {"id": i32, "name": string(32)},
                ...
            ]
        """
        with self.assertRaises(m._InternalGrammarError):
            m.parse(self.test_bad_status_code_matcher.__doc__)

    def test_nullable_schema(self):
        """Schema::
            GET /users
            {"name": string(33)*}
            201
        """
        schema = m.parse(self.test_nullable_schema.__doc__)
        assert schema == {
            'request': {
                'methods': [m.M_GET],
                'route': ['/users', {}],
                'schema': {
                    'name': ((m.T_STRING, 33), True)
                }
            },
            'responses': [
                {
                    'status_code': [201],
                    'schema': None
                }
            ]
        }

    def test_empty_response(self):
        """Schema::

            DELETE /user/<i32:id>
            201
            4XX/5XX
            {"error": string}
        """
        schema = m.parse(self.test_empty_response.__doc__)
        assert schema == {'request': {'methods': [4],
                                      'route': ['/user/<id>', {'id': 8}],
                                      'schema': None},
                          'responses': [{'schema': None, 'status_code': [201]},
                                        {'schema': {'error': ((11, None),
                                                              False)},
                                         'status_code': ['4XX', '5XX']}]}


class TestValidation(unittest.TestCase):

    def test_validate_bool(self):
        assert m.validate_bool(True, None) is None
        with self.assertRaises(m.ValidationError) as exc:
            m.validate_bool(1, None)
        assert exc.exception.code == m.ErrInvalidBool[0]

    def test_validate_u8(self):
        assert m.validate_u8(199, None) is None
        with self.assertRaises(m.ValidationError) as exc:
            m.validate_u8(1999, None)
        assert exc.exception.code == m.ErrInvalidU8[0]

    def test_validate_u16(self):
        assert m.validate_u16(65535, None) is None
        with self.assertRaises(m.ValidationError) as exc:
            m.validate_u16(65535*2, None)
        assert exc.exception.code == m.ErrInvalidU16[0]

    def test_validate_u32(self):
        assert m.validate_u32(4294967295, None) is None
        with self.assertRaises(m.ValidationError) as exc:
            m.validate_u32(4294967296, None)
        assert exc.exception.code == m.ErrInvalidU32[0]

    def test_validate_u64(self):
        assert m.validate_u64(0xffffffffffffffff, None) is None
        with self.assertRaises(m.ValidationError) as exc:
            m.validate_u64(0xffffffffffffffff + 1, None)
        assert exc.exception.code == m.ErrInvalidU64[0]

    def test_validate_float(self):
        assert m.validate_float(0.1, None) is None
        assert m.validate_float(1, None) is None
        with self.assertRaises(m.ValidationError) as exc:
            m.validate_float('1', None)
        assert exc.exception.code == m.ErrInvalidFloat[0]

    def test_validate_string(self):
        assert m.validate_string('test', (m.T_STRING, None), None) is None
        assert m.validate_string('test', (m.T_STRING, 4), None) is None
        assert m.validate_string(u'unicode', (m.T_STRING, None), None) is None
        with self.assertRaises(m.ValidationError) as exc:
            m.validate_string(1, (m.T_STRING, None), None)
        assert exc.exception.code == m.ErrInvalidString[0]
        with self.assertRaises(m.ValidationError) as exc:
            m.validate_string("test", (m.T_STRING, 3), None)
        assert exc.exception.code == m.ErrInvalidString[0]

    def test_validate_type(self):
        assert m.validate_type(18, m.T_I8, None) is None
        with self.assertRaises(m.ValidationError) as exc:
            m.validate_type(1888, m.T_I8, None)
        assert exc.exception.code == m.ErrInvalidI8[0]
        with self.assertRaises(m.ValidationError) as exc:
            m.validate_type(19, (m.T_STRING, 31), None)
        assert exc.exception.code == m.ErrInvalidString[0]
        assert m.validate_type('abc', (m.T_STRING, 3), None) is None

    def test_validate_array_case_simple_1(self):
        val_ok = [1, 2, 3, 4, 5]
        val_bad = [1, 2, 3, 4, 256]
        typ = [(m.T_U8, False), m.S_ELLIPSIS]
        assert m.validate_array(val_ok, typ, None) is None
        with self.assertRaises(m.ValidationError) as exc:
            m.validate_array(val_bad, typ, None)
        assert exc.exception.code == m.ErrInvalidU8[0]

    def test_validate_array_case_simple_2(self):
        val_ok = ["abc", "efg", "hij"]
        val_bad = ["abc", "efg", "hijopq"]
        typ = [((m.T_STRING, 3), False), m.S_ELLIPSIS]
        assert m.validate_array(val_ok, typ, None) is None
        with self.assertRaises(m.ValidationError):
            m.validate_array(val_bad, typ, None)

    def test_validate_array_complex_1(self):
        val_ok = [1, 256, 3, 255]
        val_bad = [1, 256, 3, 256]
        typ = [(m.T_U8, False), (m.T_U32, False), (m.T_U8, False),
               m.S_ELLIPSIS]
        assert m.validate_array(val_ok, typ, None) is None
        with self.assertRaises(m.ValidationError):
            m.validate_array(val_bad, typ, None)

    def test_validate_array_complex_2(self):
        val_ok = [{"name": 'jack', "id": 32},
                  {"name": 'chao', "id": 33},
                  {"name": 'ming', "id": 34},
                  ]
        val_bad = [{"name": 'jack', "id": 32},
                   {"name": 'chao-wang', "id": 33},
                   {"name": 'ming', "id": 34},
                   ]
        typ = [({"name": ((m.T_STRING, 4), False), "id": (m.T_I32, False)},
                False),
               m.S_ELLIPSIS]
        assert m.validate_array(val_ok, typ, None) is None
        with self.assertRaises(m.ValidationError):
            m.validate_array(val_bad, typ, None)

    def test_validate_array_no_ellipsis(self):
        val_ok = [{"name": 'jack', "id": 32},
                  {"name": 'chao', "id": 33}]
        val_bad = [{"name": 'jack', "id": 32},
                   {"name": 'chao', "id": 33},
                   {"name": 'ming', "id": 34},
                   ]
        typ = [({"name": ((m.T_STRING, 4), False), "id": (m.T_I32, False)},
                False),
               ({"name": ((m.T_STRING, 4), False), "id": (m.T_I32, False)},
                False)]
        assert m.validate_array(val_ok, typ, None) is None
        with self.assertRaises(m.ValidationError):
            m.validate_array(val_bad, typ, None)

    def test_validate_array_nested(self):
        val_ok = [{"child": [15, 16, 17]}, {"child": [25, 26, 37]}]
        val_bad = [{"child": [15, 16, 17]}, {"child": [25, 266, 37]}]
        typ = [({"child": ([(m.T_U8, False), m.S_ELLIPSIS], False)}, False),
               m.S_ELLIPSIS]
        assert m.validate_array(val_ok, typ, None) is None
        with self.assertRaises(m.ValidationError):
            m.validate_array(val_bad, typ, None)

    def test_validate_array_ellipsis_empty_val_1(self):
        val = []
        typ = [(m.T_U8, False), m.S_ELLIPSIS]
        assert m.validate_array(val, typ, None) is None

    def test_validate_array_ellipsis_empty_val_2(self):
        val = [1]
        typ = [(m.T_U8, False), (m.T_U8, False), m.S_ELLIPSIS]
        assert m.validate_array(val, typ, None) is None

    def test_validate_object(self):
        val_ok = {"name": "abcd", "id": 1}
        val_bad = {"name": "abcdefg", "id": 111111111}
        typ = {"name": ((m.T_STRING, 4), False), "id": (m.T_I32, False)}
        assert m.validate_object(val_ok, typ, None) is None
        with self.assertRaises(m.ValidationError):
            m.validate_object(val_bad, typ, None)

    def test_validate_object_nested(self):
        val_ok = {"name": {"name": {"name": "hello world"}}}
        val_bad = {"name": {"name": {"name": "hello world!"}}}
        typ = {"name": ({"name": ({"name": ((m.T_STRING, 11), False)}, False)},
                        False)}
        assert m.validate_object(val_ok, typ, None) is None
        with self.assertRaises(m.ValidationError):
            m.validate_object(val_bad, typ, None)

    def test_validate_object_not_exist_keys_1(self):
        val_ok = {"name": "name", "value": "value"}
        val_bad = {"name": "name"}
        val_bad2 = {"name": "name", "value": "value", "value2": "value2"}
        typ = {"name": ((m.T_STRING, None), False),
               "value": ((m.T_STRING, None), False)}
        assert m.validate_object(val_ok, typ, None) is None
        with self.assertRaises(m.ValidationError):
            m.validate_object(val_bad, typ, None)
        with self.assertRaises(m.ValidationError):
            m.validate_object(val_bad2, typ, None)

    def test_validate_object_not_exist_keys_2(self):
        val_ok = {"name": "name", "value": "value"}
        val_ok2 = {"name": "name", "value": "value", "value2": "value2"}
        typ = {"name": ((m.T_STRING, None), False),
               "value": ((m.T_STRING, None), False), m.S_ELLIPSIS: None}
        assert m.validate_object(val_ok, typ, None) is None
        assert m.validate_object(val_ok2, typ, None) is None

    def test_validate_object_nullable_key_can_not_exist(self):
        val_ok = {"name": "name"}
        val_bad = {"value": "value"}
        typ = {"name": ((m.T_STRING, None), False),
               "value": ((m.T_STRING, None), True)}
        assert m.validate_object(val_ok, typ, None) is None
        with self.assertRaises(m.ValidationError):
            m.validate_object(val_bad, typ, None)

    def test_array_nullable_element_1(self):
        val_ok = [1, None, 2, None]
        val_bad = [1, None, None, None]
        typ = [(m.T_U8, False), (m.T_U8, True), (m.T_U8, False), (m.T_U8,
                                                                  True)]
        assert m.validate_array(val_ok, typ, None) is None
        with self.assertRaises(m.ValidationError):
            m.validate_array(val_bad, typ, None)

    def test_array_nullable_element_2(self):
        val = [None] * 100
        typ = [(m.T_U8, True), m.S_ELLIPSIS]
        assert m.validate_array(val, typ, None) is None

    def test_validate_json_None(self):
        assert m.validate_json(None, None, None) is None
        with self.assertRaises(m.ValidationError):
            m.validate_json({'key': 'val'}, None, None)

    def test_validate_bad_typ(self):
        with self.assertRaises(m.ValidationError):
            m.validate_json({'key': 'val'}, 1, None)

    def test_validate_method(self):
        assert m.validate_method('POST', [m.M_POST], None) is None
        assert m.validate_method('POST', [m.M_POST, m.M_PUT], None) is None

    def test_validate_route(self):
        val_ok = {'id': 123}
        val_bad = {'id': 1234}
        typ = ['/<id>', {'id': m.T_U8}]
        assert m.validate_route(val_ok, typ, None) is None
        with self.assertRaises(m.ValidationError):
            m.validate_route(val_bad, typ, None)

    def test_validate_route_string(self):
        val_ok = {'arg': 'string'}
        val_bad = {'arg': 'long string'}
        typ = ['/<arg>', {'arg': (m.T_STRING, 6)}]
        assert m.validate_route(val_ok, typ, None) is None
        with self.assertRaises(m.ValidationError):
            m.validate_route(val_bad, typ, None)

    def test_match_status_code(self):
        assert m.match_status_code('4XX', 404)
        assert not m.match_status_code('4XX', 504)
        assert m.match_status_code(404, 404)
        assert not m.match_status_code(404, 401)

    def test_validate_empty_string_response(self):
        assert m.validate_response(Response('', 201), [{'status_code': [201],
                                                        'schema': None}]) is \
            None
        assert m.validate_response(('', 201), [{'status_code': [201],
                                                'schema': None}]) is \
            None


if __name__ == '__main__':
    unittest.main()
