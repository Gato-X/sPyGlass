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


import ctypes
from gltypes import NumberType,MinimalNumberType
from glcompat import *
import numpy as N
from mathtools import *



class Vbo(object):
	def __init__(self, target, total_values, data_type, usage = GL_STATIC_DRAW, data=None):
		self._vbo = None

		self._total_values = total_values

		self._data_type = data_type = NumberType(data_type)

		self._gl_type = data_type.asGlType()
		self._numpy_type = data_type.asNumpyType()
		self._bytes_per_item = data_type.bytes

		if data is not None:
			self._buffer = toNumpyArray(data, self._numpy_type)
		else:
			self._buffer = N.zeros(self._total_values, dtype=self._numpy_type)


		assert(self._buffer.size == self._total_values)

		dptr = self._buffer.ravel().ctypes.data_as(ctypes.c_void_p)

		self._vbo = glGenBuffers(1)

		#print "Vbo id:",self._vbo
		#print self._buffer.size, self._total_values, self._bytes_per_item, self._buffer.nbytes

		self._target = target

		glBindBuffer(target, self._vbo)
		glBufferData(target, self._total_values * self._bytes_per_item, dptr, usage)


	# returns a NumberType
	def getDataType(self):
		return self._data_type


	def bind(self):
		glBindBuffer(self._target,self._vbo)


	def __del__(self):
		if self._vbo is not None and bool(glDeleteBuffers):
			glDeleteBuffers(1, GLuint(self._vbo))


	def getBuffer(self):
		return self._buffer




class IndexVbo(Vbo):
	def __init__(self, data, usage = GL_STATIC_DRAW, force_large_data=False):
		try:
			total_indices = int(data)
			data = None
			data_type = "uint32" if force_large_data or total_indices > 65536 else "uint16"
		except:
			data = toNumpyArray(data, "u4" if force_large_data else "auto")
			total_indices = data.size
			data_type = str(data.dtype)
			if "'" in data_type:
				data_type = data_type.split("'")[1] # eg: dtype('uint32') -> "uint32"

		super(IndexVbo,self).__init__(
								GL_ELEMENT_ARRAY_BUFFER,
								total_indices,
								data_type,
								usage,
								data)



# an ENTITY is a triangle, a quad a line, a tri-strip, etc..
# a RECORD is a group of items that belong to a single vertex. A row in the data array
# a ITEM is a single value in a record (a float, an int, etc...)
# a FIELD is a logical collection of items: a normal, a position, etc...
# a SLICE is a collection of columns from the data that belong to the same field

class DataVbo(Vbo):
	class Error(ValueError):
		pass

	def __init__(self, data, usage = GL_STATIC_DRAW):

		if isNumpyArray(data):
			self._data = data
		else:
			data = self._data = toNumpyArray(data, NumpyDefaultFloatType)
	
		shape = data.shape

		self._bytes_per_item = data.dtype.itemsize

		self._items_per_record = data.size / shape[0]

		self._total_records = shape[0]
		self._bytes_per_record = self._items_per_record * self._bytes_per_item

		#print "Records: ",self._total_records
		#print "Items per record: ",self._items_per_record
		#print "Data shape: ",shape
		#print "Data flags: ",data.flags

		super(DataVbo,self).__init__(
								GL_ARRAY_BUFFER,
								self._total_records * self._items_per_record,
								data.dtype,
								usage,
								data)


		self._fields = []
		self._fields_by_name = {}

		self._total_fields_size = 0
		self._total_fields_per_record = 0


	# field_info is a list of tuples: ("field name", #items in field)
	# eg. defineFiled(("normal",3),("position,3),("tc",2))
	def defineFields(self, *field_info):
		
		offset = 0
		for f_name, f_size in field_info:

			if offset > self._items_per_record:
				raise self.Error("Record size of %s exceeded at field '%s'"%(self._items_per_record, f_name))

			if f_size < 1 or f_size > 4:
				raise self.Error("Field size %s for field '%s' is not in the range [1..4]"%(size, f_name))

			self._fields_by_name[f_name] = len(self._fields)
			# offset and f_size are in ITEMs (not bytes!)
			self._fields.append((offset, f_size, f_name))

			offset += f_size



	def setupShaderAttributes(self, shader):
		self.bind()
		for f_offset, f_size, f_name in self._fields:

			loc = shader.getAttribPos(f_name)

			if loc<0:
				continue

			byte_offset = f_offset * self._bytes_per_item

			glEnableVertexAttribArray(loc)
			glVertexAttribPointer(loc, f_size, self._gl_type, GL_FALSE, self._bytes_per_record, ctypes.c_void_p(byte_offset))

			print "Attrib %s, ofs: byte %s, size: %s elements, loc: %s, type: %s, record size: %s bytes"%(f_name, byte_offset, f_size, loc, self._gl_type, self._bytes_per_record)


	# used to compare how compatible two VAOs are
	def getShaderAttributesInfo(self, shader):
		# first the self id (a VAO implicitly binds a data VBO)
		# two VAOs are not equivalent if they don't point to the same VBO
		info = [id(self)]
		for f_offset, f_size, f_name in self._fields:
			loc = shader.getAttribPos(f_name)
			# the VertexAttribPointer's must bind the same locations for each field
			info.append(loc)

		return tuple(info)


	def getSlice(self, field_name, from_record=0, to_record=-1):
		f = self._fields[self._fields_by_name[field_name]]
		return self._data[from_record, to_record, f[0]:f[0]+f[1]]


	def updateData(self, from_record = 0, to_record=-1):

		if to_record < 0:
			to_record += self._total_records

		if from_record < 0:
			from_record += self._total_records


		offset = from_record * self._bytes_per_record
		size = (to_record - from_record) * self._bytes_per_record

		glBufferSubData(GL_ARRAY_BUFFER, offset, size, self._data[from_record:].ravel().ctypes.data_as(ctypes.c_void_p))





