# -*- coding: utf-8 -*-
"""
    flask-docjson
    ~~~~~~~~~~~~~

    Validate flask request and response json schemas via docstring.

    :copyright: (c) 2016 by Chao Wang (hit9).
    :license: BSD, see LICENSE for more details.
"""

import ctypes
from functools import wraps
import json
import sys

from flask import request, Response
from ply import lex, yacc

__version__ = '0.1.3'


###
# Compact
###

if sys.version_info.major == 3:
    basestring = (str, bytes)
    unicode = str
    long = int

    def json_loads(data):
        if isinstance(data, bytes):
            data = str(data, 'utf8')
        return json.loads(data)

    def get_func_code(func):
        return func.__code__

else:

    def json_loads(data):
        return json.loads(data)

    def get_func_code(func):
        return func.func_code


###
# Exceptions
###

class Error(Exception):
    """A flask-docjson error occurred."""
    pass


class ParserError(Error):
    """A parser error occurred."""


class LexerError(ParserError):
    """A lexer error occurred."""
    pass


class GrammarError(ParserError):
    """A grammar error occurred."""
    pass


class ValidationError(Error):
    """A validation error occurred."""

    def __init__(self, code=None, reason=None, value=None):
        self.code = code
        self.reason = reason
        self.value = value

    def __str__(self):
        try:
            return 'ValidationError: {0}, {1}: {2}'.format(
                self.code, self.reason, self.value)
        except (ValueError, TypeError):
            return 'ValidationError'

    def __repr__(self):
        return '<{}>'.format(str(self))


class RequestValidationError(ValidationError):
    """A validation error occurred while validating request data."""


class ResponseValidationError(ValidationError):
    """A validation error occurred while validating response data."""
    pass


class _InternalError(Exception):
    """Internal used purpose exception base."""
    pass


class _InternalLexerError(_InternalError):
    """Internal used purpose lexer error base."""
    pass


class _InternalGrammarError(_InternalError):
    """Internal used purpose grammar error base."""


ErrInvalidBool = (0x0100, "invalid boolean")
ErrInvalidU8 = (0x0200, "invalid u8")
ErrInvalidU16 = (0x0300, "invalid u16")
ErrInvalidU32 = (0x0400, "invalid u32")
ErrInvalidU64 = (0x0500, "invalid u64")
ErrInvalidI8 = (0x0600, "invalid i8")
ErrInvalidI16 = (0x0700, "invalid i16")
ErrInvalidI32 = (0x0800, "invalid i32")
ErrInvalidI64 = (0x0900, "invalid i64")
ErrInvalidFloat = (0x1000, "invalid float")
ErrInvalidString = (0x1100, "invalid string")
ErrNotArray = (0x1200, "not an array")
ErrShouldBeEmptyArray = (0x1201, "should be an empty array")
ErrArrayElementsNotEnough = (0x1202, "array elements not enough")
ErrArrayLength = (0x1203, "invalid array length")
ErrNotObject = (0x1300, "not an object")
ErrObjectKeyNotFound = (0x1301, "key not found in object")
ErrObjectUnexpectedKey = (0x1302, "unexpected key in object")
ErrNullable = (0x1400, "cannot be null")
ErrShouldBeNull = (0x1401, "should be null")
ErrInvalidJSON = (0x1500, "invalid json")
ErrInvalidMethod = (0x1600, "invalid method")
ErrRouteVarNotFound = (0x1700, "route variable not found")
ErrInvalidResponse = (0x1800, "invalid response")

###
# Schema
###

S_ELLIPSIS = 0

T_BOOL = 1
T_U8 = 2
T_U16 = 3
T_U32 = 4
T_U64 = 5
T_I8 = 6
T_I16 = 7
T_I32 = 8
T_I64 = 9
T_FLOAT = 10
T_STRING = 11

M_POST = 1
M_GET = 2
M_PUT = 3
M_DELETE = 4
M_PATCH = 5
M_HEAD = 6
M_OPTIONS = 7


###
# Lexer
###

literals = ':,()[]{}/<>*'

t_ignore = ' \t\r'   # whitespace

tokens = (
    'POST',
    'GET',
    'PUT',
    'DELETE',
    'PATCH',
    'HEAD',
    'OPTIONS',
    'ELLIPSIS',
    'BOOL',
    'U8',
    'U16',
    'U32',
    'U64',
    'I8',
    'I16',
    'I32',
    'I64',
    'FLOAT',
    'STRING',
    'IDENTIFIER',
    'STATIC_ROUTE',
    'STATUS_CODE_MATCHER',
    'LITERAL_INTEGER',
    'LITERAL_STRING',
)


