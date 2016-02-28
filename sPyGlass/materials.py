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
from texture import Texture
from mathtools import floatArray
import resources as R
from tools import *


class Material:
	def __init__(self):
		self._texture = [None,None,None] # three textures supported
		self._diffuse_color = floatArray([0.8,0.8,0.8])
		self._ambient_color = floatArray([0.2,0.2,0.2])
		self._specular_color = floatArray([1.0,1.0,1.0])
		self._specular_exp = 2.0
		self._alpha = 1.0
		self._shader = None
				

	def setTexture(self, tex_num, texture):
		self._texture[tex_num] = texture

	def setDiffuseColor(self, color):
		self._diffuse_color = floatArray(color)

	def setSpecularColor(self, color):
		self._specular_color = floatArray(color)

	def setAmbientColor(self, color):
		self._ambient_color = floatArray(color)

	def setSpecularExponent(self, exp):
		self._ambient_color = float(exp)

	def setAlpha(self, alpha):
		self._alpha = float(alpha)

	def setShader(self, shader):
		self._shader = shader # either a ShaderProgram instance or the name of a shader

	def getShaderName(self):
		try:
			return self._shader.getName()
		except:
			return self._shader

	def getShader(self):
		if self._shader is None:
			return None
		try:
			self._shader.getName()
			return self._shader
		except:
			self._shader = R.loadShaderProgram(self._shader)
			return self._shader


# if shader==None, then the material must specify which shader to use
	def toCompiled(self, shader=None):

		if shader is None:
			shader = self.getShader()

		assert(shader)

		code = "def binder():\n\tpass\n"

		# items made up of 3 floats
		for what in ("diffuse_color","specular_color","ambient_color"):
			loc = shader.getUniformPos(what)
			if loc>0:
				code += "\tglUniform3fv(%s, 1, mat._%s)\n"%(loc,what)

		# items made up of 1 float
		for what in ("specular_exp","alpha"):
			loc = shader.getUniformPos(what)
			if loc>0:
				code += "\tglUniform1f(%s, mat._%s)\n"%(loc,what)

		# textures
		for i in xrange(3):
			loc = shader.getUniformPos("texture%s"%i)
			if loc>0:
				try: # see if the texture is already loaded
					self._texture[i].id()
				except:
					if self._texture[i] is None:
						self._texture[i] = Texture.getNullTexture()
					else:
						self._texture[i] = R.loadTexture(self._texture[i])

				code += "\tmat._texture[%s].bind(%s,%s)\n"%(i,i,loc)

		c = compile(code, "<compiled material>", "exec")

		print code

		ns = dict(mat = self, glUniform3fv=glUniform3fv, glUniform1f=glUniform1f)
	
		exec c in ns

		return ns['binder']


class MaterialsList:

	def __init__(self, filename=None):
		if filename is not None:
			self.load(filename)


	def _parseColor(self, txt, filename, n):
		try:
			return parseColor(txt)[0]
		except ValueError:
			print "%s:%s - invalid color: '%s'"%(filename, n, txt)
	
	
	def _parseFloat(self, txt, filename, n):
		try:
			return parseFloat(txt)[0]
		except ValueError:
			print "%s:%s - invalid value: '%s'"%(filename, n, txt)
	

	def load(self, filename):
		self._materials = {}
		mat_num = 1
		current_material = None
		mat = Material()

		for n,line in enumerate(R.openResource(filename,"rt")):
			line = line.strip()
			if not line or line.startswith("#"):
				continue

			if "#" in line:
				line = line.partition("#")[0]

			cmd,_,line = line.partition(" ")

			if cmd == "newmtl":
				if current_material:
					self._materials[current_material] = mat
					self._materials["#%s"%mat_num] = mat
					mat_num += 1

				mat = Material()
				current_material = line

			elif cmd == "Ka": # ambient color
				mat._ambient_color = self._parseColor(line, filename, n)

			elif cmd == "Kd": # diffuse color
				mat._diffuse_color = self._parseColor(line, filename, n)
			
			elif cmd == "Ks": # specular color
				mat._specular_color = self._parseColor(line, filename, n)
			
			elif cmd == "Ns": # specular exponent
				mat._specular_exp = self._parseFloat(line, filename, n)

			elif cmd == "d": # opacity
				mat._alpha = self._parseFloat(line, filename, n)

			elif cmd == "Tr": # transparency
				mat._alpha = 1.0 - self._parseFloat(line, filename, n)
		
			elif cmd == "map_Kd" or cmd == "tex0": # diffuse texture (or texture 0)
				mat._texture[0] = line

			elif cmd == "map_Ks" or cmd == "tex1": # specular map (or texture 1)
				mat._texture[1] = line
			
			elif cmd == "map_bump" or cmd == "tex2": # bump map (or texture 2)
				mat._texture[2] = line

			#this is an extension of sPyGlass
			elif cmd == "shader":
				mat._shader = line
			else:
				print "%s:%s - command not understood: '%s'"%(filename, n, cmd)

		if current_material:
			self._materials[current_material] = mat
			self._materials["#%s"%mat_num] = mat
			mat_num += 1


	def update(self, other): # as in dictionaries
		for k,v in other._materials:
			self._materials[k] = v


	def getMaterial(self, name):
		return self._materials[name]


	def getMaterialNames(self):
		return self._materials.keys()



