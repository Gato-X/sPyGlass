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


from camera import OrthoCamera
import libs.transformations as T
import numpy as N
from glcompat import *
from mathtools import floatArray

class Scene(object):

	def __init__(self):
		self._model_m_changed = True
		self._camera = None
		self._default_camera = OrthoCamera()
		self.setCamera(None)

		self._model_m = T.identity_matrix()
		self._model_m_stack = [T.identity_matrix()]
		self._light_position = floatArray([1000.0, 1000.0, 1000.0])

		# these are computed and cached:
		self._normal_m = None
		self._modelview_m = None
		self._light_m = None
		self._view_m = self._projection_m = None
		

	def pushTransform(self, add_transform=None):
		self._model_m_stack.append(self._model_m)
		if add_transform is not None:
			self._model_m = N.dot(self._model_m, add_transform)
			self._model_m_changed = True
		

	def popTransform(self):
		if len(self._model_m_stack)>1:
			self._model_m = self._model_m_stack.pop()
		else:
			self._model_m = T.identity_matrix()

		self._model_m_changed = True


	def resetTransform(self):
		self._model_m = T.identity_matrix()
		del self._model_m_stack[1:]
		self._model_m_changed = True


	def replaceLastTransform(self, transform):
		self._model_m = N.dot(self._model_m_stack[-1], transform)
		self._model_m_changed = True


	def _prepareMatrices(self):
		if self._model_m_changed or self._camera_changed:
			if self._camera_changed:
				self._view_m, self._projection_m = self._camera.getMatrices()
				self._camera_changed = False

				self._light_m = self._view_m

			self._modelview_m = N.dot(self._view_m, self._model_m)
			self._model_m_changed = False

			m = self._modelview_m[0:3,0:3]
			try:
				self._normal_m = N.transpose(N.linalg.inv(m))
			except:
				self._normal_m = m


	def getCamera(self):
		return self._camera
	

	def setCamera(self, cam):
		if cam is None:
			cam = self._default_camera

		if cam == self._camera:
			return

		# this is to avoid endless recursivity in Scene.setCamera and Camera.releaseFromScene
		old_cam = self._camera
		self._camera = self._default_camera

		if old_cam: old_cam.releaseFromScene()

		# setting this here also avoids endless recursivity
		self._camera = cam

		self._camera.attachToScene(self)
		self._camera_changed = True


	# this is called by the camera instance when a parameter changes
	def flagCameraChanged(self):
		self._camera_changed = True
		

	def uploadUniforms(self, shader):
		self._prepareMatrices()

		glUniformMatrix4fv(shader.uni_modelview_m,1,GL_TRUE, self._modelview_m.ravel())
		glUniformMatrix3fv(shader.uni_normal_m,1,GL_TRUE, self._normal_m.ravel())
		glUniformMatrix4fv(shader.uni_light_m,1,GL_TRUE, self._light_m.ravel())
		glUniformMatrix4fv(shader.uni_projection_m,1,GL_TRUE,self._projection_m.ravel())
#		glUniformMatrix3fv(shader.uni_light_m,1,GL_TRUE, N.dot(self._light_m, self._modelview_m[0:3,0:3]).ravel())
		glUniform3fv(shader.uni_light0_position,1,self._light_position.ravel())

	
