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
try:
	import Image
except:
	from PIL import Image

import os
import pygame
import weakref
import gltools as glt
from texture import Texture
from materials import MaterialsList
from shader import ShaderProgram, Shader
from text import LitteraFont
_data_py = os.path.abspath(os.path.dirname(__file__))
_data_dir = None

def setResourcesPath(resources_path):
	global _data_dir
	_data_dir = os.path.normpath(os.path.join(_data_py, resources_path))


setResourcesPath(os.path.join('..', 'data'))

_weak_cache = weakref.WeakValueDictionary()
_strong_cache = {}

def cached(group = None, weak=True):
	cache = _weak_cache if weak else _strong_cache

	def deco(func):
		def memo(*args, **kwargs):

			k = (group, args, tuple(kwargs.items()))

			try:
				hash(k)
			except TypeError:
				k = '%s:%s' % (group, repr(k))

			try:
				return cache[k]
			except KeyError:
				result = func(*args, **kwargs)
				cache[k] = result
				return result

		return memo

	return deco


def resourcePath(filename):
	return os.path.join(_data_dir, filename)


def openResource(filename, mode = 'rb'):
	return open(resourcePath(filename), mode)



@cached('SURFACE')
def loadSurface(filename, convert = True):
	if filename.startswith('#'):
		surf = pygame.Surface((16, 16))
		surf.fill(pygame.Color(filename[1:]))
	else:
		surf = pygame.image.load(resourcePath(filename))
	if convert:
		surf = surf.convert()
	return surf


@cached('IMAGE')
def loadImage(filename, convert = True):
	img = Image.open(resourcePath(filename))
	return img


@cached('TEXTURE')
def loadTexture(filename):
	return Texture(filename)


@cached('MATS', False)
def loadMaterials(filename):
	if '.' not in filename:
		filename = filename + '.mtl'
	return MaterialsList(filename)


@cached('FONT')
def loadFont(filename):
	return LitteraFont(resourcePath(filename))


def loadMaterial(descr):
	assert(':' in descr)
	filename, _, material = descr.partition(":")

	return loadMaterials(filename).getMaterial(material)
	

def loadShader(filename):
	if '_v.' in filename:
		shdr = Shader('VERTEX', openResource(filename, 'rt'))
	elif '_f.' in filename:
		shdr = Shader('FRAGMENT', openResource(filename, 'rt'))
	else:
		raise ValueError('Unknown shader type: %s' % filename)
	return shdr


@cached('SHADER_P')
def loadShaderProgram(name):
	vs = loadShader(name + '_v.shdr')
	fs = loadShader(name + '_f.shdr')
	return ShaderProgram(name, [vs, fs])

