
class FreeBlock:
	def __init__(self, page, start, size):
		self.page = page
		self.start = start
		self.size = size

	@classmethod
	def fromAllocated(cls, ab):
		return cls(ab._page, ab._start, ab._size)

	def reduceHead(self, delta):
		self.size -= delta
		self.start += delta

	def expandTail(self, delta):
		self.size += delta

	def __str__(self):
		return "<Free block [%s:%s-%s] of size %s>"%(self.page, self.start, self.start+self.size, self.size)


class AllocatedBlock:
	def  __init__(self, manager, page_id, start, size, id):
		self._manager = manager
		self._page = page_id
		self._start = start
		self._size = size
		self._id = id

	def free(self):
		self._manager.free(self)

	def __del__(self):
		self._manager.free(self)


	@property
	def start(self):
		return self._start

	@property
	def size(self):
		return self._size

	@property
	def page_data(self):
		return self._manager.getPageData(self._page)

	def __str__(self):
		return "<Allocated block %s [%s:%s-%s] of size %s>"%(self._id, self._page, self._start, self._start+self._size, self._size)


class MemoryManager(object):
	def __init__(self):
		self._allocated_blocks = {} # map of allocated blocks by ID
		self._free_blocks = [] # list of free blocks
		self._pages = []
		self._free_blocks_by_address = False
		self._current_id = 1


	def _allocNewPage(self,min_size):
		raise RuntimeError("Must subclass from MemoryManager")
		# must return the page data, and the actual size of the page
		#return None,min_size


	def _newId(self):
		self._current_id+=1
		return self._current_id-1

	def getPageData(self, page_id):
		return self._pages[page_id]

	def free(self, allocated_block):
		id = allocated_block._id
		try:
			b = self._allocated_blocks[id]
		except:
			return

		if b is None: return

		self._free_blocks.append(FreeBlock.fromAllocated(b))
		self._free_blocks.sort(key=lambda block:(block.page, block.start))
		del self._allocated_blocks[id]
		# see if we can merge blocks

		updated_blocks_list = []

		last_fb = self._free_blocks[0]
		merged = True
		for i in xrange(1, len(self._free_blocks)):
			merged = False
			fb = self._free_blocks[i]

			if last_fb.page == fb.page and last_fb.start+last_fb.size == fb.start:
				last_fb.expandTail(fb.size)
				merged = True
				continue

			updated_blocks_list.append(last_fb)

			last_fb = fb

		if merged:
			updated_blocks_list.append(last_fb)


		self._free_blocks = updated_blocks_list
		self._free_blocks_by_address = True


	def dump(self):
		print "dump ---------------"
		print "Free blocks:"
		for bk in self._free_blocks:
			print bk
		print "Allocated blocks:"
		for bk in self._allocated_blocks.values():
			print bk
		print "--------------------"


	def alloc(self, size):
		if self._free_blocks_by_address:
			self._free_blocks.sort(key=lambda block:block.size)
			self._free_blocks_by_address = False

		lo = 0
		tot = hi = len(self._free_blocks)

		while lo < hi:
			mid = (lo+hi)//2
			if self._free_blocks[mid].size < size: lo = mid+1
			else: hi = mid

		if lo == tot: # no free block large enough. Request another page
			#print "Not enough space, requesting a new page"
			page_num = len(self._pages)

			d_s = self._allocNewPage(size)

			if d_s:
				page_data, page_size = d_s
				self._free_blocks.append(FreeBlock(page_num, 0, page_size))

				self._pages.append(page_data)
				tot = len(self._free_blocks)

		if lo == tot:
			raise MemoryError("No memory to allocate another page")

		fb = self._free_blocks[lo]

		block_id = self._newId()

		block = AllocatedBlock(self, fb.page, fb.start, size, block_id)

		if fb.size == size:
			del self._free_blocks[lo] # block completely used
		else:
			self._free_blocks[lo].reduceHead(size)

		self._allocated_blocks[block_id] = block

		return block

