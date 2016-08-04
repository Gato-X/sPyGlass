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


DEBUG_save_planning_images = True


try:
	import Image, ImageDraw
except:
	from PIL import Image, ImageDraw

#from mathtools import *
from sortedcontainers.sorteddict import SortedList



# a graph must implement the folowing method:
#    getNode(id)
# which must return a node (typically the same class as src_node, dest_node, etc..)
# each node, must implement the followint methods:
#    getAdjacencies()
#    distanceTo()
#    getLeafId()


class Router:
	def __init__(self, graph):
		self._graph = graph

	# compute de minimum distances from a given node to a list of nodes
	def computeDistances(self, src_node, dest_node_list): # uses Dijkstra

		g = self._graph

		dest_node_ids = set([a.getLeafId() if a is not None else -1 for a in dest_nodes ])

		if src_node is None or not any(dest_nodes):
			return [None]*len(dest_list)

		search_front_queue = SortedList()

		search_front_queue.add((0,src_node.getLeafId()))
		search_front_p = {}
		target_distances = {}
		frozen = set()

		loops = 0

		while search_front_queue:
			loops += 1
			d,a = search_front_queue.pop(0)
			if a in frozen: # ignore duplicates
				continue

			# target found
			if a == dest_node_ids:
				target_distances[a] = d
				dest_node_ids.remove(a)
				if len(dest_node_ids) == 0:
					break

			frozen.add(a)

			node = g.getNode(a)

			for adj in node.getAdjacencies().keys():
				if adj in frozen: # don't try to even check nodes that have been already frozen
					continue

				new_d = d + node.distanceTo(g.getNode(adj))

				# route to adj through a is longer than what we already had. Dismiss
				if adj in search_front_p and new_d > search_front_p[adj]:
					continue

				search_front_p[adj] = new_d
				# this might add duplicate adj items (ideally we would delete any previous insertion)
				# because we can't easily erase from the queue.
				search_front_queue.add((new_d, adj))

		distances = []
		for t in dest_node_ids:
			try:
				distances.append(target_distances[t])
			except:
				distances.append(None)

		return distances



	def computeRoute(self, src_node, dest_node, use_a_star=True): # uses A*
		g = self._graph

		if src_node is None or dest_node is None:
			return None

		src_node_id = src_node.getLeafId()
		dest_node_id = dest_node.getLeafId()

		search_front_queue = SortedList()
		h = 0#src_node.distanceTo(dest_node) # A* heuristic distance value

		search_front_queue.add((h,h,src_node_id))
		search_front_p = {}
		frozen = set()

		loops = 0

		while search_front_queue:
			loops += 1
			d,old_h,a = search_front_queue.pop(0)
			if a in frozen: # ignore duplicates
				continue

			# target found
			if a == dest_node_id:
				break

			frozen.add(a)

			node = g.getNode(a)

			for adj, portal in node.getAdjacencies().iteritems():
				if adj in frozen: # don't try to even check nodes that have been already frozen
					continue

				dg = node.distanceTo(g.getNode(adj))

				new_h = node.distanceTo(dest_node)

				#new_d = (d+dg)-old_h+new_h

				new_d = d + dg


				# route to adj through a is longer than what we already had. Dismiss
				if adj in search_front_p and new_d > search_front_p[adj][0]:
					continue

				search_front_p[adj] = (new_d, a, portal)

				# this might add duplicate adj items (ideally we would delete any previous insertion)
				# because we can't easily erase from the queue.
				search_front_queue.add((new_d, new_h, adj))

		print loops

		p = dest_node_id
		route = [(p,None)] # stores tuples: node_number, exit portal
		while p in search_front_p:
			_,prev,portal = search_front_p[p]
			route.append((prev, portal))
			p = prev

		route.reverse()

		return route


	def getWaypointCalculator(self, source, dest, randomize = True):
		route = self.computeRoute(source, dest)
		return self._routeWaypointCalculator(source, dest, route, randomize)


	# smooth out the path
	def _routeWaypointCalculator(self, src, dest, route, randomize=True):
		yield src
		pos = src[0:2]

		next_node = next_portal = next_node_center = None

		for i in xrange(0, len(route)):

			portal = next_portal
			node_center = next_node_center

			next_a_num,next_portal = route[i]
			next_node = self.getNode(next_a_num)
			next_node_center = next_node.getCenter()

			if i == 0: continue

			x,y = pos

			line = (x,y,next_node_center[0], next_node_center[1])
			pt, st, within = getSegmentIntersection(portal, line, only_in_segment=False)

			# see if we can go from where we are to the center of the next node
			# in a straight line


			if within:# we advanced to the next node in a straight line towards its center
				pos = pt
				yield pt
			else:# we advance towards the exit portal, with a little curve
				s = st[0]
				if s<0.1: s = 0.1
				elif s>0.9: s = 0.9
				pos = new_x,new_y = (portal[2]-portal[0])*s + portal[0], (portal[3]-portal[1])*s + portal[1]

				# midpoint between portal exits
				mx,my= (new_x+x)*0.5, (new_y+y)*0.5

				#push it a little bit towards the node center

				yield (node_center[0]-mx)*0.1+mx, (node_center[1]-my)*0.1+my

				yield pos

		if len(route)<2:
			# so we have at least three waypoints
			yield (src[0]+dest[0])*0.5, (src[1]+dest[1])*0.5


		yield dest


import Queue
import threading
import weakref
class RouterBatchProcessor:
	def __init__(self, router):
		self._router = router
		self._to_do = Queue.Queue()
		self._done = Queue.Queue()

		self._do_end = False

		self._thread = threading.Thread(target = self._worker)
		self._thread.start()


	def requestJob(self, src, dest, method, obj=None):
		self._to_do.put((src, dest, (method, weakref.ref(obj) if obj else None)))


	def dispatch(self): # dispatch only one (will call this every frame)
		try:
			cb, result = self._done.get(False)
			method, object = cb
			if object:
				o = object()
				if o is not None:
					method(o,result)
			else:
				method(result)
		except Queue.Empty:
			pass


	def finish(self):
		self._do_end = True
		self._thread.join()


	def _worker(self):
		while not self._do_end:
			try:
				src, dest, cb = self._to_do.get(True,0.5)
				wp = self._router.getWaypointCalculator(src, dest)
				self._done.put((cb, wp))

			except Queue.Empty:
				pass


if __name__=="__main__":
	from quadtree import QTree, QTreeMap
	import random
	import numpy as N

	w,h = (512,512)

	img = Image.new("L", (w,h), color=255)
	draw = ImageDraw.Draw(img)

	
	random.seed(102)

	for i in xrange(8):
		x0 = random.randint(-10,w-10)
		y0 = random.randint(-10,h-10)
		x1 = random.randint(10,200)+x0
		y1 = random.randint(10,200)+y0
		
		draw.ellipse((x0,y0,x1,y1), fill=0)

	arr = N.array(img.getdata()).reshape((w,h))

	qt = QTree(QTreeMap(arr))

	rt = Router(qt)

	n1 = qt.getContainingNode((10,10))
	n2 = qt.getContainingNode((w-10,h-10))

	print n1
	print n2

	route = rt.computeRoute(n1,n2)

	route_points = map(lambda pt:qt.getNode(pt[0]).getCenter(), route)
	qt.saveNodesImage("test2.png", hilights= route )

	img.save("test.png")

