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


import pygame
from glcompat import *
fsize = ctypes.sizeof(ctypes.c_float)

def isColorLike(col1, col2):
	dr = abs(col1[0] - col2[0])
	if dr > 5:
		return False
	dg = abs(col1[1] - col2[1])
	if dg > 5:
		return False
	db = abs(col1[2] - col2[2])
	if db > 5:
		return False
	return True


def isGray(col):
	if max(col[0], col[1], col[2]) - min(col[0], col[1], col[2]) >= 5:
		return False
	return (float(col[0]) + float(col[1]) + float(col[2])) / 3.0


def getViewportSize():
	vp = glGetIntegerv(GL_VIEWPORT)
	return (vp[2], vp[3])


def getMaxTextureSize():
	return glGetIntegerv(GL_MAX_TEXTURE_SIZE)


def getGlInfo():
	info = []
	info.append('Actual color bits: r%d g%d b%d a%d' % (pygame.display.gl_get_attribute(pygame.GL_RED_SIZE),
	 pygame.display.gl_get_attribute(pygame.GL_GREEN_SIZE),
	 pygame.display.gl_get_attribute(pygame.GL_BLUE_SIZE),
	 pygame.display.gl_get_attribute(pygame.GL_ALPHA_SIZE)))
	info.append('Actual depth bits: %d' % (pygame.display.gl_get_attribute(pygame.GL_DEPTH_SIZE),))
	info.append('Actual stencil bits: %d' % (pygame.display.gl_get_attribute(pygame.GL_STENCIL_SIZE),))
	info.append('Actual multisampling samples: %d' % (pygame.display.gl_get_attribute(pygame.GL_MULTISAMPLESAMPLES),))
	info.append('Viewport size: %dx%s' % getViewportSize())
	return info