def t_error(t):
    raise _InternalLexerError('illegal char %r at line %d' % (t.value[0],
                                                              t.lineno))


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_POST(t):
    r'POST'
    t.value = M_POST
    return t


def t_GET(t):
    r'GET'
    t.value = M_GET
    return t


def t_PUT(t):
    r'PUT'
    t.value = M_PUT
    return t


def t_DELETE(t):
    r'DELETE'
    t.value = M_DELETE
    return t


def t_HEAD(t):
    r'HEAD'
    t.value = M_HEAD
    return t


def t_OPTIONS(t):
    r'OPTIONS'
    t.value = M_OPTIONS
    return


def t_ELLIPSIS(t):
    r'\.\.\.'
    t.value = S_ELLIPSIS
    return t


def t_PATCH(t):
    r'PATCH'
    t.value = M_PATCH
    return t


def t_BOOL(t):
    r'bool'
    t.value = T_BOOL
    return t


def t_U8(t):
    r'u8'
    t.value = T_U8
    return t


def t_U16(t):
    r'u16'
    t.value = T_U16
    return t


def t_U32(t):
    r'u32'
    t.value = T_U32
    return t


def t_U64(t):
    r'u64'
    t.value = T_U64
    return t


def t_I8(t):
    r'i8'
    t.value = T_I8
    return t


def t_I16(t):
    r'i16'
    t.value = T_I16
    return t


def t_I32(t):
    r'i32'
    t.value = T_I32
    return t


def t_I64(t):
    r'i64'
    t.value = T_I64
    return t


def t_FLOAT(t):
    r'float'
    t.value = T_FLOAT
    return t


def t_STRING(t):
    r'string'
    t.value = T_STRING
    return t


def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    return t


def t_STATIC_ROUTE(t):
    r'\B/[^<{\r\n\s]*'
    return t


def t_STATUS_CODE_MATCHER(t):
    r'[0-9]+[X]+'
    return t


def t_LITERAL_INTEGER(t):
    r'[+-]?[0-9]+'
    t.value = int(t.value)
    return t


def t_LITERAL_STRING(t):
    r'(\"([^\\\n]|(\\.))*?\")'
    s = t.value[1:-1]
    maps = {
        't': '\t',
        'r': '\r',
        'n': '\n',
        '\\': '\\',
        '"': '\"'
    }
    i = 0
    length = len(s)
    val = ''
    while i < length:
        if s[i] == '\\':
            i += 1
            if s[i] in maps:
                val += maps[s[i]]
            else:
                raise _InternalLexerError('unsupported escaping char %r at '
                                          'line %d' % (s[i], t.lineno))
        else:
            val += s[i]
        i += 1
    t.value = val
    return t


###
# Parser
###

def _parse_seq(p):
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    elif len(p) == 3:
        p[0] = [p[1]] + p[2]
    elif len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 1:
        p[0] = []


def p_error(p):
    if p is None:
        raise _InternalGrammarError('grammar error at EOF')
    raise _InternalGrammarError('grammar error %r at line %d' % (p.value,
                                                                 p.lineno))


def p_start(p):
    '''start : request response_seq'''
    p[0] = dict(request=p[1], responses=p[2])


def p_request(p):
    '''request : method_seq route json_schema
               | method_seq route'''
    if len(p) == 4:
        p[0] = dict(methods=p[1], route=p[2], schema=p[3])
    elif len(p) == 3:
        p[0] = dict(methods=p[1], route=p[2], schema=None)


def p_method_seq(p):
    '''method_seq : method '/' method_seq
                  | method method_seq
                  |'''
    _parse_seq(p)


def p_method(p):
    '''method : POST
              | GET
              | PUT
              | DELETE
              | PATCH
              | HEAD
              | OPTIONS'''
    p[0] = p[1]


def p_route(p):
    '''route : route route_item
             |'''
    if len(p) == 3:
        if p[2][1]:
            dct = dict(list(p[1][1].items()) + [p[2][1]])
            p[0] = [p[1][0] + p[2][0] + '<' + p[2][1][0] + '>', dct]
        else:
            p[0] = [p[1][0] + p[2][0], p[1][1]]
    elif len(p) == 1:
        p[0] = ['', {}]


