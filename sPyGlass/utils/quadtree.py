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
import math

try:
	import Image, ImageDraw
except:
	from PIL import Image, ImageDraw




class QTreeMap:
	def __init__(self, map=None):
		if map is not None:
			self.setMap(map)
		else:
			self._width = 10
			self._height = 10
			self._map = N.zeros((width, height))


	# map is a numpy 2x2 array
	def setMap(self, map):
		self._map = map
		self._height,self._width = self._map.shape
		

	@property
	def width(self):
		return self._width


	@property
	def height(self):
		return self._height


	def getObstruction(self, area):
		x0,y0,x1,y1 = area.rect()
		x0 = int(x0)
		x1 = int(x1)
		y0 = int(y0)
		y1 = int(y1)

		o = N.any(self._map[y0:y1,x0:x1])

		if o:
			if N.all(self._map[y0:y1,x0:x1]):
				return 0 #not obstructed
			return 1 # partially obstructed
		return 2 # completely obstructed






class QTreeNode:
	def __init__(self, x1,y1,x2,y2,extra=None):
		self.x1 = x1
		self.x2 = x2
		self.y1 = y1
		self.y2 = y2
		self._extra = extra
		self._adj = None

	def isLeaf(self):
		try:
			int(self._extra)
			return True
		except:
			return False

	def rect(self):
		return (self.x1,self.y1,self.x2,self.y2)


	def setLeafId(self, id):
		self._extra = id


	def getLeafId(self):
		try:
			return int(self._extra)
		except:
			return None


	def setChildren(self, ch):
		self._extra = ch


	def getChildren(self):
		assert not self.isLeaf()
		return self._extra


	def __str__(self):
		if self._extra is None:
			return "<QTNode %s>"%(self.rect(),)
		if self.isLeaf():
			return "<QTNode %s, ID=%s>"%(self.rect(),self._extra)
		else:
			return "<QTNode %s, ch=%s>"%(self.rect(),len(self._extra))


	def distanceTo(self, other):
		dx = (other.x1+other.x2) - (self.x1+self.x2)
		dy = (other.y1+other.y2) - (self.y1+self.y2)

		return math.sqrt(dx*dx+dy*dy)*0.5


	def hasPoint(self, point):
		return (point[0]>=self.x1 and point[0]<=self.x2 and
				point[1]>=self.y1 and point[1]<=self.y2)


	def setAdjacencies(self, adj):
		self._adj = adj


	def getAdjacencies(self):
		return self._adj


	def getCenter(self):
		return (self.x1+self.x2)*0.5, (self.y1+self.y2)*0.5



