# -*- coding: utf-8 -*-
"""
    flask-docjson
    ~~~~~~~~~~~~~

    A micro flask extension to validate json schemas via docstring.

    :copyright: (c) 2016 by Chao Wang (hit9).
    :license: BSD, see LICENSE for more details.
"""

from ply import lex, yacc

__version__ = '0.0.1'


###
# Exceptions
###

class Error(Exception):
    pass


class LexerError(Error):
    pass


class GrammerError(Exception):
    pass


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


class Request(object):
    def __init__(self, methods=None, route=None, schema=None):
        if methods is None:
            methods = []
        self.methods = methods
        self.route = route
        self.schema = schema


class Response(object):
    def __init__(self, status_code=None, schema=None):
        self.status_code = status_code
        self.schema = schema


class Schema(object):
    def __init__(self, request=None, responses=None):
        if responses is None:
            responses = []
        self.request = request
        self.responses = responses


###
# Lexer
###

literals = ':,()[]{}/<>'

t_ignore = ' \t\r'   # whitespace

tokens = (
    'POST',
    'GET',
    'PUT',
    'DELETE',
    'PATCH',
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
    raise LexerError('Illegal characher %r at line %d' %
                     (t.value[0], t.lineno))


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
    r'\B/[^<{\r\n]*'
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
                msg = 'Unexcepted escaping characher: %s' % s[i]
                raise LexerError(msg)
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
    elif len(p) == 1:
        p[0] = []


def p_error(p):
    if p is None:
        raise GrammerError('Grammer error at EOF')
    raise GrammerError('Grammer error %r at line %d' % (p.value, p.lineno))


def p_start(p):
    '''start : request response_seq'''
    p[0] = Schema(request=p[1], responses=p[2])


def p_request(p):
    '''request : method_seq route json_schema'''
    p[0] = Request(methods=p[1], route=p[2], schema=p[3])


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
              | PATCH'''
    p[0] = p[1]


def p_route(p):
    '''route : route route_item
             |'''
    if len(p) == 3:
        if p[2][1]:
            p[0] = [p[1][0] + p[2][0] + '<' + p[2][1][0] + '>',
                    p[1][1] + [p[2][1]]]
        else:
            p[0] = [p[1][0] + p[2][0], p[1][1]]
    elif len(p) == 1:
        p[0] = ['', []]


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
    '''response_item : status_code_seq json_schema'''
    p[0] = Response(status_code=p[1], schema=p[2])


def p_status_code_seq(p):
    '''status_code_seq : status_code_item '/' status_code_seq
                       | status_code_item status_code_seq
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
    '''object : '{' kv_seq '}' '''
    p[0] = dict(p[2])


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
             | json_schema'''
    p[0] = p[1]


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
    lexer.lineno = 1
    return parser.parse(data)


def parse(data):
    block_start = False
    lines = []
    for line in data.splitlines():
        if not block_start:
            if 'Schema::' in line:
                block_start = True
            continue
        if not line or line.isspace() \
                or line.startswith('\t') \
                or line.startswith('    '):
            lines.append(line)
        else:
            break
    return parse_schema('\n'.join(lines))
