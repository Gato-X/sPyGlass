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


class Vao:
	def __init__(self, shader=None, data_vbo=None):
		self._vao = glGenVertexArray()
		self._info = None
		if shader is not None and data_vbo is not None:
			self.setup(shader, data_vbo)


	def setup(self, shader, data_vbo):
		shader.use() # TODO: Required??
		glBindVertexArray(self._vao)
		data_vbo.bind()
		data_vbo.setupShaderAttributes(shader)
		self._info = data_vbo.getShaderAttributesInfo(shader)
		glBindVertexArray(0)


	def isCompatible(self, shader, data_vbo):
		return self._info and self._info == data_vbo.getShaderAttributesInfo(shader)


	def bind(self):
		glBindVertexArray(self._vao)


	def __del__(self):
		try:
			glDeleteVertexArray(self._vao)
		except:
			pass



