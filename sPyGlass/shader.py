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
from glcompat import *
_version_mapping = {}

class ShaderProgram:
	_defaultUniforms = [
	 'light_m',
	 'normal_m',
	 'modelview_m',
	 'projection_m',
	 'diffuse_color',
	 'ambient_color',
	 'specular_color',
	 'specular_exp',
	 'alpha',
	 'light0_position']

	_defaultAttribs = [
	 'position',
	 'normal',
	 'color',
	 'tc']

	def __init__(self, name, shaders, uniforms = 'default', attribs = 'default'):
		self._name = name
		self._program = glCreateProgram()
		self._loc_attribs = {}
		self._loc_uni = {}
		for s in shaders:
			glAttachShader(self._program, s._shader)

		glLinkProgram(self._program)
		if glGetProgramiv(self._program, GL_LINK_STATUS) != GL_TRUE:
			raise RuntimeError(glGetProgramInfoLog(self._program))
		glUseProgram(self._program)
		if uniforms:
			if uniforms == 'default':
				uniforms = ShaderProgram._defaultUniforms
			for uniform in uniforms:
				self.getUniformPos(uniform, True)

		if attribs:
			if attribs == 'default':
				attribs = ShaderProgram._defaultAttribs
			for attrib in attribs:
				self.getAttribPos(attrib, True)

		glUseProgram(0)

	def getUniformPos(self, uniform, register = False):
		try:
			return self._loc_uni[uniform]
		except:
			loc = glGetUniformLocation(self._program, uniform)
			if loc == -1:
				print 'Not such uniform in shader: %s' % uniform
			self._loc_uni[uniform] = loc
			if register:
				setattr(self, 'uni_' + uniform, loc)
			return loc

	def getAttribPos(self, attrib, register = False):
		try:
			return self._loc_attribs[attrib]
		except:
			loc = glGetAttribLocation(self._program, attrib)
			if loc == -1:
				print 'Not such attribute in shader: %s' % attrib
			self._loc_attribs[attrib] = loc
			if register:
				setattr(self, 'attr_' + attrib, loc)
			return loc

	def getName(self):
		return self._name

	def use(self):
		glUseProgram(self._program)


class Shader:

	def __init__(self, shdr_type, filename = None):
		self._shader = None
		if shdr_type == 'VERTEX':
			shdr_type = GL_VERTEX_SHADER
		elif shdr_type == 'FRAGMENT':
			shdr_type = GL_FRAGMENT_SHADER
		else:
			raise ValueError('Unknown shader type: %s' % shdr_type)
		self._shdr_type = shdr_type
		if filename is not None:
			self.fromFile(filename)

	def fromFile(self, file_):
		txt = None
		try:
			txt = file_.read()
		except:
			with open(file_) as f:
				txt = f.read()

		if txt is not None:
			self.fromString(txt)

	def fromString(self, source):
		shader = glCreateShader(self._shdr_type)
		glShaderSource(shader, source)
		glCompileShader(shader)
		if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
			raise RuntimeError(glGetShaderInfoLog(shader))
		self._shader = shader

