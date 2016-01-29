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
import resources as R

class Texture:

	_null_texture = None

	@classmethod
	def getNullTexture(cls):
		if cls._null_texture == None:
			cls._null_texture = Texture("#white")
		return cls._null_texture


	def __init__(self, filename=None, smoothing=True):
		self._smoothing = smoothing
		self._id = 0
		if filename:
			self.load(filename)


	def load(self, filename):
		surf = R.loadSurface(filename, False)
		self.setFromSurface(surf)
		pass


	def setFromSurface(self, surf):
		data = pygame.image.tostring(surf, "RGBA", 1)

		self._width = w = surf.get_width()
		self._height = h = surf.get_height()

		if not self._id:
			id = self._id = glGenTextures(1)
		else:
			id = self._id

		glBindTexture(GL_TEXTURE_2D,id)
		if self._smoothing:
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		else:
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
		glBindTexture(GL_TEXTURE_2D,0)


	def update(self, surf):
		glBindTexture(GL_TEXTURE_2D,self._id)
		data = pygame.image.tostring(surf, "RGBA", 1)
		glTexSubImage2D(GL_TEXTURE_2D, 0, 0,0, self._width, self._height, GL_RGBA, GL_UNSIGNED_BYTE, data )
		glBindTexture(GL_TEXTURE_2D,0)


	def width(self):
		return self._width


	def height(self):
		return self._height


	def id(self):
		return self._id


	def bind(self, sampler_num, uniform_location):
		glUniform1i(uniform_location, sampler_num) # assign the sampler to the texture
		glActiveTexture(GL_TEXTURE0 + sampler_num) # make sure the sampler is enabled
		glBindTexture(GL_TEXTURE_2D, self._id) # select the current texture


	def __del__(self):
		try:
			glDeleteTextures(self._id)
		except:
			pass

