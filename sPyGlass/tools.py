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
from mathtools import floatArray
float_re = re.compile('\\s*(([+-]?)((?:\\d+(?:\\.\\d*)?)|(?:\\.\\d+))(?:[eE]([+-]?)(\\d+))?)(.*)')

def parseFloat(txt):
	orig_txt = txt
	mo = float_re.match(txt)
	if not mo:
		raise ValueError('Invalid float: %s' % orig_txt)
	return (float(mo.group(1)), mo.group(6))


def parseColor(txt):
	orig_txt = txt
	rgb = [0, 0, 0]
	for i in xrange(3):
		try:
			rgb[i], txt = parseFloat(txt)
		except ValueError:
			raise ValueError('Invalid color: %s' % orig_txt)

	return (floatArray(rgb), txt)

