# -*- coding: utf-8 -*-

import unittest
import flask_docjson as m


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
                    'name': (m.T_STRING, None),
                    'number': m.T_I16,
                    'children': [{'id': m.T_I32}, m.S_ELLIPSIS]
                },
            },
            'responses': [
                {'status_code': [200],
                 'schema': {
                     'id': m.T_I32,
                     'name': (m.T_STRING, None),
                     'number': m.T_I16,
                     'children': [{'id': m.T_I32}, m.S_ELLIPSIS]
                 }},
                {'status_code': ['4XX', '5XX'],
                 'schema': {'message': (m.T_STRING, None)}}
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
            'specialkey"\t\r': m.T_I8,
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
                 'schema': {'id': m.T_I32, 'name': (m.T_STRING, 33)}}
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
                 'schema': [{'id': m.T_I32, 'name': (m.T_STRING, 32)},
                            m.S_ELLIPSIS]}
            ]
        }


class TestValidation(unittest.TestCase):

    def test_validate_bool(self):
        assert m.validate_bool(True) is None
        with self.assertRaises(m.ValidationError):
            m.validate_bool(1)

    def test_validate_u8(self):
        assert m.validate_u8(199) is None
        with self.assertRaises(m.ValidationError):
            m.validate_u8(1999)

    def test_validate_u16(self):
        assert m.validate_u16(65535) is None
        with self.assertRaises(m.ValidationError):
            m.validate_u16(65535*2)

    def test_validate_u32(self):
        assert m.validate_u32(4294967295) is None
        with self.assertRaises(m.ValidationError):
            m.validate_u32(4294967296)

    def test_validate_u64(self):
        assert m.validate_u64(0xffffffffffffffff) is None
        with self.assertRaises(m.ValidationError):
            m.validate_u64(0xffffffffffffffff + 1)

    def test_validate_float(self):
        assert m.validate_float(0.1) is None
        assert m.validate_float(1) is None
        with self.assertRaises(m.ValidationError):
            m.validate_float('1')

    def test_validate_string(self):
        assert m.validate_string('test', (m.T_STRING, None)) is None
        assert m.validate_string('test', (m.T_STRING, 4)) is None
        assert m.validate_string(u'unicode', (m.T_STRING, None)) is None
        with self.assertRaises(m.ValidationError):
            m.validate_string(1, (m.T_STRING, None))
        with self.assertRaises(m.ValidationError):
            m.validate_string("test", (m.T_STRING, 3))

    def test_validate_type(self):
        assert m.validate_type(18, m.T_I8) is None
        with self.assertRaises(m.ValidationError):
            m.validate_type(1888, m.T_I8)
        with self.assertRaises(m.ValidationError):
            m.validate_type(19, (m.T_STRING, 31))
        assert m.validate_type('abc', (m.T_STRING, 3)) is None

    def test_validate_array(self):
        pass


if __name__ == '__main__':
    unittest.main()
