"""
The MIT License (MIT)

Copyright (c) 2015 Guillermo Romero Franco (AKA Gato)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import re
import numpy as N
import ctypes
from glcompat import *
from collections import namedtuple

class NumberType:

    class NTValueError(ValueError):
        pass

    _float_sizes = (ctypes.sizeof(ctypes.c_float), ctypes.sizeof(ctypes.c_double))
    _type_re = re.compile('^(u|unsigned)?[ _]?((?:(int|float)[ _]?(8|32|16))|byte)$')
    _gl_type_t = namedtuple('_gl_type_t', ['gl_type',
     'is_signed',
     'is_float',
     'gl_type_name'])
    _gl_types = {'GL_BYTE': _gl_type_t(GLbyte, True, False, GL_BYTE),
     'GL_UNSIGNED_BYTE': _gl_type_t(GLubyte, False, False, GL_UNSIGNED_BYTE),
     'GL_SHORT': _gl_type_t(GLshort, True, False, GL_SHORT),
     'GL_UNSIGNED_SHORT': _gl_type_t(GLushort, False, False, GL_UNSIGNED_SHORT),
     'GL_INT': _gl_type_t(GLint, True, False, GL_INT),
     'GL_UNSIGNED_INT': _gl_type_t(GLuint, False, False, GL_UNSIGNED_INT),
     'GL_FLOAT': _gl_type_t(GLfloat, True, True, GL_FLOAT),
     'GL_DOUBLE': _gl_type_t(GLdouble, True, True, GL_DOUBLE)}

    def __init__(self, t):
        if isinstance(t, N.dtype):
            self._fromNtype(t)
        elif 'ctypes' in str(t):
            self._fromCtype(t)
        elif str(t).startswith('GL_'):
            self._fromGLtype(t)
        elif isinstance(t, type):
            self._fromPyType(t)
        else:
            self._fromTypeDescription(t)

    def _fromNtype(self, dtype):
        self._bytes = dtype.itemsize
        self._is_float = dtype.kind == 'f'
        self._is_signed = True if self._is_float else 'u' not in dtype.str

    def _fromCtype(self, ct):
        s = str(ct)
        self._bytes = ctypes.sizeof(ct)
        self._is_float = 'float' in s or 'double' in s
        self._is_signed = True if self._is_float else 'c_u' not in s

    def _fromGLtype(self, glt):
        s = str(glt).split()[0]
        try:
            t = self._gl_types[s]
        except:
            raise NumberType.NTValueError('No such type %s; not one of: %s' % (s, self._gl_types.keys()))

        self._bytes = ctypes.sizeof(t.gl_type)
        self._is_float = t.is_float
        self._is_signed = t.is_signed

    def _fromPyType(self, t):
        if t == type(1):
            return self._fromGLtype('GL_INT')
        if t == type(1.0):
            return self._fromGLtype('GL_FLOAT')
        raise NumberType.NTValueError("Don't know how to interpret type: %s" % (t,))

    def _fromTypeDescription(self, t):
        mo = self._type_re.match(t)
        if mo is not None:
            if mo.group(2) == 'byte':
                self._is_float = False
                self._bytes = 1
                self._is_signed = not mo.group(1)
                return
            if mo.group(3) == 'float':
                self._is_float = True
                size = int(mo.group(4)) / 8
                if size not in self._float_sizes:
                    raise NumberType.NTValueError('Float of %s bytes not supported' % size)
                self._bytes = size
                self._is_signed = True
                return
            if mo.group(3) == 'int':
                self._is_float = False
                self._bytes = int(mo.group(4)) / 8
                self._is_signed = not mo.group(1)
                return
        raise NumberType.NTValueError('Unkown type: %s' % t)

    def asGlType(self):
        for t in self._gl_types.values():
            if ctypes.sizeof(t.gl_type) != self._bytes:
                continue
            if t.is_signed != self._is_signed:
                continue
            if t.is_float != self._is_float:
                continue
            return t.gl_type_name

        raise NumberType.NTValueError("Don't know how to convert %s to OpenGL type" % self)

    def asNumpyType(self):
        c = 'f' if self._is_float else ('i' if self._is_signed else 'u')
        return N.dtype('%s%s' % (c, self._bytes))

    def asCtype(self):
        if self._is_float:
            for c in [ctypes.c_float, ctypes.c_double, ctypes.c_longdouble]:
                if ctypes.sizeof(c) == self._bytes:
                    return c

        bits = self._bytes * 8
        if self._is_signed:
            t = 'ctypes.c_int%s' % bits
        else:
            t = 'ctypes.c_uint%s' % bits
        return eval(t)

    def __str__(self, sep = '_'):
        t = 'float' if self._is_float else 'int'
        s = self._bytes * 32
        if self._is_signed:
            return '%s%s%s' % (t, sep, s)
        else:
            return 'unsigned%s%s%s%s' % (sep,
             t,
             sep,
             s)

    @property
    def bits(self):
        return self._bytes * 8

    @property
    def bytes(self):
        return self._bytes

    def isFloat(self):
        return self._is_float

    def isSigned(self):
        return self._is_signed


class MinimalNumberType:

    def __init__(self, d):
        self._is_float = False
        self._min_val = 0
        self._max_val = 0
        self._value = d
        self._type = None
        self._test(d)
        self._buildType()

    def getType(self):
        return self._type

    def _buildType(self):
        if self._is_float:
            self._type = NumberType('float 32')
            return
        bits = 8
        signed = self._min_val < 0
        if signed:
            if self._min_val < -128 or self._max_val >= 128:
                bits = 16
                if self._min_val < -32768 or self._max_val >= 32768:
                    bits = 32
        elif self._max_val >= 256:
            bits = 16
            if self._min_val >= 4294967296:
                bits = 32
        if signed:
            self._type = NumberType('int %s' % bits)
        else:
            self._type = NumberType('unsigned int %s' % bits)

    def _test(self, d):
        if isinstance(d, float):
            self._is_float = True
            self._min_val = None
            self._max_val = None
            return True
        if isinstance(d, int):
            self._min_val = min(self._min_val, d)
            self._max_val = min(self._max_val, d)
            return False
        if isinstance(d, list) or isinstance(d, tuple):
            r = False
            for v in d:
                r = self._test(v)
                if r:
                    break

            return r
        try:
            t = d.dtype
            s = d.shape
        except:
            raise NumberType.NTValueError("Don't know how to interpret %s as a number or sequence of numbers" % d)

        if t.kind == 'f':
            self._is_float = True
            self._min_val = None
            self._max_val = None
            return True
        if len(s) == 0:
            self._min_val = min(self._min_val, d)
            self._max_val = min(self._max_val, d)
            return False
        for v in d:
            r = self._test(v)
            if r:
                break

        if r:
            return True
