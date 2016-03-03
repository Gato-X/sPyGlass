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


import numpy as N
import libs.transformations as T
from mathtools import *
from gltools import getViewportSize

class Camera(object):

	def __init__(self):
		self._scene = None
		self._projection_m = None
		self._projection_changed = False

		self.resetView()
		self._projection_m = self._getNewProjectionMatrix()
	
	def getMatrices(self):
		if self._projection_changed:
			self._projection_m = self._getNewProjectionMatrix()
			self._projection_changed = False

		return self._view_m, self._projection_m


	def resetView(self):
		self._view_m = T.identity_matrix()
		if self._scene: self._scene.flagCameraChanged(self)

	
	def transform(self, trans):
		self._view_m = N.dot(self._view_m, trans)
		if self._scene: self._scene.flagCameraChanged(self)


	def setTransform(self, trans):
		self._view_m = trans
		if self._scene: self._scene.flagCameraChanged(self)


	def getScene(self):
		return self._scene


	def releaseFromScene(self):
		if self._scene is not None:
			self._scene.setCamera(None)
			self._scene = None


	def attachToScene(self, scene):
		if scene == self._scene:
			return

		if self._scene:
			self.releaseFromScene()

		scene.setCamera(self)
		self._scene = scene


	def viewportChanged(self, width, height):
		pass


class PerspectiveCamera(Camera):
	def __init__(self, fov = 60.0, near=0.5, far=1000):
		self._near = near
		self._far = far
		self._fov = fov
		super(PerspectiveCamera, self).__init__()


	@property
	def fov(self):
		return self._fov

	@fov.setter
	def fov(self, value):
		self._fov = value
		self._projection_changed = True
		if self._scene: self._scene.flagCameraChanged(self)


	@property
	def near(self):
		return self._near

	@near.setter
	def near(self, value):
		self._near = value
		self._projection_changed = True
		if self._scene: self._scene.flagCameraChanged(self)


	@property
	def far(self):
		return self._far

	@far.setter
	def far(self, value):
		self._far = value
		self._projection_changed = True
		if self._scene: self._scene.flagCameraChanged(self)


	def setParameters(self, fov=None, near=None, far=None):
		if fov: self._fov = fov
		if near: self._near = near
		if far: self._far = far
		
		self._projection_changed = True
		if self._scene: self._scene.flagCameraChanged(self)


	def setPosition(self, position, look_at=None, up = None):
		if look_at is not None:
			self._view_m = lookAtMtx(position, look_at, up or [0.0,1.0,0.0])
		else:
			self._view_m[0:3,3] = N.dot(self._view_m[0:3,0:3],-eye)
	
		if self._scene: self._scene.flagCameraChanged(self)


	def _getNewProjectionMatrix(self):
		return frustumProjMtx(self._fov, self._near, self._far)



	def viewportChanged(self):
		self._projection_changed = True
		if self._scene: self._scene.flagCameraChanged(self)



class OrthoCamera(Camera):
	def __init__(self, max_x=None, max_y=None):
		self._scene = None
		self.setArea(None)
		super(OrthoCamera, self).__init__()


	def setArea(self, x_max, y_max=None, x_min=None, y_min=None):

		self._area_set = (x_min, y_min, x_max, y_max)

		if y_min is None:
			if y_max is None:
				self._y_min = -1
				self._y_max =  1
			else:
				self._y_min = -y_max*0.5
				self._y_max =  y_max*0.5
		elif y_max is None:
			assert(False) # can't just specify minimum
		else:
			self._y_min = y_min
			self._y_max = y_max

		if x_min is None:
			if x_max is None:

				vpw, vph = getViewportSize()
				f = float(vpw)/float(vph) * (self._y_max - self._y_min)

				self._x_min = -f*0.5
				self._x_max =  f*0.5
			else:
				self._x_min = -x_max*0.5
				self._x_max =  x_max*0.5
		elif x_max is None:
			assert(False) # can't just specify minimum
		else:
			self._x_min = x_min
			self._x_max = x_max


		self._projection_changed = True
		if self._scene: self._scene.flagCameraChanged(self)


	def _getNewProjectionMatrix(self):
		return T.clip_matrix(self._x_min, self._x_max, self._y_min, self._y_max, -1, 1)#  0.,0.,.,1.,-1.,1.,False)


	def viewportChanged(self):
		x_min, y_min, x_max, y_max = self._area_set
		self.setArea(x_max, y_max, x_min, y_min)
