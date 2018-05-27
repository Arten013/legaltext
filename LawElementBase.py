from abc import ABCMeta, abstractmethod
from LawError import *
import asyncio
import queue

# 法令テキストの要素クラスのベース
class LawElementBase(metaclass=ABCMeta):
	def __init__(self, lawdata, parent):
		self.parent = parent
		self.lawdata = lawdata
		self.etypes = self.lawdata.etypes
		self.child_etype = None
		self.id = None
		self._num = None
		self._child = None

	@abstractmethod
	def inheritance(self):
		#self.num = self.get_number()
		self.texts = []

	@property
	def num(self):
		if self._num is None:
			self._num = self.get_number()
		return self._num

	@num.setter
	def num(self, x):
		self._num = x

	@property
	def etype(self):
		return self.__class__.__name__

	def __str__(self):
		return str(self.parent)+str(self.get_number())

	def is_leaf(self, error_ok):
		if len(list(self.iter_children(error_ok))) == 0:
			return True
		return False

	def is_text(self):
		return False

	# 文書構造が正しいかのチェック
	def structure_check(self):
		self.parent_check()
		self.brothers_check()
		self.num
		#self.number_check()
		return True

	PARENT_CANDIDATES = ()
	def parent_check(self):
		if not isinstance(self.parent, self.PARENT_CANDIDATES):
			raise HieralchyError(self.lawdata, "invalid hieralchy "+self.parent.__class__.__name__ + " -> " + self.__class__.__name__)

	def brothers_check(self):
		if self.parent is None:
			return
		if self.child_etype is None:
			return
		if self.__class__.__name__ != self.parent.child_etype:
			raise HieralchyError(self.lawdata, "different type elements in the same layer: {0} and {1}".format(self.__class__.__name__, self.parent.child_etype))

	def number_check(self):
		if self.parent is None:
			return True

		l = []
		for ce in self.parent.iter_children():
			n = ce.get_number()
			if n.num in l:
				raise HieralchyError(self.lawdata, "element number duplication: {}".format(str(n)))
			l += [n.num]
		return True

	# 子をイテレート
	def iter_children(self, error_ok=False):
		if self._child is not None:
			yield from self._child
		self._child = []
		for ce in self._iter_possible_children():
			if self._check_child(ce, error_ok):
				yield ce
				self._child.append(ce)
				self.child_etype = ce.__class__.__name__
		raise StopIteration()

	# 子をイテレート
	async def async_iter_children(self, error_ok=False):
		if self._child is not None:
			for ce in self._child:
				yield ce
			return
		self._child = []
		async for ce in self._async_iter_possible_children():
			if self._check_child(ce, error_ok):
				yield ce
				self._child.append(ce)
				self.child_etype = ce.__class__.__name__
		return

	# 子孫をすべてイテレート
	def iter_descendants(self, error_ok=False, bfs=False):
		if bfs is True:
			q = queue.Queue()
			for child in self.iter_children(error_ok=error_ok):
				q.put(child)
			while not q.is_empty():
				yield q.get()
				for child in e.iter_children(error_ok=error_ok):
					q.put(child)
			q.join()
		else:
			for child in self.iter_children(error_ok=error_ok):
				#print(self, "->", child)
				yield child
				if not child.is_text():
					yield from child.iter_descendants(error_ok=error_ok, bfs=False)

	# 子孫をすべてイテレート
	async def async_iter_descendants(self, error_ok=False, bfs=False):
		if bfs is True:
			q = asyncio.Queue()
			async for child in self.async_iter_children(error_ok=error_ok):
				await q.put(child)
			while not q.is_empty():
				yield await q.get()
				async for child in e.async_iter_children(error_ok=error_ok):
					await q.put(child)
			await q.join()
		else:
			async for child in self.async_iter_children(error_ok=False):
				#print(self, "->", child)
				yield child
				if not child.is_text():
					async for child in child.async_iter_descendants(error_ok=False, bfs=False):
						yield child

	# 子孫をすべてイテレート
	async def async_iter_descendants_by_hierarchy(self, error_ok=False):
		children = [child async for child in self.async_iter_children(error_ok=error_ok)]
		while len(children) > 0:
			yield children
			next_children = []
			for e in children:
				next_children.extend([child async for child in e.async_iter_children(error_ok=error_ok)])
			children = next_children

	async def async_iter_sentence(self):
		async for ce in self.async_iter_descendants():
			yield ce.get_sentences()


	# 文を獲得
	def get_sentences(self):
		return []

	@abstractmethod
	def _iter_possible_children(self):
		pass

	@abstractmethod
	def _async_iter_possible_children(self):
		pass

	def _check_child(self, e, error_ok):
		if not e.__class__.__name__ in self.etypes:
			return False
		if error_ok:
			return True
		return e.structure_check()

	@abstractmethod
	def get_number(self):
		pass

