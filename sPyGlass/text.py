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
import zipfile
import os.path
import pygame
import StringIO
from vbo import DataVbo, IndexVbo
from materials import Material
from texture import Texture
from objmanager import ObjManager
import resources as R
from collections import namedtuple
import numpy as N
from mathtools import NumpyDefaultFloatType
from mem import MemoryManager

try:
	import xml.etree.ElementTree as ET
except:
	import xml.etree.ElemTree as ET


# This class loads a font from a zip file as generated with this tool: http://kvazars.com/littera/

class LitteraFont:

	Glyph = namedtuple("Glyph",["id","x","y","width","height","xoffset","yoffset","xadvance","page"])

	def __init__(self, font_file):
		self._glyphs = {}
		self._kern = {}
		self._page = {}

		if "." not in font_file:
			font_file = font_file+".zip"

		with zipfile.ZipFile(font_file,'r') as z:
			if font_file.lower().endswith(".zip"):
				font_file = os.path.basename(font_file)[:-4]

			xml = z.read(font_file+".fnt")
			xroot = ET.fromstring(xml)
			# misc info
			com = xroot.find('common')
			self._line_height = int(com.get("lineHeight"))
			self._base = int(com.get("base"))
			self._imgw = int(com.get("scaleW"))
			self._imgh = int(com.get("scaleH"))
		

			# load the textures
			for page in xroot.find('pages').findall("page"):
				id = int(page.get("id"))
				img_filename = page.get("file")
				img = z.read(img_filename)
				surf = pygame.image.load(StringIO.StringIO(img),img_filename)
				tex = Texture()
				tex.setFromSurface(surf)
				self._page[id] = tex

				assert(id == 0) # for now, we only support single-page fonts
			
			# load the glyph data
			for char in xroot.find("chars").findall("char"):
				d = {}
				for f in self.Glyph._fields:
					d[f] = int(char.get(f))

				g=self.Glyph(**d)
				self._glyphs[g.id] = g

			# load the kerning data
			for kern in xroot.find("kernings").findall("kerning"):
				t = (int(kern.get("first")), int(kern.get("second")))
				self._kern[t] = int(kern.get("amount"))


		self._material = Material()

		self._material.setTexture(0,self._page[0])

		

	def getKerning(self, c1, c2):
		try:
			return self._kern[(c1,c2)]
		except:
			return 0


	def getTexture(self, id):
		return self._page[id]


	def getMaterial(self):
		return self._material


	def getGlyph(self, c):
		try:
			return self._glyphs[c]
		except:
			return None
			

class TextMemoryManager(MemoryManager):
		def __init__(self, page_size = 4096):
			super(TextMemoryManager, self).__init__()
			self._page_size = page_size

			indices = []

			j = 0
			for i in xrange(2*page_size): # in case a large page is requested
				indices.extend([j,j+1,j+3,j+1,j+2,j+3])
				j += 4

			indices = N.array(indices, dtype="u2")

			self._indices_vbo = IndexVbo(indices)
			self._shader = R.loadShaderProgram("text")

		# allocate a page for at least min_size vertices
		def _allocNewPage(self, min_size):
			size = max(min_size, self._page_size)
			data = N.zeros((size,4),dtype=NumpyDefaultFloatType) # pos(2)+uv(2) -> 4
			data_vbo = DataVbo(data, GL_DYNAMIC_DRAW)
			data_vbo.defineFields(("position",2),("tc",2))

			return data_vbo, size


		def getIndicesVbo(self):
			return self._indices_vbo


		def getShader(self):
			return self._shader



class Text(ObjManager):
	_mem = None

	# note initial_size (for now) is the max number of characters the Text instance
	# can render
	def __init__(self, font = None, text = None, origin_at_base=True):
		if Text._mem is None:
			Text._mem = TextMemoryManager()

		self._mem = Text._mem

		self._data_vbo_mem = None
		self._data_vbo = None

		super(Text,self).__init__(None, self._mem.getIndicesVbo())

		self._shader = self._mem.getShader()

		self._font = font

		if text is not None:
			self.setText(text, origin_at_base)



	def setFont(self, font):
		self._font = font


	def setText(self, text, origin_at_base=True):

		txt_size = len(text)

		if self._data_vbo_mem is None or  txt_size > len(self._text): # we need to reallocate
			if self._data_vbo_mem:
				self._data_vbo_mem.free()
			self._data_vbo_mem = self._mem.alloc(txt_size*4)
			self._data_vbo = self._data_vbo_mem.page_data

		self._text = text
		font = self._font
		data = self._data_vbo.getBuffer()

		x = 0
		y = font._base if origin_at_base else 0

		i0 = i1 = self._data_vbo_mem.start
		tot_prims = 0

		prev = None

		xmin = xmax = ymin = ymax = None

		for c in text:
			if c == '\n':
				x = 0
				y -= font._line_height
				prev = None
				continue

			c_num = ord(c)
			g = font.getGlyph(c_num) or font.getGlyph(32)
			if g is None:
				continue

			if g.width != 0 and g.height != 0:
				x += font.getKerning(prev, c_num)

				x0 = x + g.xoffset
				y0 = y - g.yoffset
				x1 = x0 + g.width
				y1 = y0 - g.height

				xmin = x0 if xmin is None else min(xmin,x0)
				xmin = min(xmin,x1)
				ymin = y0 if ymin is None else min(ymin,y0)
				ymin = min(ymin,y1)
				xmax = x0 if xmax is None else max(xmax,x0)
				xmax = max(xmax,x1)
				ymax = y0 if ymax is None else max(ymax,y0)
				ymax = max(ymax,y1)

				u0 = float(g.x)/float(font._imgw)
				u1 = u0 + float(g.width)/float(font._imgw)

				v0 = -float(g.y)/float(font._imgh)
				v1 = v0 -float(g.height)/float(font._imgh)

				data[i1]=[x0,y0,u0,v0]
				data[i1+1]=[x1,y0,u1,v0]
				data[i1+2]=[x1,y1,u1,v1]
				data[i1+3]=[x0,y1,u0,v1]
				i1 += 4
				tot_prims += 2 # rather than multiplying later by 2

			prev = c_num
			x += g.xadvance

		self.bounds = pygame.Rect(xmin,ymin,xmax-xmin,ymax-ymin)

		self.clearBatches()
		if i0 != i1:
			self._data_vbo.updateData(i0, i1)
			# (i0/4)*6 :
			# 4 vertices per quad, 6 indices per quad (2 triangles)
			self.addBatch(self._shader, font.getMaterial(), (i0/4)*6, tot_prims)


	def __del__(self):
		if self._data_vbo_mem is not None:
			self._data_vbo_mem.free()

