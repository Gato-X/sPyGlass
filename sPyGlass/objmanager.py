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
from collections import namedtuple
from vao import Vao


class ObjManager(object):

	_points_per_primitive = {
			GL_TRIANGLES:(3,0),
			GL_TRIANGLE_STRIP:(1,2), # 1 per primitive + 2
			GL_LINE_STRIP:(1,1),
			GL_LINES:(2,0),
			GL_POINTS:(1,0)
		}


	Batch = namedtuple("Batch",[
				"shader",
				"mbinder",
				"vao",
				"primitive_type",
				"total_points",
				"data_type",
				"offset",
			])

	_mbinder_cache = {}

	_vao_cache = {}


	def __init__(self, data_vbo, indices_vbo):
		self._data_vbo = data_vbo
		self._indices_vbo = indices_vbo
		self._batches = []
		self._last_shader = None
		self._last_mbinder = None
		self._transform = None



	def _getMaterialBinder(self, shader, material):
		t = (material,shader)
		try:
			mb = self._mbinder_cache[t]
		except:
			mb = self._mbinder_cache[t] = material.toCompiled(shader)

		return mb


	def _getVao(self, shader, data_vbo):
		info = data_vbo.getShaderAttributesInfo(shader)
		try:
			vao = self._vao_cache[info]
		except:
			vao = self._vao_cache[info] = Vao(shader, data_vbo)

		return vao


	def clearCache(self):
		self._vao_cache = {}
		self._mbinder_cache = {}


	def addBatch(self, shader, material, first_index, total_primitives, primitive_type = GL_TRIANGLES ):
		
		ppp = self._points_per_primitive[primitive_type]
	
		dtype = self._indices_vbo.getDataType()

		mbinder = self._getMaterialBinder(shader, material)

		vao = self._getVao(shader, self._data_vbo)

		ofs = first_index * dtype.bytes

		self._batches.append(self.Batch(
				shader = shader,
				mbinder = mbinder,
				vao = vao,
				primitive_type = primitive_type,
				total_points = total_primitives * ppp[0] + ppp[1],
				data_type = dtype.asGlType(),
				offset = ctypes.c_void_p(ofs),
			))

		self._batches.sort()


	def clearBatches(self):
		self._batches = []


	def setTransform(self, transform):
		self._transform = transform


	def resetTransform(self):
		self._transform = None


	def drawMany(self, scene, instances):

		shader = None
		mbinder = None
		vao = None

		scene.pushTransform()

		for b_num, batch in enumerate(self._batches):
			if batch.shader != shader:
				shader = batch.shader
				shader.use()
				scene.uploadUniforms(shader)
				vao = None # TODO: required??
				mbinder = None

			if batch.vao != vao:
				vao = batch.vao
				vao.bind()

			batch_mbinder = batch.mbinder

			self._indices_vbo.bind()

			for inst in instances:
				if inst.binders is not None:
					new_mbinder = inst.binders[b_num]
				else:
					new_mbinder = batch_mbinder

				if new_mbinder != mbinder:
					mbinder = new_mbinder
					mbinder()

				scene.replaceLastTransform(inst.transform)
				glDrawElements(batch.primitive_type, batch.total_points, batch.data_type, batch.offset)

		scene.popTransform()


	def draw(self, scene):

		if self._transform is not None:
			scene.pushTransform(self._transform)

		shader = None
		mbinder = None
		vao = None

		for batch in self._batches:
			if batch.shader != shader:
				shader = batch.shader
				shader.use()
				scene.uploadUniforms(shader)
				vao = None # TODO: required??
				mbinder = None

			if batch.vao != vao:
				vao = batch.vao
				vao.bind()

			if batch.mbinder != mbinder:
				mbinder = batch.mbinder
				mbinder()

			self._indices_vbo.bind()
			glDrawElements(batch.primitive_type, batch.total_points, batch.data_type, batch.offset)

		if self._transform is not None:
			scene.popTransform()
			