def p_route_item(p):
    '''route_item : STATIC_ROUTE route_var
                  | STATIC_ROUTE'''
    if len(p) == 3:
        p[0] = [p[1], p[2]]
    elif len(p) == 2:
        p[0] = [p[1], None]


def p_route_var(p):
    '''route_var : '<' type ':' IDENTIFIER '>'
                 | '<' IDENTIFIER '>' '''
    if len(p) == 6:
        p[0] = (p[4], p[2])
    elif len(p) == 4:
        p[0] = (p[2], None)


def p_response_seq(p):
    '''response_seq : response_item response_seq
                    |'''
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    elif len(p) == 1:
        p[0] = []


def p_response_item(p):
    '''response_item : status_code_seq json_schema
                     | status_code_seq'''
    if len(p) == 3:
        p[0] = dict(status_code=p[1], schema=p[2])
    elif len(p) == 2:
        p[0] = dict(status_code=p[1], schema=None)


def p_status_code_seq(p):
    '''status_code_seq : status_code_item '/' status_code_seq
                       | status_code_item
                       |'''
    _parse_seq(p)


def p_status_code_item(p):
    '''status_code_item : LITERAL_INTEGER
                        | STATUS_CODE_MATCHER'''
    p[0] = p[1]


def p_json_schema(p):
    '''json_schema : object
                   | array '''
    p[0] = p[1]


def p_object(p):
    '''object : '{' kv_seq '}'
              | '{' kv_seq ELLIPSIS '}' '''
    dct = dict(p[2])
    if len(p) == 5:
        dct[S_ELLIPSIS] = None
    p[0] = dct


def p_kv_seq(p):
    '''kv_seq : kv ',' kv_seq
              | kv kv_seq
              |'''
    _parse_seq(p)


def p_kv(p):
    '''kv : LITERAL_STRING ':' value'''
    p[0] = (p[1], p[3])


def p_array(p):
    '''array : '[' value_seq ']'
             | '[' value_seq ELLIPSIS ']' '''
    if len(p) == 4:
        p[0] = p[2]
    elif len(p) == 5:
        p[0] = p[2] + [p[3]]


def p_value_seq(p):
    '''value_seq : value ',' value_seq
                 | value value_seq
                 |'''
    _parse_seq(p)


def p_value(p):
    '''value : type
             | json_schema
             | type '*'
             | json_schema '*' '''
    if len(p) == 3:
        p[0] = (p[1], True)
    elif len(p) == 2:
        p[0] = (p[1], False)


def p_type(p):
    '''type : BOOL
            | U8
            | U16
            | U32
            | U64
            | I8
            | I16
            | I32
            | I64
            | FLOAT
            | string_type'''
    p[0] = p[1]


def p_string_type(p):
    '''string_type : STRING
                   | STRING '(' LITERAL_INTEGER ')' '''
    if len(p) == 2:
        p[0] = (T_STRING, None)
    elif len(p) == 5:
        p[0] = (T_STRING, p[3])


lexer = lex.lex()
parser = yacc.yacc(debug=False, write_tables=0)


def parse_schema(data):
    """Parse schema string to schema dict.
    """
    lexer.lineno = 1
    return parser.parse(data)


def parse(data):
    """Parse docstring to schema dict.
    Returns ``None`` if:
        1. ``data`` is ``None`` or falsely.
        2. No schema sign found in ``data``.
    """
    if not data:
        return None
    block_start = False
    lines = []
    ident = None
    for line in data.splitlines():
        if not block_start:
            if 'Schema::' in line or \
                    'Schema:' in line:
                block_start = True
            continue
        if not line or line.isspace():
            continue  # skip space or empty lines
        _ident = len(line) - len(line.lstrip())
        if ident is None:
            ident = _ident
            lines.append(line)
        else:
            if ident <= _ident:
                lines.append(line)
            else:
                break
    if block_start:
        return parse_schema('\n'.join(lines))
    return None


def parse_from_func(func):
    """Parse schema from function by parsing its ``__doc__``.
    Returns ``None`` if given func has no ``__doc__``.
    """
    data = getattr(func, '__doc__', None)
    if data is None:
        return None
    try:
        return parse(data)
    except _InternalError as exc:
        func_code = get_func_code(func)
        msg = '{}:{}:{}: {}'.format(func_code.co_filename,
                                    func_code.co_firstlineno,
                                    func_code.co_name,
                                    str(exc))
        if isinstance(exc, _InternalLexerError):
            raise LexerError(msg)
        elif isinstance(exc, _InternalGrammarError):
            raise GrammarError(msg)
        else:
            raise ParserError(msg)


