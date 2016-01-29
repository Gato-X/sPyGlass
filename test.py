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
import time
from sPyGlass.gltools import *
import sPyGlass.resources as R
import operator
from sPyGlass.mathtools import floatArray, planeNormal, mmult
from sPyGlass.vbo import DataVbo, IndexVbo
from sPyGlass.scene import Scene
from sPyGlass.objmanager import ObjManager
from sPyGlass.camera import PerspectiveCamera
import sPyGlass.libs.transformations as T
from sPyGlass.text import Text

class Cube(ObjManager):
	def __init__(self):
		pos = []
		for i in xrange(8):
			pos.append([
						1.0 if i & 1 else -1.0,
						1.0 if i & 2 else -1.0,
						1.0 if i & 4 else -1.0,
					])
		
		faces = [[0,1,3,2],[1,5,7,3],[2,3,7,6],[0,4,5,1],[0,2,6,4],[4,6,7,5]]

		vertices = []
		indices = []
		i = 0
		for f in faces:
			p_arr = map(lambda i:floatArray(pos[i]), f)

			n = list(planeNormal(p_arr[0], p_arr[1], p_arr[2]))

			indices.extend([i,i+1,i+3,i+1,i+2,i+3])
			i +=4

			for j,v in enumerate(f):
				vertices.append(list(p_arr[j]) + n)

		vertices = floatArray(vertices)

		self._data_vbo = DataVbo(vertices)
		self._indices_vbo = IndexVbo(indices)

		self._data_vbo.defineFields(("position",3),("normal",3))

		shader = R.loadShaderProgram("phong")

		mat = R.loadMaterial("default:red_plastic")

		super(Cube,self).__init__(self._data_vbo, self._indices_vbo)

		self.addBatch(shader, mat, 0, 12)


class MainScene(Scene):

	def __init__(self):
		super(MainScene,self).__init__()

		self._fnt = R.loadFont("test-font")

		self._cube = Cube()

		cam = PerspectiveCamera()

		self.setCamera(cam)

		cam.setPosition(floatArray((0,0,5)),floatArray((0,0,0)))

		self._text = Text()
		self._text.setFont(self._fnt)
	
		self._text.setText("This is\na test")


	def destroy(self):
		pass

	def draw(self, t):
		self._cube.setTransform(
			mmult(
				T.scale_matrix(0.1),
				T.rotation_matrix(t*0.001, [1,0,1])
			)
		)
		self._cube.draw(self)
		self._text.setTransform(
			mmult(
				T.scale_matrix(0.009),
				T.rotation_matrix(t*0.0001, [0,1,1])
			)
		)
		self._text.draw(self)


	def loop(self):
		try:
			max_fps = 65.0
			frame_ticks = 1000.0 / max_fps
			tz = pygame.time.get_ticks()

			print "Looping"

			while True:
				glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

				t = pygame.time.get_ticks()

				if t-tz > 5000:
					print "Done"
					break

				self.draw(t)

				pygame.display.flip()

				dt = pygame.time.get_ticks() - t

				pygame.time.delay(max(0,int(frame_ticks - dt))) # be nice and yield some time

		except:
			self.destroy()
			raise






def main():
	pygame.init()
	pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 16)
	screen = pygame.display.set_mode((800,600), pygame.OPENGL|pygame.DOUBLEBUF)

	glEnable(GL_DEPTH_TEST)
	glDepthFunc(GL_LEQUAL)
	glDisable(GL_CULL_FACE)
	glBlendFunc(GL_SRC_ALPHA, GL_ONE)
	glViewport(0,0,800,600)

	print '\n'.join(getGlInfo())


	print "Running..."
	frame = 0
	old_t = 0

	scene = MainScene()

	scene.loop()

	scene.destroy()

main()