class QTree:
	def __init__(self, map=None, max_depth=6):
		self._root_node = None
		if map:
			self.compute(map, max_depth)


	def compute(self, map, max_depth):
		self._root_node = None
		self._map = map
		self._max_depth = max_depth
		self._computeNodes()
		self._buildGraph()


	def getContainingNode(self, map_pos):
	   return self._getContainingNode(map_pos, self._root_node)


	def getAdjacencies(self, area_id):
		return self._leaf_nodes[area_id].getAdjacencies()


	def printTouchingNodes(self, leaf_node_id):
		print "For region: ",self._leaf_nodes[leaf_node_id]
		ta = self.getTouchingNodes(self._root_node, self._leaf_nodes[leaf_node_id])
		for t in ta:
			print "	%s through %s"%(self._leaf_nodes[t[0]], t[1])


	def printTree(self, area, indent=0):
		print " "*indent, area
		try:
			children = area.getChildren()
		except:
			return
		for c in children:
			self.printTree(c, indent+2)


	def getNode(self, area_id):
		return self._leaf_nodes[area_id]

	#-- helper methods


	def _computeNodes(self):
		self._leaf_nodes = []
		self._root_node = QTreeNode(0.0,0.0,self._map.width-1,self._map.height-1)
		self._split(self._root_node, self._max_depth)


	def _buildGraph(self):
		self._adj = {}

		for area in self._leaf_nodes:
			ta = self.getTouchingNodes(self._root_node, area) # this is rather expensive. So we cache it
			area.setAdjacencies(ta)



	# returns a list of (leaf_node_id, portal)
	def getTouchingNodes(self, node, area):
		if self.intersects(area, node):
			if node.isLeaf():
				portal = self.getPortal(area, node)
				if portal is not None:
					return {node.getLeafId():portal}
			else:
				touching = {}
				for child in node.getChildren():
					touching.update(self.getTouchingNodes(child, area))
				return touching

		return {}


	def intersects(self, a1, a2):
		if a1.x1 > a2.x2: return False
		if a2.x1 > a1.x2: return False
		if a1.y1 > a2.y2: return False
		if a2.y1 > a1.y2: return False

		return True


	def touches(self, a1, a2):
		code = 0
		if a1.x1 == a2.x2: code |= 1
		if a2.x1 == a1.x2: code |= 1+4
		if a1.y1 == a2.y2: code |= 2+8
		if a2.y1 == a1.y2: code |= 2+16

		if (code & 3) == 3: return False # diagonal adjacent

		return code >> 2


	# areas must be touching. Otherwise it's undefined
	def getPortal(self, a1, a2):
		# vertical portal
		x0=x1=y0=y1=0
		if a1.x1 == a2.x2:
			x0 = x1 = a1.x1
			y0 = max(a1.y1,a2.y1)
			y1 = min(a1.y2,a2.y2)
		elif a2.x1 == a1.x2:
			x0 = x1 = a2.x1
			y0 = max(a1.y1,a2.y1)
			y1 = min(a1.y2,a2.y2)
		# horizontal portal
		elif a1.y1 == a2.y2:
			y0 = y1 = a1.y1
			x0 = max(a1.x1,a2.x1)
			x1 = min(a1.x2,a2.x2)
		elif a2.y1 == a1.y2:
			y0 = y1 = a2.y1
			x0 = max(a1.x1,a2.x1)
			x1 = min(a1.x2,a2.x2)

		if x0==x1 and y0==y1: return None
		return x0,y0,x1,y1

	#-- internal methods


	def _getContainingNode(self, pos, root_node):
		if root_node.hasPoint(pos):
			leaf_id = root_node.getLeafId()
			if leaf_id is not None:
				return root_node
			else:
				for c in root_node.getChildren():
					r = self._getContainingNode(pos, c)
					if r is not None:
						return r
		return None



	def _split(self, area, levels_to_go):

		obs = self._map.getObstruction(area)

		if obs == 0: # not obstructed
			area.setLeafId(len(self._leaf_nodes)) # number of leaf
			self._leaf_nodes.append(area)
			return True

		if levels_to_go==0 or obs == 2: # no more levels or fully obstructed
			return False

		x0,y0,x1,y1 = area.rect()
		xm = (x0+x1)/2
		ym = (y0+y1)/2

		levels_to_go -= 1

		sub_areas = [
			QTreeNode(x0,y0,xm,ym),
			QTreeNode(xm,y0,x1,ym),
			QTreeNode(x0,ym,xm,y1),
			QTreeNode(xm,ym,x1,y1)
		]

		children = None

		for a in sub_areas:
			h = self._split(a, levels_to_go)
			if h:
				try:
					children.append(a)
				except:
					children = [a]

		area.setChildren(children)

		return bool(children)




	def saveNodesImage(self, filename, hilights=None, waypoints=None, backdrop=None):

		img = Image.new("RGB", (self._map.width, self._map.height))
		draw = ImageDraw.Draw(img)

		for r in self._leaf_nodes:
			draw.rectangle(r.rect(),outline=(64,0,0))

		if hilights:
			points=[]
			for hl,portal in hilights:
				r = self.getNode(hl)
				points.append(r.getCenter())

				draw.rectangle(r.rect(),fill=(0,0,128),outline=(128,0,0))

			draw.line(points, fill=(255,255,0))

			for hl,portal in hilights:
				if portal:
					x0,y0,x1,y1 =  map(int,portal)

					draw.line(((x0,y0),(x1,y1)),fill=(0,255,0))

		if waypoints:
			waypoints =[(w[0],w[1]) for w in waypoints]
			draw.point(waypoints,fill=(255,0,255))

			x,y = waypoints[0]
			draw.ellipse((x-1,y-1,x+1,y+1), fill=(128,128,128))

		img.save(filename)