###
# Validation
###

P_REQUEST = 1
P_RESPONSE = 2


def raise_validation_error(errtyp, value, p):
    if p == P_REQUEST:
        cls = RequestValidationError
    elif p == P_RESPONSE:
        cls = ResponseValidationError
    else:
        cls = ValidationError
    code, reason = errtyp
    raise cls(code=code, reason=reason, value=value)


def validate_bool(val, p):
    if isinstance(val, bool):
        return
    raise_validation_error(ErrInvalidBool, val, p)


def validate_u8(val, p):
    if isinstance(val, int) and ctypes.c_uint8(val).value == val:
        return
    raise_validation_error(ErrInvalidU8, val, p)


def validate_u16(val, p):
    if isinstance(val, int) and ctypes.c_uint16(val).value == val:
        return
    raise_validation_error(ErrInvalidU16, val, p)


def validate_u32(val, p):
    if isinstance(val, int) and ctypes.c_uint32(val).value == val:
        return
    raise_validation_error(ErrInvalidU32, val, p)


def validate_u64(val, p):
    if isinstance(val, (int, long)) and ctypes.c_uint64(val).value == val:
        return
    raise_validation_error(ErrInvalidU64, val, p)


def validate_i8(val, p):
    if isinstance(val, int) and ctypes.c_int8(val).value == val:
        return
    raise_validation_error(ErrInvalidI8, val, p)


def validate_i16(val, p):
    if isinstance(val, int) and ctypes.c_int16(val).value == val:
        return
    raise_validation_error(ErrInvalidI16, val, p)


def validate_i32(val, p):
    if isinstance(val, int) and ctypes.c_int32(val).value == val:
        return
    raise_validation_error(ErrInvalidI32, val, p)


def validate_i64(val, p):
    if isinstance(val, (int, long)) and ctypes.c_int64(val).value == val:
        return
    raise_validation_error(ErrInvalidI64, val, p)


def validate_float(val, p):
    if isinstance(val, (int, long, float)):
        return
    raise_validation_error(ErrInvalidFloat, val, p)


def validate_string(val, typ, p):
    if isinstance(val, basestring):
        if typ[1] is None or len(val) <= typ[1]:
            return
    raise_validation_error(ErrInvalidString, val, p)


def validate_type(val, typ, p):
    if typ == T_BOOL:
        return validate_bool(val, p)
    elif typ == T_U8:
        return validate_u8(val, p)
    elif typ == T_U16:
        return validate_u16(val, p)
    elif typ == T_U32:
        return validate_u32(val, p)
    elif typ == T_U64:
        return validate_u64(val, p)
    elif typ == T_I8:
        return validate_i8(val, p)
    elif typ == T_I16:
        return validate_i16(val, p)
    elif typ == T_I32:
        return validate_i32(val, p)
    elif typ == T_I64:
        return validate_i64(val, p)
    elif typ == T_FLOAT:
        return validate_float(val, p)
    elif isinstance(typ, tuple) and typ[0] == T_STRING:
        return validate_string(val, typ, p)


def validate_array(val, typ, p):
    if not isinstance(val, list):
        raise_validation_error(ErrNotArray, val, p)
    if not typ:
        if val:  # Must be empty array
            raise_validation_error(ErrShouldBeEmptyArray, val, p)
        return
    for i in range(len(typ)):
        ityp = typ[i]
        if i < len(typ)-1 and typ[i+1] == S_ELLIPSIS:
            while i < len(val):
                ival = val[i]
                i += 1
                validate_value(ival, ityp, p)
            return None
        else:
            if i >= len(val):
                raise_validation_error(ErrArrayElementsNotEnough, val, p)
            ival = val[i]
            validate_value(ival, ityp, p)
    if len(typ) != len(val):  # No ELLIPSIS
        raise_validation_error(ErrArrayLength, val, p)


def validate_object(val, typ, p):
    if not isinstance(val, dict):
        raise_validation_error(ErrNotObject, val, p)
    for key, ityp in typ.items():
        if key == S_ELLIPSIS:
            continue
        if key not in val:
            _, nullable = ityp
            if nullable:
                continue
            errtyp = ErrObjectKeyNotFound[0], \
                "key {} not found in object".format(key)
            raise_validation_error(errtyp, val, p)
        ival = val[key]
        validate_value(ival, ityp, p)
    if S_ELLIPSIS not in typ:
        for key in val:
            if key not in typ:
                errtyp = ErrObjectUnexpectedKey[0], \
                    "unexpected key {} in object".format(key)
                raise_validation_error(errtyp, val, p)


