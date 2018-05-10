from abc import ABCMeta, abstractmethod
from LawError import *

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

	# 文書構造が正しいかのチェック
	def structure_check(self):
		self.parent_check()
		self.brothers_check()
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

	# 子孫をすべてイテレート
	def iter_descendants(self, error_ok=False):
		for child in self.iter_children(error_ok=False):
			#print(self, "->", child)
			yield child
			yield from child.iter_descendants(error_ok=False)

	# 文を獲得
	def get_sentences(self):
		return []

	@abstractmethod
	def _iter_possible_children(self):
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