def validate_value(val, typ, p):  # Main entry
    ityp, nullable = typ
    if val is None:
        if not nullable:
            raise_validation_error(ErrNullable, val, p)
        return
    if isinstance(ityp, dict):
        validate_object(val, ityp, p)
    elif isinstance(ityp, list):
        validate_array(val, ityp, p)
    else:
        validate_type(val, ityp, p)


def validate_json(val, typ, p):
    if typ is None:
        if val is not None:
            raise_validation_error(ErrShouldBeNull, val, p)
        return
    if isinstance(typ, (list, dict)):
        ityp = (typ, False)  # top json mustn't be null
        return validate_value(val, ityp, p)
    raise_validation_error(ErrInvalidJSON, val, p)


def validate_method(val, typ, p):
    if val == 'POST' and M_POST in typ:
        return
    elif val == 'GET' and M_GET in typ:
        return
    elif val == 'PUT' and M_PUT in typ:
        return
    elif val == 'DELETE' and M_DELETE in typ:
        return
    elif val == 'PATCH' and M_PATCH in typ:
        return
    elif val == 'HEAD' and M_HEAD in typ:
        return
    elif val == 'OPTIONS' and M_OPTIONS in typ:
        return
    raise_validation_error(ErrInvalidMethod, val, p)


def validate_route(val, typ, p):
    args_typ = typ[1]
    for key, ityp in args_typ.items():
        if key not in val:
            errtyp = ErrRouteVarNotFound[0], \
                'route variable {} not found in route args'.format(key)
            raise_validation_error(errtyp, val, p)
        ival = val[key]
        validate_type(ival, ityp, p)


def validate_request(typ):
    validate_method(request.method, typ['methods'], P_REQUEST)
    validate_route(request.view_args, typ['route'], P_REQUEST)
    validate_json(request.get_json(), typ['schema'], P_REQUEST)


def match_status_code(matcher, code):
    code_s = str(code)
    matcher_s = str(matcher)
    if len(code_s) != len(matcher_s):
        return False
    for i, ch in enumerate(code_s):
        if matcher_s[i] == ch or matcher_s[i] == 'X':
            continue
        else:
            return False
    return True


def validate_response(val, typ):
    p = P_RESPONSE
    if isinstance(val, basestring):
        status_code = 200
        data = val
    elif isinstance(val, Response):
        status_code = val.status_code
        data = val.get_data()
    elif isinstance(val, (tuple, list)):
        data = val[0]
        status_code = val[1]
    else:
        raise_validation_error(ErrInvalidResponse, val, p)
    if data:
        try:
            response_json = json.loads(str(data, 'utf8'))
        except ValueError:
            raise_validation_error(ErrInvalidResponse, val, p)
    else:
        response_json = None
    for response_typ in typ:
        code_matchers = response_typ['status_code']
        json_typ = response_typ['schema']
        for code_matcher in code_matchers:
            if match_status_code(code_matcher, status_code):
                if json_typ is None:
                    if response_json is None:
                        return
                    if response_json == '':
                        return  # Enable empty string''  # noqa
                elif json_typ is not None and response_json is not None:
                    return validate_json(response_json, json_typ, p)
    raise_validation_error(ErrInvalidResponse, val, p)


def validate(func):
    """A decorator that is used to validate request and response for given
    api function, example::

        @app.route('/user/<id>', methods=['GET'])
        @validate
        def get_user(id):
            '''Schema::

                GET /user/<i32:id>

                200
                {
                    "id": i32,
                    "name": string(32)
                }
            '''
            pass
    """
    schema = parse_from_func(func)
    if schema is None:
        return func

    @wraps(func)
    def wrapper(*args, **kwargs):
        validate_request(schema['request'])
        response = func(*args, **kwargs)
        validate_response(response, schema['responses'])
        return response
    return wrapper


def register_all(app):
    """Register all view functions for given flask app, example::

        app = Flask(__name__)
        from .views import *
        register_all(app)
    """
    for endpoint, view_func in app.view_functions.items():
        if endpoint == 'static':
            continue
        app.view_functions[endpoint] = validate(view_func)
